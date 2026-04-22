#replaces scorer.py, which is now only used for the old scoring system


"""
Enhanced risk scoring using the enriched feature set.
"""

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


def _compute_feature_contributions(features: dict, weights: dict) -> tuple:
    """
    Compute risk contributions for each category.
    Returns (total_score, list_of_contributions).
    """
    # Authentication & identity
    auth_score = 0.0
    if features.get("auth_oauth2", False) or features.get("oauth_supported", False):
        auth_score = 0.0
    elif features.get("auth_basic", False):
        auth_score = 0.7
    elif features.get("auth_api_key", False):
        auth_score = 0.4
    else:
        auth_score = 1.0  # no authentication at all

    if features.get("mfa_available", False):
        auth_score *= 0.5

    # Encryption & TLS
    tls_score = 0.0
    tls_version = features.get("tls_version", "")
    if tls_version and "TLSv1.3" in tls_version:
        tls_score = 0.0
    elif tls_version and "TLSv1.2" in tls_version:
        tls_score = 0.3
    else:
        tls_score = 0.8

    if not features.get("has_https", False):
        tls_score = 1.0

    if not features.get("cert_valid", True):
        tls_score += 0.2

    # Security headers
    headers_score = 0.0
    if not features.get("hsts_enabled", False):
        headers_score += 0.25
    if not features.get("csp_enabled", False):
        headers_score += 0.25
    if not features.get("xframe_enabled", False):
        headers_score += 0.2
    if not features.get("xcontenttype_enabled", False):
        headers_score += 0.15
    if not features.get("referrer_policy_enabled", False):
        headers_score += 0.1
    if not features.get("permissions_policy_enabled", False):
        headers_score += 0.05
    headers_score = min(1.0, headers_score)

    # Vulnerabilities & reputation
    vuln_score = features.get("vulnerability_risk", 0.0)   # already 0-1
    rep_score = 1.0 - features.get("external_reputation_score", 0.5)

    # Compliance
    compliance_bonus = 0.0
    if features.get("gdpr_compliant", False):
        compliance_bonus += 0.1
    if features.get("iso27001_compliant", False):
        compliance_bonus += 0.1
    if features.get("soc2_compliant", False):
        compliance_bonus += 0.1

    # Weighted sum (weights can be configured in settings)
    w_auth = getattr(settings, "w_auth", 0.20)
    w_tls = getattr(settings, "w_tls", 0.20)
    w_headers = getattr(settings, "w_headers", 0.15)
    w_vuln = getattr(settings, "w_vulnerabilities", 0.30)
    w_rep = getattr(settings, "w_reputation", 0.15)

    total = (w_auth * auth_score +
             w_tls * tls_score +
             w_headers * headers_score +
             w_vuln * vuln_score +
             w_rep * rep_score)

    # Apply compliance bonus (reduce total)
    total = max(0.0, min(1.0, total - compliance_bonus))

    contributions = [
        {"component": "authentication", "value": round(auth_score, 4), "weight": w_auth, "contribution": round(w_auth * auth_score, 4)},
        {"component": "encryption_tls", "value": round(tls_score, 4), "weight": w_tls, "contribution": round(w_tls * tls_score, 4)},
        {"component": "security_headers", "value": round(headers_score, 4), "weight": w_headers, "contribution": round(w_headers * headers_score, 4)},
        {"component": "vulnerabilities", "value": round(vuln_score, 4), "weight": w_vuln, "contribution": round(w_vuln * vuln_score, 4)},
        {"component": "external_reputation", "value": round(rep_score, 4), "weight": w_rep, "contribution": round(w_rep * rep_score, 4)},
        {"component": "compliance_bonus", "value": compliance_bonus, "weight": -1, "contribution": round(-compliance_bonus, 4)},
    ]
    return total, contributions


def score_risk(features: dict) -> dict:
    """
    Main scoring function. Features should include all collected fields.
    """
    base_score, contributions = _compute_feature_contributions(features, {})

    # ML prediction (optional)
    ml = predict_risk_with_ml(features)

    if ml is not None:
        alpha = getattr(settings, "ml_weight", 0.3)
        risk_score = round(alpha * ml["risk_score_ml"] + (1 - alpha) * base_score, 4)
        model_source = "hybrid_ml_rules"
    else:
        risk_score = round(base_score, 4)
        model_source = "rules_only"

    level = classify(risk_score)
    decision = decision_from_level(level)

    # Confidence based on data completeness
    completeness = float(features.get("data_completeness_score", 0.5))
    confidence = 0.45 + 0.45 * completeness
    if features.get("blacklist_flag", False):
        confidence += 0.03
    if features.get("cert_valid", False) and features.get("has_https", False):
        confidence += 0.02
    confidence = round(min(0.95, max(0.0, confidence)), 4)

    out = {
        "risk_score": risk_score,
        "risk_level": level,
        "decision": decision,
        "confidence": confidence,
        "contributions": contributions,
        "model_source": model_source,
    }
    if ml is not None:
        out["ml"] = ml
    return out