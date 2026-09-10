import io
import pymupdf as fitz
import pdfplumber
from PIL import Image
from typing import List, Dict, Any
from backend.app.core.logging import logger

try:
    import pytesseract
    # Quick binary check — if tesseract isn't on PATH, mark as unavailable
    pytesseract.get_tesseract_version()
    HAS_PYTESSERACT = True
    logger.info("Tesseract OCR binary detected and available.")
except Exception:
    HAS_PYTESSERACT = False
    logger.warning("Tesseract not found on PATH — image OCR will use fallback text.")

# Max pixmap DPI for scanned page rendering (keeps memory safe on free tier)
RENDER_DPI = 72  # Low-res render is enough for OCR; default 96dpi uses too much RAM

class OCRService:

    @staticmethod
    def extract_text(file_name: str, content: bytes, mime_type: str) -> List[Dict[str, Any]]:
        """
        Extract text from PDF, JPG, or PNG documents.
        Returns: [{"page_number": 1, "text": "..."}, ...]
        """
        logger.info(f"Extracting text from '{file_name}' (mime: {mime_type})")
        results = []
        ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

        # ── PDF Processing ────────────────────────────────────────────────────
        if ext == "pdf" or mime_type == "application/pdf":
            try:
                doc = fitz.open(stream=content, filetype="pdf")
                for page_idx in range(len(doc)):
                    page = doc[page_idx]
                    page_text = page.get_text("text") or ""

                    # Only run OCR on sparse pages AND only if tesseract is available
                    if len(page_text.strip()) < 50 and HAS_PYTESSERACT:
                        try:
                            # Low-DPI matrix to avoid memory explosion on free-tier
                            mat = fitz.Matrix(RENDER_DPI / 72, RENDER_DPI / 72)
                            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
                            img = Image.open(io.BytesIO(pix.tobytes("png")))
                            ocr_text = pytesseract.image_to_string(img, timeout=30)
                            if len(ocr_text.strip()) > len(page_text.strip()):
                                page_text = ocr_text
                        except Exception as ocr_err:
                            logger.warning(f"OCR on page {page_idx+1} failed: {ocr_err}")

                    results.append({"page_number": page_idx + 1, "text": page_text})
                return results

            except Exception as e:
                logger.error(f"PyMuPDF failed for '{file_name}': {e} — falling back to pdfplumber")
                try:
                    with pdfplumber.open(io.BytesIO(content)) as pdf:
                        for idx, page in enumerate(pdf.pages):
                            results.append({
                                "page_number": idx + 1,
                                "text": page.extract_text() or ""
                            })
                    return results
                except Exception as pe:
                    logger.error(f"pdfplumber also failed for '{file_name}': {pe}")
                    return [{"page_number": 1, "text": ""}]

        # ── Image Processing (JPG / PNG) ──────────────────────────────────────
        elif ext in ["jpg", "jpeg", "png"] or "image" in mime_type:
            try:
                img = Image.open(io.BytesIO(content)).convert("RGB")
                text = ""

                if HAS_PYTESSERACT:
                    try:
                        text = pytesseract.image_to_string(img, timeout=30)
                        logger.info(f"Tesseract extracted {len(text)} chars from image '{file_name}'")
                    except Exception as te:
                        logger.warning(f"Tesseract failed on '{file_name}': {te}")

                # If no text was extracted, keep empty — don't fabricate content
                results.append({"page_number": 1, "text": text.strip()})
                return results

            except Exception as ie:
                logger.error(f"Image OCR failed for '{file_name}': {ie}")
                return [{"page_number": 1, "text": ""}]

        return [{"page_number": 1, "text": ""}]
