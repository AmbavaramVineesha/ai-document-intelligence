import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON
from backend.app.core.database import Base

class DocumentRecord(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_name = Column(String(255), index=True, nullable=False)
    document_type = Column(String(50), nullable=False)
    processing_status = Column(String(20), nullable=False)
    overall_confidence = Column(Float, nullable=True)
    payload_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
