from sqlalchemy import Column, Integer, String, Float, Date, Text, ForeignKey, JSON, TIMESTAMP
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class Permit(Base):
    __tablename__ = "permits"
    id = Column(Integer, primary_key=True, index=True)
    raw_json = Column(JSON)
    permit_id = Column(String, index=True)
    city = Column(String, index=True)
    address = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    permit_type = Column(String)
    description = Column(String)
    valuation = Column(Float)
    status = Column(String)
    filed_date = Column(Date)
    issued_date = Column(Date)
    applicant = Column(String)
    contractor = Column(String)
    owner = Column(String)
    source_url = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

    scores = relationship("Score", back_populates="permit")
    enrichments = relationship("Enrichment", back_populates="permit")
    packages = relationship("Package", back_populates="permit")

class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True, index=True)
    permit_id = Column(Integer, ForeignKey("permits.id"))
    win_score = Column(Float)
    value_score = Column(Float)
    delay_score = Column(Float)
    commercial_score = Column(Float)
    competition_score = Column(Float)
    reasoning = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

    permit = relationship("Permit", back_populates="scores")

class Enrichment(Base):
    __tablename__ = "enrichments"
    id = Column(Integer, primary_key=True, index=True)
    permit_id = Column(Integer, ForeignKey("permits.id"))
    type = Column(String)
    data = Column(JSON)
    url = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

    permit = relationship("Permit", back_populates="enrichments")

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    permit_id = Column(Integer, ForeignKey("permits.id"))
    vertical = Column(String)
    content = Column(JSON)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

    permit = relationship("Permit", back_populates="packages")

class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, unique=True, index=True)
    urls = Column(JSON)
    last_fetch = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
