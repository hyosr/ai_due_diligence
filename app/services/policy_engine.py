from typing import Dict, Any, List


def evaluate_policies(scored: Dict[str, Any], features: Dict[str, Any], service_meta: Dict[str, Any]) -> Dict[str, Any]:
    matched: List[Dict[str, str]] = []

    if features.get("blacklist") == 1.0:
        matched.append({"policy_id": "P-001", "action": "BLOCK", "reason": "Service appears in blacklist."})
        return {"decision": "BLOCK", "policy_id": "P-001", "policy_reason": "Service appears in blacklist.", "matched_policies": matched}

    if features.get("has_https") == 0 and features.get("ssl_valid") == 0:
        matched.append({"policy_id": "P-002", "action": "BLOCK", "reason": "No HTTPS and invalid/missing SSL."})
        return {"decision": "BLOCK", "policy_id": "P-002", "policy_reason": "No HTTPS and invalid/missing SSL.", "matched_policies": matched}

    service_type = (service_meta.get("service_type") or "").lower()
    if service_type == "ai api" and features.get("weak_auth") == 1.0:
        matched.append({"policy_id": "P-003", "action": "REVIEW", "reason": "External AI API uses weak/missing authentication."})
        return {"decision": "REVIEW", "policy_id": "P-003", "policy_reason": "External AI API uses weak/missing authentication.", "matched_policies": matched}

    if features.get("compliance_bonus", 0.0) < 0.5 and scored.get("risk_score", 0.0) >= 0.4:
        matched.append({"policy_id": "P-004", "action": "REVIEW", "reason": "Low compliance evidence with medium+ risk."})
        return {"decision": "REVIEW", "policy_id": "P-004", "policy_reason": "Low compliance evidence with medium+ risk.", "matched_policies": matched}

    # -------- NEW: low-confidence override ----------
    if scored.get("confidence", 0.0) < 0.60:
        matched.append({"policy_id": "P-005", "action": "REVIEW", "reason": "Low confidence in assessment data quality."})
        return {"decision": "REVIEW", "policy_id": "P-005", "policy_reason": "Low confidence in assessment data quality.", "matched_policies": matched}






    matched.append({"policy_id": "P-000", "action": scored.get("decision", "REVIEW"), "reason": "Default model-based decision."})
    return {
        "decision": scored.get("decision", "REVIEW"),
        "policy_id": "P-000",
        "policy_reason": "Default model-based decision.",
        "matched_policies": matched
    }