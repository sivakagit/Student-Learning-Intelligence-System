"""
SLIS — API Routes
"""

import json
import sys
import os
import importlib
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from .ml import get_regressor, get_classifier, get_features
from .schemas import (
    PredictRequest, PredictResponse,
    RecommendationsResponse, StudentSummary, StudentDetail, DashboardSummary
)

# Resolve recommendations.py location relative to THIS file's directory (backend/)
# backend/routes.py -> parent = project root -> recommendations.py
_PROJECT_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
)

router = APIRouter()

CLEAN_DIR = "data/cleaned"
_cache: dict = {}


def _load_data():
    if _cache:
        return _cache

    master   = pd.read_csv(f"{CLEAN_DIR}/master_features.csv")
    profiles = pd.read_csv(f"{CLEAN_DIR}/student_profiles_clean.csv")
    scores_s = pd.read_csv(f"{CLEAN_DIR}/scores_summary.csv")

    # Only pull columns from profiles that are NOT already in master
    # master has: age, enrollment_year, gender_encoded, dept_encoded
    # profiles has: name, gender, department (the display versions)
    profile_cols = ["student_id", "name", "gender", "department"]
    merged = master.merge(
        profiles[profile_cols],
        on="student_id", how="left"
    ).merge(
        scores_s[["student_id", "weak_subjects"]],
        on="student_id", how="left"
    )

    def parse_ws(val):
        if isinstance(val, list): return val
        if not isinstance(val, str) or val in ("", "[]"): return []
        try: return json.loads(val.replace("'", '"'))
        except Exception: return []

    merged["weak_subjects"] = merged["weak_subjects"].apply(parse_ws)

    reg  = get_regressor()
    clf  = get_classifier()
    feat = get_features()
    X    = merged[feat].fillna(0)
    merged["predicted_score"]  = reg.predict(X).round(2)
    merged["risk_probability"] = clf.predict_proba(X)[:, 1].round(4)

    _cache["df"] = merged
    return _cache


def _get_rec_fn():
    """Load recommendations.py by absolute path — immune to sys.path/CWD issues."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "recommendations",
        os.path.join(_PROJECT_ROOT, "notebooks/recommendations.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.get_recommendations


@router.get("/students", response_model=list[StudentSummary])
def list_students(at_risk: bool | None = None):
    df = _load_data()["df"]
    if at_risk is not None:
        df = df[df["at_risk"] == int(at_risk)]
    return [
        StudentSummary(
            student_id=str(r.student_id),
            name=str(r.name),
            department=str(r.department),
            attendance_rate=round(float(r.attendance_rate), 4),
            avg_score=round(float(r.avg_score), 2),
            at_risk=bool(r.at_risk),
        )
        for r in df.itertuples()
    ]


@router.get("/students/{student_id}", response_model=StudentDetail)
def get_student(student_id: str):
    df = _load_data()["df"]
    row = df[df["student_id"] == student_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="Student not found")
    r = row.iloc[0]
    return StudentDetail(
        student_id=str(r.student_id),
        name=str(r.name),
        department=str(r.department),
        age=int(r.age),
        gender=str(r.gender),
        enrollment_year=int(r.enrollment_year),
        attendance_rate=round(float(r.attendance_rate), 4),
        avg_score=round(float(r.avg_score), 2),
        min_score=round(float(r.min_score), 2),
        std_score=round(float(r.std_score), 2),
        total_sessions=float(r.total_sessions),
        total_minutes=float(r.total_minutes),
        unique_days_active=float(r.unique_days_active),
        weak_subjects=list(r.weak_subjects) if r.weak_subjects else [],
        at_risk=bool(r.at_risk),
        predicted_score=float(r.predicted_score),
        risk_probability=float(r.risk_probability),
    )


@router.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest):
    reg  = get_regressor()
    clf  = get_classifier()
    feat = get_features()
    X    = pd.DataFrame([payload.model_dump()])[feat]
    pred_score = float(reg.predict(X)[0])
    risk_prob  = float(clf.predict_proba(X)[0, 1])
    return PredictResponse(
        predicted_score=round(pred_score, 2),
        at_risk=risk_prob >= 0.5,
        risk_probability=round(risk_prob, 4),
    )


@router.get("/recommendations/{student_id}", response_model=RecommendationsResponse)
def recommendations(student_id: str, use_ai: bool = False):
    df = _load_data()["df"]
    row = df[df["student_id"] == student_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="Student not found")
    student = row.iloc[0].to_dict()
    result = _get_rec_fn()(student, use_ai=use_ai)
    return RecommendationsResponse(**result)


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary():
    df = _load_data()["df"]
    total = len(df)
    at_risk = int(df["at_risk"].sum())
    return DashboardSummary(
        total_students=total,
        at_risk_count=at_risk,
        at_risk_pct=round(at_risk / total * 100, 1),
        avg_score=round(float(df["avg_score"].mean()), 2),
        avg_attendance=round(float(df["attendance_rate"].mean()), 4),
    )