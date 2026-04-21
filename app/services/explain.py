def build_reasons(features: dict, scored: dict) -> list[str]:
    reasons = []

    if features.get("has_https") == 0:
        reasons.append("No HTTPS detected")
    if features.get("ssl_valid") == 0:
        reasons.append("SSL certificate missing or invalid")
    if features.get("weak_auth") == 1.0:
        reasons.append("Weak or missing authentication method")
    if features.get("vulnerability_risk", 0) >= 0.2:
        reasons.append("Known vulnerabilities detected")
    if features.get("blacklist") == 1.0:
        reasons.append("Service is flagged in blacklist")
    if features.get("reputation_risk", 0) >= 0.5:
        reasons.append("Low external reputation score")
    if features.get("compliance_bonus", 0) < 0.5:
        reasons.append("Low compliance evidence (GDPR/ISO)")

    if not reasons:
        reasons.append("No critical risk factor detected")

    return reasons


def build_explainability(features: dict, scored: dict, reasons: list[str]) -> dict:
    return {
        "model_type": "rules_weighted_v1",
        "features": features,
        "scoring": scored,
        "reasons": reasons,
        "model_source": scored.get("model_source", "rules_only"),
        "ml": scored.get("ml"),
    }