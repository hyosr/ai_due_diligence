from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.db import get_db, SessionLocal
from app.models.models import Company, Assessment, Signal
from app.services.assessment_runner import run_assessment_job

from fastapi import Depends
from app.core.auth import require_api_key

router = APIRouter(prefix="/assessment", tags=["assessment"])

@router.post("/run/{company_id}")
async def run_assessment(company_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), _=Depends(require_api_key)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    assessment = Assessment(company_id=company.id, status="pending")
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    async def _job(aid: int):
        local_db = SessionLocal()
        try:
            await run_assessment_job(local_db, aid)
        finally:
            local_db.close()

    background_tasks.add_task(_job, assessment.id)

    return {
        "assessment_id": assessment.id,
        "company_id": company.id,
        "status": assessment.status
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
        "status": a.status,
        "error_message": a.error_message,
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