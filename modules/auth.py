"""
modules/auth.py
===============
User Login with Gmail + University Name Verification

What this module does
---------------------
1. Accepts a user's Gmail address (`@gmail.com` / `@googlemail.com`) and University Name
   (plus optional Full Name and optional University Verifier Email).
2. Validates inputs strictly on the server.
3. Generates a 6-digit OTP code and verification token, then sends a verification
   email carrying the user's Gmail and University Name:
     * Uses real Gmail SMTP (`smtp.gmail.com`) when `GMAIL_SENDER` & `GMAIL_APP_PASSWORD`
       (or `SMTP_USER`/`SMTP_PASSWORD` / `MAIL_USERNAME`/`MAIL_PASSWORD`) are set.
     * Falls back seamlessly to an in-app verification preview (showing the generated
       OTP and clickable verification link) when SMTP is unconfigured or fails.
4. Tracks Pending -> Verified status in the shared `user_logins` table and links the
   logged-in user to their `students` assessment & planner records via `session`.
"""

import os
import re
import secrets
import smtplib
import sqlite3
from datetime import date, datetime, timedelta
from email.message import EmailMessage

from flask import (
    current_app,
    flash,
    has_request_context,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from database import db_session, fetch_one

GMAIL_RE = re.compile(r"^[a-z0-9][a-z0-9._%+-]*@(?:gmail|googlemail)\.com$", re.ASCII)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
OTP_RE = re.compile(r"^\d{6}$", re.ASCII)

COMMON_UNIVERSITIES = [
    "Anna University",
    "Visvesvaraya Technological University (VTU)",
    "Savitribai Phule Pune University",
    "University of Mumbai",
    "University of Delhi",
    "Jawaharlal Nehru Technological University (JNTU)",
    "SRM Institute of Science and Technology",
    "Vellore Institute of Technology (VIT)",
    "Manipal Academy of Higher Education",
    "Amrita Vishwa Vidyapeetham",
    "IIT Madras",
    "NIT Trichy",
]


# ---------------------------------------------------------------------------
# Step 1: Validation & Pure Helpers
# ---------------------------------------------------------------------------
def _derive_name_from_gmail(gmail):
    """Turn 'asha.kumar12@gmail.com' into a readable fallback name 'Asha Kumar12'."""
    local = gmail.split("@", 1)[0]
    cleaned = re.sub(r"[._+-]+", " ", local).strip()
    return cleaned.title()[:100] or "Student"


def validate_login_submission(form):
    """
    Validate login input: Gmail address, University Name, optional Full Name,
    and optional University Verifier Email.
    Returns (data, errors).
    """
    errors = {}

    gmail = (form.get("gmail") or "").strip().lower()
    university_name = " ".join((form.get("university_name") or "").split())
    full_name = " ".join((form.get("full_name") or "").split())
    verifier_email = (form.get("verifier_email") or "").strip().lower()

    if not gmail:
        errors["gmail"] = "Please enter your Gmail address."
    elif len(gmail) > 254 or not GMAIL_RE.fullmatch(gmail):
        errors["gmail"] = "Please enter a valid Gmail address (ending in @gmail.com)."

    if not university_name:
        errors["university_name"] = "Please enter your university name."
    elif len(university_name) < 3:
        errors["university_name"] = "University name must be at least 3 characters."
    elif len(university_name) > 150:
        errors["university_name"] = "University name must be 150 characters or fewer."

    if full_name and len(full_name) > 100:
        errors["full_name"] = "Full name must be 100 characters or fewer."

    if verifier_email:
        if len(verifier_email) > 254 or not EMAIL_RE.fullmatch(verifier_email):
            errors["verifier_email"] = "Please enter a valid verifier email address."

    resolved_name = full_name or (_derive_name_from_gmail(gmail) if "@" in gmail else "Student")

    return {
        "full_name": resolved_name,
        "gmail": gmail,
        "university_name": university_name,
        "verifier_email": verifier_email or None,
    }, errors


def generate_verification_credentials():
    """Return a cryptographically random (6-digit OTP, URL-safe token)."""
    otp_code = f"{secrets.randbelow(900000) + 100000}"
    token = secrets.token_urlsafe(24)
    return otp_code, token


def _is_placeholder_credentials(sender, app_password):
    """Return True when .env still contains the default .env.example placeholder strings."""
    sender_lower = sender.strip().lower()
    pwd_compact = "".join(app_password.split()).lower()
    if sender_lower in {"youraccount@gmail.com", "your-email@gmail.com", "you@gmail.com"}:
        return True
    if pwd_compact and set(pwd_compact) == {"x"}:
        return True
    return False


def get_smtp_config():
    """Load Gmail SMTP credentials from environment variables if configured."""
    sender = (
        os.environ.get("GMAIL_SENDER")
        or os.environ.get("SMTP_USER")
        or os.environ.get("MAIL_USERNAME")
        or ""
    ).strip()
    raw_password = (
        os.environ.get("GMAIL_APP_PASSWORD")
        or os.environ.get("SMTP_PASSWORD")
        or os.environ.get("MAIL_PASSWORD")
        or ""
    ).strip()
    host = (os.environ.get("SMTP_HOST") or "smtp.gmail.com").strip()
    try:
        port = int(os.environ.get("SMTP_PORT") or "587")
    except ValueError:
        port = 587

    # Google shows App Passwords in 4-character space-separated groups; remove spaces for SMTP AUTH.
    app_password = "".join(raw_password.split()) if host.lower().endswith("gmail.com") else raw_password
    has_values = bool(sender and app_password)
    is_placeholder = has_values and _is_placeholder_credentials(sender, raw_password)

    return {
        "configured": has_values and not is_placeholder,
        "placeholder": is_placeholder,
        "sender": sender,
        "app_password": app_password,
        "host": host,
        "port": port,
    }


def verify_smtp_connection(smtp_config=None):
    """Test SMTP TLS login without sending an email. Returns (ok, message)."""
    cfg = smtp_config if smtp_config is not None else get_smtp_config()
    if cfg.get("placeholder"):
        return False, "Placeholder values detected in .env. Replace GMAIL_SENDER and GMAIL_APP_PASSWORD first."
    if not cfg.get("configured"):
        return False, "GMAIL_SENDER or GMAIL_APP_PASSWORD is not set."
    try:
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=10) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(cfg["sender"], cfg["app_password"])
        return True, f"Connected and authenticated to {cfg['host']}:{cfg['port']} as {cfg['sender']}."
    except (smtplib.SMTPException, OSError) as exc:
        return False, f"SMTP connection failed: {exc}"


def resolve_recipients(gmail, verifier_email=None):
    """Build ordered unique list of email recipients for university verification."""
    recipients = [gmail]
    if verifier_email and verifier_email != gmail:
        recipients.append(verifier_email)
    return recipients


def build_verification_email(gmail, full_name, university_name, otp_code, verify_url, recipients):
    """Build verification subject & body containing Gmail + University Name."""
    subject = f"PLACEMENT HUB University Verification: {university_name}"
    body = (
        f"Hello {full_name},\n\n"
        "A university verification request was submitted on PLACEMENT HUB:\n\n"
        f"  Student Gmail   : {gmail}\n"
        f"  University Name : {university_name}\n"
        f"  Verification OTP: {otp_code}\n\n"
        "Verify your university details by entering the 6-digit code above on the Login page "
        "or by opening this verification link:\n"
        f"  {verify_url}\n\n"
        "If you did not initiate this login, you can safely ignore this message.\n"
    )
    return {
        "to": ", ".join(recipients),
        "subject": subject,
        "body": body,
        "university_name": university_name,
        "otp_code": otp_code,
        "verify_url": verify_url,
    }


def send_verification_email(recipients, subject, body, smtp_config=None):
    """
    Send the university verification email over Gmail SMTP when configured;
    otherwise return local_preview metadata so local testing works without SMTP.
    """
    cfg = smtp_config if smtp_config is not None else get_smtp_config()
    sent_to = ", ".join(recipients)

    if not cfg.get("configured"):
        return {
            "delivery_mode": "local_preview",
            "sent_to": sent_to,
            "error": None,
        }

    msg = EmailMessage()
    msg["From"] = cfg["sender"]
    msg["To"] = sent_to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=10) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(cfg["sender"], cfg["app_password"])
            smtp.send_message(msg)
        return {
            "delivery_mode": "gmail_smtp",
            "sent_to": sent_to,
            "error": None,
        }
    except (smtplib.SMTPException, OSError) as exc:
        if has_request_context():
            current_app.logger.warning("Gmail SMTP delivery failed, falling back to local preview: %s", exc)
        return {
            "delivery_mode": "local_preview",
            "sent_to": sent_to,
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Step 2: Database Operations
# ---------------------------------------------------------------------------
def get_user_by_gmail(gmail, db_path=None):
    """Return the user_logins dict for a Gmail address, or None."""
    if not gmail:
        return None
    row = fetch_one(
        "SELECT * FROM user_logins WHERE gmail = ?",
        (gmail.strip().lower(),),
        db_path,
    )
    return dict(row) if row else None


def get_user_by_id(user_id, db_path=None):
    """Return the user_logins dict for a primary key ID, or None."""
    if not user_id:
        return None
    row = fetch_one("SELECT * FROM user_logins WHERE id = ?", (user_id,), db_path)
    return dict(row) if row else None


def get_user_initials(full_name, gmail=""):
    """Compute 1-2 uppercase initials for the top-right profile avatar."""
    parts = [p for p in (full_name or "").strip().split() if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    if parts and len(parts[0]) >= 2:
        return parts[0][:2].upper()
    if parts:
        return parts[0][0].upper()
    if gmail:
        return gmail[0].upper()
    return "U"


def enrich_user_display(user):
    """Attach computed UI fields (initials, streak bar progress) to a user dict."""
    if not user:
        return None
    enriched = dict(user)
    streak = int(enriched.get("current_streak") or 0)
    enriched["current_streak"] = streak
    enriched["best_streak"] = int(enriched.get("best_streak") or 0)
    enriched["total_login_days"] = int(enriched.get("total_login_days") or 0)
    enriched["initials"] = get_user_initials(enriched.get("full_name"), enriched.get("gmail", ""))
    enriched["streak_goal"] = 7
    enriched["streak_pct"] = min(100, round((streak / 7) * 100)) if streak > 0 else 0
    enriched["is_consistent"] = streak >= 2
    return enriched


def evaluate_streak_transition(user_row, today_date=None):
    """
    Pure streak evaluation for daily logins.
    Returns (new_fields_dict, streak_event_dict) where event.kind is one of:
        'started' | 'streak_kept' | 'streak_broken' | 'same_day'
    """
    today_d = today_date or date.today()
    today_iso = today_d.isoformat()
    yesterday_iso = (today_d - timedelta(days=1)).isoformat()

    row_dict = dict(user_row)
    prev_streak = int(row_dict.get("current_streak") or 0)
    best_streak = int(row_dict.get("best_streak") or 0)
    total_days = int(row_dict.get("total_login_days") or 0)
    last_date = (row_dict.get("last_login_date") or "").strip() or None

    if last_date == today_iso:
        new_streak = max(1, prev_streak)
        new_best = max(best_streak, new_streak)
        new_total = max(1, total_days)
        event = {
            "kind": "same_day",
            "emoji": "🔥" if new_streak >= 2 else "👋",
            "bar_emoji": "🔥" if new_streak >= 2 else "✨",
            "particles": ["✨", "🔥", "💜"] if new_streak >= 2 else ["👋", "✨", "💜"],
            "streak": new_streak,
            "prev_streak": prev_streak,
            "best_streak": new_best,
            "title": f"Welcome back! {new_streak}-Day Streak Active",
            "subtitle": "You already checked in today — consistency keeps your placement momentum high.",
        }
    elif last_date is None or prev_streak <= 0:
        new_streak = 1
        new_best = max(best_streak, 1)
        new_total = total_days + 1
        event = {
            "kind": "started",
            "emoji": "🎉",
            "bar_emoji": "🎉",
            "particles": ["🎉", "✨", "🚀", "💜"],
            "streak": new_streak,
            "prev_streak": prev_streak,
            "best_streak": new_best,
            "title": "Day 1 Streak Started!",
            "subtitle": "Great start! Log in again tomorrow to light up your consistency streak.",
        }
    elif last_date == yesterday_iso:
        new_streak = prev_streak + 1
        new_best = max(best_streak, new_streak)
        new_total = total_days + 1
        event = {
            "kind": "streak_kept",
            "emoji": "🔥",
            "bar_emoji": "🔥",
            "particles": ["🔥", "⚡", "🌟", "✨", "🏆"],
            "streak": new_streak,
            "prev_streak": prev_streak,
            "best_streak": new_best,
            "title": f"{new_streak}-Day Streak Kept!",
            "subtitle": "Awesome consistency — you logged in yesterday and today! Your streak bar just leveled up.",
        }
    else:
        new_streak = 1
        new_best = max(best_streak, prev_streak, 1)
        new_total = total_days + 1
        event = {
            "kind": "streak_broken",
            "emoji": "💔",
            "bar_emoji": "🌱",
            "particles": ["💔", "😢", "🌱", "💪"],
            "streak": new_streak,
            "prev_streak": prev_streak,
            "best_streak": new_best,
            "title": f"Missed Yesterday! Streak Reset ({prev_streak}d → 1d)",
            "subtitle": f"You missed yesterday after a {prev_streak}-day run. Starting fresh at Day 1 today — come back tomorrow!",
        }

    fields = {
        "current_streak": new_streak,
        "best_streak": new_best,
        "last_login_date": today_iso,
        "total_login_days": new_total,
    }
    return fields, event


def _apply_streak_in_conn(conn, row, today_date=None):
    """Apply daily streak transition inside an open SQLite transaction."""
    fields, event = evaluate_streak_transition(row, today_date=today_date)
    conn.execute(
        """
        UPDATE user_logins
        SET current_streak = ?, best_streak = ?, last_login_date = ?, total_login_days = ?
        WHERE id = ?
        """,
        (
            fields["current_streak"],
            fields["best_streak"],
            fields["last_login_date"],
            fields["total_login_days"],
            row["id"],
        ),
    )
    return event


def record_login_streak(user_id, db_path=None, today_date=None):
    """Record a daily login event for user_id and return (updated_user, streak_event)."""
    with db_session(db_path) as conn:
        row = conn.execute("SELECT * FROM user_logins WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            return None, None
        event = _apply_streak_in_conn(conn, row, today_date=today_date)
        updated = conn.execute("SELECT * FROM user_logins WHERE id = ?", (user_id,)).fetchone()
    return dict(updated), event


def consume_streak_effect():
    """Pop and return any pending streak celebration/reset effect for this request."""
    if not has_request_context():
        return None
    effect = session.pop("pending_streak_effect", None)
    return effect if isinstance(effect, dict) else None


def get_logged_in_user(db_path=None):
    """Return the active session user's enriched record from user_logins, or None."""
    if not has_request_context():
        return None
    user_id = session.get("user_login_id")
    gmail = session.get("user_gmail")
    if not user_id and not gmail:
        return None

    try:
        user = None
        if user_id:
            user = get_user_by_id(user_id, db_path)
        if user is None and gmail:
            user = get_user_by_gmail(gmail, db_path)
        return enrich_user_display(user)
    except sqlite3.Error:
        return None


def _build_verify_url(token, verify_url_builder=None):
    if verify_url_builder is not None:
        return verify_url_builder(token)
    return url_for("verify_page", token=token, _external=True)


def create_or_update_login(data, db_path=None, verify_url_builder=None, force_new_verification=False,
                           smtp_config=None, today_date=None):
    """
    Create or update a login record for Gmail + University Name, and send the
    university name for verification unless the same Gmail & University are
    already verified (and force_new_verification is False).
    """
    gmail = data["gmail"].strip().lower()
    university_name = data["university_name"].strip()
    full_name = data["full_name"].strip()
    verifier_email = data.get("verifier_email")
    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    streak_event = None

    with db_session(db_path) as conn:
        student_row = conn.execute("SELECT id FROM students WHERE email = ?", (gmail,)).fetchone()
        student_id = student_row["id"] if student_row else None

        existing = conn.execute("SELECT * FROM user_logins WHERE gmail = ?", (gmail,)).fetchone()
        already_verified_same_uni = (
            existing is not None
            and existing["status"] == "verified"
            and existing["university_name"].strip().lower() == university_name.lower()
            and not force_new_verification
        )

        if already_verified_same_uni:
            conn.execute(
                """
                UPDATE user_logins
                SET full_name = ?, verifier_email = ?, student_id = COALESCE(student_id, ?)
                WHERE id = ?
                """,
                (full_name, verifier_email, student_id, existing["id"]),
            )
            streak_event = _apply_streak_in_conn(conn, existing, today_date=today_date)
            user_id = existing["id"]
            email_preview = None
            delivery_error = None
            needs_verification = False
        else:
            otp_code, token = generate_verification_credentials()
            recipients = resolve_recipients(gmail, verifier_email)
            verify_url = _build_verify_url(token, verify_url_builder)
            email_preview = build_verification_email(
                gmail=gmail,
                full_name=full_name,
                university_name=university_name,
                otp_code=otp_code,
                verify_url=verify_url,
                recipients=recipients,
            )
            delivery = send_verification_email(
                recipients=recipients,
                subject=email_preview["subject"],
                body=email_preview["body"],
                smtp_config=smtp_config,
            )
            delivery_error = delivery["error"]

            if existing is None:
                cur = conn.execute(
                    """
                    INSERT INTO user_logins (
                        student_id, full_name, gmail, university_name, verifier_email,
                        verification_code, verification_token, verification_sent_to,
                        delivery_mode, status, sent_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                    """,
                    (
                        student_id,
                        full_name,
                        gmail,
                        university_name,
                        verifier_email,
                        otp_code,
                        token,
                        delivery["sent_to"],
                        delivery["delivery_mode"],
                        now,
                    ),
                )
                user_id = cur.lastrowid
            else:
                conn.execute(
                    """
                    UPDATE user_logins
                    SET student_id = COALESCE(student_id, ?),
                        full_name = ?,
                        university_name = ?,
                        verifier_email = ?,
                        verification_code = ?,
                        verification_token = ?,
                        verification_sent_to = ?,
                        delivery_mode = ?,
                        status = 'pending',
                        sent_at = ?,
                        verified_at = NULL
                    WHERE id = ?
                    """,
                    (
                        student_id,
                        full_name,
                        university_name,
                        verifier_email,
                        otp_code,
                        token,
                        delivery["sent_to"],
                        delivery["delivery_mode"],
                        now,
                        existing["id"],
                    ),
                )
                user_id = existing["id"]
            needs_verification = True

        user = conn.execute("SELECT * FROM user_logins WHERE id = ?", (user_id,)).fetchone()

    return {
        "user": dict(user),
        "needs_verification": needs_verification,
        "email_preview": email_preview,
        "delivery_error": delivery_error,
        "streak_event": streak_event,
    }


def resend_verification(gmail, db_path=None, verify_url_builder=None, smtp_config=None):
    """Generate a fresh OTP + token for an existing login and re-send university verification."""
    user = get_user_by_gmail(gmail, db_path)
    if user is None:
        return None
    return create_or_update_login(
        {
            "full_name": user["full_name"],
            "gmail": user["gmail"],
            "university_name": user["university_name"],
            "verifier_email": user.get("verifier_email"),
        },
        db_path=db_path,
        verify_url_builder=verify_url_builder,
        force_new_verification=True,
        smtp_config=smtp_config,
    )


def _complete_verification_in_conn(conn, row, today_date=None):
    """Mark a pending user verified and update their daily login streak atomically."""
    verified_at = datetime.now().isoformat(sep=" ", timespec="seconds")
    streak_event = _apply_streak_in_conn(conn, row, today_date=today_date)
    conn.execute(
        """
        UPDATE user_logins
        SET status = 'verified',
            verified_at = ?,
            verification_code = NULL,
            verification_token = NULL
        WHERE id = ?
        """,
        (verified_at, row["id"]),
    )
    updated = conn.execute("SELECT * FROM user_logins WHERE id = ?", (row["id"],)).fetchone()
    return dict(updated), streak_event


def verify_by_otp_with_streak(gmail, otp_code, db_path=None, today_date=None):
    """Verify via 6-digit OTP and record streak. Returns (user_dict, streak_event, error)."""
    clean_gmail = (gmail or "").strip().lower()
    clean_otp = (otp_code or "").strip()

    if not clean_gmail:
        return None, None, "Session expired or missing Gmail. Please enter your Gmail again."
    if not OTP_RE.fullmatch(clean_otp):
        return None, None, "Please enter the 6-digit verification code."

    with db_session(db_path) as conn:
        row = conn.execute("SELECT * FROM user_logins WHERE gmail = ?", (clean_gmail,)).fetchone()
        if row is None:
            return None, None, "No login request was found for that Gmail address."
        expected = row["verification_code"] or ""
        if not expected or not secrets.compare_digest(expected, clean_otp):
            return None, None, "Incorrect verification code. Please check your email or resend a new code."
        updated, streak_event = _complete_verification_in_conn(conn, row, today_date=today_date)
    return updated, streak_event, None


def verify_by_otp(gmail, otp_code, db_path=None, today_date=None):
    """Verify a pending user via their 6-digit OTP code. Returns (user_dict, error_message)."""
    updated, _, err = verify_by_otp_with_streak(gmail, otp_code, db_path=db_path, today_date=today_date)
    return updated, err


def verify_by_token_with_streak(token, db_path=None, today_date=None):
    """Verify via single-use URL token and record streak. Returns (user_dict, streak_event, error)."""
    clean_token = (token or "").strip()
    if not clean_token:
        return None, None, "Missing verification token."

    with db_session(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM user_logins WHERE verification_token = ?",
            (clean_token,),
        ).fetchone()
        if row is None:
            return None, None, "That verification link is invalid or has already been used."
        updated, streak_event = _complete_verification_in_conn(conn, row, today_date=today_date)
    return updated, streak_event, None


def verify_by_token(token, db_path=None, today_date=None):
    """Verify a pending user via their single-use email link token. Returns (user_dict, error_message)."""
    updated, _, err = verify_by_token_with_streak(token, db_path=db_path, today_date=today_date)
    return updated, err


def link_student_to_login(gmail, student_id, db_path=None):
    """Link a completed student assessment ID onto any matching user_logins record."""
    if not gmail or not student_id:
        return 0
    with db_session(db_path) as conn:
        cur = conn.execute(
            "UPDATE user_logins SET student_id = ? WHERE gmail = ?",
            (student_id, gmail.strip().lower()),
        )
        return cur.rowcount


# ---------------------------------------------------------------------------
# Step 3: Web Request Handlers (called from routes in app.py)
# ---------------------------------------------------------------------------
def _preview_for_pending_user(user):
    if not user or user.get("status") != "pending":
        return None
    token = user.get("verification_token") or ""
    otp_code = user.get("verification_code") or ""
    if not token or not otp_code:
        return None
    recipients = resolve_recipients(user["gmail"], user.get("verifier_email"))
    verify_url = url_for("verify_page", token=token, _external=True)
    return build_verification_email(
        gmail=user["gmail"],
        full_name=user["full_name"],
        university_name=user["university_name"],
        otp_code=otp_code,
        verify_url=verify_url,
        recipients=recipients,
    )


def _render_login(user=None, form=None, errors=None, otp_error=None, general_error=None,
                  status=200, edit_mode=False):
    email_preview = _preview_for_pending_user(user)
    smtp_cfg = get_smtp_config()
    return render_template(
        "login.html",
        user=user,
        email_preview=email_preview,
        form=form or {},
        errors=errors or {},
        otp_error=otp_error,
        general_error=general_error,
        edit_mode=edit_mode,
        universities=COMMON_UNIVERSITIES,
        smtp_configured=smtp_cfg["configured"],
        smtp_placeholder=smtp_cfg["placeholder"],
    ), status


def handle_login_request(db_path):
    """
    GET  /login -> show login form, pending verification step, or verified account summary
    POST /login -> validate Gmail + University Name, send university name for verification
    """
    if request.method == "POST":
        data, errors = validate_login_submission(request.form)
        if errors:
            return _render_login(
                user=get_logged_in_user(db_path),
                form=request.form,
                errors=errors,
                status=400,
                edit_mode=True,
            )

        try:
            outcome = create_or_update_login(data, db_path=db_path)
        except sqlite3.Error:
            current_app.logger.exception("Could not save login request")
            return _render_login(
                form=request.form,
                general_error="Sorry, your login request could not be saved. Please try again.",
                status=500,
            )

        user = outcome["user"]
        session["user_login_id"] = user["id"]
        session["user_gmail"] = user["gmail"]
        if outcome.get("streak_event"):
            session["pending_streak_effect"] = outcome["streak_event"]

        if not outcome["needs_verification"]:
            flash(f"Welcome back! Signed in as {user['gmail']} ({user['university_name']}).", "success")
        elif outcome["delivery_error"]:
            flash(
                f"Live Gmail SMTP could not send ({outcome['delivery_error']}). "
                "Using local verification fallback below so you can still verify.",
                "warning",
            )
        elif user["delivery_mode"] == "gmail_smtp":
            flash(
                f"Verification email with university '{user['university_name']}' sent to {user['verification_sent_to']}.",
                "info",
            )
        else:
            flash(
                f"Verification code generated for '{user['university_name']}'. "
                "Enter the 6-digit OTP or click Verify via Link below.",
                "info",
            )

        return redirect(url_for("login_page"))

    # GET request
    user = get_logged_in_user(db_path)
    edit_mode = request.args.get("edit") == "1"
    form = {}
    if user and edit_mode:
        form = {
            "full_name": user.get("full_name", ""),
            "gmail": user.get("gmail", ""),
            "university_name": user.get("university_name", ""),
            "verifier_email": user.get("verifier_email") or "",
        }
    return _render_login(user=user, form=form, edit_mode=edit_mode)


def handle_verify_request(db_path):
    """
    GET  /verify?token=... -> verify university & Gmail from email link
    POST /verify           -> verify university & Gmail via 6-digit OTP code
    """
    if request.method == "POST":
        gmail = (request.form.get("gmail") or session.get("user_gmail") or "").strip().lower()
        otp_code = (request.form.get("otp") or "").strip()
        try:
            verified_user, streak_event, err = verify_by_otp_with_streak(gmail, otp_code, db_path=db_path)
        except sqlite3.Error:
            current_app.logger.exception("Could not verify OTP")
            return _render_login(
                user=get_logged_in_user(db_path),
                general_error="Sorry, verification failed due to a database error.",
                status=500,
            )

        if err:
            current = get_logged_in_user(db_path) or get_user_by_gmail(gmail, db_path)
            return _render_login(user=current, otp_error=err, status=400)

        session["user_login_id"] = verified_user["id"]
        session["user_gmail"] = verified_user["gmail"]
        if streak_event:
            session["pending_streak_effect"] = streak_event
        flash(
            f"Verified {verified_user['gmail']} for {verified_user['university_name']}!",
            "success",
        )
        return redirect(url_for("login_page"))

    # GET /verify?token=...
    token = request.args.get("token", "")
    try:
        verified_user, streak_event, err = verify_by_token_with_streak(token, db_path=db_path)
    except sqlite3.Error:
        current_app.logger.exception("Could not verify link token")
        return _render_login(
            user=get_logged_in_user(db_path),
            general_error="Sorry, verification failed due to a database error.",
            status=500,
        )

    if err:
        return _render_login(user=get_logged_in_user(db_path), general_error=err, status=400)

    session["user_login_id"] = verified_user["id"]
    session["user_gmail"] = verified_user["gmail"]
    if streak_event:
        session["pending_streak_effect"] = streak_event
    flash(
        f"Verified {verified_user['gmail']} for {verified_user['university_name']}!",
        "success",
    )
    return redirect(url_for("login_page"))


def handle_resend_request(db_path):
    """POST /login/resend -> send a fresh verification code + link with the university name."""
    gmail = (request.form.get("gmail") or session.get("user_gmail") or "").strip().lower()
    if not gmail:
        flash("Please sign in with your Gmail and university name first.", "warning")
        return redirect(url_for("login_page"))

    try:
        outcome = resend_verification(gmail, db_path=db_path)
    except sqlite3.Error:
        current_app.logger.exception("Could not resend verification")
        flash("Could not resend verification email. Please try again.", "danger")
        return redirect(url_for("login_page"))

    if outcome is None:
        flash("No pending account found for that Gmail address.", "warning")
        return redirect(url_for("login_page"))

    user = outcome["user"]
    session["user_login_id"] = user["id"]
    session["user_gmail"] = user["gmail"]
    if outcome["delivery_error"]:
        flash(
            f"Gmail SMTP failed ({outcome['delivery_error']}). "
            "New verification code generated below.",
            "warning",
        )
    else:
        flash(
            f"New verification email for '{user['university_name']}' sent to {user['verification_sent_to']}.",
            "info",
        )
    return redirect(url_for("login_page"))


def handle_profile_request(db_path):
    """GET /profile -> display user profile, university verification status, and streak bar."""
    user = get_logged_in_user(db_path)
    assessment_summary = None
    if user and user.get("student_id"):
        try:
            from modules import assessment as assessment_module

            assessment_summary = assessment_module.get_latest_assessment(user["student_id"], db_path)
        except sqlite3.Error:
            assessment_summary = None

    streak = user["current_streak"] if user else 0
    milestones = [{"day": d, "reached": streak >= d} for d in range(1, 8)]
    return render_template(
        "profile.html",
        user=user,
        assessment=assessment_summary,
        milestones=milestones,
    ), 200


def handle_logout_request():
    """POST /logout -> clear active user login session."""
    session.pop("user_login_id", None)
    session.pop("user_gmail", None)
    session.pop("pending_streak_effect", None)
    flash("You have signed out.", "info")
    return redirect(url_for("index"))


if __name__ == "__main__":
    from app import load_env_file

    load_env_file()
    ok, message = verify_smtp_connection()
    print("Gmail SMTP Check:", "OK -" if ok else "ERROR -", message)
