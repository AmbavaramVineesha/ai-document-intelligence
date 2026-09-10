import os
import json
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal, Base, engine
from backend.app.services.document_service import DocumentService

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

def process_and_save(file_path: str, document_type: str, output_name: str):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    print(f"Processing sample: {file_path} (Type: {document_type})")
    with open(file_path, "rb") as f:
        content = f.read()

    file_name = os.path.basename(file_path)
    db = SessionLocal()
    try:
        response = DocumentService.process_document(
            db=db,
            file_name=file_name,
            content=content,
            document_type=document_type
        )
        res_json = response.model_dump()
        
        out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_outputs"))
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, output_name)
        
        with open(out_file, "w", encoding="utf-8") as out_f:
            json.dump(res_json, out_f, indent=2)
            
        print(f"Saved result to {out_file} (Status: {res_json['processing_status']})")
    finally:
        db.close()

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    samples = [
        (os.path.join(base_dir, "sample_documents", "balance_sheet", "Consolidated Balance Sheet 2024.pdf"), "balance_sheet", "sample_balance_sheet_response.json"),
        (os.path.join(base_dir, "sample_documents", "cash_flows", "Consolidated Cash Flow Statement 2024.pdf"), "cash_flow_statement", "sample_cash_flow_response.json"),
        (os.path.join(base_dir, "sample_documents", "profit_loss", "Consolidated Profit & Loss 2024.pdf"), "profit_and_loss", "sample_profit_loss_response.json"),
        (os.path.join(base_dir, "sample_documents", "invoices", "batch1-1109.jpg"), "invoice", "sample_invoice_response.json"),
    ]

    for path, doc_type, out_json in samples:
        process_and_save(path, doc_type, out_json)
