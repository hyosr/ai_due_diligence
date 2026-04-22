from sqlalchemy.orm import Session
from app.models.models import Service, Assessment
from app.services.collector import collect_runtime_data
from app.services.features import extract_features
from app.services.scorer import score_risk
from app.services.explain import build_reasons, build_explainability
from app.services.policy_engine import evaluate_policies
from app.services.connectors.ssl_deep import ssl_deep_scan
from app.services.connectors.reputation import reputation_lookup
from app.services.connectors.security_headers import scan_security_headers
from app.services.connectors.domain_age import get_domain_age_signal

from app.core.db import SessionLocal   # ajoutez cet import en haut






async def run_assessment_job(assessment_id: int):
    db = SessionLocal()
    try:
        a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not a:
            return

        s = db.query(Service).filter(Service.id == a.service_id).first()
        if not s:
            a.status = "failed"
            a.error_message = "Service not found"
            db.commit()
            return

        try:
            a.status = "running"
            db.commit()

            payload = (s.metadata_json or {}).copy()
            payload["service_url"] = s.url
            payload["api_endpoint"] = s.api_endpoint
            payload["auth_method"] = s.auth_method

            # 1) Base collection
            collected = await collect_runtime_data(s.url, s.api_endpoint)

            # 2) SSL deep scan
            ssl_info = ssl_deep_scan(s.url)
            collected["ssl_deep"] = ssl_info
            if payload.get("ssl_certificate_present") is None and ssl_info.get("ssl_valid") is not None:
                payload["ssl_certificate_present"] = bool(ssl_info.get("ssl_valid"))

            # 3) Reputation connector
            rep_info = await reputation_lookup(s.url)
            collected["reputation_external"] = rep_info
            if payload.get("reputation_score_external") is None:
                payload["reputation_score_external"] = rep_info.get("reputation_score_external", 0.5)
            if payload.get("blacklist_flag") is None:
                payload["blacklist_flag"] = rep_info.get("blacklist_flag", False)

            # 4) Security headers
            headers_info = await scan_security_headers(s.url)
            collected["security_headers"] = headers_info

            # 5) Domain age
            domain_info = get_domain_age_signal(s.url)
            collected["domain_age"] = domain_info

            # 6) Pass‑through values
            payload["security_headers_score"] = headers_info.get("security_headers_score")
            payload["domain_age_risk"] = domain_info.get("domain_age_risk")

            # 7) Feature extraction + scoring
            features = extract_features(payload, collected)
            scored = score_risk(features)
            reasons = build_reasons(features, scored)

            # Policy engine override
            policy_eval = evaluate_policies(
                scored=scored,
                features=features,
                service_meta={"service_type": s.service_type, "provider": s.provider}
            )

            final_decision = policy_eval["decision"]

            explain = build_explainability(features, scored, reasons)
            explain["contributions"] = scored.get("contributions", [])
            explain["policy"] = policy_eval

            a.risk_score = scored["risk_score"]
            a.risk_level = scored["risk_level"]
            a.decision = final_decision
            a.confidence = scored["confidence"]

            a.policy_id = policy_eval.get("policy_id")
            a.policy_reason = policy_eval.get("policy_reason")
            a.policy_matches_json = policy_eval.get("matched_policies", [])

            a.reasons_json = reasons
            a.features_json = features
            a.explainability_json = explain
            a.raw_collection_json = collected
            a.contributions_json = scored.get("contributions", [])

            a.status = "done"
            a.error_message = None
            db.commit()

        except Exception as e:
            a.status = "failed"
            a.error_message = str(e)
            db.commit()

    finally:
        db.close()


