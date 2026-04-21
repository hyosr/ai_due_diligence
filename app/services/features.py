from typing import Dict, Any


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def extract_features(payload: dict, collected: dict) -> Dict[str, Any]:
    has_https = 1 if str(payload.get("service_url", "")).startswith("https://") else 0
    ssl_valid = 1 if (payload.get("ssl_certificate_present") is True or collected.get("ssl_valid") is True) else 0
    # encryption_present = 1 if payload.get("encryption_present") is True else 0


    if has_https == 1 and ssl_valid == 1:
        encryption_present = 1
    else:
        encryption_present = 1 if payload.get("encryption_present") is True else 0


    headers_score = payload.get("security_headers_score")
    headers_risk = 0.5 if headers_score is None else (1 - float(headers_score))

    domain_age_risk = payload.get("domain_age_risk")
    domain_age_risk = 0.5 if domain_age_risk is None else float(domain_age_risk)







    num_vuln = payload.get("num_known_vulnerabilities")
    vuln_risk = 0.0 if num_vuln is None else clamp01(num_vuln / 10.0)

    suspicious_logs = 1.0 if payload.get("suspicious_logs_detected") is True else 0.0

    rep = payload.get("reputation_score_external")
    rep_risk = 0.5 if rep is None else clamp01(1 - float(rep))

    reviews = payload.get("user_reviews_score")
    reviews_risk = 0.5 if reviews is None else clamp01(1 - float(reviews))

    blacklist = 1.0 if payload.get("blacklist_flag") is True else 0.0
    whitelist = 1.0 if payload.get("whitelist_flag") is True else 0.0

    gdpr = 1.0 if payload.get("gdpr_compliant") is True else 0.0
    iso = 1.0 if payload.get("iso27001_compliant") is True else 0.0


    if gdpr == 1.0 or iso == 1.0:
        compliance_bonus = 0.9  
    else:
        compliance_bonus = 0.0
    if gdpr == 1.0 and iso == 1.0:
        compliance_bonus = 1.0

    auth_method = (payload.get("auth_method") or "").lower()
    weak_auth = 1.0 if auth_method in ("", "none", "basic") else 0.0

#     config_risk = clamp01(
#     (1 - has_https) * 0.25 +
#     (1 - ssl_valid) * 0.20 +
#     (1 - encryption_present) * 0.20 +
#     weak_auth * 0.20 +
#     headers_risk * 0.15
# )




    config_risk = clamp01(
    (1 - has_https) * 0.25 +
    (1 - ssl_valid) * 0.20 +
    (1 - encryption_present) * 0.10 +   # ← diminué de 0.20 à 0.10
    weak_auth * 0.20 +
    headers_risk * 0.15
)
    


    # Augmentation du compliance_bonus pour GDPR seul
    gdpr = 1.0 if payload.get("gdpr_compliant") is True else 0.0
    iso = 1.0 if payload.get("iso27001_compliant") is True else 0.0

    # Bonus augmenté : 0.9 si GDPR, 0.9 si ISO, sinon 0
    if gdpr == 1.0 or iso == 1.0:
        compliance_bonus = 0.9
    else:
        compliance_bonus = 0.0

    reputation_risk = clamp01(
        rep_risk * 0.40 +
        reviews_risk * 0.15 +
        blacklist * 0.25 +
        domain_age_risk * 0.15 +
        (0.0 if whitelist == 1.0 else 0.05)
    )


    vulnerability_risk = clamp01(
        vuln_risk * 0.75 +
        suspicious_logs * 0.25
    )

    compliance_bonus = (gdpr + iso) / 2.0

    # --------- NEW: data completeness score ----------
    critical_fields = [
        payload.get("service_url"),
        payload.get("auth_method"),
        payload.get("num_known_vulnerabilities"),
        payload.get("encryption_present"),
        payload.get("reputation_score_external"),
        payload.get("blacklist_flag"),
        payload.get("gdpr_compliant"),
    ]
    present = sum(1 for x in critical_fields if x is not None)
    data_completeness_score = round(present / len(critical_fields), 4)

    return {
        "has_https": has_https,
        "ssl_valid": ssl_valid,
        "encryption_present": encryption_present,
        "vulnerability_risk": vulnerability_risk,
        "config_risk": config_risk,
        "reputation_risk": reputation_risk,
        "compliance_bonus": compliance_bonus,
        "weak_auth": weak_auth,
        "blacklist": blacklist,
        "whitelist": whitelist,
        "data_completeness_score": data_completeness_score,  # NEW
        "headers_risk": round(headers_risk, 4),
        "domain_age_risk": round(domain_age_risk, 4),
    }