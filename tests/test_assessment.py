"""
tests/test_assessment.py
========================
Automated tests for Member 1's real-question Skill Assessment feature.

Run from the project folder:
    python -m pytest tests -v

Every test uses its own temporary SQLite file, so your real placement.db is
never touched.
"""

import os
import sqlite3

import pytest
from markupsafe import escape as html_escape

import database
from app import create_app
from modules import assessment as am


# ---------------------------------------------------------------------------
# Helpers and fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def db_path(tmp_path):
    """A fresh database file for each test."""
    return str(tmp_path / "test_placement.db")


@pytest.fixture
def app(db_path):
    return create_app({"TESTING": True, "DATABASE": db_path})


@pytest.fixture
def client(app):
    return app.test_client()


def _wrong_option(q):
    """Return a deterministic wrong option key ('a'..'d') for question q."""
    for opt in ("a", "b", "c", "d"):
        if opt != q["answer"]:
            return opt
    raise AssertionError("No wrong option found")


def quiz_answers(correct_counts=None, set_id=1):
    """
    Build a full 20-question answer dictionary (5 per category) for the given set.
    Default: aptitude=0/5 (lvl 1, gap 4 High), coding=3/5 (lvl 3, gap 2 Medium),
             technical=4/5 (lvl 4, gap 1 Low), hr=5/5 (lvl 5, gap 0 No gap).
    """
    counts = correct_counts or {"aptitude": 0, "coding": 3, "technical": 4, "hr": 5}
    answers = {}
    for cat_key, target_correct in counts.items():
        cat_qs = am.QUESTIONS_BY_SET_AND_CATEGORY[set_id][cat_key]
        for idx, q in enumerate(cat_qs):
            answers[q["id"]] = q["answer"] if idx < target_correct else _wrong_option(q)
    return answers


def valid_form(correct_counts=None, set_id=1, **overrides):
    """A complete, valid quiz form submission. Pass keyword arguments to override fields."""
    data = {
        "name": "Asha Kumar",
        "email": "asha@example.com",
        "branch": "CSE",
        "year": "3",
        "question_set": str(set_id),
    }
    for qid, opt in quiz_answers(correct_counts, set_id=set_id).items():
        data["q_" + qid] = opt
    data.update(overrides)
    return data


def rows(db_path, sql, params=()):
    return database.fetch_all(sql, params, db_path)


# ---------------------------------------------------------------------------
# 1. Scoring & Skill gap calculation
# ---------------------------------------------------------------------------
class TestSkillGapCalculation:
    @pytest.mark.parametrize("score, expected_rating", [
        (0, 1), (19.9, 1),
        (20, 2), (25, 2), (44.9, 2),
        (45, 3), (50, 3), (69.9, 3),
        (70, 4), (75, 4), (89.9, 4),
        (90, 5), (100, 5),
    ])
    def test_score_to_rating_thresholds(self, score, expected_rating):
        assert am.score_to_rating(score) == expected_rating

    @pytest.mark.parametrize("bad", [-1, 101, "50", None, True, False])
    def test_score_to_rating_rejects_invalid_values(self, bad):
        with pytest.raises(ValueError):
            am.score_to_rating(bad)

    def test_evaluate_quiz_answers_grades_accurately(self):
        graded = am.evaluate_quiz_answers(
            quiz_answers({"aptitude": 0, "coding": 3, "technical": 4, "hr": 5})
        )
        assert graded["scores"] == {
            "aptitude": 0.0,
            "coding": 60.0,
            "technical": 80.0,
            "hr": 100.0,
        }
        assert graded["ratings"] == {
            "aptitude": 1,
            "coding": 3,
            "technical": 4,
            "hr": 5,
        }
        assert len(graded["review"]) == len(am.QUESTIONS) == 20

    @pytest.mark.parametrize("rating, expected_gap", [(1, 4), (2, 3), (3, 2), (4, 1), (5, 0)])
    def test_gap_is_five_minus_rating(self, rating, expected_gap):
        assert am.calculate_gap(rating) == expected_gap

    @pytest.mark.parametrize("bad", [0, 6, -1, 99, "3", 3.0, 2.5, None, True, False])
    def test_calculate_gap_rejects_invalid_values(self, bad):
        with pytest.raises(ValueError):
            am.calculate_gap(bad)

    @pytest.mark.parametrize("gap, level", [(4, "High"), (3, "High"), (2, "Medium"),
                                            (1, "Low"), (0, "No gap")])
    def test_priority_levels(self, gap, level):
        assert am.priority_for_gap(gap)[0] == level

    def test_calculate_skill_gaps_for_all_categories(self):
        results = am.calculate_skill_gaps(
            {"aptitude": 1, "coding": 3, "technical": 4, "hr": 5},
            scores={"aptitude": 0.0, "coding": 60.0, "technical": 80.0, "hr": 100.0},
        )
        by_key = {r["key"]: r for r in results}
        assert [r["key"] for r in results] == ["aptitude", "coding", "technical", "hr"]
        assert by_key["aptitude"]["gap"] == 4 and by_key["aptitude"]["priority"] == "High"
        assert by_key["coding"]["gap"] == 2 and by_key["coding"]["priority"] == "Medium"
        assert by_key["technical"]["gap"] == 1 and by_key["technical"]["priority"] == "Low"
        assert by_key["hr"]["gap"] == 0 and by_key["hr"]["priority"] == "No gap"
        assert by_key["aptitude"]["rating_label"] == "Beginner"
        assert by_key["technical"]["score_percent"] == 80.0
        assert by_key["technical"]["correct_count"] == 4

    def test_priority_rank_biggest_gap_first_ties_keep_category_order(self):
        results = am.calculate_skill_gaps({"aptitude": 3, "coding": 1, "technical": 1, "hr": 5})
        rank = {r["key"]: r["priority_rank"] for r in results}
        assert rank == {"coding": 1, "technical": 2, "aptitude": 3, "hr": 4}

    def test_missing_category_rejected(self):
        with pytest.raises(ValueError):
            am.calculate_skill_gaps({"aptitude": 3, "coding": 3, "technical": 3})

    def test_all_fives_means_no_gaps(self):
        results = am.calculate_skill_gaps({k: 5 for k in ("aptitude", "coding", "technical", "hr")})
        assert all(r["gap"] == 0 for r in results)


# ---------------------------------------------------------------------------
# 2. Server-side validation (function level)
# ---------------------------------------------------------------------------
class TestValidation:
    def test_valid_form_has_no_errors(self):
        data, errors = am.validate_submission(valid_form())
        assert errors == {}
        assert data["ratings"] == {"aptitude": 1, "coding": 3, "technical": 4, "hr": 5}
        assert data["scores"] == {"aptitude": 0.0, "coding": 60.0, "technical": 80.0, "hr": 100.0}
        assert data["student"]["year"] == 3

    def test_email_is_lowercased_and_spaces_trimmed(self):
        data, errors = am.validate_submission(valid_form(email="  ASHA@Example.COM ", name="  Asha  "))
        assert errors == {}
        assert data["student"]["email"] == "asha@example.com"
        assert data["student"]["name"] == "Asha"

    @pytest.mark.parametrize("qid", ["s1_apt_1", "s1_code_2", "s1_tech_3", "s1_hr_4"])
    def test_missing_question_answer_is_rejected(self, qid):
        form = valid_form()
        del form["q_" + qid]
        _, errors = am.validate_submission(form)
        assert "q_" + qid in errors
        assert len(errors) == 1

    @pytest.mark.parametrize("bad", ["e", "1", "abc", "", "   ", "a; DROP TABLE students"])
    def test_invalid_option_is_rejected(self, bad):
        _, errors = am.validate_submission(valid_form(q_s1_code_1=bad))
        assert "q_s1_code_1" in errors

    @pytest.mark.parametrize("field", ["name", "email", "branch", "year"])
    def test_missing_student_field_is_rejected(self, field):
        form = valid_form()
        del form[field]
        _, errors = am.validate_submission(form)
        assert field in errors

    @pytest.mark.parametrize("email", ["not-an-email", "a@b", "@example.com", "a b@example.com"])
    def test_bad_email_is_rejected(self, email):
        _, errors = am.validate_submission(valid_form(email=email))
        assert "email" in errors

    @pytest.mark.parametrize("year", ["0", "5", "x", "2.5"])
    def test_bad_year_is_rejected(self, year):
        _, errors = am.validate_submission(valid_form(year=year))
        assert "year" in errors

    def test_too_long_name_is_rejected(self):
        _, errors = am.validate_submission(valid_form(name="A" * 101))
        assert "name" in errors

    def test_empty_form_reports_every_field(self):
        _, errors = am.validate_submission({})
        expected_fields = {"name", "email", "branch", "year"} | {"q_" + q["id"] for q in am.QUESTIONS}
        assert set(errors) == expected_fields


# ---------------------------------------------------------------------------
# 3. The web page: real questions form, submission, results
# ---------------------------------------------------------------------------
class TestAssessmentPage:
    def test_form_page_shows_categories_and_real_questions(self, client):
        resp = client.get("/assessment")
        html = resp.get_data(as_text=True)
        assert resp.status_code == 200
        for text in ("Aptitude", "Coding", "Technical Knowledge", "HR &amp; Communication",
                     "Beginner", "Basic", "Intermediate", "Advanced", "Expert"):
            assert text in html
        for q in am.QUESTIONS:
            assert f'name="q_{q["id"]}"' in html
            assert str(html_escape(q["prompt"])) in html
        assert 'id="start-assessment-btn"' in html
        assert 'id="assessmentPagerModal"' in html
        for page_idx in range(len(am.CATEGORIES)):
            assert f'data-page="{page_idx}"' in html

    def test_page_reuses_base_template(self, client):
        html = client.get("/assessment").get_data(as_text=True)
        assert html.count("<html") == 1
        assert "navbar" in html and "Progress Dashboard" in html

    def test_successful_submission_redirects_to_result(self, client):
        resp = client.post("/assessment", data=valid_form())
        assert resp.status_code == 302
        assert "/assessment?student=1" in resp.headers["Location"]

    def test_result_page_shows_scores_gaps_priorities_and_review(self, client):
        resp = client.post("/assessment", data=valid_form(), follow_redirects=True)
        html = resp.get_data(as_text=True)
        assert resp.status_code == 200
        assert "Asha Kumar" in html
        assert "0 / 5 correct" in html
        assert "3 / 5 correct" in html
        assert "4 / 5 correct" in html
        assert "5 / 5 correct" in html
        assert "Question-by-Question Answer Review" in html
        for label in ("Aptitude", "Coding", "Technical Knowledge", "HR &amp; Communication"):
            assert label in html
        for priority in ("High", "Medium", "Low", "No gap"):
            assert priority in html
        assert "Improvement priorities" in html
        priorities = html.split("Improvement priorities")[1]
        assert priorities.index("Aptitude") < priorities.index("Coding") < priorities.index("Technical Knowledge")

    def test_all_correct_shows_no_gap_message(self, client):
        data = valid_form({"aptitude": 5, "coding": 5, "technical": 5, "hr": 5})
        html = client.post("/assessment", data=data, follow_redirects=True).get_data(as_text=True)
        assert "no skill gaps" in html
        assert "100.0%" in html

    def test_invalid_option_returns_400_and_saves_nothing(self, client, db_path):
        resp = client.post("/assessment", data=valid_form(q_coding="z", q_s1_code_1="z"))
        html = resp.get_data(as_text=True)
        assert resp.status_code == 400
        assert "Invalid option selected" in html
        assert rows(db_path, "SELECT * FROM skill_assessments") == []
        assert rows(db_path, "SELECT * FROM students") == []

    def test_missing_answer_returns_400_and_saves_nothing(self, client, db_path):
        form = valid_form()
        del form["q_s1_hr_1"]
        resp = client.post("/assessment", data=form)
        assert resp.status_code == 400
        assert "Please answer HR &amp; Communication Question 1." in resp.get_data(as_text=True)
        assert rows(db_path, "SELECT * FROM skill_assessments") == []

    def test_empty_post_returns_400(self, client):
        assert client.post("/assessment", data={}).status_code == 400

    def test_form_keeps_valid_values_after_an_error(self, client):
        html = client.post("/assessment", data=valid_form(q_s1_code_1="z")).get_data(as_text=True)
        assert 'value="Asha Kumar"' in html
        assert 'value="asha@example.com"' in html

    def test_user_text_is_escaped_in_the_result_page(self, client):
        data = valid_form(name="<script>alert(1)</script>")
        html = client.post("/assessment", data=data, follow_redirects=True).get_data(as_text=True)
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html

    def test_unknown_student_gives_404_with_message(self, client):
        resp = client.get("/assessment?student=999")
        assert resp.status_code == 404
        assert "No assessment was found" in resp.get_data(as_text=True)

    def test_non_numeric_student_parameter_just_shows_form(self, client):
        resp = client.get("/assessment?student=abc")
        assert resp.status_code == 200
        assert "Your details" in resp.get_data(as_text=True)

    def test_other_pages_still_work(self, client):
        for path in ("/", "/planner", "/progress"):
            assert client.get(path).status_code == 200

    def test_home_page_marks_assessment_as_ready(self, client):
        assert "Ready" in client.get("/").get_data(as_text=True)


# ---------------------------------------------------------------------------
# 4. Database persistence
# ---------------------------------------------------------------------------
class TestPersistence:
    def test_submission_saves_student_and_four_scored_rows(self, client, db_path):
        client.post("/assessment", data=valid_form())

        students = rows(db_path, "SELECT name, email, branch, year FROM students")
        assert len(students) == 1
        assert dict(students[0]) == {
            "name": "Asha Kumar",
            "email": "asha@example.com",
            "branch": "CSE",
            "year": 3,
        }

        saved = rows(db_path, "SELECT category, topic, self_rating, target_level, skill_gap, "
                              "score_percent FROM skill_assessments ORDER BY id")
        assert [tuple(r) for r in saved] == [
            ("Aptitude", "Overall", 1, 5.0, 4.0, 0.0),
            ("Coding", "Overall", 3, 5.0, 2.0, 60.0),
            ("Technical Knowledge", "Overall", 4, 5.0, 1.0, 80.0),
            ("HR & Communication", "Overall", 5, 5.0, 0.0, 100.0),
        ]

    def test_rows_are_linked_to_the_student(self, client, db_path):
        client.post("/assessment", data=valid_form())
        linked = rows(db_path, "SELECT COUNT(*) AS n FROM skill_assessments sa "
                               "JOIN students s ON s.id = sa.student_id WHERE s.email = ?",
                      ("asha@example.com",))
        assert linked[0]["n"] == 4

    def test_data_survives_a_new_app_instance(self, client, db_path):
        """Simulates restarting the server: data must still be in the file."""
        client.post("/assessment", data=valid_form())
        new_client = create_app({"TESTING": True, "DATABASE": db_path}).test_client()
        html = new_client.get("/assessment?student=1").get_data(as_text=True)
        assert "Asha Kumar" in html and "High" in html and "80%" in html

    def test_same_email_reuses_student_and_latest_assessment_wins(self, client, db_path):
        client.post("/assessment", data=valid_form())
        client.post(
            "/assessment",
            data=valid_form({"aptitude": 5, "coding": 3, "technical": 4, "hr": 5}, name="Asha K", year="4"),
        )

        students = rows(db_path, "SELECT name, year FROM students")
        assert len(students) == 1
        assert (students[0]["name"], students[0]["year"]) == ("Asha K", 4)
        assert rows(db_path, "SELECT COUNT(*) AS n FROM skill_assessments")[0]["n"] == 8

        latest = am.get_latest_assessment(1, db_path)
        aptitude = next(r for r in latest["results"] if r["key"] == "aptitude")
        assert aptitude["rating"] == 5 and aptitude["gap"] == 0 and aptitude["score_percent"] == 100.0

    def test_two_students_are_kept_separate(self, client, db_path):
        client.post("/assessment", data=valid_form({"aptitude": 0, "coding": 3, "technical": 4, "hr": 5}))
        client.post(
            "/assessment",
            data=valid_form({"aptitude": 1, "coding": 3, "technical": 4, "hr": 5},
                            email="bala@example.com", name="Bala"),
        )
        assert rows(db_path, "SELECT COUNT(*) AS n FROM students")[0]["n"] == 2
        one = am.get_latest_assessment(1, db_path)
        two = am.get_latest_assessment(2, db_path)
        assert one["student"]["name"] == "Asha Kumar" and two["student"]["name"] == "Bala"
        assert one["results"][0]["rating"] == 1 and two["results"][0]["rating"] == 2

    def test_get_latest_assessment_returns_none_when_missing(self, client, db_path):
        assert am.get_latest_assessment(123, db_path) is None

    def test_student_without_assessment_returns_none(self, client, db_path):
        database.execute("INSERT INTO students (name, email, branch, year) VALUES (?, ?, ?, ?)",
                         ("Nobody", "n@example.com", "IT", 1), db_path)
        assert am.get_latest_assessment(1, db_path) is None

    def test_sql_injection_text_is_stored_as_plain_text(self, client, db_path):
        evil = "x'); DROP TABLE students;--"
        client.post("/assessment", data=valid_form(name=evil))
        assert rows(db_path, "SELECT name FROM students")[0]["name"] == evil
        assert set(database.list_tables(db_path)) >= set(database.TABLE_NAMES)

    def test_save_assessment_rejects_bad_ratings_and_saves_nothing(self, client, db_path):
        student = {"name": "A", "email": "a@example.com", "branch": "CSE", "year": 1}
        with pytest.raises(ValueError):
            am.save_assessment(student, {"aptitude": 9, "coding": 3, "technical": 3, "hr": 3}, db_path)
        assert rows(db_path, "SELECT * FROM students") == []

    def test_failed_save_is_rolled_back_completely(self, client, db_path):
        """If inserting the ratings fails, the new student row must not stay behind."""
        with database.db_session(db_path) as conn:
            conn.execute("CREATE TRIGGER boom BEFORE INSERT ON skill_assessments "
                         "BEGIN SELECT RAISE(ABORT, 'simulated failure'); END;")
        student = {"name": "A", "email": "a@example.com", "branch": "CSE", "year": 1}
        with pytest.raises(sqlite3.Error):
            am.save_assessment(student, {"aptitude": 3, "coding": 3, "technical": 3, "hr": 3}, db_path)
        assert rows(db_path, "SELECT * FROM students") == []

    def test_database_error_shows_friendly_message(self, client, db_path):
        with database.db_session(db_path) as conn:
            conn.execute("CREATE TRIGGER boom BEFORE INSERT ON skill_assessments "
                         "BEGIN SELECT RAISE(ABORT, 'simulated failure'); END;")
        resp = client.post("/assessment", data=valid_form())
        html = resp.get_data(as_text=True)
        assert resp.status_code == 500
        assert "could not be saved" in html
        assert "Traceback" not in html and "simulated failure" not in html

    def test_existing_schema_is_unchanged(self, client, db_path):
        assert set(database.list_tables(db_path)) == set(database.TABLE_NAMES)
        columns = [r["name"] for r in rows(db_path, "PRAGMA table_info(skill_assessments)")]
        assert columns == ["id", "student_id", "category", "topic", "self_rating",
                           "score_percent", "target_level", "skill_gap", "assessed_at"]


# ---------------------------------------------------------------------------
# 5. CareerRide datasheet & alternating question sets
# ---------------------------------------------------------------------------
class TestCareerRideQuestionSets:
    def test_careerride_datasheet_has_three_sets_of_five_per_category(self):
        assert os.path.exists(am.DEFAULT_DATASET_PATH)
        assert am.AVAILABLE_SETS == [1, 2, 3]
        assert am.QUESTIONS_PER_CATEGORY == 5

        all_prompts = set()
        all_ids = set()
        for set_id in am.AVAILABLE_SETS:
            questions, _ = am.get_questions_for_set(set_id)
            assert len(questions) == 20
            for cat in am.CATEGORIES:
                cat_qs = am.QUESTIONS_BY_SET_AND_CATEGORY[set_id][cat["key"]]
                assert len(cat_qs) == 5
                for q in cat_qs:
                    assert q["set_id"] == set_id
                    assert "careerride.com" in q["source_url"]
                    assert q["id"] not in all_ids
                    assert q["prompt"] not in all_prompts
                    all_ids.add(q["id"])
                    all_prompts.add(q["prompt"])
        assert len(all_ids) == 60

    def test_get_requests_alternate_sets_1_2_3_1(self, client):
        seen_sets = []
        for expected_set in (1, 2, 3, 1):
            html = client.get("/assessment").get_data(as_text=True)
            assert f'name="question_set" value="{expected_set}"' in html
            assert f"Question Set {expected_set} of 3" in html
            questions, _ = am.get_questions_for_set(expected_set)
            for q in questions:
                assert f'name="q_{q["id"]}"' in html
            seen_sets.append(expected_set)
        assert seen_sets == [1, 2, 3, 1]

    def test_explicit_set_query_param_loads_requested_set(self, client):
        html = client.get("/assessment?set=2").get_data(as_text=True)
        assert 'name="question_set" value="2"' in html
        assert "Question Set 2 of 3" in html
        questions, _ = am.get_questions_for_set(2)
        for q in questions:
            assert f'name="q_{q["id"]}"' in html

    def test_submitting_alternated_set_2_grades_and_persists(self, client, db_path):
        data = valid_form({"aptitude": 5, "coding": 2, "technical": 4, "hr": 3}, set_id=2)
        resp = client.post("/assessment", data=data)
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/assessment?student=1")

        html = client.get(resp.headers["Location"]).get_data(as_text=True)
        assert "Question Set <strong>2</strong>" in html
        assert "Question-by-Question Answer Review" in html
        assert "5 / 5 correct" in html
        assert "2 / 5 correct" in html
        assert "4 / 5 correct" in html
        assert "3 / 5 correct" in html

        saved = rows(db_path, "SELECT category, self_rating, score_percent FROM skill_assessments ORDER BY id")
        assert [tuple(r) for r in saved] == [
            ("Aptitude", 5, 100.0),
            ("Coding", 2, 40.0),
            ("Technical Knowledge", 4, 80.0),
            ("HR & Communication", 3, 60.0),
        ]

    def test_validation_error_preserves_submitted_set(self, client):
        form = valid_form(set_id=3, q_s3_code_1="invalid")
        resp = client.post("/assessment", data=form)
        html = resp.get_data(as_text=True)
        assert resp.status_code == 400
        assert 'name="question_set" value="3"' in html
        assert "Question Set 3 of 3" in html
