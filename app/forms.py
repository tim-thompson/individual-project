import re

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    TextAreaField,
)
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, ValidationError, Email

from app.models import User


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Log In")


class CreateUserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    admin = BooleanField("Admin")
    properties = StringField(
        "Properties",
        description="Provide a comma separated list of user properties. For example London,Manager",
    )
    submit = SubmitField("Create")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Please use a different username.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("Please use a different email address.")


class EditUserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password", description="Password will remain the same if this field is empty"
    )
    admin = BooleanField("Admin")
    properties = StringField(
        "Properties",
        description="Provide a comma separated list of user properties. For example London,Manager",
    )
    submit = SubmitField("Save Edit")


class CreateSurveyForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    description = TextAreaField("Description")
    start_date = DateField("Start Date", validators=[DataRequired()])
    end_date = DateField("End Date", validators=[DataRequired()])
    questions = TextAreaField(
        "Questions Script",
        description="Format as follows: QUESTION:ANSWER_1;ANSWER_2;ANSWER_3<br>Example:<br>Can you work from "
        "home?:Yes;No",
        validators=[DataRequired()],
    )
    properties = StringField(
        "User Properties",
        description="Provide a comma separated list of properties. "
        "Surveys will only be sent to users with those properties. Leaving this box blank will "
        "send a survey to all users.",
    )
    submit = SubmitField("Create")

    def validate_questions(self, questions):
        for question in questions.data.split("\n"):
            match = re.match(".+:(.+;)+.+", question)
            if match is None:
                raise ValidationError(
                    "There is a problem with your question script format."
                )
        print("passed validation")
