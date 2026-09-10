from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.extraction import ProcessedDocumentResponse, ErrorResponse, ErrorDetail
from backend.app.services.document_service import DocumentService
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.core.logging import logger

router = APIRouter()

SUPPORTED_TYPES = ["invoice", "balance_sheet", "profit_and_loss", "cash_flow_statement"]

@router.post(
    "/documents/process",
    response_model=ProcessedDocumentResponse,
    status_code=status.HTTP_200_OK,
    tags=["Documents"]
)
async def process_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process a financial document (PDF / JPG / PNG).
    """
    doc_type_clean = document_type.strip().lower()
    if doc_type_clean not in SUPPORTED_TYPES:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_DOCUMENT_TYPE",
                    "message": f"Document type '{document_type}' is invalid. Supported types: {', '.join(SUPPORTED_TYPES)}."
                }
            }
        )

    filename = file.filename or "uploaded_document"
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in ["pdf", "jpg", "jpeg", "png"]:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "UNSUPPORTED_FILE_TYPE",
                    "message": f"Only PDF / JPG / PNG documents are supported. Received format '.{ext}'."
                }
            }
        )

    try:
        content = await file.read()
        result = DocumentService.process_document(
            db=db,
            file_name=filename,
            content=content,
            document_type=doc_type_clean,
            content_type=file.content_type or "application/pdf"
        )
        return result
    except Exception as e:
        logger.error(f"Error processing document {filename}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "PROCESSING_ERROR",
                    "message": f"An error occurred while processing document: {str(e)}"
                }
            }
        )

@router.get(
    "/documents/{document_name}",
    tags=["Documents"]
)
def get_document_by_name(document_name: str, db: Session = Depends(get_db)):
    """
    Retrieve the latest structured result using the document/file name.
    """
    repo = DocumentRepository(db)
    record = repo.get_by_document_name(document_name)
    if not record:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "DOCUMENT_NOT_FOUND",
                    "message": f"No processed document found with name '{document_name}'."
                }
            }
        )
    return record.payload_json

@router.get(
    "/documents",
    tags=["Documents"]
)
def list_documents(limit: int = 100, db: Session = Depends(get_db)):
    """
    List all processed documents for the dashboard.
    """
    repo = DocumentRepository(db)
    records = repo.list_all_documents(limit=limit)
    
    items = []
    for r in records:
        items.append({
            "id": r.id,
            "document_name": r.document_name,
            "document_type": r.document_type,
            "processing_status": r.processing_status,
            "overall_confidence": r.overall_confidence,
            "processed_at": r.updated_at.isoformat() + "Z",
            "file_validation_status": r.payload_json.get("file_validation", {}).get("status", "PASS")
        })
    return {"documents": items, "count": len(items)}
