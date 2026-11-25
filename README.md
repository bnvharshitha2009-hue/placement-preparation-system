# Placement Preparation and Skill Gap Analysis System

## About the Project

The **Placement Preparation and Skill Gap Analysis System** is a Python-based web application designed to help students prepare for campus placements. It helps students assess their current skills, identify areas for improvement, plan their preparation, and track their progress.

## Objectives

- Assess students' aptitude, coding, technical knowledge, and communication skills.
- Identify skill gaps and prioritize topics that need improvement.
- Generate structured placement preparation plans.
- Track practice results and preparation progress.
- Provide quizzes and mock interview practice prompts.
- Present progress information to help students prepare effectively for placements.

## Features

### 1. Skill Assessment and Gap Analysis
- Collect student details, including name, email, branch, and year of study.
- Allow students to rate their skills on a scale of 1 to 5.
- Assess four categories: Aptitude, Coding, Technical Knowledge, and HR & Communication.
- Calculate skill gaps and assign priority levels.
- Display assessment results to help students identify weaker areas.

### 2. Placement Preparation Planning
- Help students organize their placement preparation.
- Support planning for aptitude, coding, technical interviews, and HR interviews.

### 3. Practice and Progress Tracking
- Support tracking of preparation activities and practice results.
- Help students monitor improvement over time.

### 4. Quizzes and Mock Interviews
- Provide a foundation for quiz-based practice and mock interview preparation.

*Note: Features should be considered complete only after they have been implemented and tested in the application.*

## Technology Stack

- **Programming Language:** Python
- **Web Framework:** Flask
- **Database:** SQLite
- **Frontend:** HTML, CSS, Bootstrap
- **Templating Engine:** Jinja2
- **Testing:** pytest
- **Version Control:** Git and GitHub

## Project Structure

```text
placement-preparation-system/
├── app.py
├── database.py
├── modules/
│   └── assessment.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── assessment.html
│   ├── planner.html
│   ├── progress.html
│   └── placeholder.html
├── static/
├── tests/
│   └── test_assessment.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation and Setup

### Prerequisites

- Python 3.10 or later
- Git
- A GitHub account

### Step 1: Clone the Repository

```bash
git clone https://github.com/bnvharshitha2009-hue/placement-preparation-system.git
cd placement-preparation-system
```

### Step 2: Create a Virtual Environment

**Windows:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can run the Python executable inside the virtual environment directly instead.

### Step 3: Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
python app.py
```

Open the local URL displayed in the terminal. For Flask applications, this is commonly `http://127.0.0.1:5000/`.

## Running Tests

Run the assessment tests:

```bash
python -m pytest tests/test_assessment.py -v
```

Run the complete test suite:

```bash
python -m pytest -v
```

Review the test output and resolve failures before considering the application ready for submission.

## Team Contributions

The project is developed collaboratively by three team members, with responsibilities divided to ensure balanced contributions.

### Member 1 — Skill Assessment and Skill Gap Analysis
- Develop the student assessment form.
- Implement input validation and skill-gap calculations.
- Integrate assessment data with the SQLite database.
- Display assessment results and priority levels.
- Write and maintain assessment tests.
- Document the assessment module.

### Member 2 — Placement Preparation Planner
- Develop the placement preparation planning module.
- Organize preparation topics and activities.
- Implement planning functionality and related tests.
- Document the planner module.

### Member 3 — Progress Tracking and Reporting
- Develop the progress tracking and reporting module.
- Organize practice results and progress information.
- Implement progress visualizations where appropriate.
- Write related tests and document the module.

All team members contribute to integration, testing, code reviews, documentation, and project improvement.

## Version Control Workflow

The project uses Git and GitHub for collaborative development.

1. Pull the latest changes before starting work.
2. Work on the assigned feature or branch.
3. Test the changes locally.
4. Commit changes with meaningful messages.
5. Push the branch to GitHub.
6. Open a pull request when required by the team's workflow.
7. Review and integrate changes after resolving conflicts and test failures.

Example commands:

```bash
git status
git add <file-name>
git commit -m "Describe your changes"
git push origin HEAD
```

## Future Enhancements

- Personalized study schedules based on skill gaps.
- Topic-wise coding and aptitude quizzes.
- Mock interview question banks.
- Progress charts and performance summaries.
- Recommendations for improving weak skills.
- User authentication and individual student dashboards.

## Conclusion

The Placement Preparation and Skill Gap Analysis System aims to provide students with a structured approach to placement preparation by combining skill assessment, preparation planning, practice, and progress tracking in one application.

## Repository

GitHub: https://github.com/bnvharshitha2009-hue/placement-preparation-system
