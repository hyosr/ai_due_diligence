from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl


class ServiceInput(BaseModel):
    # A. basic info
    service_name: str
    service_url: HttpUrl
    service_type: Optional[str] = None
    provider: Optional[str] = None

    # B. technical data
    api_endpoint: Optional[HttpUrl] = None
    ssl_certificate_present: Optional[bool] = None
    http_headers: Optional[Dict[str, str]] = None
    auth_method: Optional[str] = None

    # C. security data
    num_known_vulnerabilities: Optional[int] = None
    encryption_present: Optional[bool] = None
    requested_permissions: Optional[List[str]] = None
    suspicious_logs_detected: Optional[bool] = None

    # D. external data
    reputation_score_external: Optional[float] = None  # 0..1
    user_reviews_score: Optional[float] = None         # 0..1
    blacklist_flag: Optional[bool] = None
    whitelist_flag: Optional[bool] = None
    gdpr_compliant: Optional[bool] = None
    iso27001_compliant: Optional[bool] = None


class ServiceCreateResponse(BaseModel):
    service_id: int
    status: str


class AssessmentRunResponse(BaseModel):
    assessment_id: int
    status: str


class AssessmentOut(BaseModel):
    service: str
    risk_score: float
    risk_level: str
    decision: str
    reasons: List[str]
    confidence: float
    status: str
    assessment_id: int