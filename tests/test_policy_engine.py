from app.services.policy_engine import evaluate_policies


def test_p001_blacklist_block():
    scored = {"risk_score": 0.2, "decision": "ALLOW", "confidence": 0.9}
    features = {"blacklist": 1.0, "has_https": 1, "ssl_valid": 1, "weak_auth": 0.0, "compliance_bonus": 1.0}
    out = evaluate_policies(scored, features, {"service_type": "SaaS"})
    assert out["policy_id"] == "P-001"
    assert out["decision"] == "BLOCK"


def test_p002_no_https_ssl_block():
    scored = {"risk_score": 0.3, "decision": "ALLOW", "confidence": 0.8}
    features = {"blacklist": 0.0, "has_https": 0, "ssl_valid": 0, "weak_auth": 0.0, "compliance_bonus": 1.0}
    out = evaluate_policies(scored, features, {"service_type": "SaaS"})
    assert out["policy_id"] == "P-002"
    assert out["decision"] == "BLOCK"


def test_p003_weak_auth_aiapi_review():
    scored = {"risk_score": 0.2, "decision": "ALLOW", "confidence": 0.9}
    features = {"blacklist": 0.0, "has_https": 1, "ssl_valid": 1, "weak_auth": 1.0, "compliance_bonus": 1.0}
    out = evaluate_policies(scored, features, {"service_type": "AI API"})
    assert out["policy_id"] == "P-003"
    assert out["decision"] == "REVIEW"


def test_p005_low_confidence_review():
    scored = {"risk_score": 0.1, "decision": "ALLOW", "confidence": 0.55}
    features = {"blacklist": 0.0, "has_https": 1, "ssl_valid": 1, "weak_auth": 0.0, "compliance_bonus": 1.0}
    out = evaluate_policies(scored, features, {"service_type": "SaaS"})
    assert out["policy_id"] == "P-005"
    assert out["decision"] == "REVIEW"


def test_default_policy():
    scored = {"risk_score": 0.1, "decision": "ALLOW", "confidence": 0.9}
    features = {"blacklist": 0.0, "has_https": 1, "ssl_valid": 1, "weak_auth": 0.0, "compliance_bonus": 1.0}
    out = evaluate_policies(scored, features, {"service_type": "SaaS"})
    assert out["policy_id"] == "P-000"
    assert out["decision"] == "ALLOW"