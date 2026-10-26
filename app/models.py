from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class SchoolSettings(db.Model):
    __tablename__ = "school_settings"
    id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(150), default="Delhi Public Model School")
    logo_path = db.Column(db.String(300), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Admin(UserMixin, db.Model):
    __tablename__ = "admins"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Test(db.Model):
    __tablename__ = "tests"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    total_questions = db.Column(db.Integer, default=20)
    duration_min = db.Column(db.Integer, default=30)
    marks_per_q = db.Column(db.Float, default=1.0)
    negative_marking = db.Column(db.Float, default=0.0)
    shuffle = db.Column(db.Boolean, default=True)
    allow_reattempt = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default="draft")  # draft | live | closed
    created_by = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    live_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)

    questions = db.relationship("Question", backref="test", cascade="all, delete-orphan", lazy="dynamic")
    attempts = db.relationship("Attempt", backref="test", cascade="all, delete-orphan", lazy="dynamic")

class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("tests.id"), nullable=False)
    q_no = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    opt_a = db.Column(db.Text, nullable=False)
    opt_b = db.Column(db.Text, nullable=False)
    opt_c = db.Column(db.Text, nullable=False)
    opt_d = db.Column(db.Text, nullable=False)
    correct_option = db.Column(db.String(5), nullable=False)  # A, B, C, D
    topic = db.Column(db.String(100), nullable=False)
    question_type = db.Column(db.String(50), default="conceptual")  # conceptual, numerical, application, recall
    difficulty = db.Column(db.String(20), default="medium")  # easy, medium, hard
    explanation = db.Column(db.Text, nullable=True)

    def to_client_dict(self):
        """Safe dictionary for student client - NEVER includes correct_option or explanation"""
        return {
            "id": self.id,
            "q_no": self.q_no,
            "text": self.text,
            "opt_a": self.opt_a,
            "opt_b": self.opt_b,
            "opt_c": self.opt_c,
            "opt_d": self.opt_d,
            "topic": self.topic,
            "question_type": self.question_type,
            "difficulty": self.difficulty
        }

class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attempts = db.relationship("Attempt", backref="student", cascade="all, delete-orphan", lazy="dynamic")

class Attempt(db.Model):
    __tablename__ = "attempts"
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("tests.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime, nullable=True)
    score = db.Column(db.Float, default=0.0)
    max_score = db.Column(db.Float, default=0.0)
    correct = db.Column(db.Integer, default=0)
    wrong = db.Column(db.Integer, default=0)
    skipped = db.Column(db.Integer, default=0)
    total_time_sec = db.Column(db.Integer, default=0)
    tab_switches = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), default="in_progress")  # in_progress | scored | feedback_pending | report_ready | failed

    answers = db.relationship("Answer", backref="attempt", cascade="all, delete-orphan", lazy="dynamic")
    feedback = db.relationship("Feedback", backref="attempt", uselist=False, cascade="all, delete-orphan")
    report = db.relationship("Report", backref="attempt", uselist=False, cascade="all, delete-orphan")

class Answer(db.Model):
    __tablename__ = "answers"
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("attempts.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    selected_option = db.Column(db.String(5), nullable=True)  # A, B, C, D or None
    is_correct = db.Column(db.Boolean, default=False)
    time_spent_sec = db.Column(db.Integer, default=0)
    change_count = db.Column(db.Integer, default=0)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)

    question = db.relationship("Question")

class Feedback(db.Model):
    __tablename__ = "feedback"
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("attempts.id"), unique=True, nullable=False)
    json_payload = db.Column(db.JSON, nullable=False)
    language = db.Column(db.String(30), default="English")
    model_used = db.Column(db.String(100), default="deep-agents")
    source = db.Column(db.String(20), default="ai")  # ai | fallback
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Report(db.Model):
    __tablename__ = "reports"
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("attempts.id"), unique=True, nullable=False)
    pdf_path = db.Column(db.String(350), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
