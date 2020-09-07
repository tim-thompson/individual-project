from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    hashed_password = db.Column(db.String(128))
    role = db.Column(db.String(80), default="USER")
    properties = db.Column(db.String(500))

    responses = db.relationship("Response", back_populates="user")
    surveys = db.relationship("Survey", back_populates="user")

    def completed_survey_ids(self):
        return set(response.question.survey_id for response in self.responses)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    description = db.Column(db.String(280))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    properties = db.Column(db.String(500))

    questions = db.relationship("Question", back_populates="survey")
    user = db.relationship("User", back_populates="surveys")


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(280))
    answers = db.Column(db.String(144))
    index = db.Column(db.Integer)
    survey_id = db.Column(db.Integer, db.ForeignKey("survey.id"))

    survey = db.RelationshipProperty("Survey", back_populates="questions")
    responses = db.RelationshipProperty("Response", back_populates="question")

    def answers_as_list(self):
        answers = self.answers.split(";")
        answers.append("None")
        return answers

    def chart_data(self):
        output = []
        answers = self.answers.split(";")
        answers.append("None")
        for answer in answers:
            output.append(
                sum(response.response == answer for response in self.responses)
            )
        return output

    def response_results(self):
        output = {}
        answers = self.answers.split(";")
        answers.append("None")
        for answer in answers:
            total = sum(response.response == answer for response in self.responses)
            output[answer] = (
                total,
                total / len(self.responses) * 100 if len(self.responses) != 0 else 0,
            )
        return output


class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    response = db.Column(db.String(144))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"))

    question = db.RelationshipProperty("Question", back_populates="responses")
    user = db.RelationshipProperty("User", back_populates="responses")
