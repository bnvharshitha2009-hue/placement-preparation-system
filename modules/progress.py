"""
modules/progress.py
===================
Member 3 - Progress Tracking, Dashboard, Analytics and Reports

What this module does
---------------------
1. Reads real student records from SQLite (`students`, `practice_results`,
   `skill_assessments`, and `preparation_tasks`) using parameterized queries.
2. Computes quiz attempt counts, average quiz scores, topic-wise scores, and
   preparation task completion percentages safely (never divides by zero).
3. Identifies weak topics and skill gaps from actual assessment scores and
   quiz results without fabricating sample student data.
4. Generates database-driven recommendations and a structured printable report.
5. Supports logging real practice quiz results into `practice_results`.
"""

import sqlite3
from datetime import date, datetime

from flask import current_app, flash, redirect, render_template, request, url_for

from database import db_session, fetch_all, fetch_one

MILESTONE_CATEGORY = "Interview Milestone"
WEAK_SCORE_THRESHOLD = 50.0
NEEDS_IMPROVEMENT_THRESHOLD = 65.0
STRONG_SCORE_THRESHOLD = 70.0

DEFAULT_CATEGORIES = (
    "Aptitude",
    "Coding",
    "Technical Knowledge",
    "HR & Communication",
)


# ---------------------------------------------------------------------------
# Database Queries (parameterized SQL only)
# ---------------------------------------------------------------------------
def get_all_students(db_path=None):
    """Return all registered students, most recently active first."""
    rows = fetch_all(
        """
        SELECT
            s.id,
            s.name,
            s.email,
            s.branch,
            s.year,
            s.created_at,
            MAX(sa.assessed_at) AS last_assessed_at,
            MAX(pr.practiced_at) AS last_practiced_at
        FROM students s
        LEFT JOIN skill_assessments sa ON sa.student_id = s.id
        LEFT JOIN practice_results pr ON pr.student_id = s.id
        GROUP BY s.id
        ORDER BY COALESCE(MAX(pr.practiced_at), MAX(sa.assessed_at), s.created_at) DESC, s.id DESC
        """,
        (),
        db_path,
    )
    return [dict(r) for r in rows]


def get_student(student_id, db_path=None):
    """Fetch a single student record by ID, or None if not found."""
    row = fetch_one(
        "SELECT id, name, email, branch, year, created_at FROM students WHERE id = ?",
        (student_id,),
        db_path,
    )
    return dict(row) if row is not None else None


def get_practice_results(student_id, db_path=None):
    """Return all practice quiz attempts for a student, newest first."""
    rows = fetch_all(
        """
        SELECT id, student_id, task_id, category, topic, score, max_score,
               duration_minutes, practiced_at
        FROM practice_results
        WHERE student_id = ?
        ORDER BY practiced_at DESC, id DESC
        """,
        (student_id,),
        db_path,
    )
    return [dict(r) for r in rows]


def get_latest_assessment_rows(student_id, db_path=None):
    """Return the rows from the student's most recent skill assessment."""
    latest = fetch_one(
        "SELECT MAX(assessed_at) AS latest FROM skill_assessments WHERE student_id = ?",
        (student_id,),
        db_path,
    )
    if latest is None or latest["latest"] is None:
        return []

    rows = fetch_all(
        """
        SELECT id, student_id, category, topic, self_rating, score_percent,
               target_level, skill_gap, assessed_at
        FROM skill_assessments
        WHERE student_id = ? AND assessed_at = ?
        ORDER BY id ASC
        """,
        (student_id, latest["latest"]),
        db_path,
    )
    return [dict(r) for r in rows]


def get_preparation_tasks(student_id, db_path=None):
    """
    Return all preparation tasks for a student (including Interview Milestone
    rows, which calculation helpers exclude from actionable task counts).
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
    return [dict(r) for r in rows]


def validate_practice_form(form):
    """Validate inputs for logging a practice quiz result."""
    errors = {}

    raw_student = (form.get("student_id") or "").strip()
    student_id = None
    if not raw_student:
        errors["student_id"] = "Please select a student."
    else:
        try:
            student_id = int(raw_student)
            if student_id <= 0:
                raise ValueError()
        except ValueError:
            errors["student_id"] = "Invalid student selected."
            student_id = None

    category = (form.get("category") or "").strip()
    if not category:
        errors["category"] = "Please select or enter a category."
    elif len(category) > 80:
        errors["category"] = "Category must be 80 characters or fewer."

    topic = (form.get("topic") or "").strip()
    if not topic:
        errors["topic"] = "Please enter a topic name (e.g. DBMS, Arrays, Operating Systems)."
    elif len(topic) > 100:
        errors["topic"] = "Topic name must be 100 characters or fewer."

    score = None
    max_score = None
    raw_score = (form.get("score") or "").strip()
    raw_max = (form.get("max_score") or "").strip()

    try:
        score = float(raw_score)
        if score < 0:
            errors["score"] = "Score cannot be negative."
    except ValueError:
        errors["score"] = "Score must be a valid number."

    try:
        max_score = float(raw_max)
        if max_score <= 0:
            errors["max_score"] = "Maximum score must be greater than 0."
    except ValueError:
        errors["max_score"] = "Maximum score must be a valid number."

    if "score" not in errors and "max_score" not in errors and score > max_score:
        errors["score"] = "Score cannot exceed the maximum score."

    raw_duration = (form.get("duration_minutes") or "").strip()
    duration_minutes = None
    if raw_duration:
        try:
            duration_minutes = int(raw_duration)
            if duration_minutes < 0:
                errors["duration_minutes"] = "Duration cannot be negative."
        except ValueError:
            errors["duration_minutes"] = "Duration must be a whole number of minutes."

    return {
        "student_id": student_id,
        "category": category,
        "topic": topic,
        "score": score,
        "max_score": max_score,
        "duration_minutes": duration_minutes,
    }, errors


def save_practice_result(
    student_id,
    category,
    topic,
    score,
    max_score,
    duration_minutes=None,
    task_id=None,
    db_path=None,
):
    """Insert a validated practice quiz result into `practice_results`."""
    if max_score is None or max_score <= 0:
        raise ValueError("max_score must be greater than 0.")
    if score is None or score < 0 or score > max_score:
        raise ValueError("score must be between 0 and max_score.")
    if duration_minutes is not None and duration_minutes < 0:
        raise ValueError("duration_minutes cannot be negative.")

    practiced_at = datetime.now().isoformat(sep=" ", timespec="seconds")
    with db_session(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO practice_results
                (student_id, task_id, category, topic, score, max_score, duration_minutes, practiced_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student_id,
                task_id,
                category.strip(),
                topic.strip() if topic else None,
                float(score),
                float(max_score),
                duration_minutes,
                practiced_at,
            ),
        )
        return cur.lastrowid


# ---------------------------------------------------------------------------
# Pure Analytics & Report Calculations (zero-division safe)
# ---------------------------------------------------------------------------
def calculate_quiz_metrics(practice_rows):
    """
    Calculate quiz attempt count, average percentage score, best score, and
    total practice duration from `practice_results` rows.
    """
    percentages = []
    total_minutes = 0

    for row in practice_rows or []:
        score = row.get("score")
        max_score = row.get("max_score")
        if score is None or max_score is None or max_score <= 0:
            continue
        pct = min(100.0, max(0.0, (float(score) / float(max_score)) * 100.0))
        percentages.append(pct)
        if row.get("duration_minutes") is not None:
            total_minutes += max(0, int(row["duration_minutes"]))

    attempts = len(percentages)
    average_score = round(sum(percentages) / attempts, 1) if attempts > 0 else 0.0
    best_score = round(max(percentages), 1) if attempts > 0 else 0.0

    return {
        "attempts": attempts,
        "average_score": average_score,
        "best_score": best_score,
        "total_minutes": total_minutes,
        "has_quizzes": attempts > 0,
    }


def calculate_topic_scores(practice_rows, assessment_rows=None):
    """
    Compute topic-wise average percentage scores (0..100).
    Uses `practice_results` when available; if no practice results exist yet,
    falls back to real `skill_assessments.score_percent` values (if scored).
    """
    grouped = {}
    for row in practice_rows or []:
        score = row.get("score")
        max_score = row.get("max_score")
        if score is None or max_score is None or max_score <= 0:
            continue
        topic_name = (row.get("topic") or "").strip() or (row.get("category") or "").strip() or "General"
        category_name = (row.get("category") or "").strip() or topic_name
        pct = min(100.0, max(0.0, (float(score) / float(max_score)) * 100.0))
        entry = grouped.setdefault(
            topic_name,
            {
                "topic": topic_name,
                "category": category_name,
                "scores": [],
                "total_minutes": 0,
                "source": "practice",
            },
        )
        entry["scores"].append(pct)
        if row.get("duration_minutes") is not None:
            entry["total_minutes"] += max(0, int(row["duration_minutes"]))

    if grouped:
        topic_scores = []
        for entry in grouped.values():
            attempts = len(entry["scores"])
            avg = round(sum(entry["scores"]) / attempts, 1) if attempts > 0 else 0.0
            topic_scores.append(
                {
                    "topic": entry["topic"],
                    "category": entry["category"],
                    "attempts": attempts,
                    "average_score": avg,
                    "total_minutes": entry["total_minutes"],
                    "source": "practice",
                }
            )
        return topic_scores

    # Fallback: real graded scores from Member 1's Skill Assessment Quiz
    assessment_scores = []
    for row in assessment_rows or []:
        if row.get("score_percent") is not None:
            category = (row.get("category") or "").strip()
            topic = (row.get("topic") or "").strip()
            label = category if not topic or topic.lower() == "overall" else topic
            assessment_scores.append(
                {
                    "topic": label,
                    "category": category,
                    "attempts": 1,
                    "average_score": round(float(row["score_percent"]), 1),
                    "total_minutes": 0,
                    "source": "assessment",
                }
            )
    return assessment_scores


def calculate_task_metrics(task_rows):
    """
    Calculate completed, pending, in-progress, and completion percentage from
    `preparation_tasks` rows (excluding Interview Milestone rows).
    """
    actionable = [
        dict(r)
        for r in (task_rows or [])
        if (r.get("category") or "").strip() != MILESTONE_CATEGORY
    ]

    milestone_date = None
    for r in task_rows or []:
        if (r.get("category") or "").strip() == MILESTONE_CATEGORY:
            milestone_date = r.get("due_date")
            break

    total = len(actionable)
    completed_tasks = [t for t in actionable if t.get("status") == "completed"]
    pending_tasks = [t for t in actionable if t.get("status") != "completed"]
    in_progress_count = sum(1 for t in actionable if t.get("status") == "in_progress")
    pending_only_count = sum(1 for t in actionable if t.get("status") == "pending")

    completed = len(completed_tasks)
    pending = len(pending_tasks)
    completion_percent = round((completed / total) * 100, 1) if total > 0 else 0.0
    pending_percent = round((pending / total) * 100, 1) if total > 0 else 0.0

    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "in_progress": in_progress_count,
        "pending_only": pending_only_count,
        "completion_percent": completion_percent,
        "pending_percent": pending_percent,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "interview_date": milestone_date,
    }


def _proficiency_from_assessment(row):
    """Return 0..100 proficiency from real score_percent or derived self_rating."""
    if row.get("score_percent") is not None:
        return round(float(row["score_percent"]), 1), "Quiz Score"
    if row.get("self_rating") is not None:
        return round((float(row["self_rating"]) / 5.0) * 100.0, 1), "Skill Level"
    return None, None


def _classify_weakness(score, skill_gap):
    """Return (status_label, bootstrap_badge, accent_key) or None if not weak."""
    if (score is not None and score < WEAK_SCORE_THRESHOLD) or (
        skill_gap is not None and float(skill_gap) >= 3.0
    ):
        return "Weak", "danger", "red"
    if (score is not None and score < NEEDS_IMPROVEMENT_THRESHOLD) or (
        skill_gap is not None and float(skill_gap) >= 2.0
    ):
        return "Needs Improvement", "warning", "orange"
    return None


def identify_weak_topics(assessment_rows, topic_scores=None):
    """
    Identify weak topics and areas needing improvement strictly from actual
    assessment rows and quiz scores. Never invents fake topics.
    """
    assessment_by_cat = {}
    for row in assessment_rows or []:
        cat = (row.get("category") or "").strip()
        if cat:
            assessment_by_cat[cat.lower()] = row

    weak_items = []
    seen_keys = set()

    # 1. Evaluate practiced quiz topics first (attaching skill gap if category matches)
    for ts in topic_scores or []:
        if ts.get("source") != "practice":
            continue
        topic_name = ts["topic"]
        cat_name = ts["category"]
        matched_assess = assessment_by_cat.get(cat_name.lower()) or assessment_by_cat.get(
            topic_name.lower()
        )
        skill_gap = (
            round(float(matched_assess["skill_gap"]), 1)
            if matched_assess and matched_assess.get("skill_gap") is not None
            else None
        )
        score = ts["average_score"]
        classification = _classify_weakness(score, skill_gap)
        if classification:
            status_label, badge, accent = classification
            weak_items.append(
                {
                    "topic": topic_name,
                    "category": cat_name,
                    "score": score,
                    "metric_label": "Quiz Avg",
                    "skill_gap": skill_gap,
                    "status": status_label,
                    "badge": badge,
                    "accent": accent,
                }
            )
        seen_keys.add(topic_name.lower())
        seen_keys.add(cat_name.lower())

    # 2. Evaluate assessment categories not already covered by practice results
    for row in assessment_rows or []:
        cat = (row.get("category") or "").strip()
        topic = (row.get("topic") or "").strip()
        display_name = cat if not topic or topic.lower() == "overall" else topic
        if display_name.lower() in seen_keys:
            continue

        score, metric_label = _proficiency_from_assessment(row)
        skill_gap = (
            round(float(row["skill_gap"]), 1)
            if row.get("skill_gap") is not None
            else None
        )
        classification = _classify_weakness(score, skill_gap)
        if classification and score is not None:
            status_label, badge, accent = classification
            weak_items.append(
                {
                    "topic": display_name,
                    "category": cat,
                    "score": score,
                    "metric_label": metric_label,
                    "skill_gap": skill_gap,
                    "status": status_label,
                    "badge": badge,
                    "accent": accent,
                }
            )

    weak_items.sort(
        key=lambda item: (
            item["score"],
            -(item["skill_gap"] if item["skill_gap"] is not None else 0.0),
        )
    )
    return weak_items


def identify_strong_topics(assessment_rows, topic_scores=None):
    """
    Identify strong topics (score >= 70% and low/no skill gap) from real
    quiz scores and assessment records.
    """
    assessment_by_cat = {}
    for row in assessment_rows or []:
        cat = (row.get("category") or "").strip()
        if cat:
            assessment_by_cat[cat.lower()] = row

    strong_items = []
    seen_keys = set()

    for ts in topic_scores or []:
        if ts.get("source") != "practice":
            continue
        topic_name = ts["topic"]
        cat_name = ts["category"]
        matched_assess = assessment_by_cat.get(cat_name.lower()) or assessment_by_cat.get(
            topic_name.lower()
        )
        skill_gap = (
            round(float(matched_assess["skill_gap"]), 1)
            if matched_assess and matched_assess.get("skill_gap") is not None
            else None
        )
        if ts["average_score"] >= STRONG_SCORE_THRESHOLD and (
            skill_gap is None or skill_gap <= 1.0
        ):
            strong_items.append(
                {
                    "topic": topic_name,
                    "score": ts["average_score"],
                    "metric_label": "Quiz Avg",
                    "skill_gap": skill_gap,
                }
            )
        seen_keys.add(topic_name.lower())
        seen_keys.add(cat_name.lower())

    for row in assessment_rows or []:
        cat = (row.get("category") or "").strip()
        topic = (row.get("topic") or "").strip()
        display_name = cat if not topic or topic.lower() == "overall" else topic
        if display_name.lower() in seen_keys:
            continue
        score, metric_label = _proficiency_from_assessment(row)
        skill_gap = (
            round(float(row["skill_gap"]), 1)
            if row.get("skill_gap") is not None
            else None
        )
        if score is not None and score >= STRONG_SCORE_THRESHOLD and (
            skill_gap is None or skill_gap <= 1.0
        ):
            strong_items.append(
                {
                    "topic": display_name,
                    "score": score,
                    "metric_label": metric_label,
                    "skill_gap": skill_gap,
                }
            )

    strong_items.sort(key=lambda item: -item["score"])
    return strong_items


def generate_recommendations(
    quiz_metrics,
    task_metrics,
    weak_topics,
    strong_topics,
    has_assessment=False,
    has_student=True,
):
    """
    Generate actionable recommendations directly from the student's actual
    assessment scores, quiz attempts, and preparation tasks.
    """
    if not has_student:
        return [
            "Complete the Skill Assessment first to record your baseline skills and unlock analytics.",
            "Generate a study roadmap in the Preparation Planner once your assessment is saved.",
        ]

    recommendations = []

    if not has_assessment:
        recommendations.append(
            "Take a Skill Assessment to measure your Aptitude, Coding, Technical Knowledge, and HR & Communication gaps."
        )

    for item in weak_topics[:3]:
        gap_note = (
            f" (skill gap: {item['skill_gap']})"
            if item.get("skill_gap") is not None
            else ""
        )
        if item["status"] == "Weak":
            recommendations.append(
                f"Prioritize {item['topic']} — current {item['metric_label'].lower()} is {item['score']}%{gap_note}. Practice foundational questions daily."
            )
        else:
            recommendations.append(
                f"Revise {item['topic']} — current {item['metric_label'].lower()} is {item['score']}%{gap_note}. Solve targeted practice sets to reach 70%+."
            )

    if not quiz_metrics["has_quizzes"]:
        if weak_topics:
            recommendations.append(
                f"Attempt a topic-wise practice quiz in {weak_topics[0]['topic']} and log your score to track improvement."
            )
        else:
            recommendations.append(
                "Attempt a topic-wise practice quiz and record your result to populate quiz performance trends."
            )
    elif quiz_metrics["average_score"] < 60.0:
        recommendations.append(
            f"Your average practice quiz score is {quiz_metrics['average_score']}%. Review wrong answers thoroughly before taking timed mocks."
        )

    if task_metrics["total"] == 0:
        recommendations.append(
            "Create a personalized study schedule in the Preparation Planner to organize pending study milestones."
        )
    elif task_metrics["pending"] > 0:
        next_task = task_metrics["pending_tasks"][0]["title"]
        recommendations.append(
            f"Complete your {task_metrics['pending']} pending preparation task(s) ({task_metrics['completion_percent']}% done). Next up: {next_task}."
        )
    else:
        recommendations.append(
            "You have completed 100% of your planned preparation tasks — take full-length timed mock tests to keep sharp."
        )

    if (
        strong_topics
        and not weak_topics
        and quiz_metrics["has_quizzes"]
        and quiz_metrics["average_score"] >= 70.0
    ):
        strong_names = ", ".join(s["topic"] for s in strong_topics[:3])
        recommendations.append(
            f"Strong mastery in {strong_names}. Focus on speed optimization and mock interviews."
        )

    return recommendations


def generate_progress_report(
    student,
    quiz_metrics,
    task_metrics,
    topic_scores,
    weak_topics,
    strong_topics,
    recommendations,
    assessment_summary=None,
):
    """Build a structured, printable progress report dictionary from real data."""
    has_any_data = bool(
        student
        and (
            quiz_metrics["has_quizzes"]
            or task_metrics["total"] > 0
            or (assessment_summary and assessment_summary.get("has_assessment"))
        )
    )

    if not has_any_data:
        readiness_label = "Getting Started"
        readiness_badge = "secondary"
        overall_summary = (
            "No assessment, quiz, or preparation task records are available yet. "
            "Complete a Skill Assessment and generate a Preparation Plan to begin tracking readiness."
        )
    else:
        effective_score = (
            quiz_metrics["average_score"]
            if quiz_metrics["has_quizzes"]
            else (
                assessment_summary.get("average_proficiency", 0.0)
                if assessment_summary
                else 0.0
            )
        )
        if (
            effective_score >= 75.0
            and task_metrics["completion_percent"] >= 75.0
            and not weak_topics
        ):
            readiness_label = "Placement Ready"
            readiness_badge = "success"
        elif effective_score >= 55.0 or task_metrics["completion_percent"] >= 50.0:
            readiness_label = "On Track"
            readiness_badge = "primary"
        else:
            readiness_label = "Needs Focus"
            readiness_badge = "warning"

        quiz_part = (
            f"{quiz_metrics['attempts']} practice quiz attempt(s) with an average score of {quiz_metrics['average_score']}%"
            if quiz_metrics["has_quizzes"]
            else "0 practice quiz attempts recorded yet"
        )
        task_part = (
            f"{task_metrics['completed']} of {task_metrics['total']} preparation tasks completed ({task_metrics['completion_percent']}%)"
            if task_metrics["total"] > 0
            else "no preparation tasks scheduled yet"
        )
        weak_part = (
            f"{len(weak_topics)} area(s) flagged for improvement"
            if weak_topics
            else "no critical weak areas flagged"
        )
        overall_summary = (
            f"{student['name']} currently has {quiz_part}, {task_part}, and {weak_part}."
        )

    best_topic = (
        max(topic_scores, key=lambda t: t["average_score"]) if topic_scores else None
    )
    lowest_topic = (
        min(topic_scores, key=lambda t: t["average_score"]) if topic_scores else None
    )

    return {
        "generated_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "report_date": date.today().strftime("%d %b %Y"),
        "student": student,
        "readiness_label": readiness_label,
        "readiness_badge": readiness_badge,
        "overall_summary": overall_summary,
        "quiz_summary": {
            "attempts": quiz_metrics["attempts"],
            "average_score": quiz_metrics["average_score"],
            "best_score": quiz_metrics["best_score"],
            "total_minutes": quiz_metrics["total_minutes"],
            "best_topic": best_topic,
            "lowest_topic": lowest_topic,
        },
        "strong_topics": strong_topics,
        "weak_topics": weak_topics,
        "completed_tasks": task_metrics["completed_tasks"],
        "pending_tasks": task_metrics["pending_tasks"],
        "recommendations": recommendations,
    }


def build_dashboard_data(student_id=None, db_path=None):
    """
    Assemble the complete Progress Dashboard context from the SQLite database.
    Handles missing students or empty tables gracefully.
    """
    students = get_all_students(db_path)
    selected_student = None
    not_found_error = None

    if student_id is not None:
        selected_student = get_student(student_id, db_path)
        if selected_student is None:
            not_found_error = "No student record was found for that selection."
    elif students:
        selected_student = get_student(students[0]["id"], db_path)

    if selected_student is None:
        quiz_metrics = calculate_quiz_metrics([])
        task_metrics = calculate_task_metrics([])
        topic_scores = []
        weak_topics = []
        strong_topics = []
        recommendations = generate_recommendations(
            quiz_metrics, task_metrics, weak_topics, strong_topics,
            has_assessment=False, has_student=False,
        )
        assessment_summary = {"has_assessment": False, "assessed_at": None, "average_proficiency": 0.0, "average_score": None}
        report = generate_progress_report(
            None, quiz_metrics, task_metrics, topic_scores,
            weak_topics, strong_topics, recommendations, assessment_summary,
        )
        return {
            "students": students,
            "selected_student": None,
            "selected_student_id": None,
            "not_found_error": not_found_error,
            "quiz_metrics": quiz_metrics,
            "task_metrics": task_metrics,
            "topic_scores": topic_scores,
            "weak_topics": weak_topics,
            "strong_topics": strong_topics,
            "recommendations": recommendations,
            "assessment_summary": assessment_summary,
            "report": report,
            "chart_data": {
                "topic_labels": [],
                "topic_scores": [],
                "topic_source": None,
                "task_completed": 0,
                "task_pending": 0,
                "task_total": 0,
            },
            "categories": DEFAULT_CATEGORIES,
            "report_date": date.today().strftime("%d %b %Y"),
        }

    sid = selected_student["id"]
    practice_rows = get_practice_results(sid, db_path)
    assessment_rows = get_latest_assessment_rows(sid, db_path)
    task_rows = get_preparation_tasks(sid, db_path)

    quiz_metrics = calculate_quiz_metrics(practice_rows)
    task_metrics = calculate_task_metrics(task_rows)
    topic_scores = calculate_topic_scores(practice_rows, assessment_rows)
    weak_topics = identify_weak_topics(assessment_rows, topic_scores)
    strong_topics = identify_strong_topics(assessment_rows, topic_scores)

    proficiencies = []
    scored_values = []
    assessed_at = assessment_rows[0]["assessed_at"] if assessment_rows else None
    for row in assessment_rows:
        prof, _ = _proficiency_from_assessment(row)
        if prof is not None:
            proficiencies.append(prof)
        if row.get("score_percent") is not None:
            scored_values.append(float(row["score_percent"]))

    assessment_summary = {
        "has_assessment": bool(assessment_rows),
        "assessed_at": assessed_at,
        "average_proficiency": round(sum(proficiencies) / len(proficiencies), 1) if proficiencies else 0.0,
        "average_score": round(sum(scored_values) / len(scored_values), 1) if scored_values else None,
    }

    recommendations = generate_recommendations(
        quiz_metrics,
        task_metrics,
        weak_topics,
        strong_topics,
        has_assessment=assessment_summary["has_assessment"],
        has_student=True,
    )

    report = generate_progress_report(
        selected_student,
        quiz_metrics,
        task_metrics,
        topic_scores,
        weak_topics,
        strong_topics,
        recommendations,
        assessment_summary,
    )

    chart_data = {
        "topic_labels": [t["topic"] for t in topic_scores],
        "topic_scores": [t["average_score"] for t in topic_scores],
        "topic_source": topic_scores[0]["source"] if topic_scores else None,
        "task_completed": task_metrics["completed"],
        "task_pending": task_metrics["pending"],
        "task_total": task_metrics["total"],
    }

    return {
        "students": students,
        "selected_student": selected_student,
        "selected_student_id": sid,
        "not_found_error": None,
        "quiz_metrics": quiz_metrics,
        "task_metrics": task_metrics,
        "topic_scores": topic_scores,
        "weak_topics": weak_topics,
        "strong_topics": strong_topics,
        "recommendations": recommendations,
        "assessment_summary": assessment_summary,
        "report": report,
        "chart_data": chart_data,
        "categories": DEFAULT_CATEGORIES,
        "report_date": date.today().strftime("%d %b %Y"),
    }


# ---------------------------------------------------------------------------
# Web Request Handler (called from /progress in app.py)
# ---------------------------------------------------------------------------
def handle_progress_request(db_path):
    """
    GET  /progress               -> render Progress Dashboard for active student
    GET  /progress?student=ID    -> render Progress Dashboard for specific student
    POST /progress               -> validate and save a new practice quiz result
    """
    if request.method == "POST":
        data, errors = validate_practice_form(request.form)
        student_id = data["student_id"]

        if not errors and get_student(student_id, db_path) is None:
            errors["student_id"] = "Selected student was not found."

        if errors:
            dashboard = build_dashboard_data(student_id=student_id, db_path=db_path)
            return (
                render_template(
                    "progress.html",
                    **dashboard,
                    form=request.form,
                    errors=errors,
                    open_log_modal=True,
                ),
                400,
            )

        try:
            save_practice_result(
                student_id=student_id,
                category=data["category"],
                topic=data["topic"],
                score=data["score"],
                max_score=data["max_score"],
                duration_minutes=data["duration_minutes"],
                db_path=db_path,
            )
            flash(
                f"Practice result saved for {data['topic']} ({data['score']:g}/{data['max_score']:g}).",
                "success",
            )
        except (sqlite3.Error, ValueError):
            current_app.logger.exception("Could not save practice result")
            dashboard = build_dashboard_data(student_id=student_id, db_path=db_path)
            return (
                render_template(
                    "progress.html",
                    **dashboard,
                    form=request.form,
                    general_error="Sorry, the practice result could not be saved. Please try again.",
                    errors={},
                    open_log_modal=True,
                ),
                500,
            )

        return redirect(url_for("progress_page", student=student_id))

    # GET request
    student_id = request.args.get("student", type=int)
    try:
        dashboard = build_dashboard_data(student_id=student_id, db_path=db_path)
    except sqlite3.Error:
        current_app.logger.exception("Could not load progress dashboard")
        dashboard = build_dashboard_data(student_id=None, db_path=db_path) if False else {
            "students": [],
            "selected_student": None,
            "selected_student_id": None,
            "not_found_error": None,
            "quiz_metrics": calculate_quiz_metrics([]),
            "task_metrics": calculate_task_metrics([]),
            "topic_scores": [],
            "weak_topics": [],
            "strong_topics": [],
            "recommendations": [],
            "assessment_summary": {"has_assessment": False, "assessed_at": None, "average_proficiency": 0.0, "average_score": None},
            "report": generate_progress_report(
                None, calculate_quiz_metrics([]), calculate_task_metrics([]),
                [], [], [], [], None,
            ),
            "chart_data": {"topic_labels": [], "topic_scores": [], "topic_source": None, "task_completed": 0, "task_pending": 0, "task_total": 0},
            "categories": DEFAULT_CATEGORIES,
            "report_date": date.today().strftime("%d %b %Y"),
        }
        return (
            render_template(
                "progress.html",
                **dashboard,
                form={},
                errors={},
                general_error="Sorry, progress analytics could not be loaded from the database.",
                open_log_modal=False,
            ),
            500,
        )

    status = 404 if dashboard.get("not_found_error") else 200
    return (
        render_template(
            "progress.html",
            **dashboard,
            form={},
            errors={},
            general_error=dashboard.get("not_found_error"),
            open_log_modal=False,
        ),
        status,
    )
