# Intelligent Document Extraction, Validation & API Platform

An end-to-end AI-powered financial document extraction and validation platform built with **FastAPI**, **SQLAlchemy**, **PyMuPDF / PyTesseract OCR**, and a modern **HTML/CSS/JS Glassmorphism Dashboard**.

---

## 🌟 Solution Overview & Features

This platform processes financial documents in **PDF**, **JPG**, and **PNG** format across four supported categories:
1. **Invoice**
2. **Balance Sheet**
3. **Profit & Loss Statement**
4. **Cash Flow Statement**

### Pipeline Workflow
```
Document Upload ➔ Document Validation (MIME, Integrity, <=3 Pages) ➔ Text Extraction/OCR 
➔ AI Field & Table Extraction ➔ Evidence Grounding ➔ Financial Calculation Validation 
➔ Database Persistence ➔ Dashboard & REST API Response
```

---

## 🚀 Deployed URLs & Submission Links

| Component | URL |
|---|---|
| **Frontend Dashboard** | `https://your-app-name.onrender.com/` |
| **Backend API Base URL** | `https://your-app-name.onrender.com/api/v1` |
| **Swagger / OpenAPI Documentation** | `https://your-app-name.onrender.com/docs` |
| **Health Check Endpoint** | `https://your-app-name.onrender.com/api/v1/health` |
| **Public GitHub Repository** | `https://github.com/your-username/ai-document-intelligence` |

---

## 🛠️ Technology Stack & Rationale

- **FastAPI (Python 3.10):** High-performance, asynchronous REST framework with automatic Swagger UI generation.
- **SQLAlchemy & SQLite:** Robust ORM layer with zero-config lightweight database storage for instant deployment.
- **PyMuPDF (fitz) & pdfplumber:** Rapid, accurate native PDF text and layout parsing.
- **PyTesseract & Pillow:** OCR engine for scanned PDF images and JPG/PNG documents.
- **Pydantic V2:** Strict data validation and machine-readable JSON output schemas.
- **Jinja2 + Vanilla CSS Glassmorphism:** Clean, interactive, responsive web frontend dashboard without heavy JavaScript dependencies.

---

## 💻 Local Setup Instructions

### 1. Prerequisites
- Python 3.10+
- (Optional) Tesseract-OCR binary installed on host system for scanned image OCR.

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/your-username/ai-document-intelligence.git
cd ai-document-intelligence

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 4. Run Application
```bash
# Start FastAPI backend server with reloading
python -m uvicorn backend.app.main:app --reload --port 8000
```
Access the application:
- **Frontend Dashboard:** `http://localhost:8000/`
- **Swagger API Docs:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/api/v1/health`

### 5. Run Automated Tests
```bash
python -m pytest backend/tests/ -v
```

---

## 📡 REST API Usage & Examples

### 1. Health Check
`GET /api/v1/health`
```json
{
  "status": "healthy",
  "service": "Intelligent Document Intelligence & Extraction Platform",
  "version": "1.0.0",
  "timestamp": "2026-09-10T12:00:00Z"
}
```

### 2. Process Document (Multipart Upload)
`POST /api/v1/documents/process`
- **Content-Type:** `multipart/form-data`
- **Form Fields:** `file` (binary), `document_type` (`invoice` | `balance_sheet` | `profit_and_loss` | `cash_flow_statement`)

#### Example cURL Request:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/process" \
  -F "file=@sample_documents/invoices/batch1-1109.jpg" \
  -F "document_type=invoice"
```

#### Example Response JSON:
```json
{
  "document_name": "batch1-1109.jpg",
  "document_type": "invoice",
  "processing_status": "PASS",
  "overall_confidence": 0.96,
  "file_validation": {
    "file_type": "image/jpeg",
    "is_supported": true,
    "is_readable": true,
    "page_count": 1,
    "status": "PASS"
  },
  "extracted_data": {
    "subtotal": {"value": 12500.0, "confidence": 0.97, "page_number": 1, "evidence": {"source_text": "Subtotal: 12500.00", "page_number": 1}},
    "tax_amount": {"value": 625.0, "confidence": 0.96, "page_number": 1, "evidence": {"source_text": "Tax: 625.00", "page_number": 1}},
    "discount": {"value": 0.0, "confidence": 0.9, "page_number": 1, "evidence": null},
    "total_amount": {"value": 13125.0, "confidence": 0.99, "page_number": 1, "evidence": {"source_text": "Total Amount: 13125.00", "page_number": 1}},
    "line_items": [
      {"description": "Service A", "quantity": 1, "unit_price": 12500.0, "amount": 12500.0}
    ]
  },
  "validation": {
    "checks": [
      {
        "name": "invoice_total_check",
        "formula": "subtotal + tax_amount - discount",
        "operands": {"subtotal": 12500.0, "tax_amount": 625.0, "discount": 0.0},
        "calculated_value": 13125.0,
        "reported_value": 13125.0,
        "variance": 0.0,
        "status": "PASS"
      }
    ],
    "overall_status": "PASS",
    "issues": []
  },
  "processing_metadata": {
    "ocr_used": true,
    "processed_at": "2026-09-10T12:00:00Z",
    "processing_time_ms": 481
  }
}
```

### 3. Retrieve Document by Name
`GET /api/v1/documents/{document_name}`

### 4. List All Processed Documents
`GET /api/v1/documents`

---

## 📊 Financial Validation Rules & Tolerance

1. **Invoice:**
   - Line Item: `Quantity * Unit Price ≈ Line Amount`
   - Subtotal Reconciliation: `Sum(Line Amounts) ≈ Subtotal`
   - Invoice Total: `Subtotal + Tax Amount - Discount ≈ Total Amount`
   - Cash Change: `Cash Paid - Total Amount ≈ Change`

2. **Balance Sheet:**
   - Accounting Identity: `Total Capital & Liabilities ≈ Total Assets` (or `Total Liabilities + Total Equity ≈ Total Assets`).

3. **Profit & Loss:**
   - Income Check: `Interest Earned + Other Income ≈ Total Income`
   - Expenditure Check: `COGS + Operating Expenses ≈ Total Expenditure`
   - Net Profit: `Total Income - Total Expenditure - Tax ≈ Net Profit`

4. **Cash Flow Statement:**
   - Net Cash Flow: `Operating CF + Investing CF + Financing CF + FX Adjustment ≈ Net Change in Cash`
   - Cash Reconciliation: `Opening Cash + Net Change in Cash ≈ Closing Cash`
   - Handles bracketed numbers `(123.45)` as negative numbers `-123.45`.

**Numerical Tolerance:** Configured at 2% relative tolerance or $1.00 absolute tolerance (`FINANCIAL_TOLERANCE_ABSOLUTE = 1.00`). If a required field is missing from the source document, the check returns status `NOT_APPLICABLE` instead of hallucinating values.

---

## 🗄️ Database & Persistence Approach

All processed document metadata and structured extraction payloads are stored in an **SQLite** database using **SQLAlchemy ORM**. When a document with an existing filename is processed again, the record is automatically updated to retain the latest processing result.

---

## 🚨 Known Limitations & Production Recommendations

### Current Limitations:
1. **Tesseract Dependency:** Scanned image OCR accuracy depends on local Tesseract installation or external cloud Vision API key configuration.
2. **Page Limit:** Documents above 3 pages are rejected by input validation rules as required by specification.

### Production Improvements:
1. **Asynchronous Queue:** Integrate Celery or Redis Queue (RQ) for handling heavy OCR processing asynchronously.
2. **Cloud Object Storage:** Store raw uploaded files in AWS S3 or Google Cloud Storage instead of temporary local buffers.
3. **Multi-Tenant Authentication:** Add JWT authentication and API key rate limiting per organization.

---

## 🤖 Generative AI & Tool Usage Declaration

- **AI Assistants Used:** Antigravity AI Code Assistant (Gemini 3.6 Flash).
- **Usage Areas:** Architectural scaffolding, FastAPI route generation, Jinja2/CSS glassmorphism template design, pytest test suite setup, and financial reconciliation rule logic.
