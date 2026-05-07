"""
SLIS — Phase 4: Recommendation Engine
Rule-based logic + Google Gemini AI for personalized student recommendations.
"""

import os
import json
from pathlib import Path

import requests
import pandas as pd
from dotenv import load_dotenv

# ---------------------------------------------------
# Environment setup
# ---------------------------------------------------

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

BASE_DIR = Path(__file__).resolve().parent.parent
CLEAN_DIR = BASE_DIR / "data" / "cleaned"


# ══════════════════════════════════════════════════════
# RULE-BASED ENGINE
# ══════════════════════════════════════════════════════

def rule_based_recommendations(student: dict) -> list[dict]:

    recs = []

    attendance_rate = student.get("attendance_rate", 1.0)
    avg_score = student.get("avg_score", 100)
    total_sessions = student.get("total_sessions", 0)
    unique_days = student.get("unique_days_active", 0)
    weak_subjects = student.get("weak_subjects", [])
    std_score = student.get("std_score", 0)
    at_risk = student.get("at_risk", 0)

    # ---------------------------------------------
    # Attendance rules
    # ---------------------------------------------

    if attendance_rate < 0.50:

        recs.append({
            "category": "Attendance",
            "priority": "Critical",
            "message":
                f"Attendance is critically low at "
                f"{attendance_rate * 100:.1f}%. "
                f"Immediate intervention required. "
                f"Meet with your academic advisor this week."
        })

    elif attendance_rate < 0.65:

        recs.append({
            "category": "Attendance",
            "priority": "High",
            "message":
                f"Attendance is {attendance_rate * 100:.1f}%, "
                f"below the 65% risk threshold. "
                f"Aim to attend every class consistently."
        })

    elif attendance_rate < 0.80:

        recs.append({
            "category": "Attendance",
            "priority": "Medium",
            "message":
                f"Attendance is {attendance_rate * 100:.1f}%. "
                f"Try maintaining above 80% for stronger performance."
        })

    # ---------------------------------------------
    # Score rules
    # ---------------------------------------------

    if avg_score < 40:

        recs.append({
            "category": "Academic Performance",
            "priority": "Critical",
            "message":
                f"Average score of {avg_score:.1f}% is critically low. "
                f"Seek tutoring support immediately."
        })

    elif avg_score < 55:

        recs.append({
            "category": "Academic Performance",
            "priority": "High",
            "message":
                f"Average score of {avg_score:.1f}% needs improvement. "
                f"Schedule daily revision sessions and practice tests."
        })

    # ---------------------------------------------
    # Weak subject rules
    # ---------------------------------------------

    if isinstance(weak_subjects, str):

        try:
            weak_subjects = json.loads(
                weak_subjects.replace("'", '"')
            )

        except Exception:
            weak_subjects = []

    for subject in weak_subjects:

        recs.append({
            "category": "Subject Support",
            "priority": "High",
            "message":
                f"Scoring below 50% in {subject}. "
                f"Attend extra support sessions for {subject}."
        })

    # ---------------------------------------------
    # Engagement rules
    # ---------------------------------------------

    if total_sessions < 30:

        recs.append({
            "category": "Engagement",
            "priority": "High",
            "message":
                f"Only {total_sessions} platform sessions recorded. "
                f"Increase LMS engagement and daily logins."
        })

    elif total_sessions < 60:

        recs.append({
            "category": "Engagement",
            "priority": "Medium",
            "message":
                f"Platform engagement is low "
                f"({total_sessions} sessions). "
                f"Aim for at least 3 sessions weekly."
        })

    # ---------------------------------------------
    # Consistency rules
    # ---------------------------------------------

    if unique_days < 20:

        recs.append({
            "category": "Consistency",
            "priority": "Medium",
            "message":
                f"Only active on {unique_days} days. "
                f"Consistent study habits improve retention."
        })

    if std_score > 20:

        recs.append({
            "category": "Consistency",
            "priority": "Medium",
            "message":
                f"High score variability detected "
                f"(std dev: {std_score:.1f}). "
                f"Focus on regular preparation."
        })

    # ---------------------------------------------
    # Positive reinforcement
    # ---------------------------------------------

    if attendance_rate >= 0.90 and avg_score >= 75:

        recs.append({
            "category": "Encouragement",
            "priority": "Info",
            "message":
                "Excellent academic consistency and attendance. "
                "Keep up the strong performance."
        })

    elif at_risk == 0 and avg_score >= 60:

        recs.append({
            "category": "Encouragement",
            "priority": "Info",
            "message":
                "You are performing well overall. "
                "Maintain your current learning habits."
        })

    # ---------------------------------------------
    # Sort priorities
    # ---------------------------------------------

    priority_order = {
        "Critical": 0,
        "High": 1,
        "Medium": 2,
        "Info": 3,
    }

    recs.sort(
        key=lambda r: priority_order.get(
            r["priority"],
            99
        )
    )

    return recs


# ══════════════════════════════════════════════════════
# AI-POWERED ENGINE (Google Gemini)
# ══════════════════════════════════════════════════════

def ai_recommendations(student: dict) -> str:

    if not GEMINI_API_KEY:

        return (
            "AI recommendations unavailable: "
            "GEMINI_API_KEY not configured."
        )

    weak_subjects = student.get("weak_subjects", [])

    if isinstance(weak_subjects, str):

        try:
            weak_subjects = json.loads(
                weak_subjects.replace("'", '"')
            )

        except Exception:
            weak_subjects = []

    summary = f"""
Student Profile:
- Department: {student.get('department', 'N/A')}
- Enrollment Year: {student.get('enrollment_year', 'N/A')}
- Attendance Rate: {student.get('attendance_rate', 0) * 100:.1f}%
- Average Score: {student.get('avg_score', 0):.1f}%
- Min Score: {student.get('min_score', 0):.1f}%
- Score Std Dev: {student.get('std_score', 0):.1f}
- Total Platform Sessions: {student.get('total_sessions', 0)}
- Total Study Minutes: {student.get('total_minutes', 0)}
- Unique Active Days: {student.get('unique_days_active', 0)}
- Weak Subjects: {', '.join(weak_subjects) if weak_subjects else 'None'}
- At-Risk: {'Yes' if student.get('at_risk', 0) == 1 else 'No'}
- Predicted Score: {student.get('predicted_score', 'N/A')}
"""

    prompt = (
        "You are an academic advisor AI.\n"
        "Provide concise, practical, actionable advice.\n"
        "Return 3-5 numbered recommendations.\n\n"
        f"{summary}"
    )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

        return (
            data["candidates"][0]
            ["content"]["parts"][0]["text"]
            .strip()
        )

    except requests.exceptions.HTTPError as e:

        return (
            f"Gemini API HTTP error: "
            f"{e.response.status_code}"
        )

    except Exception as e:

        return (
            f"Gemini API error: {str(e)}"
        )


# ══════════════════════════════════════════════════════
# COMBINED ENGINE
# ══════════════════════════════════════════════════════

def get_recommendations(
    student: dict,
    use_ai: bool = False
) -> dict:

    rule_recs = rule_based_recommendations(student)

    result = {
        "student_id": student.get(
            "student_id",
            "unknown"
        ),

        "at_risk": bool(
            student.get("at_risk", 0)
        ),

        "rule_based": rule_recs,

        "ai_powered": None,
    }

    # Optional AI call
    if use_ai:

        try:
            result["ai_powered"] = (
                ai_recommendations(student)
            )

        except Exception as e:

            result["ai_powered"] = (
                f"AI unavailable: {str(e)}"
            )

    return result


# ══════════════════════════════════════════════════════
# STANDALONE TEST
# ══════════════════════════════════════════════════════

if __name__ == "__main__":

    try:

        master = pd.read_csv(
            CLEAN_DIR / "master_features.csv"
        )

        scores = pd.read_csv(
            CLEAN_DIR / "scores_summary.csv"
        )

        profiles = pd.read_csv(
            CLEAN_DIR / "student_profiles_clean.csv"
        )

        merged = master.merge(
            scores[
                ["student_id", "weak_subjects"]
            ],
            on="student_id",
            how="left",
        )

        merged = merged.merge(
            profiles[
                ["student_id", "department"]
            ],
            on="student_id",
            how="left",
        )

        test_student = merged[
            merged["at_risk"] == 1
        ].iloc[0].to_dict()

        result = get_recommendations(
            test_student,
            use_ai=False,
        )

        print(json.dumps(
            result,
            indent=2
        ))

    except Exception as e:

        print(
            f"Standalone test failed: {str(e)}"
        )