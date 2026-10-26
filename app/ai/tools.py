import json
from langchain_core.tools import tool
from app.models import db, Attempt, Answer, Question, Test

def _fetch_attempt_records(attempt_id: int):
    attempt = Attempt.query.get(attempt_id)
    if not attempt:
        return None, None, None
    answers = Answer.query.filter_by(attempt_id=attempt_id).all()
    questions = Question.query.filter_by(test_id=attempt.test_id).order_by(Question.q_no).all()
    q_map = {q.id: q for q in questions}
    ans_map = {a.question_id: a for a in answers}
    return attempt, questions, ans_map

@tool
def get_attempt_data(attempt_id: int) -> str:
    """Fetches anonymized performance data for a student's attempt including all questions, responses, time spent, and correctness."""
    attempt, questions, ans_map = _fetch_attempt_records(attempt_id)
    if not attempt:
        return json.dumps({"error": f"Attempt {attempt_id} not found"})

    items = []
    for q in questions:
        ans = ans_map.get(q.id)
        items.append({
            "q_no": q.q_no,
            "topic": q.topic,
            "question_type": q.question_type,
            "difficulty": q.difficulty,
            "selected_option": ans.selected_option if ans else None,
            "correct_option": q.correct_option,
            "is_correct": ans.is_correct if ans else False,
            "time_spent_sec": ans.time_spent_sec if ans else 0,
            "change_count": ans.change_count if ans else 0,
            "explanation": q.explanation
        })

    payload = {
        "attempt_id": attempt.id,
        "test_id": attempt.test_id,
        "score": attempt.score,
        "max_score": attempt.max_score,
        "correct": attempt.correct,
        "wrong": attempt.wrong,
        "skipped": attempt.skipped,
        "total_time_sec": attempt.total_time_sec,
        "tab_switches": attempt.tab_switches,
        "questions": items
    }
    return json.dumps(payload, indent=2)

@tool
def topic_accuracy(attempt_id: int) -> str:
    """Calculates deterministic topic-wise accuracy, total questions per topic, and correct count."""
    attempt, questions, ans_map = _fetch_attempt_records(attempt_id)
    if not attempt:
        return json.dumps({"error": f"Attempt {attempt_id} not found"})

    topic_stats = {}
    for q in questions:
        t = q.topic or "General"
        if t not in topic_stats:
            topic_stats[t] = {"total": 0, "correct": 0, "wrong": 0, "skipped": 0, "time_sec": 0}
        
        topic_stats[t]["total"] += 1
        ans = ans_map.get(q.id)
        if ans and ans.selected_option:
            topic_stats[t]["time_sec"] += ans.time_spent_sec
            if ans.is_correct:
                topic_stats[t]["correct"] += 1
            else:
                topic_stats[t]["wrong"] += 1
        else:
            topic_stats[t]["skipped"] += 1

    for t, s in topic_stats.items():
        s["accuracy_pct"] = round((s["correct"] / s["total"] * 100), 1) if s["total"] > 0 else 0
        s["avg_time_per_q_sec"] = round(s["time_sec"] / s["total"], 1) if s["total"] > 0 else 0

    return json.dumps(topic_stats, indent=2)

@tool
def type_accuracy(attempt_id: int) -> str:
    """Calculates accuracy broken down by question type (conceptual, numerical, application, recall)."""
    attempt, questions, ans_map = _fetch_attempt_records(attempt_id)
    if not attempt:
        return json.dumps({"error": f"Attempt {attempt_id} not found"})

    type_stats = {}
    for q in questions:
        qt = q.question_type or "conceptual"
        if qt not in type_stats:
            type_stats[qt] = {"total": 0, "correct": 0, "wrong": 0}
        type_stats[qt]["total"] += 1
        ans = ans_map.get(q.id)
        if ans and ans.selected_option and ans.is_correct:
            type_stats[qt]["correct"] += 1
        elif ans and ans.selected_option:
            type_stats[qt]["wrong"] += 1

    for qt, s in type_stats.items():
        s["accuracy_pct"] = round((s["correct"] / s["total"] * 100), 1) if s["total"] > 0 else 0

    return json.dumps(type_stats, indent=2)

@tool
def time_stats(attempt_id: int) -> str:
    """Computes time analytics: average solve time, rushed incorrect questions, and outlier bottlenecks."""
    attempt, questions, ans_map = _fetch_attempt_records(attempt_id)
    if not attempt:
        return json.dumps({"error": f"Attempt {attempt_id} not found"})

    times = []
    rushed_questions = []
    stuck_questions = []

    for q in questions:
        ans = ans_map.get(q.id)
        spent = ans.time_spent_sec if ans else 0
        times.append(spent)
        
        # Rush flag: took < 12 seconds and answered incorrectly
        if ans and ans.selected_option and not ans.is_correct and spent < 12:
            rushed_questions.append({
                "q_no": q.q_no,
                "topic": q.topic,
                "spent_sec": spent
            })

    avg_time = round(sum(times) / len(times), 1) if times else 0
    # Stuck threshold: > 2.5 times average or > 120s
    stuck_threshold = max(60, avg_time * 2.5)

    for q in questions:
        ans = ans_map.get(q.id)
        spent = ans.time_spent_sec if ans else 0
        if spent > stuck_threshold:
            stuck_questions.append({
                "q_no": q.q_no,
                "topic": q.topic,
                "spent_sec": spent,
                "is_correct": ans.is_correct if ans else False
            })

    res = {
        "total_time_sec": attempt.total_time_sec,
        "avg_time_per_q_sec": avg_time,
        "tab_switches": attempt.tab_switches,
        "rushed_mistakes_count": len(rushed_questions),
        "rushed_mistakes": rushed_questions,
        "stuck_questions_count": len(stuck_questions),
        "stuck_questions": stuck_questions
    }
    return json.dumps(res, indent=2)

@tool
def class_benchmark(test_id: int) -> str:
    """Calculates class benchmark statistics for the test to compare student against peer cohort."""
    attempts = Attempt.query.filter(Attempt.test_id == test_id, Attempt.status.in_(["scored", "feedback_pending", "report_ready"])).all()
    if not attempts:
        return json.dumps({"total_submissions": 0, "class_avg_score": 0})

    scores = [a.score for a in attempts]
    avg_score = round(sum(scores) / len(scores), 2)
    max_score = attempts[0].max_score if attempts else 0

    return json.dumps({
        "total_submissions": len(attempts),
        "class_avg_score": avg_score,
        "class_max_score": max_score,
        "class_avg_pct": round((avg_score / max_score * 100), 1) if max_score > 0 else 0
    }, indent=2)
