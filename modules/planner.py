"""
modules/planner.py
==================
Member 2 - Preparation Planner

What this module does
---------------------
1. Reads a student's latest Skill Assessment & Skill Gap data (via assessment.py).
2. Accepts a target interview date (and optional daily study hours) from the user.
3. Validates all inputs on the server (date format, not in the past, valid student).
4. Generates a prioritized, day-by-day preparation plan weighted by skill gaps
   (biggest skill gaps get more tasks and earlier deadlines).
5. Persists tasks in the shared `preparation_tasks` table and supports updating
   task status (pending -> in_progress -> completed).
"""

import sqlite3
from datetime import date, datetime, timedelta

from flask import current_app, flash, redirect, render_template, request, url_for

from database import db_session, fetch_all, fetch_one
from modules import assessment as assessment_module

MILESTONE_CATEGORY = "Interview Milestone"
VALID_STATUSES = ("pending", "in_progress", "completed")
DEFAULT_HOURS_PER_DAY = 2
MIN_HOURS_PER_DAY = 1
MAX_HOURS_PER_DAY = 12

# Curated study task templates ordered from foundational to advanced/mock.
TASK_BANK = {
    "Aptitude": [
        ("Quantitative Basics & Formulas", "Review percentages, ratios, profit & loss, and time-speed-distance formulas."),
        ("Logical Reasoning Drills", "Solve 25 timed puzzles covering seating arrangement, syllogisms, and blood relations."),
        ("Verbal Ability & Reading Comp", "Practise 3 reading comprehension passages and grammar error-spotting sets."),
        ("Timed Aptitude Mock Test", "Complete a 45-minute full-length aptitude mock test and review every wrong answer."),
    ],
    "Coding": [
        ("Arrays, Strings & Hashing", "Solve 6 foundational problems on two-pointers, sliding window, and hash maps."),
        ("Recursion, Trees & Graphs", "Practise tree/graph traversals (BFS/DFS) and write clean recursive solutions."),
        ("Dynamic Programming & Greedy", "Work through 4 classic DP and greedy interview problems with complexity analysis."),
        ("Timed Coding Assessment", "Solve 2 medium coding problems in 60 minutes without looking at hints."),
    ],
    "Technical Knowledge": [
        ("DBMS & SQL Queries", "Revise normalization, ACID properties, indexing, and write 10 SQL join/aggregation queries."),
        ("Operating Systems & Concurrency", "Review processes vs threads, deadlocks, scheduling, and memory management."),
        ("Computer Networks & OOP", "Revise TCP/IP, HTTP/HTTPS, DNS, and OOP design principles with real examples."),
        ("Core CS Rapid-Fire Q&A", "Answer 20 common technical interview questions aloud and refine concise explanations."),
    ],
    "HR & Communication": [
        ("Craft Your Introduction & Resume Pitch", "Prepare a crisp 90-second self-introduction and walkthrough of top projects."),
        ("STAR Method Behavioral Stories", "Write 5 structured STAR stories covering teamwork, conflict, leadership, and failure."),
        ("Company & Role Research", "Research target companies, common HR questions, and prepare 3 thoughtful questions to ask."),
        ("Full HR Mock Interview", "Record or practice a 20-minute mock HR interview focusing on clarity and confidence."),
    ],
}


# ---------------------------------------------------------------------------
# Step 1: Validation & Pure Planning Logic
# ---------------------------------------------------------------------------
def validate_plan_request(form, today=None):
    """
    Validate interview date, student_id, and optional hours_per_day.
    Returns (data, errors).
    """
    today = today or date.today()
    errors = {}

    raw_student = (form.get("student_id") or "").strip()
    student_id = None
    if not raw_student:
        errors["student_id"] = "Please select a student with a completed skill assessment."
    else:
        try:
            student_id = int(raw_student)
            if student_id <= 0:
                raise ValueError()
        except ValueError:
            errors["student_id"] = "Invalid student selection."
            student_id = None

    raw_date = (form.get("interview_date") or "").strip()
    interview_date = None
    if not raw_date:
        errors["interview_date"] = "Please choose your target interview date."
    else:
        try:
            interview_date = date.fromisoformat(raw_date)
            if interview_date < today:
                errors["interview_date"] = "Interview date cannot be in the past."
                interview_date = None
        except ValueError:
            errors["interview_date"] = "Please enter a valid date (YYYY-MM-DD)."

    raw_hours = (form.get("hours_per_day") or "").strip()
    hours_per_day = DEFAULT_HOURS_PER_DAY
    if raw_hours:
        try:
            hours_per_day = int(raw_hours)
            if not MIN_HOURS_PER_DAY <= hours_per_day <= MAX_HOURS_PER_DAY:
                errors["hours_per_day"] = f"Daily study hours must be between {MIN_HOURS_PER_DAY} and {MAX_HOURS_PER_DAY}."
        except ValueError:
            errors["hours_per_day"] = "Daily study hours must be a whole number."

    data = {
        "student_id": student_id,
        "interview_date": interview_date,
        "hours_per_day": hours_per_day,
    }
    return data, errors


def _task_count_for_gap(gap):
    """Determine how many tasks to schedule for a category based on its skill gap."""
    if gap >= 3:
        return 4
    if gap == 2:
        return 3
    if gap == 1:
        return 2
    return 1


def generate_study_plan(assessment, interview_date, hours_per_day=DEFAULT_HOURS_PER_DAY,
                        today=None, assessment_ids=None):
    """
    Build a prioritized list of preparation tasks from a student's assessment
    and target interview date.

    Returns:
        {
            "days_remaining": int,
            "total_hours": int,
            "tasks": [...],
            "category_summary": [...],
        }
    """
    today = today or date.today()
    days_remaining = max(0, (interview_date - today).days)
    effective_days = max(1, days_remaining)
    assessment_ids = assessment_ids or {}

    # Sort categories by priority_rank (biggest gap first)
    prioritized = sorted(assessment["results"], key=lambda r: r["priority_rank"])

    raw_tasks = []
    category_summary = []
    total_gap_weight = sum(max(1, r["gap"] + 1) for r in prioritized)
    total_hours = effective_days * hours_per_day

    for item in prioritized:
        label = item["label"]
        gap = item["gap"]
        count = _task_count_for_gap(gap)
        bank = TASK_BANK.get(label, [])
        chosen = bank[:count]

        weight = max(1, gap + 1)
        allocated_hours = max(1, round(total_hours * (weight / total_gap_weight)))

        category_summary.append({
            "label": label,
            "rating": item["rating"],
            "gap": gap,
            "priority": item["priority"],
            "badge": item["badge"],
            "task_count": len(chosen),
            "allocated_hours": allocated_hours,
        })

        for title, description in chosen:
            raw_tasks.append({
                "category": label,
                "priority": item["priority"],
                "badge": item["badge"],
                "gap": gap,
                "skill_assessment_id": assessment_ids.get(label),
                "title": f"[{item['priority']}] {title}",
                "description": description,
            })

    # Add a final pre-interview mock & revision task
    raw_tasks.append({
        "category": "Final Revision",
        "priority": "Final",
        "badge": "primary",
        "gap": 0,
        "skill_assessment_id": None,
        "title": "Final Pre-Interview Revision & Mock Check",
        "description": "Review key formulas, core CS notes, and your STAR stories. Rest well before the interview.",
    })

    # Distribute due dates evenly from today up to the interview date
    n_tasks = len(raw_tasks)
    for idx, task in enumerate(raw_tasks):
        if days_remaining == 0:
            due = today
        elif idx == n_tasks - 1:
            # Final revision lands on the day before (or interview day if 1 day away)
            due = interview_date - timedelta(days=1) if days_remaining >= 2 else interview_date
        else:
            span = max(1, days_remaining - 1) if days_remaining >= 2 else days_remaining
            offset = round((idx / max(1, n_tasks - 2)) * span)
            due = min(interview_date, today + timedelta(days=offset))
        task["due_date"] = due.isoformat()
        task["status"] = "pending"

    return {
        "days_remaining": days_remaining,
        "total_hours": total_hours,
        "tasks": raw_tasks,
        "category_summary": category_summary,
    }


# ---------------------------------------------------------------------------
# Step 2: Database Helpers (all queries use ? placeholders)
# ---------------------------------------------------------------------------
def get_students_with_assessments(db_path=None):
    """Return students who have at least one skill assessment, newest first."""
    rows = fetch_all(
        """
        SELECT s.id, s.name, s.email, s.branch, s.year, MAX(sa.assessed_at) AS assessed_at
        FROM students s
        JOIN skill_assessments sa ON sa.student_id = s.id
        GROUP BY s.id
        ORDER BY assessed_at DESC
        """,
        (),
        db_path,
    )
    return [dict(r) for r in rows]


def _get_latest_assessment_ids(student_id, assessed_at, db_path=None):
    """Map category label -> skill_assessments.id for the latest submission."""
    rows = fetch_all(
        """
        SELECT id, category FROM skill_assessments
        WHERE student_id = ? AND assessed_at = ?
        """,
        (student_id, assessed_at),
        db_path,
    )
    return {r["category"]: r["id"] for r in rows}


def save_plan(student_id, interview_date, tasks, db_path=None):
    """
    Replace the student's existing preparation plan with the newly generated
    tasks and an Interview Milestone row inside a single transaction.
    """
    interview_iso = interview_date.isoformat() if isinstance(interview_date, date) else str(interview_date)

    with db_session(db_path) as conn:
        conn.execute("DELETE FROM preparation_tasks WHERE student_id = ?", (student_id,))

        conn.execute(
            """
            INSERT INTO preparation_tasks
                (student_id, skill_assessment_id, title, description, category, due_date, status)
            VALUES (?, NULL, ?, ?, ?, ?, 'pending')
            """,
            (
                student_id,
                "Target Interview Day",
                f"Interview scheduled for {interview_iso}",
                MILESTONE_CATEGORY,
                interview_iso,
            ),
        )

        conn.executemany(
            """
            INSERT INTO preparation_tasks
                (student_id, skill_assessment_id, title, description, category, due_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    student_id,
                    t.get("skill_assessment_id"),
                    t["title"],
                    t["description"],
                    t["category"],
                    t["due_date"],
                    t.get("status", "pending"),
                )
                for t in tasks
            ],
        )


def get_student_plan(student_id, db_path=None):
    """
    Load the student's saved preparation tasks and target interview date.
    Returns None if no plan has been generated yet.
    """
    rows = fetch_all(
        """
        SELECT id, student_id, skill_assessment_id, title, description,
               category, due_date, status, created_at, completed_at
        FROM preparation_tasks
        WHERE student_id = ?
        ORDER BY due_date ASC, id ASC
        """,
        (student_id,),
        db_path,
    )
    if not rows:
        return None

    interview_date = None
    tasks = []
    for r in rows:
        row_dict = dict(r)
        if row_dict["category"] == MILESTONE_CATEGORY:
            interview_date = row_dict["due_date"]
        else:
            tasks.append(row_dict)

    if not tasks and interview_date is None:
        return None

    total = len(tasks)
    completed = sum(1 for t in tasks if t["status"] == "completed")
    in_progress = sum(1 for t in tasks if t["status"] == "in_progress")
    pending = total - completed - in_progress
    completion_percent = round((completed / total) * 100) if total else 0

    days_remaining = None
    if interview_date:
        try:
            days_remaining = (date.fromisoformat(interview_date) - date.today()).days
        except ValueError:
            days_remaining = None

    return {
        "interview_date": interview_date,
        "days_remaining": days_remaining,
        "tasks": tasks,
        "stats": {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "completion_percent": completion_percent,
        },
    }


def update_task_status(task_id, student_id, new_status, db_path=None):
    """Update a task's status and completed_at timestamp."""
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {new_status!r}")

    completed_at = (
        datetime.now().isoformat(sep=" ", timespec="seconds")
        if new_status == "completed"
        else None
    )
    with db_session(db_path) as conn:
        cur = conn.execute(
            """
            UPDATE preparation_tasks
            SET status = ?, completed_at = ?
            WHERE id = ? AND student_id = ?
            """,
            (new_status, completed_at, task_id, student_id),
        )
        return cur.rowcount


# ---------------------------------------------------------------------------
# Step 3: Web Request Handler (called from /planner in app.py)
# ---------------------------------------------------------------------------
def _render_planner(db_path, selected_student_id=None, form=None, errors=None,
                    general_error=None, status=200):
    students = get_students_with_assessments(db_path)

    if selected_student_id is None and students:
        selected_student_id = students[0]["id"]

    assessment = None
    plan = None
    if selected_student_id is not None:
        assessment = assessment_module.get_latest_assessment(selected_student_id, db_path)
        if assessment is not None:
            plan = get_student_plan(selected_student_id, db_path)

    return render_template(
        "planner.html",
        students=students,
        selected_student_id=selected_student_id,
        assessment=assessment,
        plan=plan,
        form=form or {},
        errors=errors or {},
        general_error=general_error,
        today_iso=date.today().isoformat(),
    ), status


def handle_planner_request(db_path):
    """
    GET  /planner               -> show planner for selected (or latest) student
    GET  /planner?student=ID    -> show planner for student ID
    POST /planner               -> generate plan OR update task status
    """
    if request.method == "POST":
        action = (request.form.get("action") or "generate").strip()

        if action == "update_status":
            student_id = request.form.get("student_id", type=int)
            task_id = request.form.get("task_id", type=int)
            new_status = (request.form.get("status") or "").strip()
            if not student_id or not task_id or new_status not in VALID_STATUSES:
                return _render_planner(
                    db_path,
                    selected_student_id=student_id,
                    general_error="Invalid task update request.",
                    status=400,
                )
            try:
                update_task_status(task_id, student_id, new_status, db_path)
                flash("Task status updated.", "success")
            except sqlite3.Error:
                current_app.logger.exception("Could not update task status")
                return _render_planner(
                    db_path,
                    selected_student_id=student_id,
                    general_error="Could not update the task. Please try again.",
                    status=500,
                )
            return redirect(url_for("planner_page", student=student_id))

        # Generate a new preparation plan
        data, errors = validate_plan_request(request.form)
        if errors:
            return _render_planner(
                db_path,
                selected_student_id=data["student_id"],
                form=request.form,
                errors=errors,
                status=400,
            )

        student_id = data["student_id"]
        try:
            assessment = assessment_module.get_latest_assessment(student_id, db_path)
            if assessment is None:
                return _render_planner(
                    db_path,
                    selected_student_id=student_id,
                    form=request.form,
                    general_error="No skill assessment found for that student. Please complete an assessment first.",
                    status=404,
                )

            assessment_ids = _get_latest_assessment_ids(
                student_id, assessment["assessed_at"], db_path
            )
            generated = generate_study_plan(
                assessment,
                data["interview_date"],
                hours_per_day=data["hours_per_day"],
                assessment_ids=assessment_ids,
            )
            save_plan(student_id, data["interview_date"], generated["tasks"], db_path)
            flash(
                f"Preparation plan created with {len(generated['tasks'])} tasks leading up to {data['interview_date'].isoformat()}!",
                "success",
            )
        except sqlite3.Error:
            current_app.logger.exception("Could not generate preparation plan")
            return _render_planner(
                db_path,
                selected_student_id=student_id,
                form=request.form,
                general_error="Sorry, your preparation plan could not be saved. Please try again.",
                status=500,
            )

        return redirect(url_for("planner_page", student=student_id))

    # GET request
    student_id = request.args.get("student", type=int)
    try:
        return _render_planner(db_path, selected_student_id=student_id)
    except sqlite3.Error:
        current_app.logger.exception("Could not load preparation planner")
        return render_template(
            "planner.html",
            students=[],
            selected_student_id=None,
            assessment=None,
            plan=None,
            form={},
            errors={},
            general_error="Sorry, the preparation planner could not be loaded.",
            today_iso=date.today().isoformat(),
        ), 500
