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
