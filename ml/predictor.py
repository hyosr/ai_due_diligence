# ml/predictor.py
import joblib
import numpy as np
import os

# Chargement global (fait une seule fois au démarrage)
_model = None
_scaler = None

def _load_model():
    global _model, _scaler
    if _model is None:
        model_path = "ml/model.pkl"
        scaler_path = "ml/scaler.pkl"
        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            raise RuntimeError("Modèle non trouvé. Exécutez d'abord train_model.py")
        _model = joblib.load(model_path)
        _scaler = joblib.load(scaler_path)
    return _model, _scaler

def compute_auth_strength(auth_method: str) -> float:
    """Convertit la méthode d'auth en score numérique (0-1)"""
    mapping = {
        "oauth2": 0.9,
        "jwt": 0.8,
        "api_key": 0.6,
        "basic": 0.3,
        "none": 0.0
    }
    return mapping.get(auth_method.lower(), 0.5)

def predict_risk(features: dict) -> dict:
    """
    Entrée : dictionnaire contenant au minimum :
        - has_https (int 0/1)
        - ssl_valid (int 0/1)
        - auth_method (str)
        - num_vulns (int)
        - reputation (float 0-1)
        - compliance_score (float 0-1)
    Sortie : dict avec risk_score (float), risk_level (str)
    """
    model, scaler = _load_model()

    # Construire le vecteur de features dans l'ordre exact du training
    X = np.array([[
        features.get("has_https", 0),
        features.get("ssl_valid", 0),
        compute_auth_strength(features.get("auth_method", "none")),
        features.get("num_vulns", 0),
        features.get("reputation", 0.5),
        features.get("compliance_score", 0.5)
    ]])

    X_scaled = scaler.transform(X)
    prob_high = model.predict_proba(X_scaled)[0][1]  # probabilité d'être à risque élevé

    # Niveau de risque
    if prob_high < 0.3:
        risk_level = "LOW"
    elif prob_high < 0.7:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    return {
        "risk_score": float(prob_high),
        "risk_level": risk_level
    }

def explain_prediction(features: dict) -> list:
    """Génère une liste de raisons textuelles pour justifier le score"""
    reasons = []

    if features.get("auth_method") in ["basic", "none"]:
        reasons.append("Weak or missing authentication method")
    if features.get("num_vulns", 0) > 2:
        reasons.append("Known vulnerabilities detected")
    if features.get("reputation", 1) < 0.4:
        reasons.append("Low external reputation score")
    if features.get("compliance_score", 1) < 0.5:
        reasons.append("Low compliance evidence (GDPR/ISO)")
    if features.get("has_https", 1) == 0 or features.get("ssl_valid", 1) == 0:
        reasons.append("SSL certificate missing or invalid")
    if not reasons:
        reasons.append("No critical risk factor detected")

    return reasons