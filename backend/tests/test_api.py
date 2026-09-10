import io
import pytest

def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_unsupported_file_type_api(client):
    files = {"file": ("test.docx", b"dummy content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    data = {"document_type": "invoice"}
    response = client.post("/api/v1/documents/process", files=files, data=data)
    assert response.status_code == 400
    err = response.json()
    assert err["error"]["code"] == "UNSUPPORTED_FILE_TYPE"

def test_invalid_document_type_api(client):
    files = {"file": ("test.pdf", b"%PDF-1.4 dummy", "application/pdf")}
    data = {"document_type": "tax_return_invalid"}
    response = client.post("/api/v1/documents/process", files=files, data=data)
    assert response.status_code == 400
    err = response.json()
    assert err["error"]["code"] == "INVALID_DOCUMENT_TYPE"

def test_process_valid_invoice_api(client):
    fake_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000062 00000 n\n0000000117 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n166\n%%EOF"
    files = {"file": ("test_invoice_01.pdf", fake_pdf, "application/pdf")}
    data = {"document_type": "invoice"}
    
    response = client.post("/api/v1/documents/process", files=files, data=data)
    assert response.status_code == 200
    res = response.json()
    assert res["document_name"] == "test_invoice_01.pdf"
    assert res["document_type"] == "invoice"
    assert "file_validation" in res
    assert res["file_validation"]["status"] == "PASS"

def test_get_document_by_name(client):
    response = client.get("/api/v1/documents/test_invoice_01.pdf")
    assert response.status_code == 200
    res = response.json()
    assert res["document_name"] == "test_invoice_01.pdf"

def test_list_documents(client):
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert len(data["documents"]) >= 1
