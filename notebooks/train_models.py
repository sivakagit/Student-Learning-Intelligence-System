"""
SLIS — Phase 3: ML Models
  Model 1: Performance Predictor  (Regression  → predicts avg_score)
  Model 2: Risk Classifier        (Classification → predicts at_risk)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib, os

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    mean_squared_error, r2_score, mean_absolute_error,
    classification_report, confusion_matrix,
    roc_auc_score, roc_curve, ConfusionMatrixDisplay
)
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import Ridge, LogisticRegression
from xgboost import XGBRegressor, XGBClassifier

# ── Paths ──────────────────────────────────────────────
CLEAN_DIR  = "data/cleaned"
MODEL_DIR  = "models/saved"
PLOT_DIR   = "models/plots"
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(PLOT_DIR,  exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.1)

def save_plot(fig, name):
    fig.savefig(f"{PLOT_DIR}/{name}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Plot saved → {name}.png")

# ── Load data ──────────────────────────────────────────
master = pd.read_csv(f"{CLEAN_DIR}/master_features.csv")

FEATURES = [
    "age", "gender_encoded", "dept_encoded", "enrollment_year",
    "attendance_rate", "min_score", "std_score",
    "total_sessions", "total_minutes", "unique_days_active"
]
TARGET_REG  = "avg_score"
TARGET_CLF  = "at_risk"

X    = master[FEATURES]
y_r  = master[TARGET_REG]
y_c  = master[TARGET_CLF]

X_train, X_test, yr_train, yr_test, yc_train, yc_test = train_test_split(
    X, y_r, y_c, test_size=0.2, random_state=42, stratify=y_c
)

print(f"Train: {len(X_train)} | Test: {len(X_test)}")
print(f"At-risk in test: {yc_test.sum()} / {len(yc_test)}\n")

# ══════════════════════════════════════════════════════
# MODEL 1 — Performance Predictor (Regression)
# ══════════════════════════════════════════════════════
print("=" * 50)
print("MODEL 1: Performance Predictor (Regression)")
print("=" * 50)

reg_models = {
    "Ridge Regression": Pipeline([("scaler", StandardScaler()), ("model", Ridge(alpha=1.0))]),
    "Random Forest":    RandomForestRegressor(n_estimators=100, random_state=42),
    "XGBoost":          XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42, verbosity=0),
}

reg_results = {}
for name, model in reg_models.items():
    model.fit(X_train, yr_train)
    preds = model.predict(X_test)
    rmse  = np.sqrt(mean_squared_error(yr_test, preds))
    mae   = mean_absolute_error(yr_test, preds)
    r2    = r2_score(yr_test, preds)
    cv    = cross_val_score(model, X, y_r, cv=5, scoring="r2").mean()
    reg_results[name] = {"RMSE": rmse, "MAE": mae, "R2": r2, "CV_R2": cv}
    print(f"\n{name}")
    print(f"  RMSE: {rmse:.2f} | MAE: {mae:.2f} | R²: {r2:.3f} | CV R²: {cv:.3f}")

# Pick best by CV R²
best_reg_name = max(reg_results, key=lambda k: reg_results[k]["CV_R2"])
best_reg      = reg_models[best_reg_name]
print(f"\n✓ Best regression model: {best_reg_name}")

# Save best model
joblib.dump(best_reg, f"{MODEL_DIR}/performance_predictor.joblib")
print(f"  Saved → performance_predictor.joblib")

# Plot: Actual vs Predicted
preds_best = best_reg.predict(X_test)
fig, ax = plt.subplots(figsize=(7, 6))
ax.scatter(yr_test, preds_best, alpha=0.6, color="#4A90D9", edgecolors="white", s=60)
lims = [min(yr_test.min(), preds_best.min()) - 2, max(yr_test.max(), preds_best.max()) + 2]
ax.plot(lims, lims, "r--", linewidth=1.5, label="Perfect prediction")
ax.set_xlabel("Actual Score (%)")
ax.set_ylabel("Predicted Score (%)")
ax.set_title(f"Actual vs Predicted Score ({best_reg_name})\nR² = {reg_results[best_reg_name]['R2']:.3f}")
ax.legend()
save_plot(fig, "reg_actual_vs_predicted")

# Plot: Feature importance (Random Forest)
rf_reg = reg_models["Random Forest"]
importances = pd.Series(rf_reg.feature_importances_, index=FEATURES).sort_values()
fig, ax = plt.subplots(figsize=(8, 5))
importances.plot(kind="barh", color="#4A90D9", ax=ax)
ax.set_title("Feature Importance — Performance Predictor (Random Forest)")
ax.set_xlabel("Importance Score")
save_plot(fig, "reg_feature_importance")

# ══════════════════════════════════════════════════════
# MODEL 2 — Risk Classifier (Classification)
# ══════════════════════════════════════════════════════
print("\n" + "=" * 50)
print("MODEL 2: Risk Classifier (Classification)")
print("=" * 50)

clf_models = {
    "Logistic Regression": Pipeline([("scaler", StandardScaler()), ("model", LogisticRegression(random_state=42, max_iter=500))]),
    "Random Forest":       RandomForestClassifier(n_estimators=100, random_state=42),
    "XGBoost":             XGBClassifier(n_estimators=100, learning_rate=0.1, random_state=42, verbosity=0, eval_metric="logloss"),
}

clf_results = {}
for name, model in clf_models.items():
    model.fit(X_train, yc_train)
    preds  = model.predict(X_test)
    proba  = model.predict_proba(X_test)[:, 1]
    auc    = roc_auc_score(yc_test, proba)
    cv_auc = cross_val_score(model, X, y_c, cv=5, scoring="roc_auc").mean()
    clf_results[name] = {"AUC": auc, "CV_AUC": cv_auc, "preds": preds, "proba": proba}
    print(f"\n{name}")
    print(f"  ROC-AUC: {auc:.3f} | CV AUC: {cv_auc:.3f}")
    print(classification_report(yc_test, preds, target_names=["Safe", "At-Risk"], zero_division=0))

# Pick best by CV AUC
best_clf_name = max(clf_results, key=lambda k: clf_results[k]["CV_AUC"])
best_clf      = clf_models[best_clf_name]
print(f"\n✓ Best classifier: {best_clf_name}")

# Save best model
joblib.dump(best_clf, f"{MODEL_DIR}/risk_classifier.joblib")
print(f"  Saved → risk_classifier.joblib")

# Plot: Confusion Matrix
best_preds = clf_results[best_clf_name]["preds"]
fig, ax = plt.subplots(figsize=(6, 5))
ConfusionMatrixDisplay(
    confusion_matrix(yc_test, best_preds),
    display_labels=["Safe", "At-Risk"]
).plot(ax=ax, colorbar=False, cmap="Blues")
ax.set_title(f"Confusion Matrix — {best_clf_name}")
save_plot(fig, "clf_confusion_matrix")

# Plot: ROC Curve (all classifiers)
fig, ax = plt.subplots(figsize=(7, 6))
for name, res in clf_results.items():
    fpr, tpr, _ = roc_curve(yc_test, res["proba"])
    ax.plot(fpr, tpr, linewidth=2, label=f"{name} (AUC={res['AUC']:.3f})")
ax.plot([0,1],[0,1], "k--", linewidth=1)
ax.set_xlabel("False Positive Rate")
ax.set_ylabel("True Positive Rate")
ax.set_title("ROC Curves — Risk Classifier")
ax.legend(loc="lower right")
save_plot(fig, "clf_roc_curves")

# Plot: Feature importance (Random Forest classifier)
rf_clf = clf_models["Random Forest"]
importances_c = pd.Series(rf_clf.feature_importances_, index=FEATURES).sort_values()
fig, ax = plt.subplots(figsize=(8, 5))
importances_c.plot(kind="barh", color="#E05C5C", ax=ax)
ax.set_title("Feature Importance — Risk Classifier (Random Forest)")
ax.set_xlabel("Importance Score")
save_plot(fig, "clf_feature_importance")

# ── Save feature list for API ──────────────────────────
import json
meta = {
    "features": FEATURES,
    "best_regressor": best_reg_name,
    "best_classifier": best_clf_name,
    "reg_metrics": {k: {m: round(v, 4) for m, v in vals.items() if m != "preds"} for k, vals in reg_results.items()},
    "clf_metrics": {k: {"AUC": round(v["AUC"], 4), "CV_AUC": round(v["CV_AUC"], 4)} for k, v in clf_results.items()},
}
with open(f"{MODEL_DIR}/model_meta.json", "w") as f:
    json.dump(meta, f, indent=2)
print(f"\n✓ Model metadata saved → model_meta.json")
print("\n✓ Phase 3 complete. Models ready for API integration.")
