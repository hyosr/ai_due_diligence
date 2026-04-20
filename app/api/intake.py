from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.schemas import IntakeRequest
from app.models.models import Company, Source

from fastapi import Depends
from app.core.auth import require_api_key

router = APIRouter(prefix="/intake", tags=["intake"], dependencies=[Depends(require_api_key)])

@router.post("/company")
def intake_company(payload: IntakeRequest, db: Session = Depends(get_db), _=Depends(require_api_key)): 
    company = Company(name=payload.company_name, website=str(payload.website))
    db.add(company)
    db.flush()

    website_source = Source(
        company_id=company.id,
        source_type="website",
        source_url=str(payload.website),
        raw_content=None,
        metadata_json={"kind": "primary_website"}
    )
    db.add(website_source)

    for u in payload.extra_urls or []:
        db.add(Source(
            company_id=company.id,
            source_type="url",
            source_url=str(u),
            raw_content=None,
            metadata_json={"kind": "extra_url"}
        ))

    db.commit()
    db.refresh(company)

    return {
        "status": "accepted",
        "company": {
            "id": company.id,
            "name": company.name,
            "website": company.website,
            "created_at": company.created_at.isoformat()
        }
    }