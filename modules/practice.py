"""
modules/practice.py
===================
Practice & Test Schedule Module

What this module does
---------------------
1. Displays the student's upcoming Practice & Mock Test sessions synced with
   the Preparation Planner (`preparation_tasks`), showing dates and time slots.
2. Lets students schedule custom timed Practice Drills or Full Mock Tests
   into specific dates and time windows.
3. Serves interactive CareerRide question drills (5 questions by category) or
   full 20-question timed Mock Tests across Sets 1, 2, and 3.
4. Grades submissions, persists scores into `practice_results`, and automatically
   completes linked planner tasks + rebalances upcoming dates/time slots when passed.
"""

import sqlite3
from datetime import date

from flask import current_app, flash, redirect, render_template, request, url_for

from database import db_session, fetch_all
from modules import assessment as assessment_module
from modules import auth as auth_module
from modules import planner as planner_module
from modules import question_generator as qg

DEFAULT_PASS_PERCENT = 60.0
MIN_DURATION_MINUTES = 10
MAX_DURATION_MINUTES = 180

PRACTICE_CATEGORY_OPTIONS = [
    ("aptitude", "Aptitude"),
    ("coding", "Coding"),
    ("technical", "Technical Knowledge"),
    ("hr", "HR & Communication"),
    ("mock", "Full Mock Test"),
]
LABEL_TO_KEY = {c["label"]: c["key"] for c in assessment_module.CATEGORIES}
KEY_TO_LABEL = {k: v for k, v in PRACTICE_CATEGORY_OPTIONS}


def normalize_category_key(raw_category):
    """Map either a key ('aptitude') or label ('Aptitude') or 'mock' to a standard key."""
    cleaned = (raw_category or "").strip()
    lower = cleaned.lower()
    if lower in KEY_TO_LABEL:
        return lower
    if cleaned in LABEL_TO_KEY:
        return LABEL_TO_KEY[cleaned]
    if "aptitude" in lower:
        return "aptitude"
    if "coding" in lower:
        return "coding"
    if "technical" in lower:
        return "technical"
    if "hr" in lower:
        return "hr"
    if "mock" in lower or "revision" in lower:
        return "mock"
    return "aptitude"


def select_practice_questions(category_key="aptitude", set_id=1):
    """Return (questions_list, normalized_key, display_label) from the CareerRide dataset."""
    valid_set = set_id if set_id in assessment_module.AVAILABLE_SETS else assessment_module.DEFAULT_SET_ID
    norm_key = normalize_category_key(category_key)
    all_questions, by_category = assessment_module.get_questions_for_set(valid_set)
    if norm_key == "mock":
        return list(all_questions), "mock", "Full Mock Test"
    return list(by_category[norm_key]), norm_key, KEY_TO_LABEL[norm_key]


def grade_practice_submission(form, questions):
    """
    Validate and grade submitted practice answers against `questions`.
    Returns (graded_dict, errors).
    """
    errors = {}
    review = []
    correct_count = 0

    for idx, q in enumerate(questions, start=1):
        field = "q_" + q["id"]
        selected = (form.get(field) or "").strip().lower()
        if not selected:
            errors[field] = f"Please answer Question {idx}."
        elif selected not in assessment_module.VALID_OPTIONS:
            errors[field] = f"Invalid option selected for Question {idx}."
        else:
            is_correct = selected == q["answer"]
            if is_correct:
                correct_count += 1
            review.append({
                "id": q["id"],
                "number": idx,
                "category": assessment_module.CATEGORY_BY_KEY[q["category"]]["label"],
                "topic": q["topic"],
                "prompt": q["prompt"],
                "selected": selected,
                "selected_text": q["options"][selected],
                "correct_answer": q["answer"],
                "correct_text": q["options"][q["answer"]],
                "is_correct": is_correct,
                "explanation": q["explanation"],
            })

    total = len(questions)
    percent = round((correct_count / total) * 100, 1) if total else 0.0
    return {
        "score": correct_count,
        "max_score": total,
        "percent": percent,
        "passed": percent >= DEFAULT_PASS_PERCENT,
        "review": review,
    }, errors


def validate_custom_test_schedule(form, today=None):
    """Validate inputs when scheduling a custom practice or mock test slot."""
    today_d = today or date.today()
    errors = {}

    raw_student = (form.get("student_id") or "").strip()
    student_id = None
    try:
        student_id = int(raw_student)
        if student_id <= 0:
            raise ValueError()
    except ValueError:
        errors["student_id"] = "Please select a valid student."
        student_id = None

    title = " ".join((form.get("test_title") or "").split())
    if not title:
        errors["test_title"] = "Please enter a practice or mock test title."
    elif len(title) > 120:
        errors["test_title"] = "Title must be 120 characters or fewer."

    category_key = normalize_category_key(form.get("category") or "mock")
    category_label = KEY_TO_LABEL.get(category_key, "Full Mock Test")

    raw_date = (form.get("due_date") or "").strip()
    due_date = None
    if not raw_date:
        errors["due_date"] = "Please choose a scheduled date."
    else:
        try:
            due_date = date.fromisoformat(raw_date)
            if due_date < today_d:
                errors["due_date"] = "Scheduled date cannot be in the past."
                due_date = None
        except ValueError:
            errors["due_date"] = "Please enter a valid date (YYYY-MM-DD)."

    start_time = (form.get("start_time") or planner_module.DEFAULT_DAILY_START_TIME).strip()
    if not planner_module.TIME_RE.fullmatch(start_time):
        errors["start_time"] = "Please enter a valid start time (HH:MM)."

    raw_dur = (form.get("duration_minutes") or "45").strip()
    duration_minutes = 45
    try:
        duration_minutes = int(raw_dur)
        if not MIN_DURATION_MINUTES <= duration_minutes <= MAX_DURATION_MINUTES:
            errors["duration_minutes"] = (
                f"Duration must be between {MIN_DURATION_MINUTES} and {MAX_DURATION_MINUTES} minutes."
            )
    except ValueError:
        errors["duration_minutes"] = "Duration must be a whole number of minutes."

    return {
        "student_id": student_id,
        "title": title,
        "category_key": category_key,
        "category_label": category_label,
        "due_date": due_date,
        "start_time": start_time,
        "duration_minutes": duration_minutes,
    }, errors


def schedule_custom_test_session(data, db_path=None):
    """Insert a scheduled practice/mock test session into preparation_tasks."""
    due_iso = data["due_date"].isoformat()
    time_slot = planner_module._format_time_slot(data["start_time"], 0, data["duration_minutes"])
    description = (
        f"Scheduled {data['category_label']} session "
        f"({data['duration_minutes']} min at {time_slot})."
    )

    with db_session(db_path) as conn:
        max_order_row = conn.execute(
            "SELECT COALESCE(MAX(sort_order), 0) AS m FROM preparation_tasks WHERE student_id = ? AND category != ?",
            (data["student_id"], planner_module.MILESTONE_CATEGORY),
        ).fetchone()
        next_order = int(max_order_row["m"] or 0) + 1
        cur = conn.execute(
            """
            INSERT INTO preparation_tasks
                (student_id, skill_assessment_id, title, description, category,
                 due_date, time_slot, estimated_minutes, sort_order, status)
            VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
            (
                data["student_id"],
                data["title"],
                description,
                data["category_label"],
                due_iso,
                time_slot,
                data["duration_minutes"],
                next_order,
            ),
        )
        return cur.lastrowid


def save_practice_attempt(student_id, category_label, topic, score, max_score,
                          duration_minutes, task_id=None, db_path=None,
                          auto_complete=True):
    """
    Persist an attempt in `practice_results`. If linked to a planner task and
    score >= DEFAULT_PASS_PERCENT (60%), mark the task completed and rebalance schedule.
    """
    valid_task_id = None
    with db_session(db_path) as conn:
        if task_id:
            row = conn.execute(
                "SELECT id FROM preparation_tasks WHERE id = ? AND student_id = ?",
                (task_id, student_id),
            ).fetchone()
            if row:
                valid_task_id = row["id"]

        cur = conn.execute(
            """
            INSERT INTO practice_results
                (student_id, task_id, category, topic, score, max_score, duration_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student_id,
                valid_task_id,
                category_label,
                topic,
                float(score),
                float(max_score),
                max(0, int(duration_minutes)),
            ),
        )
        attempt_id = cur.lastrowid

    percent = round((score / max_score) * 100, 1) if max_score else 0.0
    task_completed = False
    rebalance = None
    if valid_task_id and auto_complete and percent >= DEFAULT_PASS_PERCENT:
        outcome = planner_module.apply_task_status(
            valid_task_id, student_id, "completed", db_path=db_path
        )
        task_completed = outcome["updated"] > 0
        rebalance = outcome["rebalance"]

    return {
        "attempt_id": attempt_id,
        "percent": percent,
        "task_completed": task_completed,
        "rebalance": rebalance,
    }


def get_practice_history(student_id, db_path=None):
    """Return recent practice & mock test attempts for `student_id`, newest first."""
    rows = fetch_all(
        """
        SELECT pr.id, pr.student_id, pr.task_id, pr.category, pr.topic,
               pr.score, pr.max_score, pr.duration_minutes, pr.practiced_at,
               pt.title AS task_title
        FROM practice_results pr
        LEFT JOIN preparation_tasks pt ON pt.id = pr.task_id
        WHERE pr.student_id = ?
        ORDER BY pr.practiced_at DESC, pr.id DESC
        LIMIT 20
        """,
        (student_id,),
        db_path,
    )
    history = []
    for r in rows:
        item = dict(r)
        max_s = item["max_score"] or 1
        item["percent"] = round((item["score"] / max_s) * 100, 1)
        item["passed"] = item["percent"] >= DEFAULT_PASS_PERCENT
        history.append(item)
    return history


def _resolve_selected_student(students, db_path, requested_id=None):
    if not students:
        return None
    valid_ids = {s["id"] for s in students}
    if requested_id in valid_ids:
        return requested_id
    logged_user = auth_module.get_logged_in_user(db_path)
    if logged_user and logged_user.get("student_id") in valid_ids:
        return logged_user["student_id"]
    return students[0]["id"]


def _render_practice(db_path, selected_student_id=None, category_key="aptitude", set_id=1,
                     task_id=None, ai_set_id=None, practice_result=None, quiz_errors=None,
                     form_values=None, schedule_errors=None, schedule_form=None,
                     general_error=None, status=200):
    students = planner_module.get_students_with_assessments(db_path)
    student_id = _resolve_selected_student(students, db_path, requested_id=selected_student_id)

    plan = planner_module.get_student_plan(student_id, db_path) if student_id else None
    history = get_practice_history(student_id, db_path) if student_id else []
    assessment = assessment_module.get_latest_assessment(student_id, db_path) if student_id else None

    weakest_key = "aptitude"
    if assessment and assessment.get("results"):
        top_priority = min(assessment["results"], key=lambda r: r["priority_rank"])
        weakest_key = top_priority["key"]

    linked_task = None
    if plan and task_id:
        linked_task = next((t for t in plan["tasks"] if t["id"] == task_id), None)
        if linked_task and category_key == "aptitude" and not request.args.get("category"):
            category_key = normalize_category_key(linked_task["category"])

    active_ai_set = qg.get_ai_question_set(ai_set_id, student_id=student_id, db_path=db_path) if ai_set_id else None
    if active_ai_set:
        questions = active_ai_set["questions"]
        active_key = active_ai_set["category_key"]
        active_label = f"{active_ai_set['category_label']} (Gemini AI · {active_ai_set['topic_focus']})"
    else:
        questions, active_key, active_label = select_practice_questions(category_key, set_id=set_id)

    return render_template(
        "practice.html",
        students=students,
        selected_student_id=student_id,
        plan=plan,
        history=history,
        linked_task=linked_task,
        category_options=PRACTICE_CATEGORY_OPTIONS,
        available_sets=assessment_module.AVAILABLE_SETS,
        active_key=active_key,
        active_label=active_label,
        active_set=set_id if set_id in assessment_module.AVAILABLE_SETS else 1,
        active_ai_set=active_ai_set,
        weakest_key=weakest_key,
        gemini_status=qg.get_gemini_status(),
        questions=questions,
        practice_result=practice_result,
        quiz_errors=quiz_errors or {},
        form_values=form_values or {},
        schedule_errors=schedule_errors or {},
        schedule_form=schedule_form or {},
        general_error=general_error,
        today_iso=date.today().isoformat(),
    ), status


def handle_practice_request(db_path):
    """
    GET  /practice -> show scheduled practice/tests, interactive quiz runner, and test history
    POST /practice -> generate Gemini AI set, submit practice quiz, or schedule a custom test session
    """
    if request.method == "POST":
        action = (request.form.get("action") or "submit_practice").strip()

        if action == "generate_ai":
            student_id = request.form.get("student_id", type=int)
            category_key = normalize_category_key(request.form.get("category_key") or "aptitude")
            if category_key == "mock":
                category_key = "aptitude"
            topic_focus = (request.form.get("topic_focus") or "").strip()
            difficulty = (request.form.get("difficulty") or "standard").strip().lower()
            task_id = request.form.get("task_id", type=int)

            if not student_id:
                return _render_practice(
                    db_path,
                    general_error="Please select a student first.",
                    status=400,
                )

            try:
                generated = qg.generate_and_save_question_set(
                    student_id=student_id,
                    category_key=category_key,
                    topic_focus=topic_focus,
                    difficulty=difficulty,
                    db_path=db_path,
                )
                flash(
                    f"Generated 5 verified {generated['category_label']} questions using {generated['model_name']}!",
                    "success",
                )
                return redirect(
                    url_for(
                        "practice_page",
                        student=student_id,
                        ai_set=generated["ai_set_id"],
                        task_id=task_id,
                    )
                    + "#practice-runner"
                )
            except (RuntimeError, ValueError) as exc:
                flash(str(exc), "warning")
                return redirect(url_for("practice_page", student=student_id, category=category_key, task_id=task_id))
            except Exception as exc:
                current_app.logger.warning("Gemini question generation failed: %s", exc)
                flash("Could not generate Gemini questions right now. Using CareerRide dataset instead.", "warning")
                return redirect(url_for("practice_page", student=student_id, category=category_key, task_id=task_id))

        if action == "schedule_session":
            data, errors = validate_custom_test_schedule(request.form)
            if errors:
                return _render_practice(
                    db_path,
                    selected_student_id=data["student_id"],
                    schedule_errors=errors,
                    schedule_form=request.form,
                    status=400,
                )
            try:
                schedule_custom_test_session(data, db_path=db_path)
                flash(
                    f"Scheduled '{data['title']}' on {data['due_date'].isoformat()} at {data['start_time']}.",
                    "success",
                )
            except sqlite3.Error:
                current_app.logger.exception("Could not schedule practice test")
                return _render_practice(
                    db_path,
                    selected_student_id=data["student_id"],
                    schedule_form=request.form,
                    general_error="Sorry, the practice session could not be scheduled.",
                    status=500,
                )
            return redirect(url_for("practice_page", student=data["student_id"]))

        # action == "submit_practice"
        student_id = request.form.get("student_id", type=int)
        category_key = request.form.get("category_key") or "aptitude"
        set_id = request.form.get("set_id", type=int) or 1
        task_id = request.form.get("task_id", type=int)
        ai_set_id = request.form.get("ai_set_id", type=int)
        elapsed_raw = request.form.get("duration_minutes", type=int)
        duration_minutes = max(1, min(MAX_DURATION_MINUTES, elapsed_raw)) if elapsed_raw else 10

        active_ai_set = qg.get_ai_question_set(ai_set_id, student_id=student_id, db_path=db_path) if ai_set_id else None
        if active_ai_set:
            questions = active_ai_set["questions"]
            active_key = active_ai_set["category_key"]
            active_label = active_ai_set["category_label"]
            topic_summary = f"Gemini AI · {active_ai_set['topic_focus']}"
        else:
            questions, active_key, active_label = select_practice_questions(category_key, set_id=set_id)
            topic_summary = f"Set {set_id} ({len(questions)} Qs)"

        graded, quiz_errors = grade_practice_submission(request.form, questions)
        if quiz_errors:
            return _render_practice(
                db_path,
                selected_student_id=student_id,
                category_key=active_key,
                set_id=set_id,
                task_id=task_id,
                ai_set_id=ai_set_id,
                quiz_errors=quiz_errors,
                form_values=request.form,
                general_error="Please answer every question before submitting your practice test.",
                status=400,
            )

        saved_meta = None
        if student_id:
            try:
                saved_meta = save_practice_attempt(
                    student_id=student_id,
                    category_label=active_label,
                    topic=topic_summary,
                    score=graded["score"],
                    max_score=graded["max_score"],
                    duration_minutes=duration_minutes,
                    task_id=task_id,
                    db_path=db_path,
                )
                if saved_meta["task_completed"]:
                    flash(
                        f"Great score ({graded['percent']}%)! Linked planner task marked completed "
                        "and upcoming dates rebalanced.",
                        "success",
                    )
                else:
                    flash(f"Practice test graded: {graded['score']} / {graded['max_score']} ({graded['percent']}%).", "info")
            except sqlite3.Error:
                current_app.logger.exception("Could not save practice attempt")
                return _render_practice(
                    db_path,
                    selected_student_id=student_id,
                    category_key=active_key,
                    set_id=set_id,
                    task_id=task_id,
                    ai_set_id=ai_set_id,
                    general_error="Could not save your practice result.",
                    status=500,
                )

        graded["saved_meta"] = saved_meta
        return _render_practice(
            db_path,
            selected_student_id=student_id,
            category_key=active_key,
            set_id=set_id,
            task_id=task_id,
            ai_set_id=ai_set_id,
            practice_result=graded,
        )

    # GET /practice
    student_id = request.args.get("student", type=int)
    category_key = request.args.get("category") or "aptitude"
    set_id = request.args.get("set", type=int) or 1
    task_id = request.args.get("task_id", type=int)
    ai_set_id = request.args.get("ai_set", type=int)
    return _render_practice(
        db_path,
        selected_student_id=student_id,
        category_key=category_key,
        set_id=set_id,
        task_id=task_id,
        ai_set_id=ai_set_id,
    )
