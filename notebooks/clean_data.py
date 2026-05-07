import pandas as pd
import numpy as np
import os

RAW_DIR    = "data/raw"
CLEAN_DIR  = "data/cleaned"
os.makedirs(CLEAN_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# Load raw datasets
# ─────────────────────────────────────────────
profiles   = pd.read_csv(f"{RAW_DIR}/student_profiles.csv")
attendance = pd.read_csv(f"{RAW_DIR}/attendance.csv")
scores     = pd.read_csv(f"{RAW_DIR}/scores.csv")
activity   = pd.read_csv(f"{RAW_DIR}/activity_logs.csv")

# ─────────────────────────────────────────────
# Clean: Student Profiles
# ─────────────────────────────────────────────
profiles["age"] = profiles["age"].clip(15, 35)           # remove impossible ages
profiles["gender"] = profiles["gender"].str.strip()
profiles["department"] = profiles["department"].str.strip()
profiles = profiles.drop_duplicates(subset="student_id")

# Encode gender and department
profiles["gender_encoded"] = profiles["gender"].map({"Male": 0, "Female": 1, "Other": 2})
profiles["dept_encoded"]   = profiles["department"].astype("category").cat.codes

profiles.to_csv(f"{CLEAN_DIR}/student_profiles_clean.csv", index=False)
print(f"Profiles cleaned   → {len(profiles)} rows")

# ─────────────────────────────────────────────
# Clean + Feature Engineer: Attendance
# ─────────────────────────────────────────────
attendance["date"]    = pd.to_datetime(attendance["date"])
attendance["present"] = attendance["present"].astype(int)
attendance = attendance.dropna()

# Per-student attendance rate
att_summary = (
    attendance.groupby("student_id")["present"]
    .agg(total_days="count", days_present="sum")
    .reset_index()
)
att_summary["attendance_rate"] = (att_summary["days_present"] / att_summary["total_days"]).round(4)

att_summary.to_csv(f"{CLEAN_DIR}/attendance_summary.csv", index=False)
attendance.to_csv(f"{CLEAN_DIR}/attendance_clean.csv", index=False)
print(f"Attendance cleaned → {len(attendance)} rows | summary: {len(att_summary)} students")

# ─────────────────────────────────────────────
# Clean + Feature Engineer: Scores
# ─────────────────────────────────────────────
scores = scores.dropna()
scores["score"]       = scores["score"].clip(0, scores["max_score"])
scores["score_pct"]   = (scores["score"] / scores["max_score"] * 100).round(2)

# Per-student score summaries
score_summary = (
    scores.groupby("student_id")["score_pct"]
    .agg(avg_score="mean", min_score="min", max_score="max", std_score="std")
    .reset_index()
    .round(2)
)

# Per-subject average (for weak-subject detection)
subject_scores = (
    scores.groupby(["student_id", "subject"])["score_pct"]
    .mean()
    .reset_index()
    .rename(columns={"score_pct": "avg_subject_score"})
    .round(2)
)
weak_subjects = (
    subject_scores[subject_scores["avg_subject_score"] < 50]
    .groupby("student_id")["subject"]
    .apply(list)
    .reset_index()
    .rename(columns={"subject": "weak_subjects"})
)

score_summary = score_summary.merge(weak_subjects, on="student_id", how="left")
score_summary["weak_subjects"] = score_summary["weak_subjects"].apply(
    lambda x: x if isinstance(x, list) else []
)

scores.to_csv(f"{CLEAN_DIR}/scores_clean.csv", index=False)
score_summary.to_csv(f"{CLEAN_DIR}/scores_summary.csv", index=False)
print(f"Scores cleaned     → {len(scores)} rows | summary: {len(score_summary)} students")

# ─────────────────────────────────────────────
# Clean + Feature Engineer: Activity Logs
# ─────────────────────────────────────────────
activity["date"]             = pd.to_datetime(activity["date"])
activity["duration_minutes"] = activity["duration_minutes"].clip(0, 300)
activity = activity.dropna()

activity_summary = (
    activity.groupby("student_id")
    .agg(
        total_sessions=("activity_type", "count"),
        total_minutes=("duration_minutes", "sum"),
        avg_session_duration=("duration_minutes", "mean"),
        unique_days_active=("date", "nunique"),
    )
    .reset_index()
    .round(2)
)

activity.to_csv(f"{CLEAN_DIR}/activity_logs_clean.csv", index=False)
activity_summary.to_csv(f"{CLEAN_DIR}/activity_summary.csv", index=False)
print(f"Activity cleaned   → {len(activity)} rows | summary: {len(activity_summary)} students")

# ─────────────────────────────────────────────
# Master Feature Table (used for ML in Phase 3)
# ─────────────────────────────────────────────
master = profiles[["student_id", "age", "gender_encoded", "dept_encoded", "enrollment_year"]].copy()
master = master.merge(att_summary[["student_id", "attendance_rate"]], on="student_id", how="left")
master = master.merge(score_summary[["student_id", "avg_score", "min_score", "std_score"]], on="student_id", how="left")
master = master.merge(activity_summary[["student_id", "total_sessions", "total_minutes", "unique_days_active"]], on="student_id", how="left")

# Risk label: at-risk if attendance < 65% OR avg_score < 45
master["at_risk"] = (
    (master["attendance_rate"] < 0.65) | (master["avg_score"] < 45)
).astype(int)

master = master.fillna(0)
master.to_csv(f"{CLEAN_DIR}/master_features.csv", index=False)

# Summary report
total   = len(master)
at_risk = master["at_risk"].sum()
print(f"\nMaster feature table → {total} students")
print(f"  At-risk students   → {at_risk} ({at_risk/total*100:.1f}%)")
print(f"  Safe students      → {total - at_risk} ({(total-at_risk)/total*100:.1f}%)")
print(f"\n✓ All cleaned datasets saved to {CLEAN_DIR}")
print("\nFeature columns:", list(master.columns))
