from sqlalchemy.orm import Session
from app.models.models import Company, Assessment, Signal
from app.services.fetcher import fetch_website_text
from app.services.extractor import run_all_signals
from app.services.scoring import compute_weighted_score
from app.services.explainability import build_summary

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

        website_text, links = await fetch_website_text(company.website)
        context = {"website_text": website_text, "links": links}
        signal_results = await run_all_signals(
            company={"id": company.id, "name": company.name, "website": company.website},
            context=context
        )

        score_payload = compute_weighted_score(signal_results)
        score = score_payload["score"]
        explanations = score_payload["explanations"]
        confidence = round(
            (sum(1 for s in signal_results if s.get("numeric_value") is not None) / max(len(signal_results), 1)) * 100,
            2
        )
        summary = build_summary(score, confidence, explanations)

        # delete old signals if re-run
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

        assessment.score = score
        assessment.confidence = confidence
        assessment.summary = summary
        assessment.explainability_json = {"items": explanations}
        assessment.status = "done"
        assessment.error_message = None
        db.commit()
    except Exception as e:
        assessment.status = "failed"
        assessment.error_message = str(e)
        db.commit()