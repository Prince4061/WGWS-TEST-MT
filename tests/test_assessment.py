import os
import io
import unittest
from datetime import datetime
from app import create_app
from app.models import db, Admin, Test, Question, Student, Attempt, Answer, Feedback, Report, SchoolSettings
from app.services.csv_service import generate_csv_template, validate_and_parse_csv
from app.services.scoring import calculate_attempt_score
from app.services.test_engine import get_remaining_seconds
from app.ai.fallback import generate_rule_based_feedback
from app.ai.schemas import StudentFeedbackSchema
from app.services.pdf_service import generate_pdf_report

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test-secret"
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "test_uploads")
    REPORT_FOLDER = os.path.join(os.path.dirname(__file__), "test_reports")
    DEFAULT_SCHOOL_NAME = "Test High School"

class AssessmentTrackerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_01_admin_and_school_seeded(self):
        """Verify default admin and school settings are initialized"""
        admin = Admin.query.filter_by(username="prince").first()
        self.assertIsNotNone(admin)
        self.assertTrue(admin.check_password("tarunsirkijai"))

        school = SchoolSettings.query.first()
        self.assertIsNotNone(school)
        self.assertEqual(school.school_name, "Test High School")

    def test_02_csv_template_generation(self):
        """Verify CSV template generates valid headers and rows"""
        csv_text = generate_csv_template()
        self.assertIn("question_no,question,option_a,option_b,option_c,option_d", csv_text)
        self.assertIn("correct_option,topic,question_type,difficulty,explanation", csv_text)
        self.assertIn("Fractions", csv_text)

    def test_03_csv_validation_failure(self):
        """Verify CSV validator catches invalid headers or options"""
        test = Test(name="Unit Test", subject="Math", class_name="10", created_by=1)
        db.session.add(test)
        db.session.commit()

        bad_csv = io.BytesIO(b"question,option_a,option_b\nWhat is 1+1?,1,2\n")
        success, errors, count = validate_and_parse_csv(bad_csv, test)
        self.assertFalse(success)
        self.assertTrue(any("Missing required columns" in e for e in errors))

    def test_04_csv_validation_success_and_import(self):
        """Verify valid CSV imports cleanly into Question models"""
        test = Test(name="Unit Test", subject="Math", class_name="10", total_questions=2, created_by=1)
        db.session.add(test)
        db.session.commit()

        valid_csv = (
            "question_no,question,option_a,option_b,option_c,option_d,correct_option,topic,question_type,difficulty,explanation\n"
            "1,What is 2+2?,2,3,4,5,C,Addition,numerical,easy,2+2=4\n"
            "2,What is 5*5?,10,20,25,30,C,Multiplication,numerical,easy,5*5=25\n"
        )
        success, errors, count = validate_and_parse_csv(io.StringIO(valid_csv), test)
        self.assertTrue(success)
        self.assertEqual(count, 2)
        self.assertEqual(Question.query.filter_by(test_id=test.id).count(), 2)

    def test_05_deterministic_scoring(self):
        """Verify deterministic scoring calculations and negative marking"""
        test = Test(
            name="Scoring Test", subject="Science", class_name="9",
            total_questions=2, marks_per_q=2.0, negative_marking=0.5,
            duration_min=15, created_by=1
        )
        db.session.add(test)
        db.session.commit()

        q1 = Question(test_id=test.id, q_no=1, text="Q1", opt_a="A", opt_b="B", opt_c="C", opt_d="D",
                      correct_option="A", topic="Physics", question_type="conceptual", difficulty="easy")
        q2 = Question(test_id=test.id, q_no=2, text="Q2", opt_a="A", opt_b="B", opt_c="C", opt_d="D",
                      correct_option="B", topic="Chemistry", question_type="recall", difficulty="easy")
        db.session.add_all([q1, q2])
        db.session.commit()

        student = Student(name="Priya Patel", class_name="9")
        db.session.add(student)
        db.session.commit()

        attempt = Attempt(test_id=test.id, student_id=student.id, started_at=datetime.utcnow(), status="in_progress")
        db.session.add(attempt)
        db.session.commit()

        # Student answered Q1 correctly ('A') and Q2 incorrectly ('C')
        ans1 = Answer(attempt_id=attempt.id, question_id=q1.id, selected_option="A", time_spent_sec=15)
        ans2 = Answer(attempt_id=attempt.id, question_id=q2.id, selected_option="C", time_spent_sec=20)
        db.session.add_all([ans1, ans2])
        db.session.commit()

        result = calculate_attempt_score(attempt.id)

        # Expected score: 2.0 (correct) - 0.5 (negative) = 1.5
        self.assertEqual(result["correct"], 1)
        self.assertEqual(result["wrong"], 1)
        self.assertEqual(result["score"], 1.5)
        self.assertEqual(result["max_score"], 4.0)
        self.assertEqual(result["percentage"], 37.5)

    def test_06_server_timer_calculation(self):
        """Verify server authoritative remaining time calculation"""
        test = Test(name="Timer Test", subject="Math", class_name="8", duration_min=10)
        db.session.add(test)
        db.session.commit()

        attempt = Attempt(test_id=test.id, student_id=1, started_at=datetime.utcnow())
        rem = get_remaining_seconds(attempt, test)
        # Remaining should be approximately 600 seconds (within 5s tolerance)
        self.assertTrue(595 <= rem <= 600)

    def test_07_rule_based_fallback_validates_pydantic_schema(self):
        """Verify rule-based evaluation strictly adheres to Pydantic StudentFeedbackSchema"""
        test = Test(name="Fallback Test", subject="Math", class_name="10", total_questions=1)
        db.session.add(test)
        db.session.commit()

        q = Question(test_id=test.id, q_no=1, text="Test Q", opt_a="A", opt_b="B", opt_c="C", opt_d="D",
                     correct_option="A", topic="Algebra")
        student = Student(name="Rahul Verma", class_name="10")
        db.session.add_all([q, student])
        db.session.commit()

        attempt = Attempt(test_id=test.id, student_id=student.id, score=1.0, max_score=1.0, correct=1, wrong=0)
        db.session.add(attempt)
        db.session.commit()

        fb = generate_rule_based_feedback(attempt.id)
        # Validate against schema
        validated = StudentFeedbackSchema.model_validate(fb)
        self.assertIsNotNone(validated.summary)
        self.assertTrue(len(validated.strengths) >= 1)
        self.assertTrue(len(validated.action_plan) >= 1)

    def test_08_pdf_report_compilation(self):
        """Verify PDF report generates without errors and creates valid PDF file"""
        test = Test(name="PDF Test", subject="Science", class_name="7", total_questions=1)
        student = Student(name="Simran Kaur", class_name="7")
        db.session.add_all([test, student])
        db.session.commit()

        q = Question(test_id=test.id, q_no=1, text="Is water H2O?", opt_a="Yes", opt_b="No", opt_c="Maybe", opt_d="None",
                     correct_option="A", topic="Chemistry", explanation="Water is H2O.")
        db.session.add(q)
        db.session.commit()

        attempt = Attempt(
            test_id=test.id, student_id=student.id, started_at=datetime.utcnow(),
            submitted_at=datetime.utcnow(), score=1.0, max_score=1.0,
            correct=1, wrong=0, skipped=0, total_time_sec=45, status="scored"
        )
        db.session.add(attempt)
        db.session.commit()

        # Seed feedback
        fb = generate_rule_based_feedback(attempt.id)
        feedback_rec = Feedback(attempt_id=attempt.id, json_payload=fb, source="fallback")
        db.session.add(feedback_rec)
        db.session.commit()

        pdf_path = generate_pdf_report(attempt.id, reports_dir=TestConfig.REPORT_FOLDER)
        self.assertTrue(os.path.exists(pdf_path))
        self.assertTrue(os.path.getsize(pdf_path) > 1000)

if __name__ == "__main__":
    unittest.main()
