# placement-preparation-system
A Python-based system to assess student skills, identify gaps, generate personalized placement preparation plans, practice quizzes, prepare for technical and HR interviews, and track progress. Built with Flask, SQLite, Bootstrap, and Chart.js using Git and GitHub for collaboration.

# Placement Preparation and Skill Gap Analysis System

A college team project that helps students prepare for campus placements. It is designed to show a student which skills are strong and which are weak (the **skill gap**), turn those gaps into a study plan, and track progress over time.

> **Project status:** only the shared foundation is finished (Flask app, database, page layout and Home page). The three feature modules are **not connected yet**; their pages show a "Coming soon" placeholder.

## Features

**Working now (shared foundation)**
- Flask application with a Home page and a Bootstrap 5 navigation bar
- Placeholder pages for the three modules
- Shared SQLite database with four related tables (created automatically)
- Safe database helper functions that use parameterized queries

**Planned (one module per team member, not implemented in the foundation)**
- **Skill Assessment:** skill ratings (1-5), aptitude, coding, technical and HR assessments, skill gap calculation, strong and weak topics
- **Preparation Planner:** study tasks and deadlines based on the skill gaps
- **Progress Dashboard:** practice results and task completion shown with Chart.js charts

## Technology stack

| Part | Technology |
|---|---|
| Language | Python 3 |
| Web framework | Flask |
| Database | SQLite (built into Python) |
| Front end | HTML, Jinja2 templates, Bootstrap 5 |
| Charts | Chart.js (planned, used by the Progress module) |
| Testing | pytest |
| Version control | Git and GitHub |

## Project structure

```
project/
├── app.py                 Flask app: Home page + placeholder module pages
├── database.py            SQLite connection, shared tables, safe query helpers
├── planner.py             Member 2 interface (empty functions)
├── progress.py            Member 3 interface (empty functions)
├── requirements.txt       Python packages needed
├── .gitignore             Files Git must not save
├── README.md              This file
├── templates/
│   ├── base.html          Common layout + navigation bar
│   ├── index.html         Home page with the three module cards
│   └── placeholder.html   "Coming soon" page used until a module is ready
└── member1/               Member 1's module (assessment.py, assessment.html,
                           style.css, test_assessment.py), not connected yet
```

## Installation on Windows

You need **Python 3.9 or newer** and **Git**. Download Python from python.org (tick **"Add python.exe to PATH"** during installation) and Git from git-scm.com.

**1. Check the tools** (open PowerShell or Command Prompt):

```powershell
python --version
git --version
```

**2. Get the project:**

```powershell
git clone <your-github-repo-url>
cd <project-folder-name>
```

**3. Create a virtual environment** (a private box for this project's packages):

```powershell
python -m venv .venv
```

**4. Activate the virtual environment:**

```powershell
# PowerShell
.venv\Scripts\Activate.ps1

# Command Prompt (cmd)
.venv\Scripts\activate.bat
```

When it works, `(.venv)` appears at the start of the line.
If PowerShell says *"running scripts is disabled"*, run this once and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

On macOS or Linux, activate with `source .venv/bin/activate`.

**5. Install the dependencies:**

```powershell
pip install -r requirements.txt
```

**6. Start the application:**

```powershell
python app.py
```

Open **http://127.0.0.1:5000** in your browser. The database file `placement.db` is created automatically the first time. Press `Ctrl + C` to stop the server. When you finish, type `deactivate` to leave the virtual environment.

## Running the tests

There are no tests for the foundation yet. Member 1's tests run with:

```powershell
cd member1
python -m pytest test_assessment.py -v
```

## Database tables

All tables are created in `database.py`. Foreign keys are switched on.

| Table | Purpose | Linked to |
|---|---|---|
| `students` | Student profile (name, unique email, branch, year) | - |
| `skill_assessments` | One row per student per topic: self rating (1-5), score %, target level, skill gap | `student_id` -> `students` |
| `preparation_tasks` | Study tasks with status `pending` / `in_progress` / `completed` | `student_id` -> `students`; optional `skill_assessment_id` -> `skill_assessments` |
| `practice_results` | Practice attempts (score, max score, minutes) | `student_id` -> `students`; optional `task_id` -> `preparation_tasks` |

Always use `?` placeholders and pass the values separately. Never put user input directly into SQL text:

```python
from database import fetch_one, execute

student = fetch_one("SELECT * FROM students WHERE email = ?", (email,))
new_id = execute("INSERT INTO students (name, email, branch, year) VALUES (?, ?, ?, ?)",
                 (name, email, branch, year))
```

## Team member responsibilities

| Member | Module | Files | Main work |
|---|---|---|---|
| **Member 1** | Skill Assessment and Skill Gap Analysis | `assessment.py`, `assessment.html`, `style.css`, `test_assessment.py` | Self-rating form, four assessments, skill gap calculation, strong/weak topics, results |
| **Member 2** | Preparation Planner | `planner.py` and its own templates | Create and manage study tasks and deadlines from the skill gaps |
| **Member 3** | Progress Tracking and Dashboard | `progress.py` and its own templates | Record practice results, show progress with Chart.js charts |

**Everyone shares:** `app.py`, `database.py`, `templates/base.html`, `requirements.txt` and this README. Tell the team before changing a shared file, especially the database tables, because every module depends on them.

## Connecting a finished module

1. Put the module file in the project root (next to `app.py`).
2. In `app.py`, either call its functions from the placeholder route, or register its Flask Blueprint and **delete the matching placeholder route** (otherwise two routes share one address).
3. Update that module's entry in `MODULES` in `app.py` (set `"ready": True` and change `"endpoint"` if the Blueprint uses a different one). Also update the matching `url_for(...)` link in `templates/base.html` and `templates/index.html`.

Notes for Member 1's module:
- `member1/assessment.py` is a self-contained Blueprint (`assessment_bp`, address prefix `/assessment`). Keep `assessment.html` and `style.css` in the same folder as `assessment.py`.
- It currently has its **own** tables (`assessments`, `responses`, `skill_results`) and does not write to the shared `skill_assessments` table. The team must decide how to combine them.
- Its `students` table has the same columns as the shared one. To use one database file, set `app.config["ASSESSMENT_DB"] = app.config["DATABASE"]` before registering the Blueprint.
- Its page has its own navigation bar and does not extend `templates/base.html` yet.

## Git and GitHub collaboration workflow

**One-time setup (team leader):** create an empty repository on GitHub, push this project to the `main` branch, and add the other members as collaborators (Settings -> Collaborators).

**Every team member, for every piece of work:**

```bash
# 1. Start from the latest main branch
git checkout main
git pull origin main

# 2. Create your own branch (use a clear name)
git checkout -b feature/assessment-form

# 3. Work, then check what changed
git status

# 4. Save your work in small commits with clear messages
git add .
git commit -m "Add skill rating form"

# 5. Upload your branch to GitHub
git push -u origin feature/assessment-form
```

6. On GitHub, click **Compare & pull request**, describe your change, and ask a teammate to review it.
7. After approval, **merge** the pull request into `main`.
8. Everyone runs `git checkout main` and `git pull origin main` to get the update.

**Team rules**
- Never commit directly to `main`; always use a branch and a pull request.
- Pull the latest `main` before you start new work.
- Do not commit `.venv/`, `*.db` files or `.env` files (`.gitignore` already blocks them).
- Never commit passwords or secret keys.
- If you get a **merge conflict**, open the marked file, keep the correct lines, remove the `<<<<<<<`, `=======` and `>>>>>>>` markers, then `git add` and `git commit`. Ask the team if you are unsure.
- Add any new package to `requirements.txt` and tell the team to run `pip install -r requirements.txt`.

## Configuration (optional)

| Variable | Meaning | Default |
|---|---|---|
| `SECRET_KEY` | Signs sessions and flash messages | `dev-only-change-me` (development only) |
| `DATABASE_PATH` | Location of the SQLite file | `placement.db` next to `app.py` |

## Not done yet

- Student login and registration
- The Planner and Progress features, and all Chart.js charts
- Connecting Member 1's module to this app
- Tests for the foundation
