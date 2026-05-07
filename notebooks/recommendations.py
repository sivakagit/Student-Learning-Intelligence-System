"""
SLIS — Phase 4: Recommendation Engine
Rule-based logic + Google Gemini AI for personalized student recommendations.
"""

import os
import json
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
CLEAN_DIR = "data/cleaned"


# ══════════════════════════════════════════════════════
# RULE-BASED ENGINE
# ══════════════════════════════════════════════════════

def rule_based_recommendations(student: dict) -> list[dict]:
    recs = []

    attendance_rate = student.get("attendance_rate", 1.0)
    avg_score       = student.get("avg_score", 100)
    total_sessions  = student.get("total_sessions", 0)
    unique_days     = student.get("unique_days_active", 0)
    weak_subjects   = student.get("weak_subjects", [])
    std_score       = student.get("std_score", 0)
    at_risk         = student.get("at_risk", 0)

    # Attendance rules
    if attendance_rate < 0.50:
        recs.append({"category": "Attendance", "priority": "Critical",
            "message": f"Attendance is critically low at {attendance_rate*100:.1f}%. Immediate intervention required. Meet with your academic advisor this week."})
    elif attendance_rate < 0.65:
        recs.append({"category": "Attendance", "priority": "High",
            "message": f"Attendance is {attendance_rate*100:.1f}%, below the 65% risk threshold. Aim to attend every class for the next 4 weeks to recover your standing."})
    elif attendance_rate < 0.80:
        recs.append({"category": "Attendance", "priority": "Medium",
            "message": f"Attendance is {attendance_rate*100:.1f}%. Try to maintain above 80% to stay in good academic standing."})

    # Score rules
    if avg_score < 40:
        recs.append({"category": "Academic Performance", "priority": "Critical",
            "message": f"Average score of {avg_score:.1f}% is critically low. Enroll in tutoring support immediately and review all past exam papers."})
    elif avg_score < 55:
        recs.append({"category": "Academic Performance", "priority": "High",
            "message": f"Average score of {avg_score:.1f}% needs improvement. Set aside dedicated daily study time and attempt practice tests each week."})

    # Weak subject rules
    if isinstance(weak_subjects, str):
        try:
            weak_subjects = json.loads(weak_subjects.replace("'", '"'))
        except Exception:
            weak_subjects = []
    for subject in weak_subjects:
        recs.append({"category": "Subject Support", "priority": "High",
            "message": f"Scoring below 50% in {subject}. Seek extra help — attend office hours or join a study group for {subject}."})

    # Engagement rules
    if total_sessions < 30:
        recs.append({"category": "Engagement", "priority": "High",
            "message": f"Only {total_sessions} platform sessions recorded. Log in daily to access course materials, attempt quizzes, and track progress."})
    elif total_sessions < 60:
        recs.append({"category": "Engagement", "priority": "Medium",
            "message": f"Platform engagement is low ({total_sessions} sessions). Aim for at least 3 active sessions per week."})

    if unique_days < 20:
        recs.append({"category": "Consistency", "priority": "Medium",
            "message": f"Active on only {unique_days} unique days. Consistent daily engagement is more effective than occasional long sessions."})

    if std_score > 20:
        recs.append({"category": "Consistency", "priority": "Medium",
            "message": f"High variability in scores (std dev: {std_score:.1f}). Performance is inconsistent — focus on weaker areas regularly."})

    # Positive reinforcement
    if attendance_rate >= 0.90 and avg_score >= 75:
        recs.append({"category": "Encouragement", "priority": "Info",
            "message": "Excellent attendance and strong scores! Consider mentoring peers or taking on advanced coursework."})
    elif at_risk == 0 and avg_score >= 60:
        recs.append({"category": "Encouragement", "priority": "Info",
            "message": "You are on track. Keep up the consistent effort and engagement."})

    priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Info": 3}
    recs.sort(key=lambda r: priority_order.get(r["priority"], 99))
    return recs


# ══════════════════════════════════════════════════════
# AI-POWERED ENGINE (Google Gemini)
# ══════════════════════════════════════════════════════

def ai_recommendations(student: dict) -> str:
    if not GEMINI_API_KEY:
        return "AI recommendations unavailable: GEMINI_API_KEY not set in .env"

    weak_subjects = student.get("weak_subjects", [])
    if isinstance(weak_subjects, str):
        try:
            weak_subjects = json.loads(weak_subjects.replace("'", '"'))
        except Exception:
            weak_subjects = []

    summary = f"""Student Profile:
- Department: {student.get('department', 'N/A')}
- Enrollment Year: {student.get('enrollment_year', 'N/A')}
- Attendance Rate: {student.get('attendance_rate', 0)*100:.1f}%
- Average Score: {student.get('avg_score', 0):.1f}%
- Min Score: {student.get('min_score', 0):.1f}%
- Score Std Dev: {student.get('std_score', 0):.1f}
- Total Platform Sessions: {student.get('total_sessions', 0)}
- Total Study Minutes: {student.get('total_minutes', 0)}
- Unique Active Days: {student.get('unique_days_active', 0)}
- Weak Subjects: {', '.join(weak_subjects) if weak_subjects else 'None'}
- At-Risk: {'Yes' if student.get('at_risk', 0) == 1 else 'No'}
- Predicted Score: {student.get('predicted_score', 'N/A')}"""

    prompt = (
        "You are an academic advisor AI for a university student learning system.\n"
        "Based on the following student data, provide 3-5 specific, actionable, and encouraging "
        "recommendations to help this student improve their academic performance.\n"
        "Be concise, empathetic, and practical. Format each recommendation as a numbered point.\n\n"
        f"{summary}\n\nRecommendations:"
    )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
f"gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    )

    try:
        response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=20)
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except requests.exceptions.HTTPError as e:
        return f"Gemini API HTTP error: {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Gemini API error: {str(e)}"


# ══════════════════════════════════════════════════════
# COMBINED — called by FastAPI backend
# ══════════════════════════════════════════════════════

def get_recommendations(student: dict, use_ai: bool = True) -> dict:
    rule_recs = rule_based_recommendations(student)
    result = {
        "student_id": student.get("student_id", "unknown"),
        "at_risk": bool(student.get("at_risk", 0)),
        "rule_based": rule_recs,
        "ai_powered": None,
    }
    if use_ai:
        result["ai_powered"] = ai_recommendations(student)
    return result


# ══════════════════════════════════════════════════════
# STANDALONE TEST
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        master   = pd.read_csv(f"{CLEAN_DIR}/master_features.csv")
        scores   = pd.read_csv(f"{CLEAN_DIR}/scores_summary.csv")
        profiles = pd.read_csv(f"{CLEAN_DIR}/student_profiles_clean.csv")

        merged = master.merge(scores[["student_id", "weak_subjects"]], on="student_id", how="left")
        merged = merged.merge(profiles[["student_id", "department"]], on="student_id", how="left")

        test_student = merged[merged["at_risk"] == 1].iloc[0].to_dict()

        print(f"\nStudent : {test_student['student_id']}")
        print(f"Attendance: {test_student['attendance_rate']*100:.1f}% | Avg Score: {test_student['avg_score']:.1f}%\n")

        result = get_recommendations(test_student, use_ai=bool(GEMINI_API_KEY))

        print("── Rule-Based Recommendations ───────────────────")
        for rec in result["rule_based"]:
            print(f"\n[{rec['priority']}] {rec['category']}")
            print(f"  {rec['message']}")

        if result["ai_powered"]:
            print("\n── AI Recommendations (Gemini) ──────────────────")
            print(result["ai_powered"])

        print("\n✓ Recommendation engine working correctly.")

    except FileNotFoundError:
        demo = {
            "student_id": "STU0001", "attendance_rate": 0.55, "avg_score": 42.0,
            "min_score": 28.0, "std_score": 18.5, "total_sessions": 25,
            "unique_days_active": 15, "total_minutes": 420,
            "weak_subjects": ["Math", "Physics"], "enrollment_year": 2023,
            "department": "Computer Science", "at_risk": 1,
        }
        result = get_recommendations(demo, use_ai=False)
        print(f"\nDemo student: {demo['student_id']}")
        print("── Rule-Based Recommendations ───────────────────")
        for rec in result["rule_based"]:
            print(f"\n[{rec['priority']}] {rec['category']}")
            print(f"  {rec['message']}")
        print("\n✓ Recommendation engine working correctly.")
