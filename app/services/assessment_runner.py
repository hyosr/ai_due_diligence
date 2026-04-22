from sqlalchemy.orm import Session
from app.models.models import Company, Assessment, Signal
from app.services.fetcher import fetch_website_text
from app.services.extractor import run_all_signals
from app.services.explainability import build_summary
from app.services.feature_collector import collect_all_features
from app.services.enriched_scorer import score_risk
from app.core.config import settings

async def run_assessment_job(db: Session, assessment_id: int):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        return
    company = db.query(Company).filter(Company.id == assessment.company_id).first()
    if not company:
        assessment.status = "failed"
        assessment.error_message = "Company not found"
        db.commit()
        return

    try:
        assessment.status = "running"
        db.commit()

        # 1. Collect live features from the target URL
        live_features = await collect_all_features(
            company.website,
            shodan_api_key=getattr(settings, "SHODAN_API_KEY", None)
        )

        # 2. Build existing features (from assessment or defaults)
        existing_features = {
            "vulnerability_risk": getattr(assessment, "vulnerability_risk", 0.0) or 0.0,
            "config_risk": getattr(assessment, "config_risk", 0.0) or 0.0,
            "reputation_risk": getattr(assessment, "reputation_risk", 0.0) or 0.0,
            "compliance_bonus": getattr(assessment, "compliance_bonus", 0.0) or 0.0,
            "blacklist_flag": getattr(assessment, "blacklist_flag", False),
            "data_completeness_score": getattr(assessment, "data_completeness_score", 0.7) or 0.7,
        }

        all_features = {**live_features, **existing_features}

        # 3. Compute enriched risk score
        risk_result = score_risk(all_features)

        # 4. Store enriched results in the assessment
        assessment.score = risk_result["risk_score"]
        assessment.confidence = risk_result["confidence"]
        assessment.risk_level = risk_result["risk_level"]
        assessment.decision = risk_result["decision"]
        assessment.contributions_json = risk_result["contributions"]   # <-- KEY LINE

        # 5. (Optional) Still run signals for explanation (but do NOT overwrite score)
        website_text, links = await fetch_website_text(company.website)
        context = {"website_text": website_text, "links": links}
        signal_results = await run_all_signals(
            company={"id": company.id, "name": company.name, "website": company.website},
            context=context
        )
        explanations = [s.get("rationale") for s in signal_results if s.get("rationale")]
        summary = build_summary(assessment.score, assessment.confidence, explanations)

        # Delete old signals and add new ones
        db.query(Signal).filter(Signal.assessment_id == assessment.id).delete()
        for s in signal_results:
            db.add(Signal(
                assessment_id=assessment.id,
                key=s["key"],
                value=s.get("value"),
                numeric_value=s.get("numeric_value"),
                passed=s.get("passed"),
                weight=s.get("weight", 0.0),
                rationale=s.get("rationale")
            ))

        assessment.summary = summary
        assessment.explainability_json = {"items": explanations}
        assessment.status = "done"
        assessment.error_message = None
        db.commit()

    except Exception as e:
        assessment.status = "failed"
        assessment.error_message = str(e)
        db.commit()



























# from sqlalchemy.orm import Session
# from app.models.models import Company, Assessment, Signal
# from app.services.fetcher import fetch_website_text
# from app.services.extractor import run_all_signals
# from app.services.scoring import compute_weighted_score
# from app.services.explainability import build_summary


# from app.services.feature_collector import collect_all_features
# from app.services.enriched_scorer import score_risk


# async def run_assessment_job(db: Session, assessment_id: int):
#     assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
#     if not assessment:
#         return
#     company = db.query(Company).filter(Company.id == assessment.company_id).first()
#     if not company:
#         assessment.status = "failed"
#         assessment.error_message = "Company not found"
#         db.commit()
#         return
    




#     # Collect live features from the target URL
#     live_features = await collect_all_features(company.website, shodan_api_key=settings.SHODAN_API_KEY)  # add SHODAN_API_KEY to config if desired

#     # Merge with existing input features (from the assessment payload)
#     existing_features = {
#         "vulnerability_risk": assessment.vulnerability_risk or 0.0,
#         "config_risk": assessment.config_risk or 0.0,
#         "reputation_risk": assessment.reputation_risk or 0.0,
#         "compliance_bonus": assessment.compliance_bonus or 0.0,
#         "blacklist_flag": assessment.blacklist_flag or False,
#         "data_completeness_score": assessment.data_completeness_score or 0.7,
#     }

#     all_features = {**live_features, **existing_features}

#     # Compute risk score using the enriched scorer
#     risk_result = score_risk(all_features)
#     assessment.score = risk_result["risk_score"]
#     assessment.confidence = risk_result["confidence"]
#     assessment.risk_level = risk_result["risk_level"]
#     assessment.decision = risk_result["decision"]

#     # Optionally store the detailed contributions and features in the assessment (add columns if needed)
#     assessment.contributions_json = risk_result["contributions"]

    







#     try:
#         assessment.status = "running"
#         db.commit()

#         website_text, links = await fetch_website_text(company.website)
#         context = {"website_text": website_text, "links": links}
#         signal_results = await run_all_signals(
#             company={"id": company.id, "name": company.name, "website": company.website},
#             context=context
#         )

#         score_payload = compute_weighted_score(signal_results)
#         score = score_payload["score"]
#         explanations = score_payload["explanations"]
#         confidence = round(
#             (sum(1 for s in signal_results if s.get("numeric_value") is not None) / max(len(signal_results), 1)) * 100,
#             2
#         )
#         summary = build_summary(score, confidence, explanations)

#         # delete old signals if re-run
#         db.query(Signal).filter(Signal.assessment_id == assessment.id).delete()

#         for s in signal_results:
#             db.add(Signal(
#                 assessment_id=assessment.id,
#                 key=s["key"],
#                 value=s.get("value"),
#                 numeric_value=s.get("numeric_value"),
#                 passed=s.get("passed"),
#                 weight=s.get("weight", 0.0),
#                 rationale=s.get("rationale")
#             ))

#         assessment.score = score
#         assessment.confidence = confidence
#         assessment.summary = summary
#         assessment.explainability_json = {"items": explanations}
#         assessment.status = "done"
#         assessment.error_message = None
#         db.commit()
#     except Exception as e:
#         assessment.status = "failed"
#         assessment.error_message = str(e)
#         db.commit()