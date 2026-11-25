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
        "ready": False,
    },
    "planner": {
        "title": "Preparation Planner",
        "icon": "🗓️",
        "member": "Member 2",
        "summary": "Turn your skill gaps into a study plan with tasks and deadlines.",
        "endpoint": "planner_page",
        "module_file": "planner.py",
        "ready": False,
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


def create_app(config=None):
    """
    Application factory. Tests can pass their own settings, for example:
        create_app({"TESTING": True, "DATABASE": "test.db"})
    """
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
        # Makes "modules" available in every template (used by the navbar).
        return {"modules": MODULES}

    @app.route("/")
    def index():
        return render_template("index.html")

    # ------------------------------------------------------------------
    # Placeholder routes. Each one only shows a "coming soon" page.
    # When a module is ready, replace the body with a call to that module
    # (or register the module's Blueprint) - see README.md.
    # ------------------------------------------------------------------
    @app.route("/assessment")
    def assessment_page():
        # TODO (Member 1): call the assessment module here.
        return render_template("placeholder.html", module=MODULES["assessment"])

    @app.route("/planner")
    def planner_page():
        # TODO (Member 2): call the planner module here.
        return render_template("placeholder.html", module=MODULES["planner"])

    @app.route("/progress")
    def progress_page():
        # TODO (Member 3): call the progress module here.
        return render_template("placeholder.html", module=MODULES["progress"])


# "python app.py" starts the development server.
if __name__ == "__main__":
    create_app().run(debug=True)