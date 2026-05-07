import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os

# ── Setup ──────────────────────────────────────────────
CLEAN_DIR = "data/cleaned"
PLOT_DIR  = "eda/plots"
os.makedirs(PLOT_DIR, exist_ok=True)

master   = pd.read_csv(f"{CLEAN_DIR}/master_features.csv")
profiles = pd.read_csv(f"{CLEAN_DIR}/student_profiles_clean.csv")
scores   = pd.read_csv(f"{CLEAN_DIR}/scores_clean.csv")

master_full = master.merge(profiles[["student_id", "department"]], on="student_id", how="left")

PALETTE = {0: "#4A90D9", 1: "#E05C5C"}
RISK_LABELS = {0: "Safe", 1: "At-Risk"}

sns.set_theme(style="whitegrid", font_scale=1.1)

def save(fig, name):
    path = f"{PLOT_DIR}/{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved → {name}.png")

# ── 1. Score Distribution ──────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
colors = [PALETTE[r] for r in master["at_risk"]]
ax.hist(master[master["at_risk"]==0]["avg_score"], bins=20, color=PALETTE[0], alpha=0.75, label="Safe")
ax.hist(master[master["at_risk"]==1]["avg_score"], bins=20, color=PALETTE[1], alpha=0.75, label="At-Risk")
ax.axvline(45, color="black", linestyle="--", linewidth=1.2, label="Risk threshold (45)")
ax.set_title("Average Score Distribution")
ax.set_xlabel("Average Score (%)")
ax.set_ylabel("Number of Students")
ax.legend()
save(fig, "1_score_distribution")

# ── 2. Attendance Rate Distribution ───────────────────
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(master[master["at_risk"]==0]["attendance_rate"], bins=20, color=PALETTE[0], alpha=0.75, label="Safe")
ax.hist(master[master["at_risk"]==1]["attendance_rate"], bins=20, color=PALETTE[1], alpha=0.75, label="At-Risk")
ax.axvline(0.65, color="black", linestyle="--", linewidth=1.2, label="Risk threshold (65%)")
ax.set_title("Attendance Rate Distribution")
ax.set_xlabel("Attendance Rate")
ax.set_ylabel("Number of Students")
ax.legend()
save(fig, "2_attendance_distribution")

# ── 3. Attendance vs. Score Scatter ───────────────────
fig, ax = plt.subplots(figsize=(8, 6))
for risk, grp in master.groupby("at_risk"):
    ax.scatter(
        grp["attendance_rate"], grp["avg_score"],
        c=PALETTE[risk], label=RISK_LABELS[risk],
        alpha=0.7, edgecolors="white", linewidth=0.4, s=60
    )
ax.axvline(0.65, color="gray", linestyle="--", linewidth=1, alpha=0.6)
ax.axhline(45,   color="gray", linestyle="--", linewidth=1, alpha=0.6)
ax.set_title("Attendance Rate vs. Average Score")
ax.set_xlabel("Attendance Rate")
ax.set_ylabel("Average Score (%)")
ax.legend()
save(fig, "3_attendance_vs_score")

# ── 4. Correlation Heatmap ────────────────────────────
fig, ax = plt.subplots(figsize=(10, 8))
numeric_cols = ["attendance_rate", "avg_score", "min_score", "std_score",
                "total_sessions", "total_minutes", "unique_days_active", "at_risk"]
corr = master[numeric_cols].corr().round(2)
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(
    corr, mask=mask, annot=True, fmt=".2f",
    cmap="coolwarm", center=0, linewidths=0.5,
    ax=ax, cbar_kws={"shrink": 0.8}
)
ax.set_title("Feature Correlation Heatmap")
save(fig, "4_correlation_heatmap")

# ── 5. At-Risk by Department ──────────────────────────
dept_risk = (
    master_full.groupby(["department", "at_risk"])
    .size()
    .unstack(fill_value=0)
    .rename(columns=RISK_LABELS)
    .reset_index()
)
fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(dept_risk))
width = 0.4
ax.bar(x - width/2, dept_risk["Safe"],    width, color=PALETTE[0], label="Safe")
ax.bar(x + width/2, dept_risk["At-Risk"], width, color=PALETTE[1], label="At-Risk")
ax.set_xticks(x)
ax.set_xticklabels(dept_risk["department"], rotation=20, ha="right")
ax.set_title("At-Risk vs. Safe Students by Department")
ax.set_ylabel("Number of Students")
ax.legend()
save(fig, "5_risk_by_department")

# ── 6. Activity Sessions vs. Score ────────────────────
fig, ax = plt.subplots(figsize=(8, 6))
for risk, grp in master.groupby("at_risk"):
    ax.scatter(
        grp["total_sessions"], grp["avg_score"],
        c=PALETTE[risk], label=RISK_LABELS[risk],
        alpha=0.7, edgecolors="white", linewidth=0.4, s=60
    )
ax.set_title("Total Activity Sessions vs. Average Score")
ax.set_xlabel("Total Sessions")
ax.set_ylabel("Average Score (%)")
ax.legend()
save(fig, "6_activity_vs_score")

# ── 7. Subject-wise Average Scores ────────────────────
subject_avg = (
    scores.groupby("subject")["score_pct"]
    .agg(["mean", "std"])
    .reset_index()
    .sort_values("mean")
)
fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.barh(subject_avg["subject"], subject_avg["mean"], color="#4A90D9", alpha=0.85)
ax.errorbar(
    subject_avg["mean"], subject_avg["subject"],
    xerr=subject_avg["std"], fmt="none", color="gray", capsize=4, linewidth=1
)
ax.axvline(50, color="#E05C5C", linestyle="--", linewidth=1.2, label="Pass mark (50)")
ax.set_title("Average Score per Subject (with Std Dev)")
ax.set_xlabel("Average Score (%)")
ax.legend()
save(fig, "7_subject_avg_scores")

# ── 8. Enrollment Year vs. Avg Score ──────────────────
fig, ax = plt.subplots(figsize=(8, 5))
sns.boxplot(
    data=master_full, x="enrollment_year", y="avg_score",
    palette="Blues", ax=ax
)
ax.axhline(45, color="#E05C5C", linestyle="--", linewidth=1.2, label="Risk threshold")
ax.set_title("Score Distribution by Enrollment Year")
ax.set_xlabel("Enrollment Year")
ax.set_ylabel("Average Score (%)")
ax.legend()
save(fig, "8_score_by_enrollment_year")

# ── Summary Stats ──────────────────────────────────────
print("\n── EDA Summary ──────────────────────────────")
print(f"Total students      : {len(master)}")
print(f"At-risk             : {master['at_risk'].sum()} ({master['at_risk'].mean()*100:.1f}%)")
print(f"Avg attendance rate : {master['attendance_rate'].mean():.2%}")
print(f"Avg score           : {master['avg_score'].mean():.1f}%")
print(f"Avg total sessions  : {master['total_sessions'].mean():.0f}")
print(f"\nCorrelation with at_risk:")
for col in ["attendance_rate", "avg_score", "total_sessions", "total_minutes"]:
    print(f"  {col:<25}: {master[col].corr(master['at_risk']):.3f}")
print("\n✓ All 8 plots saved.")
