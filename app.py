
"""
app.py
======
Main Flask application for the Placement Preparation
and Skill Gap Analysis System.

Responsibilities:
- Create and configure the Flask application.
- Initialize the shared SQLite database.
- Serve the home page.
- Serve the assessment, planner, and progress pages.

Team modules:
    Member 1 -> Skill Assessment and Skill Gap Analysis
    Member 2 -> Preparation Planner
    Member 3 -> Progress Tracking and Charts

Run:
    python app.py
"""

import os

from flask import Flask, render_template

from database import DEFAULT_DB_PATH, init_db


# Information displayed on the home page and module pages.
MODULES = {
    "assessment": {
        "title": "Skill Assessment",
        "icon": "🧠",
        "member": "Member 1",
        "summary": (
            "Assess your aptitude, coding, technical and HR skills "
            "and identify your skill gaps."
        ),
        "endpoint": "assessment_page",
        "module_file": "assessment.py",
        "ready": False,
    },
    "planner": {
        "title": "Preparation Planner",
        "icon": "🗓️",
        "member": "Member 2",
        "summary": (
            "Turn your skill gaps into a preparation plan "
            "with tasks and deadlines."
        ),
        "endpoint": "planner_page",
        "module_file": "planner.py",
        "ready": False,
    },
    "progress": {
        "title": "Progress Tracking",
        "icon": "📈",
        "member": "Member 3",
        "summary": (
            "Track practice results and task completion "
            "with progress charts."
        ),
        "endpoint": "progress_page",
        "module_file": "progress.py",
        "ready": False,
    },
}


def create_app(config=None):
    """
    Create and configure the Flask application.

    An optional dictionary allows custom settings for tests.

    Example:
        app = create_app({
            "TESTING": True,
            "DATABASE": "test.db",
        })
    """
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY",
        "dev-only-change-me",
    )

    app.config["DATABASE"] = DEFAULT_DB_PATH

    if config:
        app.config.update(config)

    # Initialize the database tables.
    init_db(app.config["DATABASE"])

    # Register all application routes.
    register_routes(app)

    return app


def register_routes(app):
    """Register the routes used by the application."""

    @app.context_processor
    def inject_modules():
        """Make module information available to every template."""
        return {"modules": MODULES}

    @app.route("/")
    def index():
        """Display the home page."""
        return render_template("index.html")

    @app.route("/assessment")
    def assessment_page():
        """Display the skill assessment page."""
        return render_template(
            "assessment.html",
            module=MODULES["assessment"],
        )

    @app.route("/planner")
    def planner_page():
        """Display the preparation planner page."""
        return render_template(
            "planner.html",
            module=MODULES["planner"],
        )

    @app.route("/progress")
    def progress_page():
        """Display the progress tracking page."""
        return render_template(
            "progress.html",
            module=MODULES["progress"],
        )


if __name__ == "__main__":
    app = create_app()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
    )
