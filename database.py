"""
database.py
===========
Shared SQLite layer for the whole team project.

This file only does three things:
  1. Opens connections to the SQLite database.
  2. Creates the shared tables (init_db).
  3. Offers small helper functions that ALWAYS use parameterized queries.

It does NOT contain any module feature (assessment, planner, progress).
Each module imports what it needs from here, for example:

    from database import get_connection, fetch_all, execute

Parameterized queries
---------------------
Never build SQL by joining strings with user input. Use "?" placeholders and
pass the values separately. This prevents SQL injection:

    fetch_one("SELECT * FROM students WHERE email = ?", (email,))
"""

import os
import sqlite3
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# The database file location. Override it with the DATABASE_PATH environment
# variable. *.db files are listed in .gitignore, so they are never committed.
DEFAULT_DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "placement.db"))


# ---------------------------------------------------------------------------
# Shared schema
#
# students (1) ---< skill_assessments
# students (1) ---< preparation_tasks
# students (1) ---< practice_results
# skill_assessments (1) ---< preparation_tasks   (optional link)
# preparation_tasks (1) ---< practice_results    (optional link)
#
# NOTE: the "students" columns match the ones used in member1/assessment.py,
# so both can create this table without conflict.
# ---------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    branch      TEXT NOT NULL,
    year        INTEGER NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- One row per student per topic, written by the Assessment module.
CREATE TABLE IF NOT EXISTS skill_assessments (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id     INTEGER NOT NULL,
    category       TEXT NOT NULL,            -- e.g. Aptitude, Coding
    topic          TEXT NOT NULL,            -- e.g. DBMS
    self_rating    INTEGER CHECK (self_rating BETWEEN 1 AND 5),
    score_percent  REAL    CHECK (score_percent BETWEEN 0 AND 100),
    target_level   REAL    CHECK (target_level BETWEEN 1 AND 5),
    skill_gap      REAL    CHECK (skill_gap >= 0),
    assessed_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- To-do items written by the Planner module.
CREATE TABLE IF NOT EXISTS preparation_tasks (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id           INTEGER NOT NULL,
    skill_assessment_id  INTEGER,            -- optional: which gap this task fixes
    title                TEXT NOT NULL,
    description          TEXT,
    category             TEXT,
    due_date             TEXT,               -- YYYY-MM-DD
    time_slot            TEXT,               -- e.g. '18:00 - 19:30'
    estimated_minutes    INTEGER NOT NULL DEFAULT 60,
    sort_order           INTEGER NOT NULL DEFAULT 0,
    status               TEXT NOT NULL DEFAULT 'pending'
                         CHECK (status IN ('pending', 'in_progress', 'completed')),
    created_at           TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    completed_at         TEXT,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_assessment_id) REFERENCES skill_assessments(id) ON DELETE SET NULL
);

-- Practice attempts, used by the Progress module for charts.
CREATE TABLE IF NOT EXISTS practice_results (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id        INTEGER NOT NULL,
    task_id           INTEGER,               -- optional: the task this practice belongs to
    category          TEXT NOT NULL,
    topic             TEXT,
    score             REAL NOT NULL CHECK (score >= 0),
    max_score         REAL NOT NULL CHECK (max_score > 0),
    duration_minutes  INTEGER CHECK (duration_minutes >= 0),
    practiced_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES preparation_tasks(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS user_logins (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id            INTEGER,
    full_name             TEXT NOT NULL,
    gmail                 TEXT NOT NULL UNIQUE,
    university_name       TEXT NOT NULL,
    verifier_email        TEXT,
    verification_code     TEXT,
    verification_token    TEXT,
    verification_sent_to  TEXT,
    delivery_mode         TEXT NOT NULL DEFAULT 'local_preview'
                          CHECK (delivery_mode IN ('gmail_smtp', 'local_preview')),
    status                TEXT NOT NULL DEFAULT 'pending'
                          CHECK (status IN ('pending', 'verified')),
    sent_at               TEXT,
    verified_at           TEXT,
    current_streak        INTEGER NOT NULL DEFAULT 0,
    best_streak           INTEGER NOT NULL DEFAULT 0,
    last_login_date       TEXT,
    last_streak_at        TEXT,
    total_login_days      INTEGER NOT NULL DEFAULT 0,
    created_at            TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS ai_question_sets (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id    INTEGER NOT NULL,
    category_key  TEXT NOT NULL,
    topic_focus   TEXT,
    difficulty    TEXT NOT NULL DEFAULT 'standard',
    model_name    TEXT NOT NULL DEFAULT 'gemini-4-hydrogen',
    questions_json TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS company_ai_tests (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id     INTEGER,
    company_slug   TEXT NOT NULL,
    company_name   TEXT NOT NULL,
    model_name     TEXT NOT NULL DEFAULT 'gemini-4-hydrogen',
    questions_json TEXT NOT NULL,
    score          INTEGER,
    max_score      INTEGER,
    created_at     TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_skill_assessments_student ON skill_assessments(student_id);
CREATE INDEX IF NOT EXISTS idx_preparation_tasks_student ON preparation_tasks(student_id);
CREATE INDEX IF NOT EXISTS idx_preparation_tasks_status  ON preparation_tasks(status);
CREATE INDEX IF NOT EXISTS idx_practice_results_student  ON practice_results(student_id);
CREATE INDEX IF NOT EXISTS idx_user_logins_gmail         ON user_logins(gmail);
CREATE INDEX IF NOT EXISTS idx_ai_question_sets_student  ON ai_question_sets(student_id);
CREATE INDEX IF NOT EXISTS idx_company_ai_tests_slug     ON company_ai_tests(company_slug);
"""

# Names of the tables created above (handy for checks and documentation).
TABLE_NAMES = (
    "students",
    "skill_assessments",
    "preparation_tasks",
    "practice_results",
    "user_logins",
    "ai_question_sets",
    "company_ai_tests",
)


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------
def get_connection(db_path=None):
    """Open a connection. Rows can be used like dictionaries: row["name"]."""
    conn = sqlite3.connect(db_path or DEFAULT_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite needs this for every connection
    return conn


@contextmanager
def db_session(db_path=None):
    """
    Open a connection, commit if everything worked, roll back on error and
    always close it:

        with db_session() as conn:
            conn.execute("INSERT INTO students (...) VALUES (?, ?, ?, ?)", values)
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path=None):
    """Create all shared tables and apply safe additive column migrations."""
    with db_session(db_path) as conn:
        conn.executescript(SCHEMA)
        _ensure_columns(
            conn,
            "user_logins",
            (
                ("current_streak", "INTEGER NOT NULL DEFAULT 0"),
                ("best_streak", "INTEGER NOT NULL DEFAULT 0"),
                ("last_login_date", "TEXT"),
                ("last_streak_at", "TEXT"),
                ("total_login_days", "INTEGER NOT NULL DEFAULT 0"),
            ),
        )
        _ensure_columns(
            conn,
            "preparation_tasks",
            (
                ("time_slot", "TEXT"),
                ("estimated_minutes", "INTEGER NOT NULL DEFAULT 60"),
                ("sort_order", "INTEGER NOT NULL DEFAULT 0"),
            ),
        )


def _ensure_columns(conn, table_name, columns):
    """Safely add missing additive columns to an existing SQLite table."""
    existing_cols = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    for col_name, col_def in columns:
        if col_name not in existing_cols:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}")


# ---------------------------------------------------------------------------
# Small parameterized query helpers
# ---------------------------------------------------------------------------
def fetch_all(sql, params=(), db_path=None):
    """Run a SELECT and return a list of rows."""
    with db_session(db_path) as conn:
        return conn.execute(sql, params).fetchall()


def fetch_one(sql, params=(), db_path=None):
    """Run a SELECT and return the first row, or None."""
    with db_session(db_path) as conn:
        return conn.execute(sql, params).fetchone()


def execute(sql, params=(), db_path=None):
    """
    Run an INSERT / UPDATE / DELETE.
    Returns the new row id for INSERT, otherwise the number of rows changed.
    """
    with db_session(db_path) as conn:
        cur = conn.execute(sql, params)
        return cur.lastrowid if sql.lstrip().upper().startswith("INSERT") else cur.rowcount


def list_tables(db_path=None):
    """Names of all tables in the database (used to check the setup)."""
    rows = fetch_all(
        "SELECT name FROM sqlite_master WHERE type = ? AND name NOT LIKE ? ORDER BY name",
        ("table", "sqlite_%"),
        db_path,
    )
    return [r["name"] for r in rows]


if __name__ == "__main__":
    # Running "python database.py" just creates the database and lists the tables.
    init_db()
    print("Database ready at:", DEFAULT_DB_PATH)
    print("Tables:", ", ".join(list_tables()))