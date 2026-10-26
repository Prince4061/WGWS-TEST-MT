from datetime import datetime, timezone
from app.models import db, Test, Attempt, Answer, Question

def get_active_test_for_class(class_name):
    """Finds the currently live test for a given class"""
    return Test.query.filter_by(class_name=str(class_name).strip(), status="live").first()

def get_remaining_seconds(attempt, test=None):
    """
    Authoritative server-side remaining time calculation.
    Returns: remaining_seconds (int, minimum 0)
    """
    if not attempt or not attempt.started_at:
        return 0
    if not test:
        test = Test.query.get(attempt.test_id)
        
    duration_sec = (test.duration_min or 30) * 60
    elapsed_sec = int((datetime.utcnow() - attempt.started_at).total_seconds())
    remaining = duration_sec - elapsed_sec
    return max(0, remaining)

def record_answer_progress(attempt_id, question_id, selected_option, dwell_increment=0, is_change=False):
    """
    Saves or updates the student's answer via AJAX, tracking time spent and answer-change count.
    """
    attempt = Attempt.query.get(attempt_id)
    if not attempt or attempt.status != "in_progress":
        return None, "Attempt is not active or has already been submitted."

    # Validate that remaining time is > 0
    if get_remaining_seconds(attempt) <= 0:
        return None, "Time has expired."

    answer = Answer.query.filter_by(attempt_id=attempt_id, question_id=question_id).first()
    if not answer:
        answer = Answer(
            attempt_id=attempt_id,
            question_id=question_id,
            selected_option=selected_option,
            time_spent_sec=dwell_increment,
            change_count=1 if selected_option else 0,
            answered_at=datetime.utcnow()
        )
        db.session.add(answer)
    else:
        if is_change or (selected_option and selected_option != answer.selected_option):
            answer.change_count += 1
        answer.selected_option = selected_option
        answer.time_spent_sec += max(0, int(dwell_increment))
        answer.answered_at = datetime.utcnow()

    db.session.commit()
    return answer, None

def log_tab_switch(attempt_id):
    """Logs client tab-switch warning without immediately terminating the student"""
    attempt = Attempt.query.get(attempt_id)
    if attempt and attempt.status == "in_progress":
        attempt.tab_switches = (attempt.tab_switches or 0) + 1
        db.session.commit()
        return attempt.tab_switches
    return 0
