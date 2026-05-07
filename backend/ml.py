"""
SLIS — ML model loader (singleton state)
"""

import joblib
import json
from pathlib import Path

_state: dict = {}

# Absolute path handling for Render
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models" / "saved"

def load_models():
    _state["regressor"] = joblib.load(
        MODEL_DIR / "performance_predictor.joblib"
    )

    _state["classifier"] = joblib.load(
        MODEL_DIR / "risk_classifier.joblib"
    )

    with open(MODEL_DIR / "model_meta.json") as f:
        _state["meta"] = json.load(f)

    print("✓ Models loaded")


def get_regressor():
    return _state["regressor"]


def get_classifier():
    return _state["classifier"]


def get_features() -> list[str]:
    return _state["meta"]["features"]


def get_meta() -> dict:
    return _state["meta"]