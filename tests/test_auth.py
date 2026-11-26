"""
tests/test_auth.py
==================
Automated tests for Gmail + University Name Login and Verification.

Run from the project folder:
    python -m pytest tests -v
"""

import os
import re
import smtplib
import sqlite3
from datetime import date, timedelta

import pytest

import database
from app import create_app, load_env_file
from modules import assessment as am
from modules import auth as auth_module


@pytest.fixture(autouse=True)
def clean_smtp_env(monkeypatch):
    """Ensure host SMTP env vars do not affect tests unless explicitly set."""
    for var in (
        "GMAIL_SENDER",
        "GMAIL_APP_PASSWORD",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "MAIL_USERNAME",
        "MAIL_PASSWORD",
        "SMTP_HOST",
        "SMTP_PORT",
    ):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_auth.db")


@pytest.fixture
def app(db_path):
    return create_app({"TESTING": True, "DATABASE": db_path})


@pytest.fixture
def client(app):
    return app.test_client()


def rows(db_path, sql, params=()):
    return database.fetch_all(sql, params, db_path)


# ---------------------------------------------------------------------------
# 1. Input validation
# ---------------------------------------------------------------------------
class TestLoginValidation:
    def test_valid_gmail_and_university_accepted(self):
        data, errors = auth_module.validate_login_submission({
            "gmail": "  Asha.Kumar@GMAIL.com ",
            "university_name": "  Anna   University  ",
            "full_name": " Asha Kumar ",
            "verifier_email": "placement@annauniv.edu",
        })
        assert errors == {}
        assert data == {
            "full_name": "Asha Kumar",
            "gmail": "asha.kumar@gmail.com",
            "university_name": "Anna University",
            "verifier_email": "placement@annauniv.edu",
        }

    def test_blank_full_name_is_derived_from_gmail(self):
        data, errors = auth_module.validate_login_submission({
            "gmail": "raj.verma99@gmail.com",
            "university_name": "IIT Madras",
        })
        assert errors == {}
        assert data["full_name"] == "Raj Verma99"

    @pytest.mark.parametrize("bad_gmail", [
        "",
        "   ",
        "not-an-email",
        "asha@yahoo.com",
        "asha@college.edu",
        "asha@gmail.org",
        "@gmail.com",
        "asha kumar@gmail.com",
    ])
    def test_non_gmail_addresses_are_rejected(self, bad_gmail):
        _, errors = auth_module.validate_login_submission({
            "gmail": bad_gmail,
            "university_name": "Anna University",
        })
        assert "gmail" in errors

    @pytest.mark.parametrize("bad_uni", ["", "   ", "AB", "U" * 151])
    def test_invalid_university_name_is_rejected(self, bad_uni):
        _, errors = auth_module.validate_login_submission({
            "gmail": "asha@gmail.com",
            "university_name": bad_uni,
        })
        assert "university_name" in errors

    def test_invalid_optional_verifier_email_is_rejected(self):
        _, errors = auth_module.validate_login_submission({
            "gmail": "asha@gmail.com",
            "university_name": "Anna University",
            "verifier_email": "bad-verifier-email",
        })
        assert "verifier_email" in errors


# ---------------------------------------------------------------------------
# 2. Email delivery (local preview vs real Gmail SMTP mock & fallback)
# ---------------------------------------------------------------------------
class TestVerificationDelivery:
    def test_create_login_generates_pending_record_and_preview_without_smtp(self, app, db_path):
        with app.test_request_context():
            outcome = auth_module.create_or_update_login(
                {
                    "full_name": "Asha Kumar",
                    "gmail": "asha@gmail.com",
                    "university_name": "Visvesvaraya Technological University",
                    "verifier_email": "registrar@vtu.ac.in",
                },
                db_path=db_path,
                verify_url_builder=lambda tok: f"http://localhost/verify?token={tok}",
            )

        user = outcome["user"]
        assert outcome["needs_verification"] is True
        assert outcome["delivery_error"] is None
        assert user["status"] == "pending"
        assert user["delivery_mode"] == "local_preview"
        assert user["verification_sent_to"] == "asha@gmail.com, registrar@vtu.ac.in"
        assert re.fullmatch(r"\d{6}", user["verification_code"])
        assert "Visvesvaraya Technological University" in outcome["email_preview"]["subject"]
        assert "Visvesvaraya Technological University" in outcome["email_preview"]["body"]
        assert "asha@gmail.com" in outcome["email_preview"]["body"]

    def test_gmail_smtp_used_when_configured(self, app, db_path, monkeypatch):
        monkeypatch.setenv("GMAIL_SENDER", "noreply@gmail.com")
        monkeypatch.setenv("GMAIL_APP_PASSWORD", "abcd efgh ijkl mnop")

        sent_messages = []

        class DummySMTP:
            def __init__(self, host, port, timeout=10):
                self.host = host
                self.port = port
                self.logged_in = None

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def ehlo(self):
                pass

            def starttls(self):
                pass

            def login(self, user, pwd):
                self.logged_in = (user, pwd)

            def send_message(self, msg):
                sent_messages.append((self.host, self.port, self.logged_in, msg))

        monkeypatch.setattr(smtplib, "SMTP", DummySMTP)

        with app.test_request_context():
            outcome = auth_module.create_or_update_login(
                {
                    "full_name": "Asha Kumar",
                    "gmail": "asha@gmail.com",
                    "university_name": "SRM Institute of Science and Technology",
                    "verifier_email": "verify@srmist.edu.in",
                },
                db_path=db_path,
                verify_url_builder=lambda tok: f"http://localhost/verify?token={tok}",
            )

        assert len(sent_messages) == 1
        host, port, creds, msg = sent_messages[0]
        assert (host, port) == ("smtp.gmail.com", 587)
        assert creds == ("noreply@gmail.com", "abcdefghijklmnop")
        assert msg["To"] == "asha@gmail.com, verify@srmist.edu.in"
        assert "SRM Institute of Science and Technology" in msg["Subject"]
        assert "SRM Institute of Science and Technology" in msg.get_content()
        assert outcome["user"]["delivery_mode"] == "gmail_smtp"
        assert outcome["delivery_error"] is None

    def test_placeholder_env_credentials_do_not_trigger_smtp(self, client, monkeypatch):
        monkeypatch.setenv("GMAIL_SENDER", "youraccount@gmail.com")
        monkeypatch.setenv("GMAIL_APP_PASSWORD", "xxxx xxxx xxxx xxxx")
        cfg = auth_module.get_smtp_config()
        assert cfg["configured"] is False
        assert cfg["placeholder"] is True

        html = client.get("/login").get_data(as_text=True)
        assert "Update .env Credentials" in html
        assert "placeholder values" in html

    def test_smtp_failure_falls_back_gracefully_to_local_preview(self, app, db_path, monkeypatch):
        monkeypatch.setenv("GMAIL_SENDER", "noreply@gmail.com")
        monkeypatch.setenv("GMAIL_APP_PASSWORD", "bad-secret")

        class FailingSMTP:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                raise smtplib.SMTPAuthenticationError(535, b"Invalid credentials")

            def __exit__(self, *args):
                return False

        monkeypatch.setattr(smtplib, "SMTP", FailingSMTP)

        with app.test_request_context():
            outcome = auth_module.create_or_update_login(
                {
                    "full_name": "Asha",
                    "gmail": "asha@gmail.com",
                    "university_name": "Anna University",
                    "verifier_email": None,
                },
                db_path=db_path,
                verify_url_builder=lambda tok: f"http://localhost/verify?token={tok}",
            )

        assert outcome["user"]["delivery_mode"] == "local_preview"
        assert outcome["user"]["status"] == "pending"
        assert "Invalid credentials" in outcome["delivery_error"]


# ---------------------------------------------------------------------------
# 3. Web routes & Assessment / Planner integration
# ---------------------------------------------------------------------------
class TestAuthRoutesAndIntegration:
    def test_login_page_renders_and_rejects_non_gmail(self, client):
        html = client.get("/login").get_data(as_text=True)
        assert "Gmail Address" in html
        assert "University Name" in html

        resp = client.post("/login", data={
            "gmail": "student@yahoo.com",
            "university_name": "Anna University",
        })
        assert resp.status_code == 400
        assert "ending in @gmail.com" in resp.get_data(as_text=True)

    def test_otp_verification_flow_marks_user_verified(self, client, db_path):
        resp = client.post("/login", data={
            "full_name": "Asha Kumar",
            "gmail": "asha@gmail.com",
            "university_name": "Anna University",
        }, follow_redirects=True)
        html = resp.get_data(as_text=True)
        assert resp.status_code == 200
        assert "Pending Verification" in html
        assert "Anna University" in html
        assert "Verification Email Preview" in html

        saved = rows(db_path, "SELECT * FROM user_logins WHERE gmail = ?", ("asha@gmail.com",))
        assert len(saved) == 1
        otp = saved[0]["verification_code"]
        assert otp in html

        # Wrong OTP is rejected
        bad = client.post("/verify", data={"gmail": "asha@gmail.com", "otp": "000000"})
        assert bad.status_code == 400
        assert "Incorrect verification code" in bad.get_data(as_text=True)

        # Correct OTP verifies and clears single-use token/code
        ok = client.post("/verify", data={"gmail": "asha@gmail.com", "otp": otp}, follow_redirects=True)
        ok_html = ok.get_data(as_text=True)
        assert ok.status_code == 200
        assert "Account Verified" in ok_html
        assert "Anna University" in ok_html

        verified_row = rows(db_path, "SELECT * FROM user_logins WHERE gmail = ?", ("asha@gmail.com",))[0]
        assert verified_row["status"] == "verified"
        assert verified_row["verification_code"] is None
        assert verified_row["verification_token"] is None

    def test_link_verification_and_single_use_token(self, client, db_path):
        client.post("/login", data={
            "gmail": "kiran@gmail.com",
            "university_name": "University of Mumbai",
        })
        token = rows(db_path, "SELECT verification_token FROM user_logins WHERE gmail = ?",
                     ("kiran@gmail.com",))[0]["verification_token"]

        resp = client.get(f"/verify?token={token}", follow_redirects=True)
        assert resp.status_code == 200
        assert "Account Verified" in resp.get_data(as_text=True)
        assert "University of Mumbai" in resp.get_data(as_text=True)

        # Replaying the same verification link fails
        replay = client.get(f"/verify?token={token}")
        assert replay.status_code == 400
        assert "invalid or has already been used" in replay.get_data(as_text=True)

    def test_resend_rotates_code_and_changing_university_retriggers_verification(self, client, db_path):
        client.post("/login", data={
            "gmail": "neha@gmail.com",
            "university_name": "Delhi University",
        })
        first = rows(db_path, "SELECT verification_code, verification_token FROM user_logins")[0]

        client.post("/login/resend", data={"gmail": "neha@gmail.com"})
        second = rows(db_path, "SELECT verification_code, verification_token FROM user_logins")[0]
        assert second["verification_token"] != first["verification_token"]

        # Verify with the rotated token
        client.get(f"/verify?token={second['verification_token']}")
        assert rows(db_path, "SELECT status FROM user_logins")[0]["status"] == "verified"

        # Logging in with a new university resets status to pending & sends new university
        resp = client.post("/login", data={
            "gmail": "neha@gmail.com",
            "university_name": "NIT Trichy",
        }, follow_redirects=True)
        assert "Pending Verification" in resp.get_data(as_text=True)
        assert "NIT Trichy" in resp.get_data(as_text=True)
        assert rows(db_path, "SELECT status FROM user_logins")[0]["status"] == "pending"

    def test_logged_in_user_prefills_assessment_links_planner_and_logs_out(self, client, db_path):
        # Log in & verify
        client.post("/login", data={
            "full_name": "Asha Kumar",
            "gmail": "asha.uni@gmail.com",
            "university_name": "VIT Vellore",
        })
        token = rows(db_path, "SELECT verification_token FROM user_logins")[0]["verification_token"]
        client.get(f"/verify?token={token}")

        # Assessment form pre-fills Full Name + Gmail and shows university badge
        assess_html = client.get("/assessment").get_data(as_text=True)
        assert 'value="Asha Kumar"' in assess_html
        assert 'value="asha.uni@gmail.com"' in assess_html
        assert "VIT Vellore" in assess_html
        assert "University Verified" in assess_html

        # Submit assessment (Set 1, which is served on first GET /assessment)
        questions, _ = am.get_questions_for_set(1)
        form = {
            "name": "Asha Kumar",
            "email": "asha.uni@gmail.com",
            "branch": "CSE",
            "year": "4",
            "question_set": "1",
        }
        for q in questions:
            form["q_" + q["id"]] = q["answer"]
        client.post("/assessment", data=form)

        # Student record linked back to user_logins & Planner picks them up
        login_row = rows(db_path, "SELECT student_id FROM user_logins WHERE gmail = ?", ("asha.uni@gmail.com",))[0]
        assert login_row["student_id"] == 1

        planner_html = client.get("/planner").get_data(as_text=True)
        assert "VIT Vellore" in planner_html
        assert "Verified" in planner_html

        # Logout clears navbar session state without deleting DB records
        out = client.post("/logout", follow_redirects=True)
        out_html = out.get_data(as_text=True)
        assert "signed out" in out_html.lower()
        assert "asha.uni@gmail.com" not in out_html
        assert len(rows(db_path, "SELECT * FROM user_logins")) == 1

    def test_xss_and_sql_injection_are_handled_safely(self, client, db_path):
        evil_uni = "<script>alert(1)</script>'; DROP TABLE user_logins;--"
        resp = client.post("/login", data={
            "full_name": "<img src=x onerror=alert(2)>",
            "gmail": "safe.user@gmail.com",
            "university_name": evil_uni,
        }, follow_redirects=True)
        html = resp.get_data(as_text=True)
        assert resp.status_code == 200
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
        assert set(database.list_tables(db_path)) == set(database.TABLE_NAMES)


# ---------------------------------------------------------------------------
# 4. Local .env loading
# ---------------------------------------------------------------------------
class TestEnvFileLoader:
    def test_load_env_file_parses_values_without_overwriting_existing(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "# Comment line\n"
            "\n"
            'GMAIL_SENDER="sender@gmail.com"\n'
            "export GMAIL_APP_PASSWORD='abcd efgh ijkl mnop'\n"
            "SECRET_KEY=already-in-shell-should-win\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("SECRET_KEY", "shell-secret")

        loaded = load_env_file(str(env_file))
        assert loaded["GMAIL_SENDER"] == "sender@gmail.com"
        assert os.environ["GMAIL_SENDER"] == "sender@gmail.com"
        assert os.environ["GMAIL_APP_PASSWORD"] == "abcd efgh ijkl mnop"
        # Existing shell environment variable must not be overwritten
        assert os.environ["SECRET_KEY"] == "shell-secret"

    def test_load_env_file_ignores_missing_file(self, tmp_path):
        assert load_env_file(str(tmp_path / "does_not_exist.env")) == {}


# ---------------------------------------------------------------------------
# 5. Top-Right Profile Icon, User Profile & Consistency Streak Pop-up Effects
# ---------------------------------------------------------------------------
class TestProfileAndStreakSystem:
    def test_evaluate_streak_transitions(self):
        d1 = date(2026, 11, 20)
        d2 = date(2026, 11, 21)
        d4 = date(2026, 11, 23)  # skipped 2026-11-22

        # First-ever login
        fields1, ev1 = auth_module.evaluate_streak_transition({}, today_date=d1)
        assert fields1["current_streak"] == 1
        assert fields1["best_streak"] == 1
        assert fields1["total_login_days"] == 1
        assert ev1["kind"] == "started"

        # Same-day repeat does not double increment
        fields_same, ev_same = auth_module.evaluate_streak_transition(fields1, today_date=d1)
        assert fields_same["current_streak"] == 1
        assert fields_same["total_login_days"] == 1
        assert ev_same["kind"] == "same_day"

        # Next day keeps streak & increments
        fields2, ev2 = auth_module.evaluate_streak_transition(fields1, today_date=d2)
        assert fields2["current_streak"] == 2
        assert fields2["best_streak"] == 2
        assert fields2["total_login_days"] == 2
        assert ev2["kind"] == "streak_kept"
        assert ev2["emoji"] == "🔥"

        # Missing a day resets current_streak to 1 while keeping best_streak
        fields4, ev4 = auth_module.evaluate_streak_transition(
            {**fields2, "current_streak": 5, "best_streak": 5},
            today_date=d4,
        )
        assert fields4["current_streak"] == 1
        assert fields4["best_streak"] == 5
        assert fields4["total_login_days"] == 3
        assert ev4["kind"] == "streak_broken"
        assert ev4["emoji"] == "💔"

    def test_first_verification_starts_streak_and_triggers_popup_once(self, client, db_path):
        client.post("/login", data={
            "full_name": "Asha Kumar",
            "gmail": "asha.streak@gmail.com",
            "university_name": "Anna University",
        })
        token = rows(db_path, "SELECT verification_token FROM user_logins WHERE gmail = ?",
                     ("asha.streak@gmail.com",))[0]["verification_token"]

        first_html = client.get(f"/verify?token={token}", follow_redirects=True).get_data(as_text=True)
        assert 'id="streak-popup"' in first_html
        assert 'data-streak-kind="started"' in first_html
        assert "Day 1 Streak Started!" in first_html
        assert "1d Streak" in first_html

        # Refreshing must not replay the one-time pop-up
        second_html = client.get("/login").get_data(as_text=True)
        assert 'id="streak-popup"' not in second_html

    def test_consecutive_day_login_keeps_streak_and_animates_to_streak_bar(self, client, db_path):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        database.execute(
            """
            INSERT INTO user_logins (
                full_name, gmail, university_name, status,
                current_streak, best_streak, last_login_date, total_login_days
            ) VALUES (?, ?, ?, 'verified', 2, 2, ?, 2)
            """,
            ("Asha Kumar", "consistent@gmail.com", "VIT Vellore", yesterday),
            db_path,
        )

        resp = client.post("/login", data={
            "full_name": "Asha Kumar",
            "gmail": "consistent@gmail.com",
            "university_name": "VIT Vellore",
        }, follow_redirects=True)
        html = resp.get_data(as_text=True)
        assert 'id="streak-popup"' in html
        assert 'data-streak-kind="streak_kept"' in html
        assert "3-Day Streak Kept!" in html
        assert "streak-flying-emoji" in html
        assert "3d Streak" in html
        assert "Consistent!" in html

        row = rows(db_path, "SELECT current_streak, best_streak, total_login_days FROM user_logins")[0]
        assert (row["current_streak"], row["best_streak"], row["total_login_days"]) == (3, 3, 3)

    def test_missed_yesterday_resets_streak_and_triggers_broken_effect(self, client, db_path):
        two_days_ago = (date.today() - timedelta(days=2)).isoformat()
        database.execute(
            """
            INSERT INTO user_logins (
                full_name, gmail, university_name, status,
                current_streak, best_streak, last_login_date, total_login_days
            ) VALUES (?, ?, ?, 'verified', 5, 5, ?, 5)
            """,
            ("Ravi Dev", "missed@gmail.com", "IIT Madras", two_days_ago),
            db_path,
        )

        resp = client.post("/login", data={
            "full_name": "Ravi Dev",
            "gmail": "missed@gmail.com",
            "university_name": "IIT Madras",
        }, follow_redirects=True)
        html = resp.get_data(as_text=True)
        assert 'id="streak-popup"' in html
        assert 'data-streak-kind="streak_broken"' in html
        assert "Missed Yesterday! Streak Reset" in html
        assert "💔" in html
        assert "1d Streak" in html

        row = rows(db_path, "SELECT current_streak, best_streak, total_login_days FROM user_logins")[0]
        assert (row["current_streak"], row["best_streak"], row["total_login_days"]) == (1, 5, 6)

    def test_top_right_profile_icon_and_profile_page(self, client, db_path):
        # Guest top-right bar before login
        guest_html = client.get("/").get_data(as_text=True)
        assert 'id="profileMenuBtn"' in guest_html
        assert "Not Logged In" in guest_html
        assert 'id="streak-bar-widget"' in guest_html

        # Empty profile view prompts login
        empty_profile = client.get("/profile").get_data(as_text=True)
        assert "No Active User Logged In" in empty_profile

        # Sign in & verify
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        database.execute(
            """
            INSERT INTO user_logins (
                full_name, gmail, university_name, status,
                current_streak, best_streak, last_login_date, total_login_days
            ) VALUES (?, ?, ?, 'verified', 3, 4, ?, 4)
            """,
            ("Asha Kumar", "asha.profile@gmail.com", "Anna University", yesterday),
            db_path,
        )
        client.post("/login", data={
            "full_name": "Asha Kumar",
            "gmail": "asha.profile@gmail.com",
            "university_name": "Anna University",
        })

        # Top-right profile icon notifies who is logged in on any page (e.g. Home)
        home_html = client.get("/").get_data(as_text=True)
        assert "AK" in home_html
        assert "Asha Kumar" in home_html
        assert "asha.profile@gmail.com" in home_html
        assert "dot-verified" in home_html
        assert "4d Streak" in home_html

        # Profile page shows full identity, streak milestones, and best streak
        profile_html = client.get("/profile").get_data(as_text=True)
        assert "User Profile &amp; Streak" in profile_html
        assert "Asha Kumar" in profile_html
        assert "Anna University" in profile_html
        assert "7-Day Consistency Bar" in profile_html

    def test_init_db_migrates_legacy_user_logins_table(self, tmp_path):
        legacy_db = str(tmp_path / "legacy.db")
        with sqlite3.connect(legacy_db) as conn:
            conn.execute(
                """
                CREATE TABLE user_logins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    full_name TEXT NOT NULL,
                    gmail TEXT NOT NULL UNIQUE,
                    university_name TEXT NOT NULL
                )
                """
            )
        database.init_db(legacy_db)
        cols = {r["name"] for r in database.fetch_all("PRAGMA table_info(user_logins)", db_path=legacy_db)}
        assert {"current_streak", "best_streak", "last_login_date", "total_login_days"} <= cols
