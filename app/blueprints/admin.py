import os
import csv
import io
from datetime import datetime
from flask import (
    Blueprint, render_template, redirect, url_for, request, flash,
    send_file, Response, current_app, jsonify
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import db, Test, Question, Attempt, Student, SchoolSettings
from app.services.csv_service import generate_csv_template, validate_and_parse_csv

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/dashboard")
@login_required
def dashboard():
    tests = Test.query.order_by(Test.created_at.desc()).all()
    total_tests = len(tests)
    live_tests = sum(1 for t in tests if t.status == "live")
    total_attempts = Attempt.query.count()
    school_settings = SchoolSettings.query.first()

    return render_template(
        "admin/dashboard.html",
        tests=tests,
        total_tests=total_tests,
        live_tests=live_tests,
        total_attempts=total_attempts,
        school_settings=school_settings
    )

@admin_bp.route("/tests/new", methods=["GET", "POST"])
@login_required
def new_test():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        subject = request.form.get("subject", "").strip()
        class_name = request.form.get("class_name", "").strip()
        total_q = int(request.form.get("total_questions", 20))
        duration_min = int(request.form.get("duration_min", 30))
        marks_per_q = float(request.form.get("marks_per_q", 1.0))
        negative_marking = float(request.form.get("negative_marking", 0.0))
        shuffle = bool(request.form.get("shuffle"))
        allow_reattempt = bool(request.form.get("allow_reattempt"))

        if not name or not subject or not class_name:
            flash("Test Name, Subject, and Class are required.", "danger")
            return redirect(url_for("admin.new_test"))

        test = Test(
            name=name,
            subject=subject,
            class_name=class_name,
            total_questions=total_q,
            duration_min=duration_min,
            marks_per_q=marks_per_q,
            negative_marking=negative_marking,
            shuffle=shuffle,
            allow_reattempt=allow_reattempt,
            status="draft",
            created_by=current_user.id
        )
        db.session.add(test)
        db.session.commit()

        flash(f"Assessment '{name}' created. Please upload questions CSV now.", "success")
        return redirect(url_for("admin.upload_questions", test_id=test.id))

    return render_template("admin/create_test.html")

@admin_bp.route("/template.csv")
def download_template():
    """Generates and serves the CSV template defined in PRD Section 4.3"""
    csv_data = generate_csv_template()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=assessment_questions_template.csv"}
    )

@admin_bp.route("/tests/<int:test_id>/upload", methods=["GET", "POST"])
@login_required
def upload_questions(test_id):
    test = Test.query.get_or_404(test_id)
    errors = []

    if request.method == "POST":
        file = request.files.get("csv_file")
        if not file or file.filename == "":
            flash("Please choose a CSV file to upload.", "danger")
            return redirect(request.url)

        if not file.filename.lower().endswith(".csv"):
            flash("Only .csv files are supported.", "danger")
            return redirect(request.url)

        custom_count = request.form.get("selected_count")
        selected_count = int(custom_count) if custom_count and custom_count.isdigit() else None

        success, err_list, count = validate_and_parse_csv(file.stream, test, selected_count)
        if success:
            flash(f"Successfully loaded and validated {count} questions for '{test.name}'.", "success")
            return redirect(url_for("admin.preview_test", test_id=test.id))
        else:
            errors = err_list

    return render_template("admin/upload_csv.html", test=test, errors=errors)

@admin_bp.route("/tests/<int:test_id>/preview")
@login_required
def preview_test(test_id):
    test = Test.query.get_or_404(test_id)
    questions = Question.query.filter_by(test_id=test.id).order_by(Question.q_no).all()
    return render_template("admin/preview.html", test=test, questions=questions)

@admin_bp.route("/tests/<int:test_id>/live", methods=["POST"])
@login_required
def make_live(test_id):
    test = Test.query.get_or_404(test_id)
    
    if test.questions.count() == 0:
        flash("Cannot make a test live without uploading questions first.", "warning")
        return redirect(url_for("admin.upload_questions", test_id=test.id))

    # Deactivate any other currently live test for this class
    other_live = Test.query.filter_by(class_name=test.class_name, status="live").all()
    for ot in other_live:
        ot.status = "closed"
        ot.closed_at = datetime.utcnow()

    test.status = "live"
    test.live_at = datetime.utcnow()
    db.session.commit()

    flash(f"Test '{test.name}' is now LIVE for Class {test.class_name}!", "success")
    return redirect(url_for("admin.live_monitor", test_id=test.id))

@admin_bp.route("/tests/<int:test_id>/close", methods=["POST"])
@login_required
def close_test(test_id):
    test = Test.query.get_or_404(test_id)
    test.status = "closed"
    test.closed_at = datetime.utcnow()
    db.session.commit()

    flash(f"Test '{test.name}' has been closed.", "info")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/tests/<int:test_id>/monitor")
@login_required
def live_monitor(test_id):
    test = Test.query.get_or_404(test_id)
    attempts = Attempt.query.filter_by(test_id=test.id).order_by(Attempt.started_at.desc()).all()
    
    in_progress_count = sum(1 for a in attempts if a.status == "in_progress")
    submitted_count = sum(1 for a in attempts if a.status != "in_progress")

    return render_template(
        "admin/monitor.html",
        test=test,
        attempts=attempts,
        in_progress_count=in_progress_count,
        submitted_count=submitted_count
    )

@admin_bp.route("/tests/<int:test_id>/monitor/data")
@login_required
def monitor_data(test_id):
    """JSON polling endpoint for live real-time dashboard updates"""
    test = Test.query.get_or_404(test_id)
    attempts = Attempt.query.filter_by(test_id=test.id).order_by(Attempt.started_at.desc()).all()

    items = []
    for a in attempts:
        student = Student.query.get(a.student_id)
        items.append({
            "attempt_id": a.id,
            "student_name": student.name if student else "Unknown",
            "status": a.status,
            "score": a.score,
            "max_score": a.max_score,
            "tab_switches": a.tab_switches or 0,
            "time_sec": a.total_time_sec or 0
        })

    return jsonify({
        "status": test.status,
        "total": len(attempts),
        "in_progress": sum(1 for a in attempts if a.status == "in_progress"),
        "submitted": sum(1 for a in attempts if a.status != "in_progress"),
        "attempts": items
    })

@admin_bp.route("/tests/<int:test_id>/results")
@login_required
def results(test_id):
    test = Test.query.get_or_404(test_id)
    attempts = Attempt.query.filter_by(test_id=test.id).order_by(Attempt.score.desc()).all()
    
    scores = [a.score for a in attempts if a.status != "in_progress"]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    highest = max(scores) if scores else 0
    lowest = min(scores) if scores else 0

    return render_template(
        "admin/results.html",
        test=test,
        attempts=attempts,
        avg_score=avg_score,
        highest=highest,
        lowest=lowest
    )

@admin_bp.route("/tests/<int:test_id>/results.csv")
@login_required
def export_results_csv(test_id):
    test = Test.query.get_or_404(test_id)
    attempts = Attempt.query.filter_by(test_id=test.id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Attempt ID", "Student Name", "Class", "Score", "Max Score",
        "Percentage", "Correct", "Wrong", "Skipped", "Time (seconds)",
        "Tab Switches", "Status", "Date Submitted"
    ])

    for a in attempts:
        student = Student.query.get(a.student_id)
        pct = round(a.score / a.max_score * 100, 1) if a.max_score > 0 else 0
        sub_date = a.submitted_at.strftime("%Y-%m-%d %H:%M") if a.submitted_at else "In Progress"
        writer.writerow([
            a.id,
            student.name if student else "Unknown",
            student.class_name if student else test.class_name,
            a.score,
            a.max_score,
            f"{pct}%",
            a.correct,
            a.wrong,
            a.skipped,
            a.total_time_sec,
            a.tab_switches,
            a.status,
            sub_date
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=results_{test.name.replace(' ', '_')}.csv"}
    )

@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    school_settings = SchoolSettings.query.first()
    if not school_settings:
        school_settings = SchoolSettings()
        db.session.add(school_settings)
        db.session.commit()

    if request.method == "POST":
        school_name = request.form.get("school_name", "").strip()
        if school_name:
            school_settings.school_name = school_name

        logo_file = request.files.get("logo_file")
        if logo_file and logo_file.filename != "":
            filename = secure_filename(logo_file.filename)
            ext = os.path.splitext(filename)[1].lower()
            if ext in [".png", ".jpg", ".jpeg"]:
                save_name = f"school_logo{ext}"
                save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], save_name)
                logo_file.save(save_path)
                school_settings.logo_path = save_path
                flash("School logo uploaded successfully!", "success")
            else:
                flash("Only PNG and JPG formats are accepted for logos.", "danger")

        db.session.commit()
        flash("School settings updated.", "success")
        return redirect(url_for("admin.settings"))

    return render_template("admin/settings.html", school_settings=school_settings)
