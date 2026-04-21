from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from sqlalchemy import desc

from app.core.auth import require_api_key
from app.core.db import get_db, SessionLocal
from app.models.models import Service, Assessment
from app.schemas.schemas import ServiceInput, ServiceCreateResponse, AssessmentRunResponse, AssessmentOut
from app.services.runner import run_assessment_job

from fastapi import APIRouter, Header, HTTPException


from ml.predictor import predict_risk, explain_prediction

from app.core.db import SessionLocal
 


router = APIRouter(prefix="/assessment", tags=["assessment"], dependencies=[Depends(require_api_key)])


@router.post("/service", response_model=ServiceCreateResponse)
def create_service(payload: ServiceInput, db: Session = Depends(get_db)):
    s = Service(
        name=payload.service_name,
        url=str(payload.service_url),
        service_type=payload.service_type,
        provider=payload.provider,
        api_endpoint=str(payload.api_endpoint) if payload.api_endpoint else None,
        auth_method=payload.auth_method,
        metadata_json=payload.model_dump(mode="json")    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"service_id": s.id, "status": "accepted"}


@router.post("/run/{service_id}", response_model=AssessmentRunResponse)
async def run_assessment(service_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    s = db.query(Service).filter(Service.id == service_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Service not found")

    a = Assessment(service_id=s.id, status="pending")
    db.add(a)
    db.commit()
    db.refresh(a)

    async def _job(aid: int):
        local_db = SessionLocal()
        try:
            await run_assessment_job(local_db, aid)
        finally:
            local_db.close()

    background_tasks.add_task(_job, a.id)
    return {"assessment_id": a.id, "status": "pending"}


@router.get("/{assessment_id}", response_model=AssessmentOut)
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")

    s = db.query(Service).filter(Service.id == a.service_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Service not found")

    return {
        "service": s.name,
        "risk_score": a.risk_score,
        "risk_level": a.risk_level,
        "decision": a.decision,
        "reasons": a.reasons_json or [],
        "confidence": a.confidence,
        "status": a.status,
        "assessment_id": a.id
    }







@router.get("/history/{service_id}")
def get_assessment_history(service_id: int, db: Session = Depends(get_db)):
    s = db.query(Service).filter(Service.id == service_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Service not found")

    rows = (
        db.query(Assessment)
        .filter(Assessment.service_id == service_id)
        .order_by(desc(Assessment.created_at))
        .all()
    )

    return {
        "service_id": service_id,
        "service_name": s.name,
        "items": [
            {
                "assessment_id": r.id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "status": r.status,
                "risk_score": r.risk_score,
                "risk_level": r.risk_level,
                "decision": r.decision,
                "confidence": r.confidence,
                "reasons": r.reasons_json or []
            }
            for r in rows
        ]
    }








@router.get("/raw/{assessment_id}")
def get_assessment_raw(assessment_id: int, db: Session = Depends(get_db)):
    a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")

    return {
        "assessment_id": a.id,
        "status": a.status,
        "risk_score": a.risk_score,
        "risk_level": a.risk_level,
        "decision": a.decision,
        "confidence": a.confidence,
        "policy_id": a.policy_id,
        "policy_reason": a.policy_reason,
        "policy_matches": a.policy_matches_json or [],
        "reasons": a.reasons_json or [],
        "features": a.features_json or {},
        "contributions": (a.explainability_json or {}).get("contributions", []),
        "explainability": a.explainability_json or {},
        "raw_collection": a.raw_collection_json or {},
    }










