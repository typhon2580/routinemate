from datetime import date, datetime

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.config["SECRET_KEY"] = "routinemate-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///routinemate.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"


CATEGORIES = [
    "Health",
    "Study",
    "Work",
    "Fitness",
    "Personal",
    "Coding",
    "Relaxation",
    "Other",
]

PRIORITIES = ["Low", "Medium", "High"]
STATUSES = ["Pending", "Completed"]


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    tasks = db.relationship(
        "RoutineTask",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class RoutineTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    task_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    category = db.Column(db.String(50), nullable=False, default="Other")
    priority = db.Column(db.String(20), nullable=False, default="Medium")
    status = db.Column(db.String(20), nullable=False, default="Pending")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    @property
    def is_completed(self):
        return self.status == "Completed"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_global_data():
    return {
        "categories": CATEGORIES,
        "priorities": PRIORITIES,
        "statuses": STATUSES,
        "today": date.today(),
    }


@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("An account with this email already exists.", "danger")
            return redirect(url_for("register"))

        new_user = User(username=username, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))

        login_user(user)
        flash("Login successful.", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    selected_status = request.args.get("status", "All")
    selected_priority = request.args.get("priority", "All")
    selected_category = request.args.get("category", "All")
    selected_date = request.args.get("date", "today")

    query = RoutineTask.query.filter_by(user_id=current_user.id)

    if selected_date == "today":
        query = query.filter_by(task_date=date.today())

    if selected_status != "All":
        query = query.filter_by(status=selected_status)

    if selected_priority != "All":
        query = query.filter_by(priority=selected_priority)

    if selected_category != "All":
        query = query.filter_by(category=selected_category)

    tasks = query.order_by(
        RoutineTask.task_date.asc(),
        RoutineTask.start_time.asc()
    ).all()

    today_tasks = RoutineTask.query.filter_by(
        user_id=current_user.id,
        task_date=date.today()
    ).all()

    total_tasks = len(today_tasks)
    completed_tasks = len([task for task in today_tasks if task.status == "Completed"])
    pending_tasks = total_tasks - completed_tasks

    progress_percentage = 0

    if total_tasks > 0:
        progress_percentage = round((completed_tasks / total_tasks) * 100)

    return render_template(
        "dashboard.html",
        tasks=tasks,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        progress_percentage=progress_percentage,
        selected_status=selected_status,
        selected_priority=selected_priority,
        selected_category=selected_category,
        selected_date=selected_date,
    )


@app.route("/add-task", methods=["GET", "POST"])
@login_required
def add_task():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        task_date = request.form.get("task_date", "")
        start_time = request.form.get("start_time", "")
        end_time = request.form.get("end_time", "")
        category = request.form.get("category", "Other")
        priority = request.form.get("priority", "Medium")
        status = request.form.get("status", "Pending")

        if not title or not task_date:
            flash("Title and date are required.", "danger")
            return redirect(url_for("add_task"))

        new_task = RoutineTask(
            title=title,
            description=description,
            task_date=datetime.strptime(task_date, "%Y-%m-%d").date(),
            start_time=datetime.strptime(start_time, "%H:%M").time() if start_time else None,
            end_time=datetime.strptime(end_time, "%H:%M").time() if end_time else None,
            category=category,
            priority=priority,
            status=status,
            user_id=current_user.id,
        )

        db.session.add(new_task)
        db.session.commit()

        flash("Task added successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_task.html")


@app.route("/edit-task/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    task = RoutineTask.query.filter_by(
        id=task_id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        task_date = request.form.get("task_date", "")
        start_time = request.form.get("start_time", "")
        end_time = request.form.get("end_time", "")
        category = request.form.get("category", "Other")
        priority = request.form.get("priority", "Medium")
        status = request.form.get("status", "Pending")

        if not title or not task_date:
            flash("Title and date are required.", "danger")
            return redirect(url_for("edit_task", task_id=task.id))

        task.title = title
        task.description = description
        task.task_date = datetime.strptime(task_date, "%Y-%m-%d").date()
        task.start_time = datetime.strptime(start_time, "%H:%M").time() if start_time else None
        task.end_time = datetime.strptime(end_time, "%H:%M").time() if end_time else None
        task.category = category
        task.priority = priority
        task.status = status

        db.session.commit()

        flash("Task updated successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("edit_task.html", task=task)


@app.route("/delete-task/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):
    task = RoutineTask.query.filter_by(
        id=task_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(task)
    db.session.commit()

    flash("Task deleted successfully.", "info")
    return redirect(url_for("dashboard"))


@app.route("/toggle-task/<int:task_id>", methods=["POST"])
@login_required
def toggle_task(task_id):
    task = RoutineTask.query.filter_by(
        id=task_id,
        user_id=current_user.id
    ).first_or_404()

    if task.status == "Completed":
        task.status = "Pending"
    else:
        task.status = "Completed"

    db.session.commit()

    flash("Task status updated.", "success")
    return redirect(url_for("dashboard"))


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)