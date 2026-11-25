"""
tests/test_assessment.py
========================
Automated tests for Member 1's Skill Assessment feature.

Run from the project folder:
    python -m pytest tests -v

Every test uses its own temporary SQLite file, so your real placement.db is
never touched.
"""

import sqlite3

import pytest

import database
from app import create_app
from modules import assessment as am


# ---------------------------------------------------------------------------
# Helpers and fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def db_path(tmp_path):
    """A fresh database file for each test."""
    return str(tmp_path / "test_placement.db")


@pytest.fixture
def app(db_path):
    return create_app({"TESTING": True, "DATABASE": db_path})


@pytest.fixture
def client(app):
    return app.test_client()


def valid_form(**overrides):
    """A complete, valid form. Pass keyword arguments to change fields."""
    data = {
        "name": "Asha Kumar",
        "email": "asha@example.com",
        "branch": "CSE",
        "year": "3",
        "rating_aptitude": "1",   # gap 4 -> High
        "rating_coding": "3",     # gap 2 -> Medium
        "rating_technical": "4",  # gap 1 -> Low
        "rating_hr": "5",         # gap 0 -> No gap
    }
    data.update(overrides)
    return data


def rows(db_path, sql, params=()):
    return database.fetch_all(sql, params, db_path)


# ---------------------------------------------------------------------------
# 1. Skill gap calculation  (gap = 5 - rating)
# ---------------------------------------------------------------------------
class TestSkillGapCalculation:
    @pytest.mark.parametrize("rating, expected_gap", [(1, 4), (2, 3), (3, 2), (4, 1), (5, 0)])
    def test_gap_is_five_minus_rating(self, rating, expected_gap):
        assert am.calculate_gap(rating) == expected_gap

    @pytest.mark.parametrize("bad", [0, 6, -1, 99, "3", 3.0, 2.5, None, True, False])
    def test_calculate_gap_rejects_invalid_values(self, bad):
        with pytest.raises(ValueError):
            am.calculate_gap(bad)

    @pytest.mark.parametrize("gap, level", [(4, "High"), (3, "High"), (2, "Medium"),
                                            (1, "Low"), (0, "No gap")])
    def test_priority_levels(self, gap, level):
        assert am.priority_for_gap(gap)[0] == level

    def test_calculate_skill_gaps_for_all_categories(self):
        results = am.calculate_skill_gaps({"aptitude": 1, "coding": 3, "technical": 4, "hr": 5})
        by_key = {r["key"]: r for r in results}
        assert [r["key"] for r in results] == ["aptitude", "coding", "technical", "hr"]
        assert by_key["aptitude"]["gap"] == 4 and by_key["aptitude"]["priority"] == "High"
        assert by_key["coding"]["gap"] == 2 and by_key["coding"]["priority"] == "Medium"
        assert by_key["technical"]["gap"] == 1 and by_key["technical"]["priority"] == "Low"
        assert by_key["hr"]["gap"] == 0 and by_key["hr"]["priority"] == "No gap"
        assert by_key["aptitude"]["rating_label"] == "Beginner"

    def test_priority_rank_biggest_gap_first_ties_keep_category_order(self):
        results = am.calculate_skill_gaps({"aptitude": 3, "coding": 1, "technical": 1, "hr": 5})
        rank = {r["key"]: r["priority_rank"] for r in results}
        assert rank == {"coding": 1, "technical": 2, "aptitude": 3, "hr": 4}

    def test_missing_category_rejected(self):
        with pytest.raises(ValueError):
            am.calculate_skill_gaps({"aptitude": 3, "coding": 3, "technical": 3})

    def test_all_fives_means_no_gaps(self):
        results = am.calculate_skill_gaps({k: 5 for k in ("aptitude", "coding", "technical", "hr")})
        assert all(r["gap"] == 0 for r in results)


# ---------------------------------------------------------------------------
# 2. Server-side validation (function level)
# ---------------------------------------------------------------------------
class TestValidation:
    def test_valid_form_has_no_errors(self):
        data, errors = am.validate_submission(valid_form())
        assert errors == {}
        assert data["ratings"] == {"aptitude": 1, "coding": 3, "technical": 4, "hr": 5}
        assert data["student"]["year"] == 3

    def test_email_is_lowercased_and_spaces_trimmed(self):
        data, errors = am.validate_submission(valid_form(email="  ASHA@Example.COM ", name="  Asha  "))
        assert errors == {}
        assert data["student"]["email"] == "asha@example.com"
        assert data["student"]["name"] == "Asha"

    @pytest.mark.parametrize("key", ["aptitude", "coding", "technical", "hr"])
    def test_missing_rating_is_rejected(self, key):
        form = valid_form()
        del form["rating_" + key]
        _, errors = am.validate_submission(form)
        assert "rating_" + key in errors
        assert len(errors) == 1

    @pytest.mark.parametrize("bad", ["0", "6", "-1", "10", "abc", "3.5", "", "   ", "1e1",
                                     "3; DROP TABLE students", "\u0663"])  # last one: Arabic digit 3
    def test_invalid_or_out_of_range_rating_is_rejected(self, bad):
        _, errors = am.validate_submission(valid_form(rating_coding=bad))
        assert "rating_coding" in errors

    @pytest.mark.parametrize("field", ["name", "email", "branch", "year"])
    def test_missing_student_field_is_rejected(self, field):
        form = valid_form()
        del form[field]
        _, errors = am.validate_submission(form)
        assert field in errors

    @pytest.mark.parametrize("email", ["not-an-email", "a@b", "@example.com", "a b@example.com"])
    def test_bad_email_is_rejected(self, email):
        _, errors = am.validate_submission(valid_form(email=email))
        assert "email" in errors

    @pytest.mark.parametrize("year", ["0", "5", "x", "2.5"])
    def test_bad_year_is_rejected(self, year):
        _, errors = am.validate_submission(valid_form(year=year))
        assert "year" in errors

    def test_too_long_name_is_rejected(self):
        _, errors = am.validate_submission(valid_form(name="A" * 101))
        assert "name" in errors

    def test_empty_form_reports_every_field(self):
        _, errors = am.validate_submission({})
        assert set(errors) == {"name", "email", "branch", "year",
                               "rating_aptitude", "rating_coding", "rating_technical", "rating_hr"}


# ---------------------------------------------------------------------------
# 3. The web page: form, successful submission, invalid submission
# ---------------------------------------------------------------------------
class TestAssessmentPage:
    def test_form_page_shows_categories_and_rating_scale(self, client):
        resp = client.get("/assessment")
        html = resp.get_data(as_text=True)
        assert resp.status_code == 200
        for text in ("Aptitude", "Coding", "Technical Knowledge", "HR &amp; Communication",
                     "Beginner", "Basic", "Intermediate", "Advanced", "Expert"):
            assert text in html
        for field in ("rating_aptitude", "rating_coding", "rating_technical", "rating_hr"):
            assert f'name="{field}"' in html

    def test_page_reuses_base_template(self, client):
        html = client.get("/assessment").get_data(as_text=True)
        assert html.count("<html") == 1                 # one document only
        assert "navbar" in html and "Progress Dashboard" in html

    def test_successful_submission_redirects_to_result(self, client):
        resp = client.post("/assessment", data=valid_form())
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/assessment?student=1")

    def test_result_page_shows_ratings_gaps_and_priorities(self, client):
        resp = client.post("/assessment", data=valid_form(), follow_redirects=True)
        html = resp.get_data(as_text=True)
        assert resp.status_code == 200
        assert "Asha Kumar" in html
        for label in ("Aptitude", "Coding", "Technical Knowledge", "HR &amp; Communication"):
            assert label in html
        for priority in ("High", "Medium", "Low", "No gap"):
            assert priority in html
        assert "Improvement priorities" in html
        # Aptitude has the biggest gap, so it is listed first in the priority list
        priorities = html.split("Improvement priorities")[1]
        assert priorities.index("Aptitude") < priorities.index("Coding") < priorities.index("Technical Knowledge")
        assert "HR &amp; Communication" not in priorities       # gap 0: nothing to improve

    def test_all_fives_shows_no_gap_message(self, client):
        data = valid_form(rating_aptitude="5", rating_coding="5", rating_technical="5", rating_hr="5")
        html = client.post("/assessment", data=data, follow_redirects=True).get_data(as_text=True)
        assert "no skill gaps" in html

    def test_invalid_rating_returns_400_and_saves_nothing(self, client, db_path):
        resp = client.post("/assessment", data=valid_form(rating_coding="9"))
        html = resp.get_data(as_text=True)
        assert resp.status_code == 400
        assert "Rating must be a whole number from 1 to 5." in html
        assert rows(db_path, "SELECT * FROM skill_assessments") == []
        assert rows(db_path, "SELECT * FROM students") == []

    def test_missing_rating_returns_400_and_saves_nothing(self, client, db_path):
        form = valid_form()
        del form["rating_hr"]
        resp = client.post("/assessment", data=form)
        assert resp.status_code == 400
        assert "Please rate your HR &amp; Communication skills." in resp.get_data(as_text=True)
        assert rows(db_path, "SELECT * FROM skill_assessments") == []

    def test_empty_post_returns_400(self, client):
        assert client.post("/assessment", data={}).status_code == 400

    def test_form_keeps_valid_values_after_an_error(self, client):
        html = client.post("/assessment", data=valid_form(rating_coding="9")).get_data(as_text=True)
        assert 'value="Asha Kumar"' in html
        assert 'value="asha@example.com"' in html

    def test_user_text_is_escaped_in_the_result_page(self, client):
        data = valid_form(name="<script>alert(1)</script>")
        html = client.post("/assessment", data=data, follow_redirects=True).get_data(as_text=True)
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html

    def test_unknown_student_gives_404_with_message(self, client):
        resp = client.get("/assessment?student=999")
        assert resp.status_code == 404
        assert "No assessment was found" in resp.get_data(as_text=True)

    def test_non_numeric_student_parameter_just_shows_form(self, client):
        resp = client.get("/assessment?student=abc")
        assert resp.status_code == 200
        assert "Your details" in resp.get_data(as_text=True)

    def test_other_pages_still_work(self, client):
        for path in ("/", "/planner", "/progress"):
            assert client.get(path).status_code == 200

    def test_home_page_marks_assessment_as_ready(self, client):
        assert "Ready" in client.get("/").get_data(as_text=True)


# ---------------------------------------------------------------------------
# 4. Database persistence
# ---------------------------------------------------------------------------
class TestPersistence:
    def test_submission_saves_student_and_four_rows(self, client, db_path):
        client.post("/assessment", data=valid_form())

        students = rows(db_path, "SELECT name, email, branch, year FROM students")
        assert len(students) == 1
        assert dict(students[0]) == {"name": "Asha Kumar", "email": "asha@example.com",
                                     "branch": "CSE", "year": 3}

        saved = rows(db_path, "SELECT category, topic, self_rating, target_level, skill_gap, "
                              "score_percent FROM skill_assessments ORDER BY id")
        assert [tuple(r) for r in saved] == [
            ("Aptitude", "Overall", 1, 5.0, 4.0, None),
            ("Coding", "Overall", 3, 5.0, 2.0, None),
            ("Technical Knowledge", "Overall", 4, 5.0, 1.0, None),
            ("HR & Communication", "Overall", 5, 5.0, 0.0, None),
        ]

    def test_rows_are_linked_to_the_student(self, client, db_path):
        client.post("/assessment", data=valid_form())
        linked = rows(db_path, "SELECT COUNT(*) AS n FROM skill_assessments sa "
                               "JOIN students s ON s.id = sa.student_id WHERE s.email = ?",
                      ("asha@example.com",))
        assert linked[0]["n"] == 4

    def test_data_survives_a_new_app_instance(self, client, db_path):
        """Simulates restarting the server: data must still be in the file."""
        client.post("/assessment", data=valid_form())
        new_client = create_app({"TESTING": True, "DATABASE": db_path}).test_client()
        html = new_client.get("/assessment?student=1").get_data(as_text=True)
        assert "Asha Kumar" in html and "High" in html

    def test_same_email_reuses_student_and_latest_assessment_wins(self, client, db_path):
        client.post("/assessment", data=valid_form())
        client.post("/assessment", data=valid_form(name="Asha K", year="4", rating_aptitude="5"))

        students = rows(db_path, "SELECT name, year FROM students")
        assert len(students) == 1
        assert (students[0]["name"], students[0]["year"]) == ("Asha K", 4)
        assert rows(db_path, "SELECT COUNT(*) AS n FROM skill_assessments")[0]["n"] == 8

        latest = am.get_latest_assessment(1, db_path)
        aptitude = next(r for r in latest["results"] if r["key"] == "aptitude")
        assert aptitude["rating"] == 5 and aptitude["gap"] == 0

    def test_two_students_are_kept_separate(self, client, db_path):
        client.post("/assessment", data=valid_form())
        client.post("/assessment", data=valid_form(email="bala@example.com", name="Bala",
                                                   rating_aptitude="2"))
        assert rows(db_path, "SELECT COUNT(*) AS n FROM students")[0]["n"] == 2
        one = am.get_latest_assessment(1, db_path)
        two = am.get_latest_assessment(2, db_path)
        assert one["student"]["name"] == "Asha Kumar" and two["student"]["name"] == "Bala"
        assert one["results"][0]["rating"] == 1 and two["results"][0]["rating"] == 2

    def test_get_latest_assessment_returns_none_when_missing(self, client, db_path):
        assert am.get_latest_assessment(123, db_path) is None

    def test_student_without_assessment_returns_none(self, client, db_path):
        database.execute("INSERT INTO students (name, email, branch, year) VALUES (?, ?, ?, ?)",
                         ("Nobody", "n@example.com", "IT", 1), db_path)
        assert am.get_latest_assessment(1, db_path) is None

    def test_sql_injection_text_is_stored_as_plain_text(self, client, db_path):
        evil = "x'); DROP TABLE students;--"
        client.post("/assessment", data=valid_form(name=evil))
        assert rows(db_path, "SELECT name FROM students")[0]["name"] == evil
        assert set(database.list_tables(db_path)) >= set(database.TABLE_NAMES)

    def test_save_assessment_rejects_bad_ratings_and_saves_nothing(self, client, db_path):
        student = {"name": "A", "email": "a@example.com", "branch": "CSE", "year": 1}
        with pytest.raises(ValueError):
            am.save_assessment(student, {"aptitude": 9, "coding": 3, "technical": 3, "hr": 3}, db_path)
        assert rows(db_path, "SELECT * FROM students") == []

    def test_failed_save_is_rolled_back_completely(self, client, db_path):
        """If inserting the ratings fails, the new student row must not stay behind."""
        with database.db_session(db_path) as conn:
            conn.execute("CREATE TRIGGER boom BEFORE INSERT ON skill_assessments "
                         "BEGIN SELECT RAISE(ABORT, 'simulated failure'); END;")
        student = {"name": "A", "email": "a@example.com", "branch": "CSE", "year": 1}
        with pytest.raises(sqlite3.Error):
            am.save_assessment(student, {"aptitude": 3, "coding": 3, "technical": 3, "hr": 3}, db_path)
        assert rows(db_path, "SELECT * FROM students") == []

    def test_database_error_shows_friendly_message(self, client, db_path):
        with database.db_session(db_path) as conn:
            conn.execute("CREATE TRIGGER boom BEFORE INSERT ON skill_assessments "
                         "BEGIN SELECT RAISE(ABORT, 'simulated failure'); END;")
        resp = client.post("/assessment", data=valid_form())
        html = resp.get_data(as_text=True)
        assert resp.status_code == 500
        assert "could not be saved" in html
        assert "Traceback" not in html and "simulated failure" not in html

    def test_existing_schema_is_unchanged(self, client, db_path):
        assert set(database.list_tables(db_path)) == set(database.TABLE_NAMES)
        columns = [r["name"] for r in rows(db_path, "PRAGMA table_info(skill_assessments)")]
        assert columns == ["id", "student_id", "category", "topic", "self_rating",
                           "score_percent", "target_level", "skill_gap", "assessed_at"]