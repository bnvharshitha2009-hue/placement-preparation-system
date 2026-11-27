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

import json
import math
import re
import sqlite3
from datetime import date, datetime, time, timedelta

from flask import current_app, flash, redirect, render_template, request, url_for

from database import db_session, fetch_all, fetch_one
from modules import assessment as assessment_module
from modules import auth as auth_module

MILESTONE_CATEGORY = "Interview Milestone"
VALID_STATUSES = ("pending", "in_progress", "completed")
DEFAULT_HOURS_PER_DAY = 2
MIN_HOURS_PER_DAY = 1
MAX_HOURS_PER_DAY = 12
DEFAULT_DAILY_START_TIME = "18:00"
DEFAULT_STUDY_DAYS = "all"
TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")

TIME_SLOT_PRESETS = {
    "morning": ("07:00", "Morning (07:00+)"),
    "afternoon": ("14:00", "Afternoon (14:00+)"),
    "evening": ("18:00", "Evening (18:00+)"),
    "night": ("20:30", "Night (20:30+)"),
}

STUDY_DAY_OPTIONS = {
    "all": "Every Day (Mon–Sun)",
    "weekdays": "Weekdays Only (Mon–Fri)",
    "weekends": "Weekends Focus (Sat–Sun)",
}

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

    preset = (form.get("preferred_slot") or "").strip().lower()
    raw_start = (form.get("daily_start_time") or "").strip()
    if not raw_start:
        daily_start_time = TIME_SLOT_PRESETS.get(preset, (DEFAULT_DAILY_START_TIME,))[0]
    elif not TIME_RE.fullmatch(raw_start):
        errors["daily_start_time"] = "Please enter a valid start time (HH:MM, 24-hour)."
        daily_start_time = DEFAULT_DAILY_START_TIME
    else:
        daily_start_time = raw_start

    study_days = (form.get("study_days") or DEFAULT_STUDY_DAYS).strip().lower()
    if study_days not in STUDY_DAY_OPTIONS:
        errors["study_days"] = "Please choose a valid study day schedule."
        study_days = DEFAULT_STUDY_DAYS

    data = {
        "student_id": student_id,
        "interview_date": interview_date,
        "hours_per_day": hours_per_day,
        "daily_start_time": daily_start_time,
        "study_days": study_days,
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


def _estimate_minutes_for_gap(gap):
    """Estimate realistic daily study block minutes based on skill gap severity."""
    if gap >= 3:
        return 60
    if gap == 2:
        return 45
    if gap == 1:
        return 45
    return 30


def _build_study_calendar(start_date, end_date, study_days=DEFAULT_STUDY_DAYS):
    """Return ordered list of available study dates between start_date and end_date."""
    if end_date <= start_date:
        return [start_date]

    all_days = [
        start_date + timedelta(days=i)
        for i in range((end_date - start_date).days + 1)
    ]
    if study_days == "weekdays":
        filtered = [d for d in all_days if d.weekday() < 5]
        return filtered or all_days
    if study_days == "weekends":
        filtered = [d for d in all_days if d.weekday() >= 5]
        return filtered or all_days
    return all_days


def _format_time_slot(daily_start_time, offset_minutes, duration_minutes):
    """Format 'HH:MM - HH:MM' for a study task block starting offset_minutes into the window."""
    try:
        hour, minute = [int(p) for p in daily_start_time.split(":")]
        base_dt = datetime.combine(date.today(), time(hour, minute))
    except (ValueError, TypeError):
        base_dt = datetime.combine(date.today(), time(18, 0))

    start_dt = base_dt + timedelta(minutes=offset_minutes)
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    return f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"


def assign_time_schedule(tasks, start_date, interview_date, hours_per_day=DEFAULT_HOURS_PER_DAY,
                         daily_start_time=DEFAULT_DAILY_START_TIME, study_days=DEFAULT_STUDY_DAYS,
                         occupied_today_minutes=0):
    """
    Pack tasks into exact study dates and non-overlapping daily time slots
    from start_date up to interview_date according to hours_per_day and study_days.
    Mutates each task dict with due_date, time_slot, and sort_order.
    """
    if not tasks:
        return tasks

    study_dates = _build_study_calendar(start_date, interview_date, study_days=study_days)
    final_tasks = [t for t in tasks if t.get("category") == "Final Revision"]
    regular_tasks = [t for t in tasks if t.get("category") != "Final Revision"]

    # Reserve the final prep day for Final Revision when multi-day study window exists
    if final_tasks and regular_tasks and len(study_dates) >= 2:
        if study_dates[-1] == interview_date and (interview_date - start_date).days >= 2:
            final_day = study_dates[-2]
            prep_dates = study_dates[:-1]
        else:
            final_day = study_dates[-1]
            prep_dates = study_dates[:-1] or study_dates
    else:
        final_day = study_dates[-1]
        prep_dates = study_dates

    daily_cap_mins = max(30, hours_per_day * 60)
    total_reg_mins = sum(int(t.get("estimated_minutes") or 60) for t in regular_tasks)
    available_mins = max(daily_cap_mins, (len(prep_dates) * daily_cap_mins) - occupied_today_minutes)
    if total_reg_mins > available_mins:
        day_limit = max(daily_cap_mins, math.ceil((total_reg_mins + occupied_today_minutes) / len(prep_dates)))
    else:
        day_limit = daily_cap_mins

    day_idx = 0
    clock_offset = occupied_today_minutes if prep_dates[0] == start_date else 0
    used_per_day = {d: 0 for d in study_dates}
    if prep_dates[0] == start_date:
        used_per_day[start_date] = occupied_today_minutes

    for idx, task in enumerate(regular_tasks):
        dur = int(task.get("estimated_minutes") or 60)
        # Advance to the next study date if adding this task would exceed daily study hours
        while (
            day_idx < len(prep_dates) - 1
            and used_per_day[prep_dates[day_idx]] > 0
            and used_per_day[prep_dates[day_idx]] + dur > day_limit
        ):
            day_idx += 1
            clock_offset = 0

        chosen_day = prep_dates[day_idx]
        task["due_date"] = chosen_day.isoformat()
        task["time_slot"] = _format_time_slot(daily_start_time, clock_offset, dur)
        task["sort_order"] = idx
        used_per_day[chosen_day] += dur
        clock_offset += dur

    base_order = len(regular_tasks)
    for idx, task in enumerate(final_tasks):
        dur = int(task.get("estimated_minutes") or 60)
        day_offset = used_per_day.get(final_day, 0)
        task["due_date"] = final_day.isoformat()
        task["time_slot"] = _format_time_slot(daily_start_time, day_offset, dur)
        task["sort_order"] = base_order + idx
        used_per_day[final_day] = day_offset + dur

    return tasks


def generate_study_plan(assessment, interview_date, hours_per_day=DEFAULT_HOURS_PER_DAY,
                        today=None, assessment_ids=None,
                        daily_start_time=DEFAULT_DAILY_START_TIME,
                        study_days=DEFAULT_STUDY_DAYS):
    """
    Build a time-scheduled, date-assigned preparation plan weighted by skill gaps.
    """
    today = today or date.today()
    days_remaining = max(0, (interview_date - today).days)
    effective_days = max(1, days_remaining)
    assessment_ids = assessment_ids or {}

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
        est_minutes = _estimate_minutes_for_gap(gap)

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
                "estimated_minutes": est_minutes,
                "status": "pending",
            })

    raw_tasks.append({
        "category": "Final Revision",
        "priority": "Final",
        "badge": "primary",
        "gap": 0,
        "skill_assessment_id": None,
        "title": "Final Pre-Interview Revision & Mock Check",
        "description": "Review key formulas, core CS notes, and your STAR stories. Rest well before the interview.",
        "estimated_minutes": 60,
        "status": "pending",
    })

    assign_time_schedule(
        raw_tasks,
        start_date=today,
        interview_date=interview_date,
        hours_per_day=hours_per_day,
        daily_start_time=daily_start_time,
        study_days=study_days,
    )

    non_final_dates = [
        date.fromisoformat(t["due_date"])
        for t in raw_tasks
        if t["category"] != "Final Revision"
    ]
    last_work_date = max(non_final_dates) if non_final_dates else today
    buffer_days = max(0, (interview_date - last_work_date).days)

    return {
        "days_remaining": days_remaining,
        "total_hours": total_hours,
        "total_minutes": sum(t["estimated_minutes"] for t in raw_tasks),
        "buffer_days": buffer_days,
        "tasks": raw_tasks,
        "category_summary": category_summary,
        "schedule_config": {
            "interview_date": interview_date.isoformat(),
            "hours_per_day": hours_per_day,
            "daily_start_time": daily_start_time,
            "study_days": study_days,
        },
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


def _parse_schedule_config(raw_description, interview_date):
    """Safely parse schedule preferences stored on the milestone row."""
    cfg = {
        "interview_date": interview_date,
        "hours_per_day": DEFAULT_HOURS_PER_DAY,
        "daily_start_time": DEFAULT_DAILY_START_TIME,
        "study_days": DEFAULT_STUDY_DAYS,
    }
    if not raw_description:
        return cfg
    try:
        parsed = json.loads(raw_description)
        if isinstance(parsed, dict):
            if isinstance(parsed.get("hours_per_day"), int):
                cfg["hours_per_day"] = parsed["hours_per_day"]
            if TIME_RE.fullmatch(str(parsed.get("daily_start_time") or "")):
                cfg["daily_start_time"] = parsed["daily_start_time"]
            if parsed.get("study_days") in STUDY_DAY_OPTIONS:
                cfg["study_days"] = parsed["study_days"]
    except (ValueError, TypeError):
        pass
    return cfg


def save_plan(student_id, interview_date, tasks, db_path=None, schedule_config=None):
    """
    Replace the student's existing preparation plan with the newly generated
    time-scheduled tasks and an Interview Milestone row inside a single transaction.
    """
    interview_iso = interview_date.isoformat() if isinstance(interview_date, date) else str(interview_date)
    cfg = dict(schedule_config or {})
    cfg.setdefault("interview_date", interview_iso)
    cfg.setdefault("hours_per_day", DEFAULT_HOURS_PER_DAY)
    cfg.setdefault("daily_start_time", DEFAULT_DAILY_START_TIME)
    cfg.setdefault("study_days", DEFAULT_STUDY_DAYS)
    milestone_desc = json.dumps(cfg)

    with db_session(db_path) as conn:
        conn.execute("DELETE FROM preparation_tasks WHERE student_id = ?", (student_id,))

        conn.execute(
            """
            INSERT INTO preparation_tasks
                (student_id, skill_assessment_id, title, description, category,
                 due_date, time_slot, estimated_minutes, sort_order, status)
            VALUES (?, NULL, ?, ?, ?, ?, NULL, 0, 9999, 'pending')
            """,
            (
                student_id,
                "Target Interview Day",
                milestone_desc,
                MILESTONE_CATEGORY,
                interview_iso,
            ),
        )

        conn.executemany(
            """
            INSERT INTO preparation_tasks
                (student_id, skill_assessment_id, title, description, category,
                 due_date, time_slot, estimated_minutes, sort_order, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    student_id,
                    t.get("skill_assessment_id"),
                    t["title"],
                    t["description"],
                    t["category"],
                    t["due_date"],
                    t.get("time_slot"),
                    int(t.get("estimated_minutes") or 60),
                    int(t.get("sort_order") if t.get("sort_order") is not None else idx),
                    t.get("status", "pending"),
                )
                for idx, t in enumerate(tasks)
            ],
        )


def _format_day_label(iso_date, today_d):
    try:
        d = date.fromisoformat(iso_date)
        label = d.strftime("%a, %b %d")
        if d == today_d:
            return f"Today · {label}"
        if d == today_d + timedelta(days=1):
            return f"Tomorrow · {label}"
        return label
    except ValueError:
        return iso_date or "Unscheduled"


def get_student_plan(student_id, db_path=None):
    """
    Load the student's saved preparation tasks, daily time slots, schedule config,
    and day-grouped timeline. Returns None if no plan has been generated yet.
    """
    rows = fetch_all(
        """
        SELECT id, student_id, skill_assessment_id, title, description,
               category, due_date, time_slot, estimated_minutes, sort_order,
               status, created_at, completed_at
        FROM preparation_tasks
        WHERE student_id = ?
        ORDER BY due_date ASC, sort_order ASC, id ASC
        """,
        (student_id,),
        db_path,
    )
    if not rows:
        return None

    interview_date = None
    milestone_desc = None
    tasks = []
    for r in rows:
        row_dict = dict(r)
        if row_dict["category"] == MILESTONE_CATEGORY:
            interview_date = row_dict["due_date"]
            milestone_desc = row_dict["description"]
        else:
            row_dict["estimated_minutes"] = int(row_dict.get("estimated_minutes") or 60)
            tasks.append(row_dict)

    if not tasks and interview_date is None:
        return None

    today_d = date.today()
    schedule_config = _parse_schedule_config(milestone_desc, interview_date)
    total = len(tasks)
    completed = sum(1 for t in tasks if t["status"] == "completed")
    in_progress = sum(1 for t in tasks if t["status"] == "in_progress")
    pending = total - completed - in_progress
    completion_percent = round((completed / total) * 100) if total else 0

    completed_minutes = sum(t["estimated_minutes"] for t in tasks if t["status"] == "completed")
    remaining_minutes = sum(t["estimated_minutes"] for t in tasks if t["status"] != "completed")

    days_remaining = None
    buffer_days = None
    if interview_date:
        try:
            interview_dt = date.fromisoformat(interview_date)
            days_remaining = (interview_dt - today_d).days
            active_dates = [
                date.fromisoformat(t["due_date"])
                for t in tasks
                if t["status"] != "completed" and t.get("due_date") and t["category"] != "Final Revision"
            ]
            if active_dates:
                buffer_days = max(0, (interview_dt - max(active_dates)).days)
            else:
                buffer_days = max(0, days_remaining)
        except ValueError:
            days_remaining = None

    # Group tasks by due_date cleanly for timeline display
    days_map = {}
    for t in tasks:
        d_key = t.get("due_date") or "Unscheduled"
        if d_key not in days_map:
            days_map[d_key] = {
                "date": d_key,
                "label": _format_day_label(d_key, today_d),
                "is_today": d_key == today_d.isoformat(),
                "total_minutes": 0,
                "completed_count": 0,
                "tasks": [],
            }
        days_map[d_key]["tasks"].append(t)
        days_map[d_key]["total_minutes"] += t["estimated_minutes"]
        if t["status"] == "completed":
            days_map[d_key]["completed_count"] += 1

    return {
        "interview_date": interview_date,
        "days_remaining": days_remaining,
        "buffer_days": buffer_days,
        "schedule_config": schedule_config,
        "schedule_days": list(days_map.values()),
        "tasks": tasks,
        "stats": {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "completion_percent": completion_percent,
            "completed_minutes": completed_minutes,
            "remaining_minutes": remaining_minutes,
        },
    }


def rebalance_schedule(student_id, db_path=None, today=None):
    """
    Dynamically adjust upcoming dates & time slots for unfinished tasks
    whenever work is completed (pulled forward) or reopened/overdue.
    """
    today_d = today or date.today()
    today_iso = today_d.isoformat()

    with db_session(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, title, category, due_date, time_slot, estimated_minutes,
                   sort_order, status, completed_at, description
            FROM preparation_tasks
            WHERE student_id = ?
            ORDER BY sort_order ASC, due_date ASC, id ASC
            """,
            (student_id,),
        ).fetchall()

        if not rows:
            return {"rescheduled": 0, "remaining": 0, "all_done": True, "buffer_days": 0}

        interview_date_str = None
        milestone_desc = None
        completed_tasks = []
        active_tasks = []

        for r in rows:
            d = dict(r)
            if d["category"] == MILESTONE_CATEGORY:
                interview_date_str = d["due_date"]
                milestone_desc = d["description"]
            elif d["status"] == "completed":
                completed_tasks.append(d)
            else:
                d["estimated_minutes"] = int(d.get("estimated_minutes") or 60)
                active_tasks.append(d)

        if not interview_date_str:
            return {"rescheduled": 0, "remaining": len(active_tasks), "all_done": not active_tasks, "buffer_days": 0}

        cfg = _parse_schedule_config(milestone_desc, interview_date_str)
        interview_dt = max(today_d, date.fromisoformat(interview_date_str))

        # Track effort completed today without letting bonus future tasks push today's planned tasks out
        occupied_today_minutes = 0
        for ct in completed_tasks:
            done_day = (ct.get("completed_at") or "")[:10]
            if ct.get("due_date") == today_iso or done_day == today_iso:
                occupied_today_minutes += int(ct.get("estimated_minutes") or 60)
                if ct.get("due_date") and ct["due_date"] > today_iso:
                    conn.execute(
                        "UPDATE preparation_tasks SET due_date = ? WHERE id = ?",
                        (today_iso, ct["id"]),
                    )

        if not active_tasks:
            return {
                "rescheduled": 0,
                "remaining": 0,
                "all_done": True,
                "buffer_days": max(0, (interview_dt - today_d).days),
            }

        daily_cap_mins = max(30, cfg["hours_per_day"] * 60)
        pending_originally_today = sum(
            int(t.get("estimated_minutes") or 60)
            for t in active_tasks
            if t.get("due_date") == today_iso and t.get("category") != "Final Revision"
        )
        effective_occupied_today = min(
            occupied_today_minutes,
            max(0, daily_cap_mins - pending_originally_today),
        )

        original = {t["id"]: (t.get("due_date"), t.get("time_slot")) for t in active_tasks}
        assign_time_schedule(
            active_tasks,
            start_date=today_d,
            interview_date=interview_dt,
            hours_per_day=cfg["hours_per_day"],
            daily_start_time=cfg["daily_start_time"],
            study_days=cfg["study_days"],
            occupied_today_minutes=effective_occupied_today,
        )

        # Keep completed tasks sorted ahead of pulled-in tasks on today
        completed_offset = len(completed_tasks)
        changed = 0
        for idx, t in enumerate(active_tasks):
            new_order = completed_offset + idx
            if original[t["id"]] != (t["due_date"], t["time_slot"]):
                changed += 1
            conn.execute(
                """
                UPDATE preparation_tasks
                SET due_date = ?, time_slot = ?, sort_order = ?
                WHERE id = ? AND student_id = ?
                """,
                (t["due_date"], t["time_slot"], new_order, t["id"], student_id),
            )

    non_final_dates = [
        date.fromisoformat(t["due_date"])
        for t in active_tasks
        if t.get("category") != "Final Revision"
    ]
    last_work = max(non_final_dates) if non_final_dates else today_d
    return {
        "rescheduled": changed,
        "remaining": len(active_tasks),
        "all_done": False,
        "buffer_days": max(0, (interview_dt - last_work).days),
    }


def apply_task_status(task_id, student_id, new_status, db_path=None, today=None):
    """Update a task's status and automatically rebalance remaining dates & time slots."""
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {new_status!r}")

    today_d = today or date.today()
    today_iso = today_d.isoformat()
    completed_at = (
        datetime.combine(today_d, datetime.now().time()).isoformat(sep=" ", timespec="seconds")
        if new_status == "completed"
        else None
    )
    with db_session(db_path) as conn:
        if new_status == "completed":
            cur = conn.execute(
                """
                UPDATE preparation_tasks
                SET status = ?,
                    completed_at = ?,
                    due_date = CASE WHEN due_date > ? THEN ? ELSE due_date END
                WHERE id = ? AND student_id = ?
                """,
                (new_status, completed_at, today_iso, today_iso, task_id, student_id),
            )
        else:
            cur = conn.execute(
                """
                UPDATE preparation_tasks
                SET status = ?, completed_at = ?
                WHERE id = ? AND student_id = ?
                """,
                (new_status, completed_at, task_id, student_id),
            )
        updated = cur.rowcount

    rebalance = None
    if updated > 0 and new_status in ("completed", "pending"):
        rebalance = rebalance_schedule(student_id, db_path=db_path, today=today_d)

    return {"updated": updated, "rebalance": rebalance}


def update_task_status(task_id, student_id, new_status, db_path=None, today=None):
    """Update a task's status, rebalance schedule if needed, and return updated row count."""
    return apply_task_status(task_id, student_id, new_status, db_path=db_path, today=today)["updated"]


# ---------------------------------------------------------------------------
# Step 3: Web Request Handler (called from /planner in app.py)
# ---------------------------------------------------------------------------
def _render_planner(db_path, selected_student_id=None, form=None, errors=None,
                    general_error=None, status=200):
    students = get_students_with_assessments(db_path)

    if selected_student_id is None and students:
        logged_user = auth_module.get_logged_in_user(db_path)
        valid_ids = {s["id"] for s in students}
        if logged_user and logged_user.get("student_id") in valid_ids:
            selected_student_id = logged_user["student_id"]
        else:
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
        time_presets=TIME_SLOT_PRESETS,
        study_day_options=STUDY_DAY_OPTIONS,
    ), status


def handle_planner_request(db_path):
    """
    GET  /planner               -> show planner for selected (or latest) student
    GET  /planner?student=ID    -> show planner for student ID
    POST /planner               -> generate plan, update task status, or rebalance schedule
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
                outcome = apply_task_status(task_id, student_id, new_status, db_path)
                reb = outcome.get("rebalance")
                if new_status == "completed" and reb:
                    if reb["all_done"]:
                        flash("All scheduled tasks completed ahead of your interview!", "success")
                    elif reb["rescheduled"] > 0:
                        flash(
                            f"Work completed! Dynamically rebalanced {reb['rescheduled']} upcoming task(s) "
                            f"({reb['buffer_days']} buffer day(s) before interview).",
                            "success",
                        )
                    else:
                        flash("Task marked completed and schedule refreshed.", "success")
                elif new_status == "pending" and reb:
                    flash("Task reopened and re-added to your upcoming schedule.", "info")
                else:
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

        if action == "rebalance":
            student_id = request.form.get("student_id", type=int)
            if not student_id:
                return _render_planner(db_path, general_error="Invalid student selection.", status=400)
            try:
                reb = rebalance_schedule(student_id, db_path=db_path)
                flash(
                    f"Schedule rebalanced: {reb['remaining']} unfinished task(s) packed cleanly "
                    f"with {reb['buffer_days']} buffer day(s) remaining.",
                    "info",
                )
            except sqlite3.Error:
                current_app.logger.exception("Could not rebalance schedule")
                return _render_planner(db_path, selected_student_id=student_id,
                                       general_error="Could not rebalance the schedule.", status=500)
            return redirect(url_for("planner_page", student=student_id))

        # Generate a new time-scheduled preparation plan
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
                daily_start_time=data["daily_start_time"],
                study_days=data["study_days"],
            )
            save_plan(
                student_id,
                data["interview_date"],
                generated["tasks"],
                db_path,
                schedule_config=generated["schedule_config"],
            )
            flash(
                f"Time-scheduled plan created with {len(generated['tasks'])} tasks "
                f"(starting {data['daily_start_time']} daily up to {data['interview_date'].isoformat()})!",
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
            time_presets=TIME_SLOT_PRESETS,
            study_day_options=STUDY_DAY_OPTIONS,
        ), 500
