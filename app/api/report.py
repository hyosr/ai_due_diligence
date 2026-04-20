from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.auth import require_api_key
from app.core.db import get_db
from app.models.models import Assessment, Service

router = APIRouter(prefix="/report", tags=["report"], dependencies=[Depends(require_api_key)])


@router.get("/json/{assessment_id}")
def report_json(assessment_id: int, db: Session = Depends(get_db)):
    a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    s = db.query(Service).filter(Service.id == a.service_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Service not found")

    return JSONResponse({
        "service": s.name,
        "risk_score": a.risk_score,
        "risk_level": a.risk_level,
        "decision": a.decision,
        "reasons": a.reasons_json or [],
        "confidence": a.confidence
    })