from app.core.config import settings


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


def score_risk(features: dict) -> dict:
    wv = settings.w_vulnerabilities
    wc = settings.w_config
    wr = settings.w_reputation

    vuln_part = wv * features["vulnerability_risk"]
    conf_part = wc * features["config_risk"]
    rep_part = wr * features["reputation_risk"]
    compliance_reduction = 0.10 * features["compliance_bonus"]

    raw = vuln_part + conf_part + rep_part
    adjusted = max(0.0, min(1.0, raw - compliance_reduction))

    level = classify(adjusted)
    decision = decision_from_level(level)

    # -------- NEW confidence formula ----------
    completeness = float(features.get("data_completeness_score", 0.5))
    # base from completeness
    confidence = 0.45 + 0.45 * completeness  # range ~ [0.45, 0.90]
    # bonuses
    if features.get("blacklist") == 1.0 or features.get("whitelist") == 1.0:
        confidence += 0.03
    if features.get("ssl_valid") == 1 and features.get("has_https") == 1:
        confidence += 0.02
    confidence = round(min(0.95, max(0.0, confidence)), 4)

    contributions = [
        {"component": "vulnerability_risk", "value": features["vulnerability_risk"], "weight": wv, "contribution": round(vuln_part, 4)},
        {"component": "config_risk", "value": features["config_risk"], "weight": wc, "contribution": round(conf_part, 4)},
        {"component": "reputation_risk", "value": features["reputation_risk"], "weight": wr, "contribution": round(rep_part, 4)},
        {"component": "compliance_bonus_reduction", "value": features["compliance_bonus"], "weight": -0.10, "contribution": round(-compliance_reduction, 4)},
    ]

    return {
        "risk_score": round(adjusted, 4),
        "risk_level": level,
        "decision": decision,
        "confidence": confidence,
        "contributions": contributions
    }