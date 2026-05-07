import pandas as pd
import numpy as np
from faker import Faker
from datetime import date, timedelta
import os

fake = Faker()
np.random.seed(42)
Faker.seed(42)

OUTPUT_DIR = "data/raw"
os.makedirs(OUTPUT_DIR, exist_ok=True)

NUM_STUDENTS = 200
DEPARTMENTS = ["Computer Science", "Mathematics", "Physics", "Electronics", "Civil Engineering"]
SUBJECTS = ["Math", "Physics", "Programming", "Data Structures", "English", "Statistics"]
EXAM_TYPES = ["quiz", "midterm", "final"]
ACTIVITY_TYPES = ["login", "submission", "quiz_attempt", "video_watched", "forum_post"]

# ─────────────────────────────────────────────
# 1. Student Profiles
# ─────────────────────────────────────────────
student_ids = [f"STU{str(i).zfill(4)}" for i in range(1, NUM_STUDENTS + 1)]

profiles = pd.DataFrame({
    "student_id": student_ids,
    "name": [fake.name() for _ in range(NUM_STUDENTS)],
    "age": np.random.randint(17, 25, NUM_STUDENTS),
    "gender": np.random.choice(["Male", "Female", "Other"], NUM_STUDENTS, p=[0.48, 0.48, 0.04]),
    "department": np.random.choice(DEPARTMENTS, NUM_STUDENTS),
    "enrollment_year": np.random.choice([2021, 2022, 2023, 2024], NUM_STUDENTS, p=[0.2, 0.25, 0.3, 0.25]),
    "email": [fake.email() for _ in range(NUM_STUDENTS)],
})

profiles.to_csv(f"{OUTPUT_DIR}/student_profiles.csv", index=False)
print(f"student_profiles.csv → {len(profiles)} rows")

# ─────────────────────────────────────────────
# 2. Attendance
# ─────────────────────────────────────────────
start_date = date(2024, 1, 1)
end_date   = date(2024, 5, 31)
working_days = [
    start_date + timedelta(d)
    for d in range((end_date - start_date).days + 1)
    if (start_date + timedelta(d)).weekday() < 5  # Mon–Fri
]

# Each student has a personal "base attendance probability" — drives risk later
student_attendance_prob = {
    sid: np.clip(np.random.normal(0.78, 0.15), 0.2, 1.0)
    for sid in student_ids
}

attendance_rows = []
for sid in student_ids:
    prob = student_attendance_prob[sid]
    for day in working_days:
        attendance_rows.append({
            "student_id": sid,
            "date": day.isoformat(),
            "present": int(np.random.rand() < prob),
        })

attendance = pd.DataFrame(attendance_rows)
attendance.to_csv(f"{OUTPUT_DIR}/attendance.csv", index=False)
print(f"attendance.csv       → {len(attendance)} rows")

# ─────────────────────────────────────────────
# 3. Scores
# ─────────────────────────────────────────────
# Student's "ability" correlates with attendance so risk signals are realistic
student_ability = {
    sid: np.clip(student_attendance_prob[sid] * 100 + np.random.normal(0, 10), 20, 100)
    for sid in student_ids
}

score_rows = []
for sid in student_ids:
    ability = student_ability[sid]
    for subject in SUBJECTS:
        for exam in EXAM_TYPES:
            max_score = 100
            raw = ability + np.random.normal(0, 8)
            score = int(np.clip(raw, 0, 100))
            score_rows.append({
                "student_id": sid,
                "subject": subject,
                "exam_type": exam,
                "score": score,
                "max_score": max_score,
            })

scores = pd.DataFrame(score_rows)
scores.to_csv(f"{OUTPUT_DIR}/scores.csv", index=False)
print(f"scores.csv           → {len(scores)} rows")

# ─────────────────────────────────────────────
# 4. Activity Logs
# ─────────────────────────────────────────────
activity_rows = []
for sid in student_ids:
    # More active students log more sessions
    base_prob = student_attendance_prob[sid]
    num_sessions = int(np.clip(np.random.normal(base_prob * 120, 20), 10, 180))
    for _ in range(num_sessions):
        rand_day = np.random.choice(working_days)
        activity_rows.append({
            "student_id": sid,
            "date": rand_day.isoformat(),
            "activity_type": np.random.choice(ACTIVITY_TYPES, p=[0.3, 0.25, 0.2, 0.15, 0.1]),
            "duration_minutes": int(np.clip(np.random.exponential(20), 1, 120)),
        })

activity = pd.DataFrame(activity_rows)
activity.to_csv(f"{OUTPUT_DIR}/activity_logs.csv", index=False)
print(f"activity_logs.csv    → {len(activity)} rows")

print("\n✓ All raw datasets generated.")
