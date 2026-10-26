from typing import List, Literal
from pydantic import BaseModel, Field

class StrengthItem(BaseModel):
    topic: str = Field(description="Name of the topic where student demonstrated high accuracy")
    evidence: str = Field(description="Brief evidence e.g. '100% correct in 3 questions with fast solve time'")

class WeakAreaItem(BaseModel):
    topic: str = Field(description="Name of the topic needing revision")
    question_type: str = Field(description="Type of question e.g. conceptual, numerical, application, recall")
    evidence: str = Field(description="Specific evidence e.g. 'Missed 2 out of 3 questions'")
    priority: Literal["high", "medium", "low"] = Field(description="Priority for remediation")

class MistakePatternItem(BaseModel):
    pattern: Literal["concept_gap", "careless", "calculation", "misread", "time_pressure", "general"] = Field(
        description="Category of the mistake"
    )
    details: str = Field(description="Explanation of the pattern observed across incorrect questions")

class ActionPlanItem(BaseModel):
    step: str = Field(description="Concrete action step for the student")
    estimated_time: str = Field(description="Estimated study or practice time e.g. '20 mins'")
    resource_hint: str = Field(description="Topic or chapter hint to practice e.g. 'Review NCERT Chapter 4 formulas'")

class StudentFeedbackSchema(BaseModel):
    summary: str = Field(description="2-3 sentence executive summary of overall performance and core takeaways")
    strengths: List[StrengthItem] = Field(description="List of student strengths identified")
    weak_areas: List[WeakAreaItem] = Field(description="List of weak areas needing targeted intervention")
    time_insights: List[str] = Field(description="List of insights on pacing, rush patterns, or bottlenecks")
    mistake_patterns: List[MistakePatternItem] = Field(description="Identified root causes of mistakes")
    action_plan: List[ActionPlanItem] = Field(description="3-5 concrete, grade-appropriate study tasks")
    encouragement: str = Field(description="Inspiring, uplifting closing sentence for the student")
