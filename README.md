# RoutineMate

RoutineMate is a daily routine planner web application built with Python Flask. It helps users create, manage, update, delete, and track everyday routine tasks.

## Features

- User registration and login
- Secure password hashing using Werkzeug
- User-specific routine tasks
- Add new routine tasks
- Edit existing tasks
- Delete tasks
- Mark tasks as completed or pending
- Dashboard with daily statistics
- Daily progress percentage
- Bootstrap progress bar
- Filter tasks by:
  - Date view
  - Status
  - Priority
  - Category
- Category badges
- Priority badges
- Responsive Bootstrap layout

## Tech Stack

- Python
- Flask
- SQLite
- Flask-SQLAlchemy
- Flask-Login
- Werkzeug password hashing
- HTML
- CSS
- Bootstrap
- JavaScript

## Project Structure

```txt
routinemate/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── instance/
│   └── routinemate.db
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── register.html
│   ├── login.html
│   ├── dashboard.html
│   ├── add_task.html
│   └── edit_task.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── script.js