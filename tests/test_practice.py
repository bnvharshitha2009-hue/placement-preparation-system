"""
tests/test_practice.py
======================
Automated tests for the Practice & Test Schedule tab (`modules/practice.py`).
"""

import json
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
from modules import practice as prm
from modules import question_generator as qg


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test_practice.db")
    database.init_db(path)
    return path


@pytest.fixture
def client(db_path):
    app = create_app({"TESTING": True, "DATABASE": db_path})
    return app.test_client()


def seed_student_and_plan(db_path):
    student = {"name": "Asha Kumar", "email": "asha@example.com", "branch": "CSE", "year": 3}
    saved = am.save_assessment(
        student,
        {"aptitude": 1, "coding": 3, "technical": 4, "hr": 5},
        db_path,
    )
    sid = saved["student_id"]
    latest = am.get_latest_assessment(sid, db_path)
    today = date.today()
    interview = today + timedelta(days=10)
    generated = pm.generate_study_plan(
        latest, interview, hours_per_day=2, today=today, daily_start_time="18:00"
    )
    pm.save_plan(sid, interview, generated["tasks"], db_path, schedule_config=generated["schedule_config"])
    return sid


class TestPracticeAndTestSchedule:
    def test_practice_tab_in_sidebar_and_empty_state(self, client):
        home = client.get("/").get_data(as_text=True)
        assert "Practice &amp; Test Schedule" in home
        assert "/practice" in home

        empty = client.get("/practice").get_data(as_text=True)
        assert "Complete a Skill Assessment to Track Your Practice Schedule" in empty

    def test_schedule_custom_mock_test_persists_to_schedule(self, client, db_path):
        sid = seed_student_and_plan(db_path)
        target_day = (date.today() + timedelta(days=3)).isoformat()

        resp = client.post(
            "/practice",
            data={
                "action": "schedule_session",
                "student_id": str(sid),
                "test_title": "Timed Campus Full Mock #1",
                "category": "mock",
                "due_date": target_day,
                "start_time": "20:00",
                "duration_minutes": "60",
            },
            follow_redirects=True,
        )
        html = resp.get_data(as_text=True)
        assert resp.status_code == 200
        assert "Timed Campus Full Mock #1" in html
        assert "20:00 - 21:00" in html

        # Also visible in Preparation Planner schedule
        planner_html = client.get(f"/planner?student={sid}").get_data(as_text=True)
        assert "Timed Campus Full Mock #1" in planner_html

    def test_passing_linked_practice_test_saves_result_and_updates_planner(self, client, db_path):
        sid = seed_student_and_plan(db_path)
        plan_before = pm.get_student_plan(sid, db_path)
        # Choose a pending Aptitude task scheduled on a future date to observe rebalancing
        apt_tasks = [t for t in plan_before["tasks"] if t["category"] == "Aptitude"]
        linked_task = apt_tasks[-1]

        _, by_cat = am.get_questions_for_set(1)
        questions = by_cat["aptitude"]

        post_data = {
            "action": "submit_practice",
            "student_id": str(sid),
            "category_key": "aptitude",
            "set_id": "1",
            "task_id": str(linked_task["id"]),
            "duration_minutes": "15",
        }
        for q in questions:
            post_data["q_" + q["id"]] = q["answer"]

        resp = client.post("/practice", data=post_data)
        html = resp.get_data(as_text=True)
        assert resp.status_code == 200
        assert "Score: 5 / 5 (100.0%)" in html
        assert "Linked planner task completed" in html

        # Saved in practice_results
        history = prm.get_practice_history(sid, db_path)
        assert len(history) == 1
        assert history[0]["score"] == 5.0
        assert history[0]["task_id"] == linked_task["id"]
        assert history[0]["passed"] is True

        # Planner task is marked completed
        plan_after = pm.get_student_plan(sid, db_path)
        updated_task = next(t for t in plan_after["tasks"] if t["id"] == linked_task["id"])
        assert updated_task["status"] == "completed"

    def test_failing_linked_practice_keeps_task_pending(self, client, db_path):
        sid = seed_student_and_plan(db_path)
        plan_before = pm.get_student_plan(sid, db_path)
        linked_task = plan_before["tasks"][0]

        _, by_cat = am.get_questions_for_set(1)
        questions = by_cat["aptitude"]

        post_data = {
            "action": "submit_practice",
            "student_id": str(sid),
            "category_key": "aptitude",
            "set_id": "1",
            "task_id": str(linked_task["id"]),
            "duration_minutes": "12",
        }
        for idx, q in enumerate(questions):
            # Answer only 1 right (20% < 60%)
            if idx == 0:
                post_data["q_" + q["id"]] = q["answer"]
            else:
                wrong = next(opt for opt in ("a", "b", "c", "d") if opt != q["answer"])
                post_data["q_" + q["id"]] = wrong

        resp = client.post("/practice", data=post_data)
        html = resp.get_data(as_text=True)
        assert resp.status_code == 200
        assert "Score: 1 / 5 (20.0%)" in html
        assert "Below 60% pass threshold" in html

        plan_after = pm.get_student_plan(sid, db_path)
        same_task = next(t for t in plan_after["tasks"] if t["id"] == linked_task["id"])
        assert same_task["status"] == "pending"

    def test_mock_test_mode_loads_all_20_careerride_questions(self, client, db_path):
        sid = seed_student_and_plan(db_path)
        html = client.get(f"/practice?student={sid}&category=mock&set=2").get_data(as_text=True)
        assert "Full Mock Test" in html
        assert "Question 20 of 20" in html
        questions, _ = am.get_questions_for_set(2)
        for q in questions:
            assert f'name="q_{q["id"]}"' in html


class TestGeminiQuestionGenerator:
    def test_missing_api_key_handles_gracefully_on_route(self, client, db_path, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        sid = seed_student_and_plan(db_path)

        resp = client.post(
            "/practice",
            data={"action": "generate_ai", "student_id": str(sid), "category_key": "aptitude"},
            follow_redirects=True,
        )
        html = resp.get_data(as_text=True)
        assert resp.status_code == 200
        assert "GEMINI_API_KEY is not configured" in html

    def test_validator_rejects_duplicate_options_and_bad_answers(self):
        with pytest.raises(ValueError, match="duplicate options"):
            qg._validate_and_normalize_questions(
                [{
                    "topic": "Math",
                    "prompt": "2+2?",
                    "option_a": "4",
                    "option_b": "4",
                    "option_c": "5",
                    "option_d": "6",
                    "verification_steps": "2+2=4",
                    "answer": "a",
                    "explanation": "Basic addition.",
                }],
                "aptitude",
            )

        with pytest.raises(ValueError, match="invalid answer key"):
            qg._validate_and_normalize_questions(
                [{
                    "topic": "Math",
                    "prompt": "2+2?",
                    "option_a": "4",
                    "option_b": "3",
                    "option_c": "5",
                    "option_d": "6",
                    "verification_steps": "2+2=4",
                    "answer": "z",
                    "explanation": "Basic addition.",
                }],
                "aptitude",
            )

    def test_gemini_structured_output_generates_saves_and_grades_in_practice(self, client, db_path, monkeypatch):
        sid = seed_student_and_plan(db_path)
        calls = []

        fake_questions = [
            {
                "topic": "Time & Work",
                "prompt": f"Sample Gemini Aptitude Q{i}: A does work in {i+4} days. Combined rate?",
                "option_a": f"{i+1} days",
                "option_b": f"{i+2} days",
                "option_c": f"{i+3} days",
                "option_d": f"{i+4} days",
                "verification_steps": f"Solved step by step for Q{i}; option b matches.",
                "answer": "b",
                "explanation": f"Step-by-step verified explanation for Q{i}.",
            }
            for i in range(1, 6)
        ]

        class FakeInteraction:
            output_text = json.dumps({"questions": fake_questions})

        class FakeInteractionsAPI:
            def create(self, **kwargs):
                calls.append(kwargs)
                return FakeInteraction()

        class FakeClient:
            interactions = FakeInteractionsAPI()

        orig_call = qg._call_gemini_for_questions
        monkeypatch.setattr(
            qg,
            "_call_gemini_for_questions",
            lambda cat, topic_focus="", difficulty="standard", client=None: orig_call(
                cat, topic_focus=topic_focus, difficulty=difficulty, client=FakeClient()
            ),
        )

        plan_before = pm.get_student_plan(sid, db_path)
        linked_task = plan_before["tasks"][0]

        gen_resp = client.post(
            "/practice",
            data={
                "action": "generate_ai",
                "student_id": str(sid),
                "category_key": "aptitude",
                "topic_focus": "Time & Work",
                "difficulty": "hard",
                "task_id": str(linked_task["id"]),
            },
            follow_redirects=True,
        )
        gen_html = gen_resp.get_data(as_text=True)
        assert gen_resp.status_code == 200
        assert calls and calls[0]["model"] == "gemini-4-hydrogen"
        assert calls[0]["response_format"]["mime_type"] == "application/json"
        assert "Generated 5 verified Aptitude questions using gemini-4-hydrogen!" in gen_html
        assert "Sample Gemini Aptitude Q1" in gen_html

        # Submit the generated AI set and verify grading + linked planner task completion
        ai_row = database.fetch_one("SELECT id FROM ai_question_sets WHERE student_id = ?", (sid,), db_path)
        assert ai_row is not None
        saved_qs = qg.get_ai_question_set(ai_row["id"], student_id=sid, db_path=db_path)["questions"]

        submit_data = {
            "action": "submit_practice",
            "student_id": str(sid),
            "ai_set_id": str(ai_row["id"]),
            "task_id": str(linked_task["id"]),
            "duration_minutes": "8",
        }
        for q in saved_qs:
            submit_data["q_" + q["id"]] = q["answer"]

        sub_resp = client.post("/practice", data=submit_data)
        sub_html = sub_resp.get_data(as_text=True)
        assert sub_resp.status_code == 200
        assert "Score: 5 / 5 (100.0%)" in sub_html
        assert "Linked planner task completed" in sub_html

        plan_after = pm.get_student_plan(sid, db_path)
        done = next(t for t in plan_after["tasks"] if t["id"] == linked_task["id"])
        assert done["status"] == "completed"
