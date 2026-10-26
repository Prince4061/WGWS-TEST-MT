import threading
from datetime import datetime
from flask import (
    Blueprint, render_template, redirect, url_for, request,
    session, jsonify, flash, current_app
)
from app.models import db, Student, Test, Attempt, Question, Answer, Feedback
from app.services.test_engine import (
    get_active_test_for_class, get_remaining_seconds,
    record_answer_progress, log_tab_switch
)
from app.services.scoring import calculate_attempt_score
from app.ai.agent import evaluate_student_attempt
from app.services.pdf_service import generate_pdf_report

student_bp = Blueprint("student", __name__)

def run_background_evaluation(app, attempt_id):
    """Executes Deep Agent evaluation and PDF generation asynchronously"""
    with app.app_context():
        try:
            # 1. Run Deep Agent evaluation (with automatic rule-based fallback)
            evaluate_student_attempt(attempt_id)
            # 2. Compile branded PDF report
            generate_pdf_report(attempt_id, current_app.config["REPORT_FOLDER"])
        except Exception as e:
            current_app.logger.error(f"Background evaluation worker failed: {e}")
            # Ensure attempt doesn't hang in feedback_pending
            att = Attempt.query.get(attempt_id)
            if att:
                att.status = "report_ready"
                db.session.commit()

@student_bp.route("/")
def index():
    return render_template("student/index.html")

@student_bp.route("/start", methods=["POST"])
def start():
    name = request.form.get("name", "").strip()
    class_name = request.form.get("class_name", "").strip()

    if not name or len(name) < 2 or len(name) > 50:
        flash("Please enter a valid student name (2 to 50 characters).", "warning")
        return redirect(url_for("student.index"))

    # Check for active live test for this class
    live_test = get_active_test_for_class(class_name)
    if not live_test:
        flash(f"No test is currently live for Class {class_name}. Please check with your teacher.", "info")
        return redirect(url_for("student.index"))

    # Check existing student
    student = Student.query.filter_by(name=name, class_name=class_name).first()
    if not student:
        student = Student(name=name, class_name=class_name)
        db.session.add(student)
        db.session.commit()

    # Re-attempt guard
    if not live_test.allow_reattempt:
        existing_attempt = Attempt.query.filter(
            Attempt.test_id == live_test.id,
            Attempt.student_id == student.id,
            Attempt.status != "in_progress"
        ).first()
        if existing_attempt:
            flash("You have already submitted this assessment. Re-attempts are not permitted.", "danger")
            return redirect(url_for("student.result", attempt_id=existing_attempt.id))

    # Look for or create in-progress attempt
    attempt = Attempt.query.filter_by(
        test_id=live_test.id,
        student_id=student.id,
        status="in_progress"
    ).first()

    if not attempt:
        attempt = Attempt(
            test_id=live_test.id,
            student_id=student.id,
            status="in_progress"
        )
        db.session.add(attempt)
        db.session.commit()

    session["student_id"] = student.id
    session["attempt_id"] = attempt.id
    session["test_id"] = live_test.id

    return redirect(url_for("student.instructions"))

@student_bp.route("/test/instructions")
def instructions():
    attempt_id = session.get("attempt_id")
    if not attempt_id:
        return redirect(url_for("student.index"))

    attempt = Attempt.query.get(attempt_id)
    if not attempt or attempt.status != "in_progress":
        return redirect(url_for("student.index"))

    test = Test.query.get(attempt.test_id)
    student = Student.query.get(attempt.student_id)
    return render_template("student/instructions.html", test=test, student=student, attempt=attempt)

@student_bp.route("/test/begin", methods=["POST"])
def begin():
    attempt_id = session.get("attempt_id")
    if not attempt_id:
        return redirect(url_for("student.index"))

    attempt = Attempt.query.get(attempt_id)
    if not attempt:
        return redirect(url_for("student.index"))

    if not attempt.started_at:
        attempt.started_at = datetime.utcnow()
        db.session.commit()

    return redirect(url_for("student.take_test"))

@student_bp.route("/test")
def take_test():
    attempt_id = session.get("attempt_id")
    if not attempt_id:
        flash("Session expired. Please re-enter your details.", "warning")
        return redirect(url_for("student.index"))

    attempt = Attempt.query.get(attempt_id)
    if not attempt or attempt.status != "in_progress":
        if attempt and attempt.status != "in_progress":
            return redirect(url_for("student.result", attempt_id=attempt.id))
        return redirect(url_for("student.index"))

    test = Test.query.get(attempt.test_id)
    remaining_sec = get_remaining_seconds(attempt, test)

    # Server timer check
    if remaining_sec <= 0:
        calculate_attempt_score(attempt.id)
        flash("Your test time expired and answers have been submitted automatically.", "info")
        return redirect(url_for("student.result", attempt_id=attempt.id))

    student = Student.query.get(attempt.student_id)
    questions = Question.query.filter_by(test_id=test.id).order_by(Question.q_no).all()
    safe_questions = [q.to_client_dict() for q in questions]

    # Pre-load existing answers
    answers = Answer.query.filter_by(attempt_id=attempt.id).all()
    user_answers = {a.question_id: a.selected_option for a in answers}

    return render_template(
        "student/test.html",
        test=test,
        student=student,
        attempt=attempt,
        questions=safe_questions,
        user_answers=user_answers,
        remaining_sec=remaining_sec
    )

@student_bp.route("/test/answer", methods=["POST"])
def auto_save_answer():
    attempt_id = session.get("attempt_id")
    if not attempt_id:
        return jsonify({"success": False, "error": "No active test session."}), 401

    data = request.get_json() or {}
    q_id = data.get("question_id")
    selected_opt = data.get("selected_option")
    dwell = data.get("dwell_sec", 0)
    is_change = data.get("is_change", False)

    ans, err = record_answer_progress(
        attempt_id=attempt_id,
        question_id=q_id,
        selected_option=selected_opt,
        dwell_increment=dwell,
        is_change=is_change
    )
    if err:
        return jsonify({"success": False, "error": err}), 400

    return jsonify({"success": True, "saved_option": selected_opt})

@student_bp.route("/test/tab-switch", methods=["POST"])
def report_tab_switch():
    attempt_id = session.get("attempt_id")
    if attempt_id:
        count = log_tab_switch(attempt_id)
        return jsonify({"success": True, "tab_switches": count})
    return jsonify({"success": False}), 401

@student_bp.route("/test/submit", methods=["POST"])
def submit_test():
    attempt_id = session.get("attempt_id")
    if not attempt_id:
        flash("No active test attempt found.", "danger")
        return redirect(url_for("student.index"))

    attempt = Attempt.query.get(attempt_id)
    if not attempt:
        return redirect(url_for("student.index"))

    # Deterministic Instant Scoring
    calculate_attempt_score(attempt.id)
    attempt.status = "feedback_pending"
    db.session.commit()

    # Launch Deep Agent evaluation in background thread
    app_obj = current_app._get_current_object()
    worker_thread = threading.Thread(
        target=run_background_evaluation,
        args=(app_obj, attempt.id),
        daemon=True
    )
    worker_thread.start()

    return redirect(url_for("student.result", attempt_id=attempt.id))

@student_bp.route("/result/<int:attempt_id>")
def result(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    test = Test.query.get(attempt.test_id)
    student = Student.query.get(attempt.student_id)
    feedback = Feedback.query.filter_by(attempt_id=attempt.id).first()

    pct = round((attempt.score / attempt.max_score * 100), 1) if attempt.max_score > 0 else 0
    time_min = attempt.total_time_sec // 60
    time_sec = attempt.total_time_sec % 60

    return render_template(
        "student/result.html",
        attempt=attempt,
        test=test,
        student=student,
        feedback=feedback,
        percentage=pct,
        time_display=f"{time_min}m {time_sec}s"
    )

@student_bp.route("/result/<int:attempt_id>/status")
def result_status(attempt_id):
    """JSON status polling for the result page to activate the download button"""
    attempt = Attempt.query.get_or_404(attempt_id)
    feedback = Feedback.query.filter_by(attempt_id=attempt.id).first()
    
    is_ready = attempt.status == "report_ready" or feedback is not None
    return jsonify({
        "status": attempt.status,
        "is_ready": is_ready,
        "has_feedback": feedback is not None,
        "feedback_preview": feedback.json_payload.get("summary") if (feedback and feedback.json_payload) else ""
    })
