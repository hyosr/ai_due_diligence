from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Any, Dict
from datetime import datetime

class IntakeRequest(BaseModel):
    company_name: str
    website: HttpUrl
    extra_urls: Optional[List[HttpUrl]] = []

class CompanyOut(BaseModel):
    id: int
    name: str
    website: str
    created_at: datetime

    class Config:
        from_attributes = True

class AssessmentRunOut(BaseModel):
    assessment_id: int
    company_id: int
    score: float
    confidence: float
    created_at: datetime

class SignalOut(BaseModel):
    key: str
    numeric_value: Optional[float]
    passed: Optional[bool]
    weight: float
    rationale: Optional[str]
    value: Optional[Dict[str, Any]]

class AssessmentOut(BaseModel):
    id: int
    company_id: int
    score: float
    confidence: float
    summary: Optional[str]
    explainability_json: Optional[Dict[str, Any]]
    created_at: datetime
    signals: List[SignalOut] = []

    class Config:
        from_attributes = True