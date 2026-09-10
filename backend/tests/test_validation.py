import fitz  # PyMuPDF
import pytest
from backend.app.services.document_validation_service import DocumentValidationService

def test_validate_empty_file():
    res = DocumentValidationService.validate_document("empty.pdf", b"", "application/pdf")
    assert res.status == "FAILED"
    assert "empty" in res.error_message.lower()

def test_validate_unsupported_extension():
    res = DocumentValidationService.validate_document("file.docx", b"some data", "application/docx")
    assert res.status == "FAILED"
    assert res.is_supported is False

def test_validate_exceed_page_limit():
    # Generate 4 page PDF buffer using PyMuPDF
    doc = fitz.open()
    for _ in range(4):
        doc.new_page()
    pdf_bytes = doc.tobytes()
    
    res = DocumentValidationService.validate_document("4pages.pdf", pdf_bytes, "application/pdf")
    assert res.status == "FAILED"
    assert res.page_count == 4
    assert "exceeds maximum allowed limit" in res.error_message

def test_validate_valid_pdf_within_limit():
    doc = fitz.open()
    doc.new_page()
    pdf_bytes = doc.tobytes()

    res = DocumentValidationService.validate_document("1page.pdf", pdf_bytes, "application/pdf")
    assert res.status == "PASS"
    assert res.page_count == 1
    assert res.is_readable is True
