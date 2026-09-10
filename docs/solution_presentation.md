# Technical Solution Presentation (PPT Deck Outline)
## Intelligent Document Extraction, Validation & API Platform
**Role:** AI Engineer Intern Technical Case Study

---

## Slide 1: Title & Executive Summary
- **Project Title:** Intelligent Financial Document Extraction, Validation & API Platform
- **Objective:** End-to-end service for processing PDF, JPG, and PNG financial documents (Invoices, Balance Sheets, Profit & Loss Statements, Cash Flow Statements).
- **Core Value Delivered:** Automated field & table extraction, evidence grounding, financial reconciliation math checks (PASS/FAIL/NOT_APPLICABLE), persistent database storage, REST APIs, and a sleek frontend dashboard.

---

## Slide 2: Problem Statement & Scope
- **Challenge:** Financial teams receive un-structured PDFs & image scans with diverse layouts, line items, and varying quality. Manual extraction is error-prone.
- **In-Scope Categories (4 Document Types):**
  1. **Invoice:** Header, parties, line items table, subtotal, tax, discount, total amount, cash paid, change.
  2. **Balance Sheet:** Periods, total assets, total liabilities, total equity, statement rows.
  3. **Profit & Loss:** Revenue, interest earned, COGS, operating expenses, tax, net profit.
  4. **Cash Flow Statement:** Operating, investing, financing cash flows, FX adjustment, opening & closing cash.

---

## Slide 3: Architecture & System Flow
- **Ingestion & Validation:** Multipart upload validation (file type, empty/corrupt check, max 3 pages limit).
- **OCR Engine:** Pluggable PyMuPDF / pdfplumber / PyTesseract text extraction.
- **Extraction Engine:** AI Structured Output Parser with Regex Heuristic fallback & Grounding Evidence.
- **Financial Validation Service:** Reconciles accounting formulas with configurable numerical tolerance (`Quantity * Unit Price ≈ Line Total`, `Assets ≈ Liabilities + Equity`, `Income - Exp ≈ Net Profit`, `Opening Cash + Net Change ≈ Closing Cash`).
- **Persistence & API:** SQLite + SQLAlchemy ORM, FastAPI REST endpoints (`/documents/process`, `/documents/{name}`, `/documents`, `/health`).
- **Dashboard:** Deployed HTML5/CSS Glassmorphism UI with real-time process actions and raw JSON view.

---

## Slide 4: Key Technical Features & Financial Validation Rules
| Document Type | Formula / Check | Handling Missing Data | Status Returned |
|---|---|---|---|
| **Invoice** | `subtotal + tax - discount ≈ total_amount` | Marked `NOT_APPLICABLE` | PASS / FAIL / NOT_APPLICABLE |
| **Balance Sheet** | `Total Liabilities + Equity ≈ Total Assets` | Per-period independent validation | PASS / FAIL / NOT_APPLICABLE |
| **Profit & Loss** | `Total Income - Expenditure - Tax ≈ Net Profit` | Tolerance applied (2% / 1.0 abs) | PASS / FAIL / NOT_APPLICABLE |
| **Cash Flow** | `Operating + Investing + Financing + FX ≈ Net Change` | Parentheses `(x)` converted to negative | PASS / FAIL / NOT_APPLICABLE |

---

## Slide 5: Quality Assurance & Testing Results
- **Automated Test Suite:** `pytest` suite containing **15 unit and integration tests** (100% pass rate).
- **Validation Cases Tested:**
  - File format & >3 page limit rejections (HTTP 400).
  - Clean extraction on actual dataset PDFs and scanned JPG invoices.
  - Reconciliation pass scenarios & intentional financial discrepancy detection (status FAIL).
  - Missing field handling returning `NOT_APPLICABLE`.

---

## Slide 6: Deployment & Operational Readiness
- **Dockerized Containerization:** Multi-stage Docker build with Tesseract OCR & Poppler runtime.
- **Cloud Hosting Platforms:** Fully compatible with Render, Railway, Koyeb, Docker Compose.
- **API Documentation:** Interactive Swagger / OpenAPI documentation available live at `/docs`.
