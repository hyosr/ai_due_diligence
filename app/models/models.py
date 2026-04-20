from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(1024), nullable=False)
    service_type = Column(String(100), nullable=True)   # AI API, SaaS, cloud tool
    provider = Column(String(255), nullable=True)
    api_endpoint = Column(String(1024), nullable=True)
    auth_method = Column(String(100), nullable=True)    # OAuth, API Key, None

    metadata_json = Column(JSON, nullable=True, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    assessments = relationship("Assessment", back_populates="service")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)

    status = Column(String(20), nullable=False, default="pending")  # pending|running|done|failed
    error_message = Column(Text, nullable=True)

    risk_score = Column(Float, default=0.0)          # 0..1
    risk_level = Column(String(20), default="UNKNOWN")  # LOW|MEDIUM|HIGH
    decision = Column(String(20), default="REVIEW")  # ALLOW|REVIEW|BLOCK
    confidence = Column(Float, default=0.0)          # 0..1

    reasons_json = Column(JSON, default=[])
    features_json = Column(JSON, default={})
    explainability_json = Column(JSON, default={})
    raw_collection_json = Column(JSON, default={})

    created_at = Column(DateTime, default=datetime.utcnow)

    service = relationship("Service", back_populates="assessments")

    policy_id = Column(String(50), nullable=True)
    policy_reason = Column(Text, nullable=True)
    policy_matches_json = Column(JSON, default=[])