"""
SLIS — Pydantic schemas
"""

from pydantic import BaseModel
from typing import Optional

class PredictRequest(BaseModel):
    age: float
    gender_encoded: float
    dept_encoded: float
    enrollment_year: float
    attendance_rate: float
    min_score: float
    std_score: float
    total_sessions: float
    total_minutes: float
    unique_days_active: float

class PredictResponse(BaseModel):
    predicted_score: float
    at_risk: bool
    risk_probability: float

class RecommendationItem(BaseModel):
    category: str
    priority: str
    message: str

class RecommendationsResponse(BaseModel):
    student_id: str
    at_risk: bool
    rule_based: list[RecommendationItem]
    ai_powered: Optional[str]

class StudentSummary(BaseModel):
    student_id: str
    name: str
    department: str
    attendance_rate: float
    avg_score: float
    at_risk: bool

class StudentDetail(StudentSummary):
    age: int
    gender: str
    enrollment_year: int
    min_score: float
    std_score: float
    total_sessions: float
    total_minutes: float
    unique_days_active: float
    weak_subjects: list[str]
    predicted_score: Optional[float] = None
    risk_probability: Optional[float] = None

class DashboardSummary(BaseModel):
    total_students: int
    at_risk_count: int
    at_risk_pct: float
    avg_score: float
    avg_attendance: float
