import os
from flask import Blueprint, send_file, render_template, abort, current_app
from app.models import Attempt, Test, Student, Question, Answer, Feedback, Report
from app.services.pdf_service import generate_pdf_report

report_bp = Blueprint("report", __name__)

@report_bp.route("/report/<int:attempt_id>/download")
def download_pdf(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    report = Report.query.filter_by(attempt_id=attempt.id).first()

    # If PDF has not been generated or file was deleted, compile it on-demand
    if not report or not report.pdf_path or not os.path.exists(report.pdf_path):
        pdf_path = generate_pdf_report(attempt.id, current_app.config["REPORT_FOLDER"])
    else:
        pdf_path = report.pdf_path

    student = Student.query.get(attempt.student_id)
    safe_name = (student.name if student else "Student").replace(" ", "_")
    download_filename = f"Assessment_Report_{safe_name}_Attempt_{attempt.id}.pdf"

    return send_file(
        pdf_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=download_filename
    )

@report_bp.route("/report/<int:attempt_id>/view")
def view_web_report(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    test = Test.query.get(attempt.test_id)
    student = Student.query.get(attempt.student_id)
    feedback = Feedback.query.filter_by(attempt_id=attempt.id).first()

    questions = Question.query.filter_by(test_id=test.id).order_by(Question.q_no).all()
    answers = Answer.query.filter_by(attempt_id=attempt.id).all()
    ans_map = {a.question_id: a for a in answers}

    # Build question itemization
    items = []
    for q in questions:
        ans = ans_map.get(q.id)
        items.append({
            "question": q,
            "answer": ans,
            "is_correct": ans.is_correct if ans else False,
            "selected_option": ans.selected_option if ans else None,
            "time_spent": ans.time_spent_sec if ans else 0
        })

    pct = round((attempt.score / attempt.max_score * 100), 1) if attempt.max_score > 0 else 0

    return render_template(
        "report/web_report.html",
        attempt=attempt,
        test=test,
        student=student,
        feedback=feedback,
        items=items,
        percentage=pct
    )
