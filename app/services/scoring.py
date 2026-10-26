from datetime import datetime
from app.models import db, Attempt, Answer, Question, Test

def calculate_attempt_score(attempt_id):
    """
    Deterministically computes score, correct, wrong, skipped count,
    and updates attempt and answer records in DB.
    """
    attempt = Attempt.query.get(attempt_id)
    if not attempt:
        raise ValueError(f"Attempt with ID {attempt_id} not found.")

    test = Test.query.get(attempt.test_id)
    questions = Question.query.filter_by(test_id=test.id).all()
    answers = Answer.query.filter_by(attempt_id=attempt.id).all()
    answer_map = {ans.question_id: ans for ans in answers}

    correct_count = 0
    wrong_count = 0
    skipped_count = 0
    total_score = 0.0

    marks_per_q = float(test.marks_per_q or 1.0)
    negative_marking = float(test.negative_marking or 0.0)

    for q in questions:
        ans = answer_map.get(q.id)
        if ans and ans.selected_option:
            selected = ans.selected_option.strip().upper()
            if selected == q.correct_option.strip().upper():
                ans.is_correct = True
                correct_count += 1
                total_score += marks_per_q
            else:
                ans.is_correct = False
                wrong_count += 1
                total_score -= negative_marking
        else:
            # Question skipped or no answer recorded
            if not ans:
                ans = Answer(
                    attempt_id=attempt.id,
                    question_id=q.id,
                    selected_option=None,
                    is_correct=False,
                    time_spent_sec=0,
                    change_count=0
                )
                db.session.add(ans)
            else:
                ans.is_correct = False
            skipped_count += 1

    now = datetime.utcnow()
    attempt.submitted_at = now
    if attempt.started_at:
        attempt.total_time_sec = max(1, int((now - attempt.started_at).total_seconds()))
    else:
        attempt.started_at = now
        attempt.total_time_sec = 1

    attempt.correct = correct_count
    attempt.wrong = wrong_count
    attempt.skipped = skipped_count
    # Score floor is 0 unless teacher specifically allows negative net total
    attempt.score = round(max(0.0, total_score), 2)
    attempt.max_score = round(len(questions) * marks_per_q, 2)
    attempt.status = "scored"

    db.session.commit()

    return {
        "attempt_id": attempt.id,
        "score": attempt.score,
        "max_score": attempt.max_score,
        "percentage": round((attempt.score / attempt.max_score * 100), 1) if attempt.max_score > 0 else 0,
        "correct": correct_count,
        "wrong": wrong_count,
        "skipped": skipped_count,
        "total_time_sec": attempt.total_time_sec
    }
