from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.models import Company, Assessment, Signal
from app.services.fetcher import fetch_website_text
from app.services.extractor import run_all_signals
from app.services.scoring import compute_weighted_score
from app.services.explainability import build_summary


from fastapi import Depends
from app.core.auth import require_api_key

router = APIRouter(prefix="/assessment", tags=["assessment"])

@router.post("/run/{company_id}")
async def run_assessment(company_id: int, db: Session = Depends(get_db), _=Depends(require_api_key)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    website_text, links = await fetch_website_text(company.website)
    context = {"website_text": website_text, "links": links}

    signal_results = await run_all_signals(
        company={"id": company.id, "name": company.name, "website": company.website},
        context=context
    )

    score_payload = compute_weighted_score(signal_results)
    score = score_payload["score"]
    explanations = score_payload["explanations"]

    available = sum(1 for s in signal_results if s.get("numeric_value") is not None)
    confidence = round((available / max(len(signal_results), 1)) * 100, 2)

    summary = build_summary(score, confidence, explanations)

    assessment = Assessment(
        company_id=company.id,
        score=score,
        confidence=confidence,
        summary=summary,
        explainability_json={"items": explanations}
    )
    db.add(assessment)
    db.flush()

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

    db.commit()
    db.refresh(assessment)

    return {
        "assessment_id": assessment.id,
        "company_id": company.id,
        "score": assessment.score,
        "confidence": assessment.confidence,
        "created_at": assessment.created_at.isoformat(),
        "summary": assessment.summary
    }

@router.get("/{assessment_id}")
def get_assessment(assessment_id: int, db: Session = Depends(get_db), _=Depends(require_api_key)):
    a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    signals = db.query(Signal).filter(Signal.assessment_id == assessment_id).all()

    return {
        "id": a.id,
        "company_id": a.company_id,
        "score": a.score,
        "confidence": a.confidence,
        "summary": a.summary,
        "explainability_json": a.explainability_json,
        "created_at": a.created_at.isoformat(),
        "signals": [
            {
                "key": s.key,
                "numeric_value": s.numeric_value,
                "passed": s.passed,
                "weight": s.weight,
                "rationale": s.rationale,
                "value": s.value
            } for s in signals
        ]
    }