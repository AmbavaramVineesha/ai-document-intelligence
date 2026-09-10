import io
from typing import Optional
import pymupdf as fitz
from PIL import Image
from pypdf import PdfReader
from backend.app.core.config import settings
from backend.app.schemas.extraction import FileValidationDetail
from backend.app.core.logging import logger

class DocumentValidationService:

    @staticmethod
    def validate_document(file_name: str, content: bytes, content_type: Optional[str] = None) -> FileValidationDetail:
        logger.info(f"Validating document: {file_name}, size: {len(content)} bytes")
        
        # Check empty file
        if not content or len(content) == 0:
            return FileValidationDetail(
                file_type=content_type or "unknown",
                is_supported=False,
                is_readable=False,
                page_count=0,
                status="FAILED",
                error_message="File is empty (0 bytes)."
            )

        # File size check
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            return FileValidationDetail(
                file_type=content_type or "unknown",
                is_supported=False,
                is_readable=False,
                page_count=0,
                status="FAILED",
                error_message=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."
            )

        ext = file_name.split(".")[-1].lower() if "." in file_name else ""
        
        # Check supported extension
        if ext not in settings.ALLOWED_EXTENSIONS:
            return FileValidationDetail(
                file_type=content_type or f"unknown/.{ext}",
                is_supported=False,
                is_readable=False,
                page_count=0,
                status="FAILED",
                error_message=f"Unsupported file format '.{ext}'. Supported formats: PDF, JPG, PNG."
            )

        # PDF Validation
        if ext == "pdf" or content_type == "application/pdf":
            try:
                # Try reading with PyMuPDF
                doc = fitz.open(stream=content, filetype="pdf")
                page_count = len(doc)
                
                if page_count == 0:
                    return FileValidationDetail(
                        file_type="application/pdf",
                        is_supported=True,
                        is_readable=False,
                        page_count=0,
                        status="FAILED",
                        error_message="PDF has 0 pages or is unreadable."
                    )
                
                if page_count > settings.MAX_PAGE_COUNT:
                    return FileValidationDetail(
                        file_type="application/pdf",
                        is_supported=True,
                        is_readable=True,
                        page_count=page_count,
                        status="FAILED",
                        error_message=f"Page count ({page_count}) exceeds maximum allowed limit of {settings.MAX_PAGE_COUNT} pages."
                    )

                return FileValidationDetail(
                    file_type="application/pdf",
                    is_supported=True,
                    is_readable=True,
                    page_count=page_count,
                    status="PASS"
                )
            except Exception as e:
                logger.error(f"Failed to parse PDF {file_name}: {str(e)}")
                return FileValidationDetail(
                    file_type="application/pdf",
                    is_supported=True,
                    is_readable=False,
                    page_count=0,
                    status="FAILED",
                    error_message=f"PDF integrity check failed or corrupted: {str(e)}"
                )

        # Image Validation (JPG, PNG)
        if ext in ["jpg", "jpeg", "png"] or (content_type and "image" in content_type):
            mime = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
            try:
                img = Image.open(io.BytesIO(content))
                img.verify()
                return FileValidationDetail(
                    file_type=mime,
                    is_supported=True,
                    is_readable=True,
                    page_count=1,
                    status="PASS"
                )
            except Exception as e:
                logger.error(f"Failed to open image {file_name}: {str(e)}")
                return FileValidationDetail(
                    file_type=mime,
                    is_supported=True,
                    is_readable=False,
                    page_count=0,
                    status="FAILED",
                    error_message=f"Image file is corrupted or unreadable: {str(e)}"
                )

        return FileValidationDetail(
            file_type=content_type or "unknown",
            is_supported=False,
            is_readable=False,
            page_count=0,
            status="FAILED",
            error_message="Unsupported document format."
        )
