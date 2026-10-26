import os
import sys
from pathlib import Path
from flask import Flask, send_from_directory
from flask_login import LoginManager
from app.models import db, Admin, SchoolSettings, Test
from config import Config

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

def create_app(config_class=Config):
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundle_dir = Path(sys._MEIPASS)
        template_dir = str(bundle_dir / "app" / "templates")
        static_dir = str(bundle_dir / "app" / "static")
        app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    else:
        app = Flask(__name__)

    app.config.from_object(config_class)

    # Ensure required runtime directories exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["REPORT_FOLDER"], exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    # Custom route to serve uploads from persistent UPLOAD_FOLDER
    @app.route("/static/uploads/<path:filename>")
    def custom_uploads(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # Register Blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.student import student_bp
    from app.blueprints.report import report_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(student_bp)
    app.register_blueprint(report_bp)

    with app.app_context():
        db.create_all()

        # Seed or ensure 'prince' Admin exists with password 'tarunsirkijai'
        prince_admin = Admin.query.filter_by(username="prince").first()
        if not prince_admin:
            old_admin = Admin.query.filter_by(username="admin").first()
            if old_admin:
                old_admin.username = "prince"
                old_admin.set_password("tarunsirkijai")
                db.session.commit()
            else:
                prince_admin = Admin(username="prince")
                prince_admin.set_password("tarunsirkijai")
                db.session.add(prince_admin)
                db.session.commit()
        else:
            prince_admin.set_password("tarunsirkijai")
            db.session.commit()

        # Seed initial SchoolSettings if not exists
        if not SchoolSettings.query.first():
            settings = SchoolSettings(
                school_name=app.config.get("DEFAULT_SCHOOL_NAME", "Delhi Public Model School")
            )
            db.session.add(settings)
            db.session.commit()

        # Auto-seed sample Class 10 Math assessment if no tests exist yet
        if not Test.query.first():
            try:
                from datetime import datetime
                from app.services.csv_service import validate_and_parse_csv
                demo = Test(
                    name="Class 10 Mathematics Term Assessment",
                    subject="Mathematics",
                    class_name="10",
                    total_questions=20,
                    duration_min=25,
                    marks_per_q=1.0,
                    negative_marking=0.25,
                    shuffle=True,
                    allow_reattempt=True,
                    status="live",
                    live_at=datetime.utcnow()
                )
                db.session.add(demo)
                db.session.commit()

                bundle_root = Path(getattr(sys, "_MEIPASS", Config.BASE_DIR))
                csv_path = bundle_root / "sample_data" / "sample_math_class10.csv"
                if not csv_path.exists():
                    csv_path = Path(__file__).resolve().parent.parent / "sample_data" / "sample_math_class10.csv"
                if csv_path.exists():
                    with open(csv_path, "r", encoding="utf-8") as f:
                        validate_and_parse_csv(f, demo, 20)
            except Exception as e:
                app.logger.warning(f"Could not auto-seed demo test: {e}")

    return app
