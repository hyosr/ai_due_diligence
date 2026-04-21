import os
import joblib
import numpy as np
from typing import Dict, Any, Optional

from app.services.ml_features import vectorize_features

_MODEL = None
_MODEL_VERSION = "ml-risk-v1"
_MODEL_PATH = os.getenv("ML_MODEL_PATH", "artifacts/risk_model.joblib")


def _load_model():
    global _MODEL
    if _MODEL is None and os.path.exists(_MODEL_PATH):
        _MODEL = joblib.load(_MODEL_PATH)
    return _MODEL


def predict_risk_with_ml(features: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    model = _load_model()
    if model is None:
        return None

    x = np.array([vectorize_features(features)], dtype=float)

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(x)[0]  # [LOW, MEDIUM, HIGH]
        p_low, p_med, p_high = float(proba[0]), float(proba[1]), float(proba[2])
        risk_score = p_med * 0.5 + p_high * 1.0
        pred_class = int(np.argmax(proba))
    else:
        pred_class = int(model.predict(x)[0])
        p_low = 1.0 if pred_class == 0 else 0.0
        p_med = 1.0 if pred_class == 1 else 0.0
        p_high = 1.0 if pred_class == 2 else 0.0
        risk_score = 0.5 if pred_class == 1 else (1.0 if pred_class == 2 else 0.0)

    return {
        "risk_score_ml": round(float(risk_score), 4),
        "class_probs": {
            "LOW": round(p_low, 4),
            "MEDIUM": round(p_med, 4),
            "HIGH": round(p_high, 4),
        },
        "predicted_class_idx": pred_class,
        "model_version": _MODEL_VERSION,
        "model_path": _MODEL_PATH
    }