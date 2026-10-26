import os
import json
import logging
from deepagents import create_deep_agent, SubAgent
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from app.ai.schemas import StudentFeedbackSchema
from app.ai.tools import (
    get_attempt_data,
    topic_accuracy,
    type_accuracy,
    time_stats,
    class_benchmark
)
from app.ai.prompts import (
    ORCHESTRATOR_SYSTEM_PROMPT,
    PERFORMANCE_ANALYST_PROMPT,
    TIME_ANALYST_PROMPT,
    MISTAKE_DIAGNOSER_PROMPT,
    STUDY_COACH_PROMPT
)
from app.ai.fallback import generate_rule_based_feedback
from app.models import db, Attempt, Feedback

logger = logging.getLogger(__name__)

def get_chat_model():
    """Initializes LLM chat model based on configured API keys in environment"""
    groq_key = os.getenv("GROQ_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

    if groq_key:
        return ChatGroq(
            model_name=os.getenv("DEFAULT_MODEL", "llama-3.3-70b-versatile"),
            groq_api_key=groq_key,
            temperature=0.3
        ), "groq:llama-3.3-70b-versatile"
    elif openai_key:
        return ChatOpenAI(
            model_name="gpt-4o-mini",
            api_key=openai_key,
            temperature=0.3
        ), "openai:gpt-4o-mini"
    
    return None, "none"

def build_evaluation_deep_agent(model):
    """Assembles the Deep Agent with 4 specialized sub-agents and deterministic tools"""
    
    perf_subagent = SubAgent(
        name="performance_analyst",
        description="Analyzes topic accuracy, question types, and difficulty breakdown.",
        system_prompt=PERFORMANCE_ANALYST_PROMPT,
        tools=[get_attempt_data, topic_accuracy, type_accuracy]
    )

    time_subagent = SubAgent(
        name="time_analyst",
        description="Analyzes dwell time per question, rushed incorrect attempts, and bottlenecks.",
        system_prompt=TIME_ANALYST_PROMPT,
        tools=[get_attempt_data, time_stats]
    )

    mistake_subagent = SubAgent(
        name="mistake_diagnoser",
        description="Diagnoses root causes for missed questions (concept gap, careless, etc.).",
        system_prompt=MISTAKE_DIAGNOSER_PROMPT,
        tools=[get_attempt_data]
    )

    coach_subagent = SubAgent(
        name="study_coach",
        description="Formulates high-impact 3-5 action steps and study roadmap.",
        system_prompt=STUDY_COACH_PROMPT,
        tools=[get_attempt_data, topic_accuracy]
    )

    orchestrator = create_deep_agent(
        model=model,
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        tools=[get_attempt_data, topic_accuracy, type_accuracy, time_stats, class_benchmark],
        subagents=[perf_subagent, time_subagent, mistake_subagent, coach_subagent],
        response_format=StudentFeedbackSchema
    )

    return orchestrator

def evaluate_student_attempt(attempt_id: int, language: str = "English") -> dict:
    """
    Main evaluation pipeline:
    1. Checks if LLM is available.
    2. Runs Deep Agent with sub-agents and deterministic tools.
    3. Validates output schema.
    4. Automatically falls back to deterministic rule-based feedback on failure/offline.
    5. Stores Feedback record in DB.
    """
    attempt = Attempt.query.get(attempt_id)
    if not attempt:
        raise ValueError(f"Attempt ID {attempt_id} not found.")

    model, model_name = get_chat_model()
    feedback_payload = None
    source = "ai"

    if model:
        try:
            agent = build_evaluation_deep_agent(model)
            prompt = (
                f"Evaluate the student assessment performance for Attempt ID {attempt_id}. "
                f"Use tools to fetch data and coordinate with your subagents. "
                f"Provide constructive recommendations in {language} language."
            )
            result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
            
            # Extract structured response
            structured = result.get("structured_response")
            if structured:
                if isinstance(structured, StudentFeedbackSchema):
                    feedback_payload = structured.model_dump()
                elif isinstance(structured, dict):
                    feedback_payload = structured
            
            # If not in structured_response, inspect final message content
            if not feedback_payload and result.get("messages"):
                last_msg = result["messages"][-1]
                content = getattr(last_msg, "content", "")
                if isinstance(content, str):
                    try:
                        # Attempt JSON extraction
                        start = content.find("{")
                        end = content.rfind("}")
                        if start != -1 and end != -1:
                            raw_json = json.loads(content[start:end+1])
                            validated = StudentFeedbackSchema.model_validate(raw_json)
                            feedback_payload = validated.model_dump()
                    except Exception as parse_err:
                        logger.warning(f"Failed to parse LLM JSON: {parse_err}")

        except Exception as e:
            logger.error(f"Deep Agent evaluation error: {e}. Falling back to rule-based engine.")

    # Fallback if AI not available or failed
    if not feedback_payload:
        source = "fallback"
        feedback_payload = generate_rule_based_feedback(attempt_id)

    # Persist or update feedback in database
    feedback = Feedback.query.filter_by(attempt_id=attempt_id).first()
    if not feedback:
        feedback = Feedback(
            attempt_id=attempt_id,
            json_payload=feedback_payload,
            language=language,
            model_used=model_name if source == "ai" else "rule_based_engine",
            source=source
        )
        db.session.add(feedback)
    else:
        feedback.json_payload = feedback_payload
        feedback.source = source
        feedback.model_used = model_name if source == "ai" else "rule_based_engine"

    attempt.status = "report_ready"
    db.session.commit()

    return feedback_payload
