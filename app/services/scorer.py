from app.core.config import settings
from app.services.ml_model import predict_risk_with_ml


def classify(risk_score: float) -> str:
    if risk_score >= settings.threshold_high:
        return "HIGH"
    if risk_score >= settings.threshold_medium:
        return "MEDIUM"
    return "LOW"


def decision_from_level(level: str) -> str:
    if level == "HIGH":
        return "BLOCK"
    if level == "MEDIUM":
        return "REVIEW"
    return "ALLOW"


def _rule_score(features: dict):
    wv = settings.w_vulnerabilities
    wc = settings.w_config
    wr = settings.w_reputation

    vuln_part = wv * features["vulnerability_risk"]
    conf_part = wc * features["config_risk"]
    rep_part = wr * features["reputation_risk"]
    compliance_reduction = 0.10 * features["compliance_bonus"]

    raw = vuln_part + conf_part + rep_part
    adjusted = max(0.0, min(1.0, raw - compliance_reduction))

    contributions = [
        {"component": "vulnerability_risk", "value": features["vulnerability_risk"], "weight": wv, "contribution": round(vuln_part, 4)},
        {"component": "config_risk", "value": features["config_risk"], "weight": wc, "contribution": round(conf_part, 4)},
        {"component": "reputation_risk", "value": features["reputation_risk"], "weight": wr, "contribution": round(rep_part, 4)},
        {"component": "compliance_bonus_reduction", "value": features["compliance_bonus"], "weight": -0.10, "contribution": round(-compliance_reduction, 4)},
    ]
    return adjusted, contributions


def score_risk(features: dict) -> dict:
    base_score, contributions = _rule_score(features)

    # ML prediction (optional)
    ml = predict_risk_with_ml(features)

    if ml is not None:
        # hybrid blend
        # alpha = 0.65  # weight ML
        alpha = 0.3

        risk_score = round(alpha * ml["risk_score_ml"] + (1 - alpha) * base_score, 4)
        model_source = "hybrid_ml_rules"
    else:
        risk_score = round(base_score, 4)
        model_source = "rules_only"

    level = classify(risk_score)
    decision = decision_from_level(level)

    completeness = float(features.get("data_completeness_score", 0.5))
    confidence = 0.45 + 0.45 * completeness
    if features.get("blacklist") == 1.0 or features.get("whitelist") == 1.0:
        confidence += 0.03
    if features.get("ssl_valid") == 1 and features.get("has_https") == 1:
        confidence += 0.02
    confidence = round(min(0.95, max(0.0, confidence)), 4)




    out = {
        "risk_score": risk_score,
        "risk_level": level,
        "decision": decision,
        "confidence": confidence,
        "contributions": contributions,
        "model_source": model_source
    }

    if ml is not None:
        out["ml"] = ml
        

    return out