"""
tests/test_progress.py
======================
Unit and integration tests for Member 3's Progress Tracking, Dashboard,
Analytics, and Reporting module.
"""

import os
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import database
from app import create_app
from modules import assessment as am
from modules import progress as pg


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test_progress.db")
    database.init_db(path)
    return path


@pytest.fixture
def client(db_path):
    app = create_app({"TESTING": True, "DATABASE": db_path})
    return app.test_client()


def seed_student(db_path, name="Asha Kumar", email="asha@example.com", ratings=None, scores=None):
    student = {"name": name, "email": email, "branch": "CSE", "year": 3}
    ratings = ratings or {"aptitude": 2, "coding": 1, "technical": 4, "hr": 5}
    return am.save_assessment(student, ratings, db_path, scores=scores)


# ---------------------------------------------------------------------------
# 1. Average Score & Empty Quiz Results
# ---------------------------------------------------------------------------
class TestQuizMetrics:
    def test_average_score_calculation(self):
        rows = [
            {"category": "Technical Knowledge", "topic": "DBMS", "score": 16, "max_score": 20, "duration_minutes": 20},
            {"category": "Technical Knowledge", "topic": "OS", "score": 10, "max_score": 20, "duration_minutes": 15},
            {"category": "Coding", "topic": "Arrays", "score": 9, "max_score": 10, "duration_minutes": 25},
        ]
        metrics = pg.calculate_quiz_metrics(rows)
        assert metrics["attempts"] == 3
        # (80 + 50 + 90) / 3 = 73.3
        assert metrics["average_score"] == 73.3
        assert metrics["best_score"] == 90.0
        assert metrics["total_minutes"] == 60
        assert metrics["has_quizzes"] is True

    def test_empty_quiz_results_no_zero_division(self):
        metrics = pg.calculate_quiz_metrics([])
        assert metrics["attempts"] == 0
        assert metrics["average_score"] == 0.0
        assert metrics["best_score"] == 0.0
        assert metrics["total_minutes"] == 0
        assert metrics["has_quizzes"] is False

    def test_ignores_invalid_zero_max_score(self):
        rows = [{"category": "Coding", "topic": "DP", "score": 5, "max_score": 0, "duration_minutes": 10}]
        metrics = pg.calculate_quiz_metrics(rows)
        assert metrics["attempts"] == 0
        assert metrics["average_score"] == 0.0


# ---------------------------------------------------------------------------
# 2. Task Completion & Zero Tasks
# ---------------------------------------------------------------------------
class TestTaskMetrics:
    def test_task_completion_calculations_excluding_milestone(self):
        tasks = [
            {"title": "Target Interview Day", "category": "Interview Milestone", "status": "pending"},
            {"title": "Revise DBMS", "category": "Technical Knowledge", "status": "completed"},
            {"title": "Solve Arrays", "category": "Coding", "status": "completed"},
            {"title": "Mock HR", "category": "HR & Communication", "status": "in_progress"},
            {"title": "Quant Practice", "category": "Aptitude", "status": "pending"},
        ]
        stats = pg.calculate_task_metrics(tasks)
        assert stats["total"] == 4
        assert stats["completed"] == 2
        assert stats["pending"] == 2
        assert stats["in_progress"] == 1
        assert stats["completion_percent"] == 50.0
        assert stats["pending_percent"] == 50.0
        assert stats["interview_date"] is None

    def test_zero_tasks_no_zero_division(self):
        stats = pg.calculate_task_metrics([])
        assert stats["total"] == 0
        assert stats["completed"] == 0
        assert stats["pending"] == 0
        assert stats["completion_percent"] == 0.0
        assert stats["pending_percent"] == 0.0


# ---------------------------------------------------------------------------
# 3. Topic-wise Scores & Weak-Topic Identification
# ---------------------------------------------------------------------------
class TestTopicScoresAndWeakTopics:
    def test_topic_wise_scores_from_practice(self):
        practice = [
            {"category": "Technical Knowledge", "topic": "DBMS", "score": 15, "max_score": 20, "duration_minutes": 20},
            {"category": "Technical Knowledge", "topic": "DBMS", "score": 17, "max_score": 20, "duration_minutes": 20},
            {"category": "Technical Knowledge", "topic": "Operating Systems", "score": 8, "max_score": 20, "duration_minutes": 15},
        ]
        topics = pg.calculate_topic_scores(practice)
        by_topic = {t["topic"]: t for t in topics}
        assert by_topic["DBMS"]["attempts"] == 2
        assert by_topic["DBMS"]["average_score"] == 80.0
        assert by_topic["Operating Systems"]["average_score"] == 40.0

    def test_weak_topic_identification_combines_practice_and_assessment(self):
        assessments = [
            {"category": "Coding", "topic": "Overall", "self_rating": 1, "score_percent": 20.0, "skill_gap": 4.0},
            {"category": "Technical Knowledge", "topic": "Overall", "self_rating": 3, "score_percent": 60.0, "skill_gap": 2.0},
            {"category": "HR & Communication", "topic": "Overall", "self_rating": 5, "score_percent": 95.0, "skill_gap": 0.0},
        ]
        practice = [
            {"category": "Technical Knowledge", "topic": "Operating Systems", "score": 7, "max_score": 20, "duration_minutes": 15},
        ]
        topic_scores = pg.calculate_topic_scores(practice, assessments)
        weak = pg.identify_weak_topics(assessments, topic_scores)
        weak_names = [w["topic"] for w in weak]
        assert "Coding" in weak_names
        assert "Operating Systems" in weak_names
        assert "HR & Communication" not in weak_names

        coding = next(w for w in weak if w["topic"] == "Coding")
        assert coding["status"] == "Weak"
        assert coding["skill_gap"] == 4.0


# ---------------------------------------------------------------------------
# 4. Report Generation & Recommendations
# ---------------------------------------------------------------------------
class TestReportGeneration:
    def test_report_generation_structure(self):
        student = {"id": 1, "name": "Asha Kumar", "branch": "CSE", "year": 3}
        quiz_metrics = {"attempts": 2, "average_score": 65.0, "best_score": 80.0, "total_minutes": 40, "has_quizzes": True}
        task_metrics = {
            "total": 2, "completed": 1, "pending": 1, "in_progress": 0, "pending_only": 1,
            "completion_percent": 50.0, "pending_percent": 50.0,
            "completed_tasks": [{"title": "Revise DBMS", "category": "Technical Knowledge"}],
            "pending_tasks": [{"title": "Practice OS", "category": "Technical Knowledge", "due_date": "2026-12-01"}],
            "interview_date": "2026-12-10",
        }
        topic_scores = [
            {"topic": "DBMS", "average_score": 80.0},
            {"topic": "OS", "average_score": 50.0},
        ]
        weak = [{"topic": "OS", "score": 50.0, "metric_label": "Quiz Avg", "skill_gap": 2.0, "status": "Needs Improvement", "badge": "warning", "accent": "orange"}]
        strong = [{"topic": "DBMS", "score": 80.0, "metric_label": "Quiz Avg", "skill_gap": 0.0}]
        recs = pg.generate_recommendations(quiz_metrics, task_metrics, weak, strong, has_assessment=True, has_student=True)
        report = pg.generate_progress_report(
            student, quiz_metrics, task_metrics, topic_scores, weak, strong, recs,
            {"has_assessment": True, "average_proficiency": 65.0},
        )
        assert report["student"]["name"] == "Asha Kumar"
        assert report["quiz_summary"]["attempts"] == 2
        assert len(report["strong_topics"]) == 1
        assert len(report["weak_topics"]) == 1
        assert len(report["completed_tasks"]) == 1
        assert len(report["pending_tasks"]) == 1
        assert len(report["recommendations"]) >= 1
        assert "Asha Kumar" in report["overall_summary"]


# ---------------------------------------------------------------------------
# 5. Database Operations & Flask Routes
# ---------------------------------------------------------------------------
class TestDatabaseAndRoutes:
    def test_empty_database_renders_gracefully(self, client):
        resp = client.get("/progress")
        html = resp.get_data(as_text=True)
        assert resp.status_code == 200
        assert "Your Progress Dashboard" in html
        assert "No Student Progress Data Yet" in html

    def test_save_practice_result_and_dashboard_aggregation(self, client, db_path):
        saved = seed_student(
            db_path,
            ratings={"aptitude": 2, "coding": 1, "technical": 4, "hr": 5},
            scores={"aptitude": 40.0, "coding": 20.0, "technical": 80.0, "hr": 100.0},
        )
        sid = saved["student_id"]

        # Seed preparation tasks (1 completed, 1 pending, 1 milestone)
        with database.db_session(db_path) as conn:
            conn.execute(
                "INSERT INTO preparation_tasks (student_id, title, category, due_date, status) VALUES (?, ?, ?, ?, ?)",
                (sid, "Target Interview Day", "Interview Milestone", "2026-12-15", "pending"),
            )
            conn.execute(
                "INSERT INTO preparation_tasks (student_id, title, category, due_date, status) VALUES (?, ?, ?, ?, ?)",
                (sid, "Revise SQL", "Technical Knowledge", "2026-12-01", "completed"),
            )
            conn.execute(
                "INSERT INTO preparation_tasks (student_id, title, category, due_date, status) VALUES (?, ?, ?, ?, ?)",
                (sid, "Solve Graph Problems", "Coding", "2026-12-03", "pending"),
            )

        # Post a real practice quiz attempt
        post_resp = client.post(
            "/progress",
            data={
                "student_id": str(sid),
                "category": "Technical Knowledge",
                "topic": "Operating Systems",
                "score": "8",
                "max_score": "20",
                "duration_minutes": "25",
            },
            follow_redirects=True,
        )
        assert post_resp.status_code == 200
        html = post_resp.get_data(as_text=True)
        assert "Operating Systems" in html
        assert "40.0%" in html
        assert "1 / 2" in html
        assert "50.0%" in html
        assert "Areas to Improve" in html
        assert "Recommended Next Steps" in html
        assert "Placement Readiness" in html

    def test_unknown_student_returns_404(self, client):
        resp = client.get("/progress?student=9999")
        assert resp.status_code == 404
        assert "No student record was found" in resp.get_data(as_text=True)

    def test_invalid_practice_submission_returns_400(self, client, db_path):
        saved = seed_student(db_path)
        resp = client.post(
            "/progress",
            data={
                "student_id": str(saved["student_id"]),
                "category": "Coding",
                "topic": "",
                "score": "25",
                "max_score": "20",
            },
        )
        assert resp.status_code == 400
