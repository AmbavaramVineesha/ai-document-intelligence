# System Architecture Diagram & Technical Description

```mermaid
graph TD
    Client[Web Browser / Dashboard / API Client] -->|POST /api/v1/documents/process| Ingestion[FastAPI API Controller]
    Client -->|GET /api/v1/documents| Ingestion
    Client -->|GET /api/v1/documents/{name}| Ingestion
    
    Ingestion --> ValService[Document Validation Service]
    ValService -->|Check File Type, Size, Integrity, Page Limit <= 3| ValResult{Valid?}
    
    ValResult -->|No| ReturnError[Return 400/Structured Failure JSON & Persist]
    ValResult -->|Yes| OCRService[OCR & Text Extraction Service]
    
    OCRService -->|PyMuPDF / pdfplumber / PyTesseract| ExtService[AI Field & Table Extraction Service]
    ExtService -->|Extract Fields + Grounding Evidence| FinValService[Financial Validation Service]
    
    FinValService -->|Invoice, BS, P&L, Cash Flow Math Checks| RepoLayer[Document Repository]
    RepoLayer -->|SQLAlchemy ORM| DB[(SQLite / PostgreSQL DB)]
    
    RepoLayer --> FinalResponse[Structured JSON Response]
    FinalResponse --> Client
```

## System Component Breakdown

1. **Ingestion Layer (`api/routes/documents.py`):** Accepts multipart uploads and request metadata.
2. **Validation Service (`services/document_validation_service.py`):** Ensures document is a readable PDF, JPG, or PNG under 15MB and max 3 pages.
3. **OCR Service (`services/ocr_service.py`):** Extracts text natively from digital PDFs or runs image OCR on scans.
4. **Extraction Service (`services/extraction_service.py`):** Uses AI/regex heuristics to extract all key-value pairs, tables, confidence scores, and source evidence text.
5. **Financial Validation Service (`services/financial_validation_service.py`):** Performs multi-check math reconciliation.
6. **Persistence Layer (`repositories/document_repository.py` & `models/document.py`):** Stores extraction payloads for instant dashboard retrieval.
