from app.services.scorer import score_risk

def test_scoring_output_keys():
    features = {
        "vulnerability_risk": 0.3,
        "config_risk": 0.4,
        "reputation_risk": 0.5,
        "compliance_bonus": 0.2,
        "data_completeness_score": 0.9,
        "blacklist": 0.0,
        "whitelist": 0.0,
        "ssl_valid": 1,
        "has_https": 1,
    }
    out = score_risk(features)
    assert "risk_score" in out
    assert "risk_level" in out
    assert "decision" in out
    assert "model_source" in out