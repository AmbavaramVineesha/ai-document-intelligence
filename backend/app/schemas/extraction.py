from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class FileValidationDetail(BaseModel):
    file_type: str
    is_supported: bool
    is_readable: bool
    page_count: int
    status: str  # PASS / FAILED
    error_message: Optional[str] = None

class EvidenceDetail(BaseModel):
    source_text: Optional[str] = None
    page_number: Optional[int] = None

class ExtractedField(BaseModel):
    value: Any = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    page_number: Optional[int] = None
    evidence: Optional[EvidenceDetail] = None

class FinancialCheck(BaseModel):
    name: str
    formula: str
    operands: Dict[str, Any]
    calculated_value: Optional[float] = None
    reported_value: Optional[float] = None
    variance: Optional[float] = None
    status: str  # PASS / FAIL / NOT_APPLICABLE
    details: Optional[str] = None

class FinancialValidationResult(BaseModel):
    checks: List[FinancialCheck] = []
    overall_status: str = "PASS"  # PASS / FAIL / NOT_APPLICABLE
    issues: List[str] = []

class ProcessingMetadata(BaseModel):
    ocr_used: bool = True
    processed_at: str
    processing_time_ms: int

class ProcessedDocumentResponse(BaseModel):
    document_name: str
    document_type: str
    processing_status: str  # PASS / FAILED
    overall_confidence: Optional[float] = None
    file_validation: FileValidationDetail
    extracted_data: Dict[str, Any] = {}
    validation: FinancialValidationResult
    processing_metadata: ProcessingMetadata

class ErrorDetail(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    error: ErrorDetail
