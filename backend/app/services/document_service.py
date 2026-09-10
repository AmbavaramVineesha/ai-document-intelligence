import time
import datetime
from sqlalchemy.orm import Session
from backend.app.schemas.extraction import ProcessedDocumentResponse, ProcessingMetadata
from backend.app.services.document_validation_service import DocumentValidationService
from backend.app.services.ocr_service import OCRService
from backend.app.services.extraction_service import ExtractionService
from backend.app.services.financial_validation_service import FinancialValidationService
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.core.logging import logger

class DocumentService:

    @classmethod
    def process_document(
        cls,
        db: Session,
        file_name: str,
        content: bytes,
        document_type: str,
        content_type: str = "application/pdf"
    ) -> ProcessedDocumentResponse:
        start_time = time.time()
        logger.info(f"Starting processing pipeline for file '{file_name}', type '{document_type}'")

        # 1. Document Validation
        file_val = DocumentValidationService.validate_document(file_name, content, content_type)
        
        # If file validation failed (corrupt, unsupported format, empty, or >3 pages)
        if file_val.status == "FAILED":
            processing_time_ms = int((time.time() - start_time) * 1000)
            metadata = ProcessingMetadata(
                ocr_used=False,
                processed_at=datetime.datetime.utcnow().isoformat() + "Z",
                processing_time_ms=processing_time_ms
            )
            response = ProcessedDocumentResponse(
                document_name=file_name,
                document_type=document_type,
                processing_status="FAILED",
                overall_confidence=0.0,
                file_validation=file_val,
                extracted_data={},
                validation={
                    "checks": [],
                    "overall_status": "FAIL",
                    "issues": [file_val.error_message or "File validation failed."]
                },
                processing_metadata=metadata
            )
            
            # Persist failed record in repository
            repo = DocumentRepository(db)
            repo.save_or_update_document(
                document_name=file_name,
                document_type=document_type,
                processing_status="FAILED",
                overall_confidence=0.0,
                payload_json=response.model_dump()
            )
            return response

        # 2. Text Extraction / OCR
        ocr_pages = OCRService.extract_text(file_name, content, file_val.file_type)

        # 3. Field & Table Extraction
        extracted_data = ExtractionService.extract_data(file_name, document_type, ocr_pages)

        # 4. Financial Calculation Validation
        financial_val = FinancialValidationService.validate(document_type, extracted_data)

        # Determine overall processing status & confidence
        # PASS if required validation checks pass or are N/A and file is valid
        is_val_pass = financial_val.overall_status in ["PASS", "NOT_APPLICABLE"]
        processing_status = "PASS" if is_val_pass else "FAILED"

        # Calculate overall confidence score across extracted fields
        confidences = []
        for key, field_obj in extracted_data.items():
            if isinstance(field_obj, dict) and "confidence" in field_obj:
                c = field_obj.get("confidence")
                if c is not None:
                    confidences.append(c)
        overall_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.95

        processing_time_ms = int((time.time() - start_time) * 1000)
        metadata = ProcessingMetadata(
            ocr_used=True,
            processed_at=datetime.datetime.utcnow().isoformat() + "Z",
            processing_time_ms=processing_time_ms
        )

        response = ProcessedDocumentResponse(
            document_name=file_name,
            document_type=document_type,
            processing_status=processing_status,
            overall_confidence=overall_confidence,
            file_validation=file_val,
            extracted_data=extracted_data,
            validation=financial_val,
            processing_metadata=metadata
        )

        # 5. Store Processing Result in DB
        repo = DocumentRepository(db)
        repo.save_or_update_document(
            document_name=file_name,
            document_type=document_type,
            processing_status=processing_status,
            overall_confidence=overall_confidence,
            payload_json=response.model_dump()
        )

        logger.info(f"Completed processing '{file_name}' in {processing_time_ms}ms with status: {processing_status}")
        return response
