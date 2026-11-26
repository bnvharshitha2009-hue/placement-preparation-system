"""
app.py
======
Main Flask application for the Placement Preparation and Skill Gap Analysis System.

This file is the shared foundation. It only:
  * creates the Flask app and the database tables,
  * serves the Home page,
  * serves PLACEHOLDER pages for the three modules.

The real features are NOT implemented here. Each team member builds one module:

    Member 1 -> Skill Assessment and Skill Gap Analysis   (assessment.py)
    Member 2 -> Preparation Planner                       (planner.py)
    Member 3 -> Progress Tracking and Charts              (progress.py)

Run the app:
    python app.py
"""

import os

from flask import Flask, render_template

from database import DEFAULT_DB_PATH, init_db
from modules import assessment as assessment_module  # Member 1's feature
from modules import auth as auth_module              # User Gmail + University verification
from modules import planner as planner_module        # Member 2's feature
from modules import practice as practice_module      # Practice & Test Schedule tab

# Information shown on the home page and on the placeholder pages.
# When a module is finished, set "ready" to True (see the README for the steps).
MODULES = {
    "assessment": {
        "title": "Skill Assessment",
        "icon": "🧠",
        "member": "Member 1",
        "summary": "Assess your aptitude, coding, technical and HR skills and see your skill gaps.",
        "endpoint": "assessment_page",
        "module_file": "assessment.py",
        "ready": True,
    },
    "planner": {
        "title": "Preparation Planner",
        "icon": "🗓️",
        "member": "Member 2",
        "summary": "Turn your skill gaps into a study plan with tasks and deadlines.",
        "endpoint": "planner_page",
        "module_file": "planner.py",
        "ready": True,
    },
    "practice": {
        "title": "Practice & Test Schedule",
        "icon": "📝",
        "member": "Member 2",
        "summary": "Practise scheduled topic drills and timed mock tests synced with your planner.",
        "endpoint": "practice_page",
        "module_file": "practice.py",
        "ready": True,
    },
    "progress": {
        "title": "Progress Tracking",
        "icon": "📈",
        "member": "Member 3",
        "summary": "Track practice results and task completion with charts.",
        "endpoint": "progress_page",
        "module_file": "progress.py",
        "ready": False,
    },
}


def load_env_file(env_path=None):
    """
    Load KEY=VALUE pairs from a local .env file into os.environ without
    overwriting variables already set in the terminal.
    """
    path = env_path or os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.isfile(path):
        return {}

    loaded = {}
    with open(path, encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):].strip()
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            if key:
                os.environ.setdefault(key, value)
                loaded[key] = value
    return loaded


def create_app(config=None):
    """
    Application factory. Tests can pass their own settings, for example:
        create_app({"TESTING": True, "DATABASE": "test.db"})
    """
    if not (config and config.get("TESTING")):
        load_env_file()

    app = Flask(__name__)

    # SECRET_KEY signs sessions and flash messages. For real use, set the
    # SECRET_KEY environment variable. Never commit real secrets to Git.
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
    app.config["DATABASE"] = DEFAULT_DB_PATH
    if config:
        app.config.update(config)

    # Create the shared tables when the app starts (does nothing if they exist).
    init_db(app.config["DATABASE"])

    register_routes(app)
    return app


def register_routes(app):
    """All page routes live here to keep create_app() short and readable."""

    @app.context_processor
    def inject_modules():
        # Makes "modules", logged-in user, and one-time login streak popup available in templates.
        return {
            "modules": MODULES,
            "current_user": auth_module.get_logged_in_user(app.config["DATABASE"]),
            "streak_effect": auth_module.consume_streak_effect(),
        }

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login", methods=["GET", "POST"])
    def login_page():
        return auth_module.handle_login_request(app.config["DATABASE"])

    @app.route("/profile")
    def profile_page():
        return auth_module.handle_profile_request(app.config["DATABASE"])

    @app.route("/verify", methods=["GET", "POST"])
    def verify_page():
        return auth_module.handle_verify_request(app.config["DATABASE"])

    @app.route("/login/resend", methods=["POST"])
    def resend_verification():
        return auth_module.handle_resend_request(app.config["DATABASE"])

    @app.route("/logout", methods=["POST"])
    def logout_page():
        return auth_module.handle_logout_request()

    # ------------------------------------------------------------------
    # Placeholder routes. Each one only shows a "coming soon" page.
    # When a module is ready, replace the body with a call to that module
    # (or register the module's Blueprint) - see README.md.
    # ------------------------------------------------------------------
    @app.route("/assessment", methods=["GET", "POST"])
    def assessment_page():
        # Member 1: all the work is done in modules/assessment.py.
        # GET shows the form or a result, POST validates and saves the form.
        return assessment_module.handle_assessment_request(app.config["DATABASE"])

    @app.route("/planner", methods=["GET", "POST"])
    def planner_page():
        # Member 2: all the work is done in modules/planner.py.
        return planner_module.handle_planner_request(app.config["DATABASE"])

    @app.route("/practice", methods=["GET", "POST"])
    def practice_page():
        return practice_module.handle_practice_request(app.config["DATABASE"])

    @app.route("/progress")
    def progress_page():
        # TODO (Member 3): call the progress module here.
        return render_template("placeholder.html", module=MODULES["progress"])


# "python app.py" starts the development server.
if __name__ == "__main__":
    create_app().run(debug=True)