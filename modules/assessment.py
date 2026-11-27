"""
modules/assessment.py
=====================
Member 1 - Skill Assessment and Skill Gap Analysis

What this module does
---------------------
1. Loads real placement assessment questions from `data/careerride_questions.csv`
   (sourced from careerride.com topics), organized into alternating sets with
   5 questions per category (20 questions per attempt).
2. Alternates question sets automatically on each assessment attempt
   (Set 1 -> Set 2 -> Set 3 -> Set 1) or via `?set=N`.
3. Validates every submitted answer and student field on the SERVER.
4. Grades answers on the server to compute each category's score_percent (0..100),
   derives the 1..5 skill level, and computes the skill gap:  gap = 5 - rating.
5. Saves the results in the shared SQLite database (tables from database.py).
6. Displays category scores, skill gaps, improvement priorities, and answer review.

Interface for other modules (Member 2 / Member 3)
-------------------------------------------------
    get_latest_assessment(student_id, db_path=None)
        -> dict with student, assessed_at, results (rating, score_percent, gap, priority),
           average_rating, and average_score, or None
"""

import csv
import os
import re
import sqlite3
from datetime import datetime

from flask import current_app, redirect, render_template, request, session, url_for

from database import db_session, fetch_all, fetch_one
from modules import auth as auth_module

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
MIN_RATING = 1
MAX_RATING = 5
TARGET_LEVEL = MAX_RATING          # the gap is measured against the top level
OVERALL_TOPIC = "Overall"          # value stored in skill_assessments.topic

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATASET_PATH = os.path.join(BASE_DIR, "data", "careerride_questions.csv")

CATEGORIES = [
    {
        "key": "aptitude",
        "label": "Aptitude",
        "description": "Quantitative maths, logical reasoning, probability and data interpretation.",
        "hint": "Practise timed aptitude questions every day.",
    },
    {
        "key": "coding",
        "label": "Coding",
        "description": "Complexity analysis, data structures, problem solving and algorithms.",
        "hint": "Solve coding problems regularly and review your mistakes.",
    },
    {
        "key": "technical",
        "label": "Technical Knowledge",
        "description": "Core CS subjects: DBMS, operating systems, computer networks and SQL.",
        "hint": "Revise core subjects and answer interview-style questions.",
    },
    {
        "key": "hr",
        "label": "HR & Communication",
        "description": "Behavioral interviewing (STAR), workplace judgment and communication.",
        "hint": "Do mock interviews and prepare real examples about yourself.",
    },
]
CATEGORY_BY_KEY = {c["key"]: c for c in CATEGORIES}
CATEGORY_BY_LABEL = {c["label"]: c for c in CATEGORIES}

# Skill level labels corresponding to derived rating 1..5
RATING_SCALE = [
    {"value": 1, "label": "Beginner", "meaning": "Score below 20% — build core fundamentals first."},
    {"value": 2, "label": "Basic", "meaning": "Score 20%–44% — review key concepts and practice basics."},
    {"value": 3, "label": "Intermediate", "meaning": "Score 45%–69% — solid foundation, focus on consistency."},
    {"value": 4, "label": "Advanced", "meaning": "Score 70%–89% — strong grasp, polish edge cases and speed."},
    {"value": 5, "label": "Expert", "meaning": "Score 90%–100% — placement-ready across this category."},
]
RATING_LABELS = {item["value"]: item["label"] for item in RATING_SCALE}

VALID_OPTIONS = {"a", "b", "c", "d"}
YEAR_RE = re.compile(r"[1-4]", re.ASCII)
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


# ---------------------------------------------------------------------------
# Datasheet loader (data/careerride_questions.csv)
# ---------------------------------------------------------------------------
def load_question_sets(csv_path=DEFAULT_DATASET_PATH):
    """
    Load alternating question sets from the CareerRide CSV datasheet.
    Returns (question_sets, by_set_and_category) where:
        question_sets[set_id] = [question_dict, ...]
        by_set_and_category[set_id][category_key] = [question_dict, ...]
    """
    question_sets = {}
    by_set_and_category = {}

    with open(csv_path, mode="r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            set_id = int(row["set_id"])
            cat_key = row["category"].strip()
            q = {
                "id": row["id"].strip(),
                "set_id": set_id,
                "category": cat_key,
                "number": int(row["number"]),
                "topic": row["topic"].strip(),
                "source_url": row["source_url"].strip(),
                "prompt": row["prompt"].strip(),
                "options": {
                    "a": row["option_a"].strip(),
                    "b": row["option_b"].strip(),
                    "c": row["option_c"].strip(),
                    "d": row["option_d"].strip(),
                },
                "answer": row["answer"].strip().lower(),
                "explanation": row["explanation"].strip(),
            }
            question_sets.setdefault(set_id, []).append(q)
            by_set_and_category.setdefault(set_id, {c["key"]: [] for c in CATEGORIES})
            by_set_and_category[set_id][cat_key].append(q)

    for sid in by_set_and_category:
        for cat_key in by_set_and_category[sid]:
            by_set_and_category[sid][cat_key].sort(key=lambda item: item["number"])

    return question_sets, by_set_and_category


QUESTION_SETS, QUESTIONS_BY_SET_AND_CATEGORY = load_question_sets()
AVAILABLE_SETS = sorted(QUESTION_SETS.keys())
DEFAULT_SET_ID = AVAILABLE_SETS[0]

# Backwards-compatible aliases pointing to Set 1 and all loaded questions
QUESTIONS = QUESTION_SETS[DEFAULT_SET_ID]
QUESTIONS_BY_CATEGORY = QUESTIONS_BY_SET_AND_CATEGORY[DEFAULT_SET_ID]
QUESTIONS_BY_ID = {
    q["id"]: q
    for qs in QUESTION_SETS.values()
    for q in qs
}
QUESTIONS_PER_CATEGORY = len(QUESTIONS_BY_CATEGORY[CATEGORIES[0]["key"]])


def get_questions_for_set(set_id):
    """Return (questions_list, questions_by_category_dict) for a given set_id."""
    if set_id not in QUESTION_SETS:
        raise ValueError(f"Unknown question set: {set_id!r}")
    return QUESTION_SETS[set_id], QUESTIONS_BY_SET_AND_CATEGORY[set_id]


def select_next_question_set(requested_set=None):
    """
    Pick the active question set, alternating across attempts in session
    (Set 1 -> Set 2 -> Set 3 -> Set 1 ...) unless `?set=N` specifies one.
    """
    if requested_set is not None and requested_set in QUESTION_SETS:
        chosen = requested_set
    else:
        last_set = session.get("last_question_set")
        if last_set in AVAILABLE_SETS:
            next_idx = (AVAILABLE_SETS.index(last_set) + 1) % len(AVAILABLE_SETS)
            chosen = AVAILABLE_SETS[next_idx]
        else:
            chosen = DEFAULT_SET_ID
    session["last_question_set"] = chosen
    return chosen


# ---------------------------------------------------------------------------
# Step 1: scoring and skill gap calculation (pure functions)
# ---------------------------------------------------------------------------
def score_to_rating(score_percent):
    """
    Convert a 0..100 quiz score percentage into a 1..5 skill level:
        90..100 -> 5 (Expert)      [5/5 = 100%]
        70..89  -> 4 (Advanced)    [4/5 = 80%]
        45..69  -> 3 (Intermediate)[3/5 = 60%]
        20..44  -> 2 (Basic)       [1/5 = 20%, 2/5 = 40%]
         0..19  -> 1 (Beginner)    [0/5 = 0%]
    """
    if isinstance(score_percent, bool) or not isinstance(score_percent, (int, float)):
        raise ValueError(f"Score percent must be numeric, got {score_percent!r}.")
    if not 0 <= score_percent <= 100:
        raise ValueError(f"Score percent must be between 0 and 100, got {score_percent}.")

    if score_percent >= 90:
        return 5
    if score_percent >= 70:
        return 4
    if score_percent >= 45:
        return 3
    if score_percent >= 20:
        return 2
    return 1


def evaluate_quiz_answers(answers, set_id=DEFAULT_SET_ID):
    """
    Grade submitted answers ({question_id: 'a'|'b'|'c'|'d'}) against the
    questions belonging to `set_id`.
    Returns:
        {
            "set_id":  int,
            "ratings": {category_key: 1..5},
            "scores":  {category_key: 0.0..100.0},
            "counts":  {category_key: (correct, total)},
            "review":  [...],
        }
    """
    questions, by_category = get_questions_for_set(set_id)
    missing_q = [q["id"] for q in questions if q["id"] not in answers]
    if missing_q:
        raise ValueError("Missing answers for: " + ", ".join(missing_q))

    ratings = {}
    scores = {}
    counts = {}
    review = []

    for category in CATEGORIES:
        cat_key = category["key"]
        cat_questions = by_category[cat_key]
        correct = 0
        for q in cat_questions:
            selected = answers[q["id"]]
            if selected not in VALID_OPTIONS:
                raise ValueError(f"Invalid option {selected!r} for question {q['id']}.")
            is_correct = selected == q["answer"]
            if is_correct:
                correct += 1
            review.append({
                "id": q["id"],
                "category_key": cat_key,
                "category_label": category["label"],
                "number": q["number"],
                "topic": q["topic"],
                "source_url": q["source_url"],
                "prompt": q["prompt"],
                "selected": selected,
                "selected_text": q["options"][selected],
                "correct_answer": q["answer"],
                "correct_text": q["options"][q["answer"]],
                "is_correct": is_correct,
                "explanation": q["explanation"],
            })

        total = len(cat_questions)
        score_percent = round((correct / total) * 100, 1)
        counts[cat_key] = (correct, total)
        scores[cat_key] = score_percent
        ratings[cat_key] = score_to_rating(score_percent)

    return {
        "set_id": set_id,
        "ratings": ratings,
        "scores": scores,
        "counts": counts,
        "review": review,
    }


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


def calculate_skill_gaps(ratings, scores=None, set_id=DEFAULT_SET_ID):
    """
    ratings: {"aptitude": 3, "coding": 2, "technical": 4, "hr": 5}
    scores:  optional {"aptitude": 60.0, ...}
    Returns a list with one dictionary per category (in normal category order).
    "priority_rank" 1 means "work on this first": biggest gap comes first.
    """
    missing = [c["key"] for c in CATEGORIES if c["key"] not in ratings]
    if missing:
        raise ValueError("Missing ratings for: " + ", ".join(missing))

    _, by_category = get_questions_for_set(set_id if set_id in QUESTION_SETS else DEFAULT_SET_ID)
    scores = scores or {}
    results = []
    for category in CATEGORIES:
        cat_key = category["key"]
        rating = ratings[cat_key]
        gap = calculate_gap(rating)
        priority, badge = priority_for_gap(gap)
        score_percent = scores.get(cat_key)
        total_q = len(by_category[cat_key])
        correct_q = round((score_percent / 100.0) * total_q) if score_percent is not None else None
        results.append({
            "key": cat_key,
            "label": category["label"],
            "description": category["description"],
            "hint": category["hint"],
            "rating": rating,
            "rating_label": RATING_LABELS[rating],
            "score_percent": score_percent,
            "correct_count": correct_q,
            "total_questions": total_q,
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
    Validate student details, active question set, and all 20 question responses.
    Returns (data, errors).
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

    raw_set = (form.get("question_set") or "").strip()
    if not raw_set:
        question_set = DEFAULT_SET_ID
    else:
        try:
            question_set = int(raw_set)
            if question_set not in QUESTION_SETS:
                raise ValueError()
        except ValueError:
            errors["question_set"] = "Invalid question set selected."
            question_set = DEFAULT_SET_ID

    active_questions, _ = get_questions_for_set(question_set)
    answers = {}
    for q in active_questions:
        field = "q_" + q["id"]
        raw = (form.get(field) or "").strip().lower()
        cat_label = CATEGORY_BY_KEY[q["category"]]["label"]
        if not raw:
            errors[field] = f"Please answer {cat_label} Question {q['number']}."
        elif raw not in VALID_OPTIONS:
            errors[field] = f"Invalid option selected for {cat_label} Question {q['number']}."
        else:
            answers[q["id"]] = raw

    student = {
        "name": name,
        "email": email,
        "branch": branch,
        "year": int(year) if YEAR_RE.fullmatch(year) else None,
    }

    if len(answers) == len(active_questions) and "question_set" not in errors:
        graded = evaluate_quiz_answers(answers, set_id=question_set)
        return {
            "student": student,
            "question_set": question_set,
            "answers": answers,
            "ratings": graded["ratings"],
            "scores": graded["scores"],
            "review": graded["review"],
        }, errors

    return {
        "student": student,
        "question_set": question_set,
        "answers": answers,
        "ratings": {},
        "scores": {},
        "review": [],
    }, errors


# ---------------------------------------------------------------------------
# Step 3: database operations (all queries use ? placeholders)
# ---------------------------------------------------------------------------
def save_assessment(student, ratings, db_path=None, scores=None):
    """
    Save one assessment: the student (created or updated) and 4 category rows.
    Everything happens in ONE transaction, so either all rows are saved or none.
    Returns {"student_id": ..., "assessed_at": ...}.
    """
    results = calculate_skill_gaps(ratings, scores=scores)
    email = student["email"].strip().lower()
    assessed_at = datetime.now().isoformat(sep=" ", timespec="microseconds")

    with db_session(db_path) as conn:
        row = conn.execute("SELECT id FROM students WHERE email = ?", (email,)).fetchone()
        if row:
            student_id = row["id"]
            conn.execute(
                "UPDATE students SET name = ?, branch = ?, year = ? WHERE id = ?",
                (student["name"].strip(), student["branch"].strip(), int(student["year"]), student_id),
            )
        else:
            cur = conn.execute(
                "INSERT INTO students (name, email, branch, year) VALUES (?, ?, ?, ?)",
                (student["name"].strip(), email, student["branch"].strip(), int(student["year"])),
            )
            student_id = cur.lastrowid

        conn.executemany(
            """INSERT INTO skill_assessments
                   (student_id, category, topic, self_rating, score_percent, target_level, skill_gap, assessed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    student_id,
                    r["label"],
                    OVERALL_TOPIC,
                    r["rating"],
                    r["score_percent"],
                    TARGET_LEVEL,
                    r["gap"],
                    assessed_at,
                )
                for r in results
            ],
        )
        conn.execute(
            "UPDATE user_logins SET student_id = ? WHERE gmail = ?",
            (student_id, email),
        )
    return {"student_id": student_id, "assessed_at": assessed_at}


def get_latest_assessment(student_id, db_path=None):
    """
    Load the student's most recent assessment, or None if there is none.
    Returns {"student": {...}, "assessed_at": "...", "results": [...],
             "average_rating": x, "average_score": y}
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
        """SELECT category, self_rating, score_percent FROM skill_assessments
           WHERE student_id = ? AND topic = ? AND assessed_at = ?""",
        (student_id, OVERALL_TOPIC, latest["latest"]), db_path,
    )
    ratings = {}
    scores = {}
    for r in rows:
        cat_info = CATEGORY_BY_LABEL.get(r["category"])
        if cat_info and r["self_rating"] is not None:
            cat_key = cat_info["key"]
            ratings[cat_key] = r["self_rating"]
            if r["score_percent"] is not None:
                scores[cat_key] = r["score_percent"]

    if len(ratings) != len(CATEGORIES):
        return None

    results = calculate_skill_gaps(ratings, scores=scores)
    score_values = [scores[k] for k in ratings if k in scores]
    avg_score = round(sum(score_values) / len(score_values), 1) if len(score_values) == len(CATEGORIES) else None

    return {
        "student": dict(student),
        "assessed_at": latest["latest"],
        "results": results,
        "average_rating": round(sum(ratings.values()) / len(ratings), 1),
        "average_score": avg_score,
    }


# ---------------------------------------------------------------------------
# Step 4: the web page (called from the /assessment route in app.py)
# ---------------------------------------------------------------------------
def _render_form(form=None, errors=None, general_error=None, status=200, question_set=None):
    set_id = question_set if question_set in QUESTION_SETS else DEFAULT_SET_ID
    active_questions, questions_by_category = get_questions_for_set(set_id)
    return render_template(
        "assessment.html",
        view="form",
        categories=CATEGORIES,
        question_set=set_id,
        available_sets=AVAILABLE_SETS,
        total_questions=len(active_questions),
        questions_per_category=QUESTIONS_PER_CATEGORY,
        questions_by_category=questions_by_category,
        rating_scale=RATING_SCALE,
        form=form or {},
        errors=errors or {},
        general_error=general_error,
    ), status


def handle_assessment_request(db_path):
    """
    GET  /assessment             -> show the alternating real-question assessment form
    GET  /assessment?set=N       -> show specific question set N
    GET  /assessment?student=ID  -> show that student's latest result
    POST /assessment             -> validate answers, grade, save, redirect to result
    """
    if request.method == "POST":
        data, errors = validate_submission(request.form)
        if errors:
            return _render_form(
                form=request.form,
                errors=errors,
                status=400,
                question_set=data["question_set"],
            )

        try:
            saved = save_assessment(
                data["student"],
                data["ratings"],
                db_path,
                scores=data["scores"],
            )
            # Store only compact question IDs + choices so the cookie stays small (<4 KB).
            session["last_assessment_review"] = {
                "student_id": saved["student_id"],
                "assessed_at": saved["assessed_at"],
                "question_set": data["question_set"],
                "answers": data["answers"],
            }
        except (sqlite3.Error, ValueError):
            current_app.logger.exception("Could not save the skill assessment")
            return _render_form(
                form=request.form,
                status=500,
                general_error="Sorry, your assessment could not be saved. Please try again.",
                question_set=data["question_set"],
            )
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

        review = None
        question_set = None
        last_review = session.get("last_assessment_review")
        if (
            last_review
            and last_review.get("student_id") == student_id
            and last_review.get("assessed_at") == result["assessed_at"]
        ):
            question_set = last_review.get("question_set")
            stored_answers = last_review.get("answers")
            if question_set in QUESTION_SETS and isinstance(stored_answers, dict):
                try:
                    review = evaluate_quiz_answers(stored_answers, set_id=question_set)["review"]
                except ValueError:
                    review = None

        return render_template(
            "assessment.html",
            view="result",
            result=result,
            review=review,
            question_set=question_set,
        ), 200

    requested_set = request.args.get("set", type=int)
    active_set = select_next_question_set(requested_set)
    logged_user = auth_module.get_logged_in_user(db_path)
    prefill = None
    if logged_user:
        prefill = {
            "name": logged_user.get("full_name", ""),
            "email": logged_user.get("gmail", ""),
        }
    return _render_form(form=prefill, question_set=active_set)
