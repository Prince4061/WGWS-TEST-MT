from app.models import Attempt, Answer, Question

def generate_rule_based_feedback(attempt_id: int) -> dict:
    """
    Guaranteed fallback evaluation generator that executes 100% locally
    without LLM dependencies, producing an identical structured schema.
    """
    attempt = Attempt.query.get(attempt_id)
    if not attempt:
        return {}

    answers = Answer.query.filter_by(attempt_id=attempt_id).all()
    questions = Question.query.filter_by(test_id=attempt.test_id).all()
    ans_map = {a.question_id: a for a in answers}

    topic_stats = {}
    type_stats = {}
    rushed_mistakes = []
    total_time = attempt.total_time_sec or 1

    for q in questions:
        t = q.topic or "General"
        qt = q.question_type or "conceptual"

        if t not in topic_stats:
            topic_stats[t] = {"total": 0, "correct": 0, "wrong": 0}
        topic_stats[t]["total"] += 1

        if qt not in type_stats:
            type_stats[qt] = {"total": 0, "correct": 0, "wrong": 0}
        type_stats[qt]["total"] += 1

        ans = ans_map.get(q.id)
        if ans and ans.selected_option:
            if ans.is_correct:
                topic_stats[t]["correct"] += 1
                type_stats[qt]["correct"] += 1
            else:
                topic_stats[t]["wrong"] += 1
                type_stats[qt]["wrong"] += 1
                if ans.time_spent_sec < 12:
                    rushed_mistakes.append(f"Q{q.q_no} ({t})")

    # Determine Strengths & Weak Areas
    strengths = []
    weak_areas = []

    for topic, s in topic_stats.items():
        pct = (s["correct"] / s["total"] * 100) if s["total"] > 0 else 0
        if pct >= 70:
            strengths.append({
                "topic": topic,
                "evidence": f"Demonstrated {int(pct)}% accuracy across {s['total']} questions."
            })
        elif pct <= 50:
            priority = "high" if pct < 35 else "medium"
            weak_areas.append({
                "topic": topic,
                "question_type": "conceptual / application",
                "evidence": f"Scored {int(pct)}% ({s['correct']}/{s['total']} correct). Further practice needed.",
                "priority": priority
            })

    # If no strengths/weaknesses (e.g. all 60%), provide defaults
    if not strengths:
        strengths.append({
            "topic": "Consistent Effort",
            "evidence": f"Attempted {len(questions) - attempt.skipped} questions with good foundational focus."
        })
    if not weak_areas:
        weak_areas.append({
            "topic": "Advanced Application",
            "question_type": "application",
            "evidence": "Focus on high-speed accuracy and tackling difficult level problems.",
            "priority": "low"
        })

    # Pacing insights
    avg_sec = round(total_time / max(1, len(questions)), 1)
    time_insights = [
        f"Average time per question was {avg_sec} seconds.",
    ]
    if rushed_mistakes:
        time_insights.append(
            f"Observed rush pattern on {len(rushed_mistakes)} questions ({', '.join(rushed_mistakes[:3])}) where questions were answered in under 12 seconds."
        )
    else:
        time_insights.append("Pacing was well-managed without significant signs of rushing.")

    # Mistake patterns
    mistake_patterns = []
    if rushed_mistakes:
        mistake_patterns.append({
            "pattern": "careless",
            "details": "Several errors occurred rapidly (<12s), indicating potential misreading of question prompts or answer choices."
        })
    if attempt.wrong > len(rushed_mistakes):
        mistake_patterns.append({
            "pattern": "concept_gap",
            "details": "Identified conceptual review opportunities in core topics with multiple missed items."
        })
    if not mistake_patterns:
        mistake_patterns.append({
            "pattern": "general",
            "details": "No recurring negative pattern observed; errors appear isolated."
        })

    # Action plan
    action_plan = []
    for wa in weak_areas[:3]:
        action_plan.append({
            "step": f"Review key textbook concepts and formulas in '{wa['topic']}'.",
            "estimated_time": "25 mins",
            "resource_hint": f"Topic: {wa['topic']}"
        })
    action_plan.append({
        "step": "Re-solve missed questions without looking at the solutions first.",
        "estimated_time": "15 mins",
        "resource_hint": "Mistakes Review section of this report"
    })

    pct_overall = round((attempt.score / max(1.0, attempt.max_score) * 100), 1)
    summary = (
        f"Student achieved a score of {attempt.score}/{attempt.max_score} ({pct_overall}%). "
        f"Showed strong understanding in {', '.join([s['topic'] for s in strengths[:2]])}, "
        f"with clear room for improvement in {', '.join([w['topic'] for w in weak_areas[:2]])}."
    )

    encouragement = "Great effort! Consistent daily practice on target concepts will elevate your mastery."

    return {
        "summary": summary,
        "strengths": strengths,
        "weak_areas": weak_areas,
        "time_insights": time_insights,
        "mistake_patterns": mistake_patterns,
        "action_plan": action_plan,
        "encouragement": encouragement
    }
