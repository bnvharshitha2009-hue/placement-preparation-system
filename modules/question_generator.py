"""
modules/question_generator.py
=============================
Verified Placement Question Generator using Google Gemini (`google-genai` SDK).

Uses the Interactions API (`client.interactions.create`) with `gemini-4-hydrogen`
and strict JSON Schema `response_format` to generate step-verified placement
MCQs tailored to a student's category, difficulty level, and weak topics, saving
them into `ai_question_sets` in SQLite.
"""

import json
import os
import secrets

from database import db_session, fetch_one
from modules import assessment as assessment_module

DEFAULT_GEMINI_MODEL = "gemini-4-hydrogen"
VALID_DIFFICULTIES = ("standard", "hard")

QUESTIONS_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "minItems": 5,
            "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "prompt": {"type": "string"},
                    "option_a": {"type": "string"},
                    "option_b": {"type": "string"},
                    "option_c": {"type": "string"},
                    "option_d": {"type": "string"},
                    "verification_steps": {"type": "string"},
                    "answer": {"type": "string", "enum": ["a", "b", "c", "d"]},
                    "explanation": {"type": "string"},
                },
                "required": [
                    "topic",
                    "prompt",
                    "option_a",
                    "option_b",
                    "option_c",
                    "option_d",
                    "verification_steps",
                    "answer",
                    "explanation",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["questions"],
    "additionalProperties": False,
}

SYSTEM_INSTRUCTION = (
    "You are a senior campus placement exam writer for engineering students. "
    "Generate original, unambiguous, mathematically and technically verified 4-option MCQs. "
    "Solve every calculation or code trace carefully inside `verification_steps` BEFORE "
    "selecting `answer` ('a', 'b', 'c', or 'd'). Ensure all four options are distinct and "
    "exactly one option is unquestionably correct."
)


def get_gemini_status():
    """Return whether google-genai SDK and GEMINI_API_KEY are available."""
    api_key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
    is_placeholder = api_key.lower() in {"", "your-gemini-api-key", "your_api_key"}
    try:
        from google import genai  # noqa: F401
        sdk_installed = True
    except ImportError:
        sdk_installed = False

    return {
        "sdk_installed": sdk_installed,
        "api_key_configured": bool(api_key and not is_placeholder),
        "ready": sdk_installed and bool(api_key and not is_placeholder),
        "model": DEFAULT_GEMINI_MODEL,
    }


def _validate_and_normalize_questions(raw_questions, category_key):
    """Ensure every generated MCQ has unique non-empty options, a valid answer, and explanations."""
    if not isinstance(raw_questions, list) or len(raw_questions) == 0:
        raise ValueError("Gemini did not return any questions.")

    seen_prompts = set()
    normalized = []
    batch_tag = secrets.token_hex(4)

    for idx, q in enumerate(raw_questions, start=1):
        if not isinstance(q, dict):
            raise ValueError(f"Question {idx} is malformed.")

        prompt = " ".join(str(q.get("prompt") or "").split())
        topic = " ".join(str(q.get("topic") or "Placement Practice").split())
        explanation = " ".join(str(q.get("explanation") or q.get("verification_steps") or "").split())
        answer = str(q.get("answer") or "").strip().lower()
        options = {
            opt: " ".join(str(q.get(f"option_{opt}") or "").split())
            for opt in ("a", "b", "c", "d")
        }

        if not prompt or prompt.lower() in seen_prompts:
            raise ValueError(f"Question {idx} has an empty or duplicate prompt.")
        if any(not text for text in options.values()):
            raise ValueError(f"Question {idx} is missing option text.")
        if len({t.lower() for t in options.values()}) < 4:
            raise ValueError(f"Question {idx} has duplicate options.")
        if answer not in assessment_module.VALID_OPTIONS:
            raise ValueError(f"Question {idx} returned invalid answer key {answer!r}.")
        if not explanation:
            raise ValueError(f"Question {idx} is missing an explanation.")

        seen_prompts.add(prompt.lower())
        normalized.append({
            "id": f"ai_{batch_tag}_{idx}",
            "set_id": 0,
            "category": category_key,
            "number": idx,
            "topic": topic[:80],
            "source_url": "gemini-api://gemini-4-hydrogen",
            "prompt": prompt,
            "options": options,
            "answer": answer,
            "explanation": explanation,
        })

    return normalized


def _call_gemini_for_questions(category_label, topic_focus="", difficulty="standard",
                               client=None, model=DEFAULT_GEMINI_MODEL):
    """Call Gemini Interactions API with JSON schema structured output."""
    api_key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
    if client is None:
        if not api_key or api_key.lower() in {"your-gemini-api-key", "your_api_key"}:
            raise RuntimeError("GEMINI_API_KEY is not configured in .env or environment variables.")
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError("The google-genai package is not installed. Run: pip install -U google-genai") from exc
        client = genai.Client(api_key=api_key)

    diff_desc = (
        "challenging product-company campus interview level (tricky edge cases, time complexity, multi-step math)"
        if difficulty == "hard"
        else "realistic Indian campus placement test level (TCS/Infosys/Accenture/product screening)"
    )
    focus_clause = f" concentrating specifically on '{topic_focus}'" if topic_focus else ""

    prompt = (
        f"Create exactly 5 high-accuracy multiple-choice questions for the '{category_label}' "
        f"placement category{focus_clause} at {diff_desc}.\n"
        "Requirements:\n"
        "- Do not include option letters like 'A.' inside option_a..option_d.\n"
        "- Solve each problem step by step inside `verification_steps` before setting `answer`.\n"
        "- Write a clear, concise student-friendly explanation in `explanation`."
    )

    interaction = client.interactions.create(
        model=model,
        system_instruction=SYSTEM_INSTRUCTION,
        input=prompt,
        store=False,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": QUESTIONS_JSON_SCHEMA,
        },
    )
    raw_text = interaction.output_text
    if not raw_text:
        raise ValueError("Gemini returned an empty response.")

    parsed = json.loads(raw_text)
    return parsed.get("questions") or []


def generate_and_save_question_set(student_id, category_key="aptitude", topic_focus="",
                                   difficulty="standard", db_path=None, client=None):
    """
    Generate 5 verified MCQs via Gemini API, validate them, store them in
    `ai_question_sets`, and return the saved set record.
    """
    cat_info = assessment_module.CATEGORY_BY_KEY.get(category_key)
    if not cat_info:
        cat_info = assessment_module.CATEGORY_BY_KEY["aptitude"]
        category_key = "aptitude"

    clean_diff = difficulty if difficulty in VALID_DIFFICULTIES else "standard"
    clean_focus = " ".join((topic_focus or "").split())[:100]

    raw_questions = _call_gemini_for_questions(
        cat_info["label"],
        topic_focus=clean_focus,
        difficulty=clean_diff,
        client=client,
    )
    validated_questions = _validate_and_normalize_questions(raw_questions, category_key)

    with db_session(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO ai_question_sets
                (student_id, category_key, topic_focus, difficulty, model_name, questions_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                student_id,
                category_key,
                clean_focus or cat_info["label"],
                clean_diff,
                DEFAULT_GEMINI_MODEL,
                json.dumps(validated_questions),
            ),
        )
        set_row_id = cur.lastrowid

    return {
        "ai_set_id": set_row_id,
        "student_id": student_id,
        "category_key": category_key,
        "category_label": cat_info["label"],
        "topic_focus": clean_focus or cat_info["label"],
        "difficulty": clean_diff,
        "model_name": DEFAULT_GEMINI_MODEL,
        "questions": validated_questions,
    }


def get_ai_question_set(ai_set_id, student_id=None, db_path=None):
    """Load a generated AI question set by ID, or None if not found."""
    if not ai_set_id:
        return None
    if student_id is not None:
        row = fetch_one(
            "SELECT * FROM ai_question_sets WHERE id = ? AND student_id = ?",
            (ai_set_id, student_id),
            db_path,
        )
    else:
        row = fetch_one("SELECT * FROM ai_question_sets WHERE id = ?", (ai_set_id,), db_path)

    if row is None:
        return None
    record = dict(row)
    record["questions"] = json.loads(record["questions_json"])
    record["category_label"] = assessment_module.CATEGORY_BY_KEY.get(
        record["category_key"], {}
    ).get("label", record["category_key"].title())
    return record
