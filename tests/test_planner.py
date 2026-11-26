"""
tests/test_planner.py
=====================
Unit and integration tests for Member 2's Preparation Planner module.
"""

import os
import sys
from datetime import date, timedelta

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import database
from app import create_app
from modules import assessment as am
from modules import planner as pm


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test_planner.db")
    database.init_db(path)
    return path


@pytest.fixture
def client(db_path):
    app = create_app({"TESTING": True, "DATABASE": db_path})
    return app.test_client()


def seed_student_assessment(db_path, email="asha@example.com", name="Asha Kumar",
                            ratings=None):
    student = {"name": name, "email": email, "branch": "CSE", "year": 3}
    ratings = ratings or {"aptitude": 1, "coding": 3, "technical": 4, "hr": 5}
    return am.save_assessment(student, ratings, db_path)


class TestPlanValidation:
    def test_valid_request(self):
        today = date(2026, 11, 26)
        data, errors = pm.validate_plan_request(
            {"student_id": "1", "interview_date": "2026-12-10", "hours_per_day": "3"},
            today=today,
        )
        assert errors == {}
        assert data["student_id"] == 1
        assert data["interview_date"] == date(2026, 12, 10)
        assert data["hours_per_day"] == 3

    def test_rejects_past_interview_date(self):
        today = date(2026, 11, 26)
        _, errors = pm.validate_plan_request(
            {"student_id": "1", "interview_date": "2026-11-25"},
            today=today,
        )
        assert "interview_date" in errors

    def test_rejects_invalid_date_format(self):
        _, errors = pm.validate_plan_request(
            {"student_id": "1", "interview_date": "26-12-2026"},
        )
        assert "interview_date" in errors

    def test_rejects_missing_student_id(self):
        _, errors = pm.validate_plan_request(
            {"interview_date": date.today().isoformat()},
        )
        assert "student_id" in errors

    def test_rejects_out_of_range_hours(self):
        _, errors = pm.validate_plan_request(
            {"student_id": "1", "interview_date": date.today().isoformat(), "hours_per_day": "20"},
        )
        assert "hours_per_day" in errors


class TestPlanGeneration:
    def test_prioritizes_larger_skill_gaps(self, db_path):
        saved = seed_student_assessment(db_path)
        latest = am.get_latest_assessment(saved["student_id"], db_path)
        today = date(2026, 11, 26)
        interview = today + timedelta(days=14)

        plan = pm.generate_study_plan(latest, interview, hours_per_day=3, today=today)
        assert plan["days_remaining"] == 14
        assert plan["total_hours"] == 42

        by_cat = {c["label"]: c for c in plan["category_summary"]}
        # Aptitude has gap 4 (High) -> 4 tasks; HR has gap 0 (No gap) -> 1 task
        assert by_cat["Aptitude"]["task_count"] == 4
        assert by_cat["Coding"]["task_count"] == 3
        assert by_cat["Technical Knowledge"]["task_count"] == 2
        assert by_cat["HR & Communication"]["task_count"] == 1

        # All due dates must fall between today and interview_date
        for task in plan["tasks"]:
            due = date.fromisoformat(task["due_date"])
            assert today <= due <= interview

    def test_same_day_interview_schedules_all_today(self, db_path):
        saved = seed_student_assessment(db_path)
        latest = am.get_latest_assessment(saved["student_id"], db_path)
        today = date(2026, 11, 26)

        plan = pm.generate_study_plan(latest, today, today=today)
        assert plan["days_remaining"] == 0
        assert all(t["due_date"] == today.isoformat() for t in plan["tasks"])


class TestPlannerRoutes:
    def test_empty_state_when_no_assessments(self, client):
        resp = client.get("/planner")
        html = resp.get_data(as_text=True)
        assert resp.status_code == 200
        assert "No Skill Assessments Found Yet" in html

    def test_planner_loads_assessment_and_generates_plan(self, client, db_path):
        saved = seed_student_assessment(db_path)
        sid = saved["student_id"]
        target_date = (date.today() + timedelta(days=10)).isoformat()

        resp = client.get(f"/planner?student={sid}")
        assert resp.status_code == 200
        assert "Asha Kumar" in resp.get_data(as_text=True)

        post_resp = client.post(
            "/planner",
            data={"action": "generate", "student_id": str(sid), "interview_date": target_date, "hours_per_day": "3"},
            follow_redirects=True,
        )
        html = post_resp.get_data(as_text=True)
        assert post_resp.status_code == 200
        assert target_date in html
        assert "Your Personalized Preparation Schedule" in html

        plan = pm.get_student_plan(sid, db_path)
        assert plan is not None
        assert plan["interview_date"] == target_date
        assert plan["stats"]["total"] == 11  # 4 + 3 + 2 + 1 + 1 final revision

    def test_update_task_status_persists(self, client, db_path):
        saved = seed_student_assessment(db_path)
        sid = saved["student_id"]
        target_date = (date.today() + timedelta(days=7)).isoformat()
        client.post(
            "/planner",
            data={"action": "generate", "student_id": str(sid), "interview_date": target_date},
        )
        plan = pm.get_student_plan(sid, db_path)
        first_task_id = plan["tasks"][0]["id"]

        resp = client.post(
            "/planner",
            data={
                "action": "update_status",
                "student_id": str(sid),
                "task_id": str(first_task_id),
                "status": "completed",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        updated = pm.get_student_plan(sid, db_path)
        assert updated["stats"]["completed"] == 1
        assert updated["tasks"][0]["completed_at"] is not None

    def test_past_date_post_returns_400(self, client, db_path):
        saved = seed_student_assessment(db_path)
        past = (date.today() - timedelta(days=1)).isoformat()
        resp = client.post(
            "/planner",
            data={"action": "generate", "student_id": str(saved["student_id"]), "interview_date": past},
        )
        assert resp.status_code == 400
        assert "cannot be in the past" in resp.get_data(as_text=True)


class TestTimeScheduleAndDynamicRebalancing:
    def test_generates_non_overlapping_time_slots_and_weekdays_only(self, db_path):
        saved = seed_student_assessment(db_path)
        latest = am.get_latest_assessment(saved["student_id"], db_path)
        # Start on Thursday Nov 26, 2026 -> Sat Nov 28 & Sun Nov 29 must be skipped
        today = date(2026, 11, 26)
        interview = date(2026, 12, 10)

        plan = pm.generate_study_plan(
            latest,
            interview,
            hours_per_day=2,
            today=today,
            daily_start_time="09:00",
            study_days="weekdays",
        )
        day1_tasks = [t for t in plan["tasks"] if t["due_date"] == "2026-11-26"]
        assert len(day1_tasks) >= 2
        assert day1_tasks[0]["time_slot"].startswith("09:00 - ")
        assert day1_tasks[1]["time_slot"].startswith("10:00 - ")

        for task in plan["tasks"]:
            due_d = date.fromisoformat(task["due_date"])
            assert due_d.weekday() < 5
            assert task["time_slot"] and " - " in task["time_slot"]

    def test_completing_future_task_early_pulls_remaining_tasks_forward(self, db_path):
        saved = seed_student_assessment(db_path)
        sid = saved["student_id"]
        latest = am.get_latest_assessment(sid, db_path)
        today = date(2026, 11, 26)
        interview = today + timedelta(days=12)

        generated = pm.generate_study_plan(
            latest, interview, hours_per_day=2, today=today, daily_start_time="18:00"
        )
        pm.save_plan(sid, interview, generated["tasks"], db_path, schedule_config=generated["schedule_config"])
        before = pm.get_student_plan(sid, db_path)

        # Pick an unfinished task scheduled on a future day and complete it early today
        future_tasks = [t for t in before["tasks"] if t["due_date"] > today.isoformat() and t["category"] != "Final Revision"]
        assert len(future_tasks) >= 2
        done_id = future_tasks[0]["id"]
        later_id = future_tasks[-1]["id"]
        later_due_before = (future_tasks[-1]["due_date"], future_tasks[-1]["time_slot"])

        outcome = pm.apply_task_status(done_id, sid, "completed", db_path=db_path, today=today)
        assert outcome["updated"] == 1

        after = pm.get_student_plan(sid, db_path)
        done_task = next(t for t in after["tasks"] if t["id"] == done_id)
        later_task = next(t for t in after["tasks"] if t["id"] == later_id)
        assert done_task["due_date"] == today.isoformat()
        # Because a future slot was freed, later tasks pull earlier in date or time slot
        assert (later_task["due_date"], later_task["time_slot"]) < later_due_before

    def test_reopening_completed_task_readds_to_upcoming_schedule(self, db_path):
        saved = seed_student_assessment(db_path)
        sid = saved["student_id"]
        latest = am.get_latest_assessment(sid, db_path)
        today = date(2026, 11, 26)
        interview = today + timedelta(days=7)

        generated = pm.generate_study_plan(latest, interview, hours_per_day=2, today=today)
        pm.save_plan(sid, interview, generated["tasks"], db_path, schedule_config=generated["schedule_config"])
        first_id = pm.get_student_plan(sid, db_path)["tasks"][0]["id"]

        pm.apply_task_status(first_id, sid, "completed", db_path=db_path, today=today)
        pm.apply_task_status(first_id, sid, "pending", db_path=db_path, today=today)

        reopened = next(t for t in pm.get_student_plan(sid, db_path)["tasks"] if t["id"] == first_id)
        assert reopened["status"] == "pending"
        assert reopened["completed_at"] is None
        assert reopened["due_date"] >= today.isoformat()
        assert reopened["time_slot"]

    def test_rebalance_route_moves_overdue_pending_tasks_to_today(self, client, db_path):
        saved = seed_student_assessment(db_path)
        sid = saved["student_id"]
        today = date.today()
        interview = today + timedelta(days=6)

        client.post("/planner", data={
            "action": "generate",
            "student_id": str(sid),
            "interview_date": interview.isoformat(),
            "hours_per_day": "2",
            "daily_start_time": "17:00",
        })
        plan = pm.get_student_plan(sid, db_path)
        # Simulate an overdue task from 2 days ago
        yesterday = (today - timedelta(days=2)).isoformat()
        database.execute(
            "UPDATE preparation_tasks SET due_date = ? WHERE id = ?",
            (yesterday, plan["tasks"][0]["id"]),
            db_path,
        )

        resp = client.post("/planner", data={"action": "rebalance", "student_id": str(sid)}, follow_redirects=True)
        assert resp.status_code == 200
        updated = pm.get_student_plan(sid, db_path)
        assert all(t["due_date"] >= today.isoformat() for t in updated["tasks"] if t["status"] != "completed")
        assert "17:00 -" in resp.get_data(as_text=True)

    def test_init_db_migrates_legacy_preparation_tasks_columns(self, tmp_path):
        import sqlite3

        legacy = str(tmp_path / "legacy_planner.db")
        with sqlite3.connect(legacy) as conn:
            conn.execute(
                """
                CREATE TABLE preparation_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT,
                    due_date TEXT,
                    status TEXT NOT NULL DEFAULT 'pending'
                )
                """
            )
        database.init_db(legacy)
        cols = {r["name"] for r in database.fetch_all("PRAGMA table_info(preparation_tasks)", db_path=legacy)}
        assert {"time_slot", "estimated_minutes", "sort_order"} <= cols
