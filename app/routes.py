from datetime import datetime
from functools import wraps

from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app import app, db
from app.forms import LoginForm, CreateUserForm, CreateSurveyForm
from app.models import User, Survey, Question, Response


def role_required(role="ANY"):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return app.login_manager.unauthorized()
            if (current_user.role != role) and (role != "ANY"):
                return app.login_manager.unauthorized()
            return fn(*args, **kwargs)

        return decorated_view

    return wrapper


@app.route("/")
@app.route("/surveys/")
@login_required
def index():
    user = User.query.filter_by(id=current_user.id).first()
    current_date = datetime.now().date()
    surveys = Survey.query.filter(
        Survey.id.notin_(user.completed_survey_ids()),
        current_date >= Survey.start_date,
        current_date <= Survey.end_date,
    ).all()
    return render_template("index.html", title="Home", surveys=surveys)


@app.route("/login/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("index")
        return redirect(next_page)
    return render_template("login.html", title="Log In", form=form)


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/surveys/<survey_id>/", methods=["GET", "POST"])
@login_required
def survey_response(survey_id):
    survey = Survey.query.filter_by(id=survey_id).first()
    if request.method == "POST":
        for i, question in enumerate(survey.questions):
            value = (
                request.form.get(str(i))
                if request.form.get(str(i)) is not None
                else "None"
            )
            new_response = Response(
                response=value,
                user_id=current_user.id,
                question_id=question.id,
            )
            db.session.add(new_response)
            db.session.commit()
        flash("Survey completed, thank you.")
        return redirect(url_for("index"))
    return render_template("survey_response.html", survey=survey)


@app.route("/admin/surveys/")
@role_required("ADMIN")
def admin_surveys_list():
    surveys = Survey.query.filter_by(user_id=current_user.id).all()
    return render_template("admin/surveys.html", surveys=surveys)


@app.route("/admin/surveys/new/", methods=["GET", "POST"])
@role_required("ADMIN")
def admin_new_survey():
    form = CreateSurveyForm()
    if form.validate_on_submit():
        survey = Survey(
            title=form.title.data,
            description=form.description.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            user_id=current_user.id,
        )
        db.session.add(survey)
        db.session.commit()

        question_script = form.questions.data
        for count, question in enumerate(question_script.splitlines()):
            text, answers = question.split(":", 1)
            new_question = Question(
                text=text, answers=answers, index=count, survey_id=survey.id
            )
            db.session.add(new_question)
            db.session.commit()

        flash("Survey created successfully")
        return redirect(url_for("admin_surveys_list"))
    return render_template("admin/new_survey.html", title="Create Survey", form=form)


@app.route("/admin/surveys/<survey_id>/")
@role_required("ADMIN")
def admin_survey_results(survey_id):
    survey = Survey.query.filter_by(id=survey_id).first()
    return render_template("admin/survey_results.html", survey=survey)


@app.route("/admin/surveys/<survey_id>/<question_id>")
@role_required("ADMIN")
def admin_question_details(survey_id, question_id):
    question = Question.query.filter_by(id=question_id).first()
    responses = Response.query.filter_by(question_id=question_id).all()
    users = {}
    for answer in question.answers_as_list():
        users[answer] = []
    if responses is not None:
        for response in responses:
            users[response.response].append(response.user)
    return render_template(
        "admin/question_details.html", question=question, users=users
    )


@app.route("/admin/users/new/", methods=["GET", "POST"])
def create_new_user():
    form = CreateUserForm()
    if form.validate_on_submit():
        role = "ADMIN" if form.admin.data else "USER"
        user = User(username=form.username.data, email=form.email.data, role=role)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("User created successfully")
        return redirect(url_for("create_new_user"))
    return render_template("register.html", title="Create User", form=form)
