from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.document import DocumentRecord

class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_or_update_document(
        self,
        document_name: str,
        document_type: str,
        processing_status: str,
        overall_confidence: Optional[float],
        payload_json: dict
    ) -> DocumentRecord:
        # Check if record exists for this document_name
        existing = (
            self.db.query(DocumentRecord)
            .filter(DocumentRecord.document_name == document_name)
            .first()
        )
        if existing:
            existing.document_type = document_type
            existing.processing_status = processing_status
            existing.overall_confidence = overall_confidence
            existing.payload_json = payload_json
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            record = DocumentRecord(
                document_name=document_name,
                document_type=document_type,
                processing_status=processing_status,
                overall_confidence=overall_confidence,
                payload_json=payload_json
            )
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return record

    def get_by_document_name(self, document_name: str) -> Optional[DocumentRecord]:
        return (
            self.db.query(DocumentRecord)
            .filter(DocumentRecord.document_name == document_name)
            .order_by(DocumentRecord.updated_at.desc())
            .first()
        )

    def list_all_documents(self, limit: int = 100) -> List[DocumentRecord]:
        return (
            self.db.query(DocumentRecord)
            .order_by(DocumentRecord.updated_at.desc())
            .limit(limit)
            .all()
        )
