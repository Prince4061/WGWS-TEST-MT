import os
from datetime import datetime
from app import create_app
from app.models import db, Test, SchoolSettings
from app.services.csv_service import validate_and_parse_csv

app = create_app()

def seed_demo_assessment():
    with app.app_context():
        # Ensure default school name is set
        school = SchoolSettings.query.first()
        if school:
            school.school_name = "Delhi Public Model School"
            db.session.commit()

        # Check if demo test already exists
        demo = Test.query.filter_by(name="Class 10 Mathematics Term Assessment").first()
        if not demo:
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

            csv_path = os.path.join(os.path.dirname(__file__), "sample_data", "sample_math_class10.csv")
            if os.path.exists(csv_path):
                with open(csv_path, "r", encoding="utf-8") as f:
                    success, errors, count = validate_and_parse_csv(f, demo, 20)
                    if success:
                        print(f"[OK] Seeded demo test with {count} questions for Class 10 (LIVE)!")
                    else:
                        print(f"[ERROR] Failed to seed CSV: {errors}")
            else:
                print("CSV file not found.")
        else:
            demo.status = "live"
            db.session.commit()
            print("[OK] Class 10 demo test is already seeded and set to LIVE.")

if __name__ == "__main__":
    seed_demo_assessment()
