from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import JSON

Base = declarative_base()

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    website = Column(String(500), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    sources = relationship("Source", back_populates="company", cascade="all,delete-orphan")
    assessments = relationship("Assessment", back_populates="company", cascade="all,delete-orphan")

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)  # website, url, pdf
    source_url = Column(String(1000), nullable=True)
    raw_content = Column(Text, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata_json = Column(JSON, nullable=True)

    company = relationship("Company", back_populates="sources")

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    score = Column(Float, nullable=False, default=0.0)
    confidence = Column(Float, nullable=False, default=0.0)
    summary = Column(Text, nullable=True)
    explainability_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    company = relationship("Company", back_populates="assessments")
    signals = relationship("Signal", back_populates="assessment", cascade="all,delete-orphan")

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False, index=True)
    key = Column(String(150), nullable=False, index=True)
    value = Column(JSON, nullable=True)
    numeric_value = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)
    weight = Column(Float, nullable=False, default=0.0)
    rationale = Column(Text, nullable=True)

    assessment = relationship("Assessment", back_populates="signals")