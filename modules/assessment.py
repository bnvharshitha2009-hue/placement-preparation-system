"""
modules/assessment.py
=====================
Member 1 - Skill Assessment and Skill Gap Analysis

What this module does
---------------------
1. Shows a form where a student rates 4 skill categories from 1 to 5.
2. Validates every submitted value on the SERVER (never trust the browser).
3. Calculates the skill gap for each category:      gap = 5 - rating
4. Saves the result in the shared SQLite database (tables from database.py).
5. Shows the ratings, gaps and improvement priorities.

How it connects to the rest of the project
------------------------------------------
* app.py calls   handle_assessment_request(db_path)   from the /assessment route.
* Database access uses the helpers in database.py (db_session, fetch_all, ...).
* No new tables or columns are needed. We use the existing tables:
      students           - one row per student (found by e-mail)
      skill_assessments  - one row per category per submission, stored as:
            category      = "Aptitude" / "Coding" / ...  (the category label)
            topic         = "Overall"   (this simple form rates a whole category)
            self_rating   = the student's rating, 1..5
            target_level  = 5           (the level the gap is measured against)
            skill_gap     = 5 - self_rating
            score_percent = NULL        (there is no test score in this feature)
            assessed_at   = same value for the 4 rows of one submission

Interface for other modules (Member 2 / Member 3)
-------------------------------------------------
    get_latest_assessment(student_id, db_path=None)
        -> dict with the student, the 4 results (rating, gap, priority) or None
"""

import re
import sqlite3
from datetime import datetime

from flask import current_app, redirect, render_template, request, url_for

from database import db_session, fetch_all, fetch_one

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
MIN_RATING = 1
MAX_RATING = 5
TARGET_LEVEL = MAX_RATING          # the gap is measured against the top level
OVERALL_TOPIC = "Overall"          # value stored in skill_assessments.topic

# The four categories. "key" is used in HTML form field names (rating_<key>),
# "label" is what students see and what is saved in the database.
CATEGORIES = [
    {
        "key": "aptitude",
        "label": "Aptitude",
        "description": "Quantitative maths, logical reasoning and verbal ability.",
        "hint": "Practise timed aptitude questions every day.",
    },
    {
        "key": "coding",
        "label": "Coding",
        "description": "Writing programs, solving problems and using data structures.",
        "hint": "Solve coding problems regularly and review your mistakes.",
    },
    {
        "key": "technical",
        "label": "Technical Knowledge",
        "description": "Core subjects such as DBMS, operating systems and networks.",
        "hint": "Revise core subjects and answer interview-style questions.",
    },
    {
        "key": "hr",
        "label": "HR & Communication",
        "description": "Speaking, teamwork and answering HR interview questions.",
        "hint": "Do mock interviews and prepare real examples about yourself.",
    },
]
CATEGORY_BY_KEY = {c["key"]: c for c in CATEGORIES}
CATEGORY_BY_LABEL = {c["label"]: c for c in CATEGORIES}

# The rating scale shown to students.
RATING_SCALE = [
    {"value": 1, "label": "Beginner", "meaning": "I am just starting and need to learn the basics."},
    {"value": 2, "label": "Basic", "meaning": "I know some concepts but make many mistakes."},
    {"value": 3, "label": "Intermediate", "meaning": "I can solve common problems with some effort."},
    {"value": 4, "label": "Advanced", "meaning": "I solve most problems confidently."},
    {"value": 5, "label": "Expert", "meaning": "I am fully placement-ready and could teach others."},
]
RATING_LABELS = {item["value"]: item["label"] for item in RATING_SCALE}

# Only plain digits are accepted, e.g. "3". Text like "3.5", "abc" or other
# scripts' digits are rejected. re.ASCII makes sure only 0-9 count as digits.
RATING_RE = re.compile(r"[1-5]", re.ASCII)
YEAR_RE = re.compile(r"[1-4]", re.ASCII)
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


# ---------------------------------------------------------------------------
# Step 1: skill gap calculation (pure functions - no database, easy to test)
# ---------------------------------------------------------------------------
def calculate_gap(rating):
    """
    Skill gap = 5 - rating.
    A rating of 1 gives a gap of 4 (big gap); a rating of 5 gives 0 (no gap).
    Raises ValueError if the rating is not a whole number from 1 to 5.
    """
    if isinstance(rating, bool) or not isinstance(rating, int):
        raise ValueError(f"Rating must be a whole number, got {rating!r}.")
    if not MIN_RATING <= rating <= MAX_RATING:
        raise ValueError(f"Rating must be between {MIN_RATING} and {MAX_RATING}, got {rating}.")
    return MAX_RATING - rating


def priority_for_gap(gap):
    """Turn a numeric gap into a priority name and a Bootstrap badge colour."""
    if gap >= 3:
        return "High", "danger"
    if gap == 2:
        return "Medium", "warning"
    if gap == 1:
        return "Low", "info"
    return "No gap", "success"


def calculate_skill_gaps(ratings):
    """
    ratings: {"aptitude": 3, "coding": 2, "technical": 4, "hr": 5}
    Returns a list with one dictionary per category (in the normal category
    order). "priority_rank" 1 means "work on this first": the biggest gap comes
    first, and ties keep the normal category order.
    """
    missing = [c["key"] for c in CATEGORIES if c["key"] not in ratings]
    if missing:
        raise ValueError("Missing ratings for: " + ", ".join(missing))

    results = []
    for category in CATEGORIES:
        rating = ratings[category["key"]]
        gap = calculate_gap(rating)                 # also validates the rating
        priority, badge = priority_for_gap(gap)
        results.append({
            "key": category["key"],
            "label": category["label"],
            "description": category["description"],
            "hint": category["hint"],
            "rating": rating,
            "rating_label": RATING_LABELS[rating],
            "gap": gap,
            "priority": priority,
            "badge": badge,
        })

    # sorted() is stable, so equal gaps keep the category order.
    for rank, item in enumerate(sorted(results, key=lambda r: -r["gap"]), start=1):
        item["priority_rank"] = rank
    return results


# ---------------------------------------------------------------------------
# Step 2: server-side validation
# ---------------------------------------------------------------------------
def validate_submission(form):
    """
    Check everything the student submitted.
    form: any mapping with .get(), for example Flask's request.form.
    Returns (data, errors):
        data   = {"student": {...}, "ratings": {...}}   (only the valid parts)
        errors = {"field_name": "message"}              (empty dict = all valid)
    """
    errors = {}

    name = (form.get("name") or "").strip()
    email = (form.get("email") or "").strip().lower()
    branch = (form.get("branch") or "").strip()
    year = (form.get("year") or "").strip()

    if not name:
        errors["name"] = "Please enter your name."
    elif len(name) > 100:
        errors["name"] = "Name must be 100 characters or fewer."

    if not email:
        errors["email"] = "Please enter your email address."
    elif len(email) > 254 or not EMAIL_RE.fullmatch(email):
        errors["email"] = "Please enter a valid email address."

    if not branch:
        errors["branch"] = "Please enter your branch or department."
    elif len(branch) > 100:
        errors["branch"] = "Branch must be 100 characters or fewer."

    if not year:
        errors["year"] = "Please select your year of study."
    elif not YEAR_RE.fullmatch(year):
        errors["year"] = "Year must be 1, 2, 3 or 4."

    ratings = {}
    for category in CATEGORIES:
        field = "rating_" + category["key"]
        raw = (form.get(field) or "").strip()
        if not raw:
            errors[field] = f"Please rate your {category['label']} skills."
        elif not RATING_RE.fullmatch(raw):
            errors[field] = "Rating must be a whole number from 1 to 5."
        else:
            ratings[category["key"]] = int(raw)

    student = {"name": name, "email": email, "branch": branch,
               "year": int(year) if YEAR_RE.fullmatch(year) else None}
    return {"student": student, "ratings": ratings}, errors


# ---------------------------------------------------------------------------
# Step 3: database operations (all queries use ? placeholders)
# ---------------------------------------------------------------------------
def save_assessment(student, ratings, db_path=None):
    """
    Save one assessment: the student (created or updated) and 4 rating rows.
    Everything happens in ONE transaction, so either all rows are saved or none.
    Returns {"student_id": ..., "assessed_at": ...}.
    Raises ValueError for bad ratings and sqlite3.Error for database problems.
    """
    results = calculate_skill_gaps(ratings)         # validates all 4 ratings first
    email = student["email"].strip().lower()

    # One timestamp shared by the 4 rows of this submission. Microseconds make
    # two submissions from the same student practically impossible to mix up.
    assessed_at = datetime.now().isoformat(sep=" ", timespec="microseconds")

    with db_session(db_path) as conn:
        row = conn.execute("SELECT id FROM students WHERE email = ?", (email,)).fetchone()
        if row:                                      # known student: refresh details
            student_id = row["id"]
            conn.execute(
                "UPDATE students SET name = ?, branch = ?, year = ? WHERE id = ?",
                (student["name"].strip(), student["branch"].strip(), int(student["year"]), student_id),
            )
        else:                                        # new student
            cur = conn.execute(
                "INSERT INTO students (name, email, branch, year) VALUES (?, ?, ?, ?)",
                (student["name"].strip(), email, student["branch"].strip(), int(student["year"])),
            )
            student_id = cur.lastrowid

        conn.executemany(
            """INSERT INTO skill_assessments
                   (student_id, category, topic, self_rating, target_level, skill_gap, assessed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [(student_id, r["label"], OVERALL_TOPIC, r["rating"], TARGET_LEVEL, r["gap"], assessed_at)
             for r in results],
        )
    return {"student_id": student_id, "assessed_at": assessed_at}


def get_latest_assessment(student_id, db_path=None):
    """
    Load the student's most recent assessment, or None if there is none.
    Returns {"student": {...}, "assessed_at": "...", "results": [...], "average_rating": x}
    """
    student = fetch_one(
        "SELECT id, name, email, branch, year FROM students WHERE id = ?",
        (student_id,), db_path,
    )
    if student is None:
        return None

    latest = fetch_one(
        "SELECT MAX(assessed_at) AS latest FROM skill_assessments WHERE student_id = ? AND topic = ?",
        (student_id, OVERALL_TOPIC), db_path,
    )
    if latest is None or latest["latest"] is None:
        return None

    rows = fetch_all(
        """SELECT category, self_rating FROM skill_assessments
           WHERE student_id = ? AND topic = ? AND assessed_at = ?""",
        (student_id, OVERALL_TOPIC, latest["latest"]), db_path,
    )
    ratings = {CATEGORY_BY_LABEL[r["category"]]["key"]: r["self_rating"]
               for r in rows
               if r["category"] in CATEGORY_BY_LABEL and r["self_rating"] is not None}
    if len(ratings) != len(CATEGORIES):              # incomplete data: do not guess
        return None

    results = calculate_skill_gaps(ratings)
    return {
        "student": dict(student),
        "assessed_at": latest["latest"],
        "results": results,
        "average_rating": round(sum(ratings.values()) / len(ratings), 1),
    }


# ---------------------------------------------------------------------------
# Step 4: the web page (called from the /assessment route in app.py)
# ---------------------------------------------------------------------------
def _render_form(form=None, errors=None, general_error=None, status=200):
    return render_template(
        "assessment.html",
        view="form",
        categories=CATEGORIES,
        rating_scale=RATING_SCALE,
        form=form or {},
        errors=errors or {},
        general_error=general_error,
    ), status


def handle_assessment_request(db_path):
    """
    GET  /assessment             -> show the form
    GET  /assessment?student=ID  -> show that student's latest result
    POST /assessment             -> validate, save, then redirect to the result
    """
    if request.method == "POST":
        data, errors = validate_submission(request.form)
        if errors:
            # 400 = the submitted data was not acceptable. Nothing is saved.
            return _render_form(form=request.form, errors=errors, status=400)

        try:
            saved = save_assessment(data["student"], data["ratings"], db_path)
        except (sqlite3.Error, ValueError):
            current_app.logger.exception("Could not save the skill assessment")
            return _render_form(
                form=request.form, status=500,
                general_error="Sorry, your assessment could not be saved. Please try again.",
            )
        # Redirect after POST: refreshing the result page will not re-submit the form.
        return redirect(url_for("assessment_page", student=saved["student_id"]))

    # GET request
    student_id = request.args.get("student", type=int)
    if student_id is not None:
        try:
            result = get_latest_assessment(student_id, db_path)
        except sqlite3.Error:
            current_app.logger.exception("Could not load the skill assessment")
            return _render_form(status=500, general_error="Sorry, the result could not be loaded.")
        if result is None:
            return _render_form(status=404, general_error="No assessment was found for that student.")
        return render_template("assessment.html", view="result", result=result), 200

    return _render_form()