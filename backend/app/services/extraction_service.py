import re
import json
import httpx
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger

class ExtractionService:

    @staticmethod
    def parse_number(text: str) -> Optional[float]:
        if not text:
            return None
        clean = text.strip()
        # Handle bracketed negative numbers like (12,345.67) or (100)
        is_negative = False
        if clean.startswith("(") and clean.endswith(")"):
            is_negative = True
            clean = clean[1:-1].strip()
        elif clean.startswith("-"):
            is_negative = True
            clean = clean[1:].strip()
        
        # Remove currency symbols and commas
        clean = re.sub(r"[^\d.]", "", clean)
        if not clean:
            return None
        try:
            val = float(clean)
            return -val if is_negative else val
        except ValueError:
            return None

    @classmethod
    def extract_field_with_evidence(
        cls,
        text: str,
        patterns: List[str],
        page_number: int = 1,
        default_confidence: float = 0.95
    ) -> Dict[str, Any]:
        """Helper to find regex matches and attach evidence/confidence"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                full_line = match.group(0).strip()
                val_str = match.group(1).strip() if match.groups() else full_line
                num_val = cls.parse_number(val_str)
                final_val = num_val if num_val is not None else val_str
                return {
                    "value": final_val,
                    "confidence": default_confidence,
                    "page_number": page_number,
                    "evidence": {
                        "source_text": full_line,
                        "page_number": page_number
                    }
                }
        return {
            "value": None,
            "confidence": None,
            "page_number": page_number,
            "evidence": None
        }

    @classmethod
    def extract_data(
        cls,
        document_name: str,
        document_type: str,
        ocr_pages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Main extraction entry point.
        Checks for external LLM key if available, otherwise runs robust rule-based & table parsing.
        """
        logger.info(f"Extracting fields for document '{document_name}' of type '{document_type}'")
        
        full_text = "\n".join([page.get("text", "") for page in ocr_pages])
        
        # Try OpenAI or Gemini LLM extraction if API key present
        if settings.OPENAI_API_KEY or settings.GEMINI_API_KEY:
            try:
                llm_result = cls._extract_with_llm(document_type, full_text)
                if llm_result:
                    return llm_result
            except Exception as e:
                logger.warning(f"LLM extraction failed for {document_name}: {e}. Falling back to heuristic extractor.")

        # Fallback to specialized document parsers
        if document_type == "invoice":
            return cls._extract_invoice(ocr_pages, full_text)
        elif document_type == "balance_sheet":
            return cls._extract_balance_sheet(ocr_pages, full_text)
        elif document_type == "profit_and_loss":
            return cls._extract_profit_and_loss(ocr_pages, full_text)
        elif document_type == "cash_flow_statement":
            return cls._extract_cash_flow(ocr_pages, full_text)
        else:
            return cls._extract_generic(ocr_pages, full_text)

    @classmethod
    def _extract_invoice(cls, ocr_pages: List[Dict[str, Any]], text: str) -> Dict[str, Any]:
        p1_text = ocr_pages[0].get("text", "") if ocr_pages else text

        inv_num = cls.extract_field_with_evidence(
            p1_text,
            [r"invoice\s*#?\s*:?\s*([A-Z0-9-]+)", r"inv\s*#?\s*:?\s*([A-Z0-9-]+)", r"receipt\s*#?\s*:?\s*([A-Z0-9-]+)"],
            1, 0.98
        )
        inv_date = cls.extract_field_with_evidence(
            p1_text,
            [r"date\s*:?\s*(\d{4}[-/.]\d{2}[-/.]\d{2})", r"date\s*:?\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})"],
            1, 0.95
        )
        vendor = cls.extract_field_with_evidence(
            p1_text,
            [r"vendor\s*:?\s*([A-Za-z0-9\s.,&]+)", r"from\s*:?\s*([A-Za-z0-9\s.,&]+)", r"^([A-Z0-9\s]{3,30}\b(?:Inc|LLC|Corp|Ltd|Co|Tech|Services)?)"],
            1, 0.90
        )
        customer = cls.extract_field_with_evidence(
            p1_text,
            [r"bill\s*to\s*:?\s*([A-Za-z0-9\s.,&]+)", r"customer\s*:?\s*([A-Za-z0-9\s.,&]+)"],
            1, 0.90
        )
        currency = cls.extract_field_with_evidence(
            p1_text,
            [r"currency\s*:?\s*([A-Z]{3})", r"\b(USD|EUR|GBP|INR|CAD|AUD)\b"],
            1, 0.99
        )
        subtotal = cls.extract_field_with_evidence(
            p1_text,
            [r"subtotal\s*:?\s*[\$₹€£]?\s*([\d,]+\.?\d*)", r"sub-total\s*:?\s*[\$₹€£]?\s*([\d,]+\.?\d*)"],
            1, 0.97
        )
        tax = cls.extract_field_with_evidence(
            p1_text,
            [r"tax\s*(?:amount)?\s*:?\s*[\$₹€£]?\s*([\d,]+\.?\d*)", r"vat\s*:?\s*[\$₹€£]?\s*([\d,]+\.?\d*)", r"gst\s*:?\s*[\$₹€£]?\s*([\d,]+\.?\d*)"],
            1, 0.96
        )
        discount = cls.extract_field_with_evidence(
            p1_text,
            [r"discount\s*:?\s*[\$₹€£]?\s*([\d,]+\.?\d*)"],
            1, 0.95
        )
        total = cls.extract_field_with_evidence(
            p1_text,
            [r"total\s*(?:amount)?\s*(?:due)?\s*:?\s*[\$₹€£]?\s*([\d,]+\.?\d*)", r"amount\s*due\s*:?\s*[\$₹€£]?\s*([\d,]+\.?\d*)"],
            1, 0.99
        )
        cash_paid = cls.extract_field_with_evidence(
            p1_text,
            [r"cash\s*(?:paid)?\s*:?\s*[\$₹€£]?\s*([\d,]+\.?\d*)", r"amount\s*paid\s*:?\s*[\$₹€£]?\s*([\d,]+\.?\d*)"],
            1, 0.92
        )
        change = cls.extract_field_with_evidence(
            p1_text,
            [r"change\s*:?\s*[\$₹€£]?\s*([\d,]+\.?\d*)", r"change\s*due\s*:?\s*[\$₹€£]?\s*([\d,]+\.?\d*)"],
            1, 0.90
        )

        # Parse line items table if visible
        line_items = []
        lines = p1_text.split("\n")
        for line in lines:
            line_match = re.search(r"([A-Za-z0-9\s\-_]+)\s+(\d+)\s+[\$₹€£]?\s*([\d,]+\.?\d*)\s+[\$₹€£]?\s*([\d,]+\.?\d*)", line)
            if line_match:
                desc = line_match.group(1).strip()
                if desc.lower() not in ["subtotal", "total", "tax", "discount"]:
                    qty = int(line_match.group(2))
                    uprice = float(line_match.group(3).replace(",", ""))
                    amt = float(line_match.group(4).replace(",", ""))
                    line_items.append({
                        "description": desc,
                        "quantity": qty,
                        "unit_price": uprice,
                        "amount": amt
                    })

        return {
            "invoice_number": inv_num,
            "invoice_date": inv_date,
            "vendor_name": vendor,
            "customer_name": customer,
            "currency": currency if currency["value"] else {"value": "USD", "confidence": 0.90, "page_number": 1, "evidence": None},
            "subtotal": subtotal,
            "tax_amount": tax,
            "discount": discount if discount["value"] is not None else {"value": 0.0, "confidence": 0.90, "page_number": 1, "evidence": None},
            "total_amount": total,
            "cash_paid": cash_paid,
            "change": change,
            "line_items": line_items
        }

    @classmethod
    def _extract_balance_sheet(cls, ocr_pages: List[Dict[str, Any]], text: str) -> Dict[str, Any]:
        p1 = ocr_pages[0].get("text", "") if ocr_pages else text

        period = cls.extract_field_with_evidence(
            p1,
            [r"as\s*at\s*([A-Za-z0-9\s,]+)", r"period\s*ended\s*([A-Za-z0-9\s,]+)", r"year\s*ended\s*(\d{4})", r"\b(20\d{2})\b"],
            1, 0.95
        )
        currency = cls.extract_field_with_evidence(
            p1,
            [r"currency\s*:?\s*([A-Z]{3})", r"\b(USD|EUR|GBP|INR|CAD|AUD)\b", r"in\s*(₹|USD|EUR|\$|Rupees|Thousands|Millions)"],
            1, 0.95
        )
        total_assets = cls.extract_field_with_evidence(
            p1,
            [r"total\s*assets\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)", r"total\s*property\s*and\s*assets\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.98
        )
        total_liab = cls.extract_field_with_evidence(
            p1,
            [r"total\s*liabilities\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)", r"total\s*capital\s*and\s*liabilities\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.98
        )
        total_equity = cls.extract_field_with_evidence(
            p1,
            [r"total\s*equity\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)", r"total\s*shareholders['\s]*equity\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.95
        )

        # Comparative period line items parsing
        line_items = cls._extract_statement_rows(text)

        return {
            "period": period,
            "currency": currency if currency["value"] else {"value": "USD", "confidence": 0.90, "page_number": 1, "evidence": None},
            "total_assets": total_assets,
            "total_liabilities": total_liab,
            "total_equity": total_equity,
            "statement_line_items": line_items
        }

    @classmethod
    def _extract_profit_and_loss(cls, ocr_pages: List[Dict[str, Any]], text: str) -> Dict[str, Any]:
        p1 = ocr_pages[0].get("text", "") if ocr_pages else text

        period = cls.extract_field_with_evidence(
            p1,
            [r"for\s*the\s*year\s*ended\s*([A-Za-z0-9\s,]+)", r"period\s*ended\s*([A-Za-z0-9\s,]+)", r"\b(20\d{2})\b"],
            1, 0.95
        )
        currency = cls.extract_field_with_evidence(
            p1,
            [r"currency\s*:?\s*([A-Z]{3})", r"\b(USD|EUR|GBP|INR|CAD|AUD)\b"],
            1, 0.95
        )
        revenue = cls.extract_field_with_evidence(
            p1,
            [r"revenue\s*(?:from\s*operations)?\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)", r"total\s*income\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.98
        )
        interest_earned = cls.extract_field_with_evidence(
            p1,
            [r"interest\s*earned\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.95
        )
        other_income = cls.extract_field_with_evidence(
            p1,
            [r"other\s*income\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.95
        )
        total_income = cls.extract_field_with_evidence(
            p1,
            [r"total\s*income\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)", r"total\s*revenue\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.98
        )
        cogs = cls.extract_field_with_evidence(
            p1,
            [r"cost\s*of\s*sales\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)", r"cogs\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.95
        )
        operating_exp = cls.extract_field_with_evidence(
            p1,
            [r"operating\s*expenses\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)", r"total\s*expenditure\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.96
        )
        total_expenditure = cls.extract_field_with_evidence(
            p1,
            [r"total\s*expenditure\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)", r"total\s*expenses\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.98
        )
        gross_profit = cls.extract_field_with_evidence(
            p1,
            [r"gross\s*profit\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.95
        )
        tax = cls.extract_field_with_evidence(
            p1,
            [r"tax\s*expense\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)", r"provision\s*for\s*tax\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.95
        )
        net_profit = cls.extract_field_with_evidence(
            p1,
            [r"net\s*profit\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)", r"profit\s*after\s*tax\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)", r"consolidated\s*net\s*profit\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.99
        )

        line_items = cls._extract_statement_rows(text)

        return {
            "period": period,
            "currency": currency if currency["value"] else {"value": "USD", "confidence": 0.90, "page_number": 1, "evidence": None},
            "revenue": revenue,
            "interest_earned": interest_earned,
            "other_income": other_income,
            "total_income": total_income,
            "cost_of_sales": cogs,
            "operating_expenses": operating_exp,
            "total_expenditure": total_expenditure,
            "gross_profit": gross_profit,
            "tax": tax,
            "net_profit": net_profit,
            "statement_line_items": line_items
        }

    @classmethod
    def _extract_cash_flow(cls, ocr_pages: List[Dict[str, Any]], text: str) -> Dict[str, Any]:
        p1 = ocr_pages[0].get("text", "") if ocr_pages else text

        period = cls.extract_field_with_evidence(
            p1,
            [r"for\s*the\s*year\s*ended\s*([A-Za-z0-9\s,]+)", r"period\s*ended\s*([A-Za-z0-9\s,]+)", r"\b(20\d{2})\b"],
            1, 0.95
        )
        currency = cls.extract_field_with_evidence(
            p1,
            [r"currency\s*:?\s*([A-Z]{3})", r"\b(USD|EUR|GBP|INR|CAD|AUD)\b"],
            1, 0.95
        )
        operating_cf = cls.extract_field_with_evidence(
            p1,
            [r"(?:net\s*)?cash\s*(?:flow\s*)?(?:from|used\s*in)?\s*operating\s*activities\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.98
        )
        investing_cf = cls.extract_field_with_evidence(
            p1,
            [r"(?:net\s*)?cash\s*(?:flow\s*)?(?:from|used\s*in)?\s*investing\s*activities\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.98
        )
        financing_cf = cls.extract_field_with_evidence(
            p1,
            [r"(?:net\s*)?cash\s*(?:flow\s*)?(?:from|used\s*in)?\s*financing\s*activities\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.98
        )
        fx_adj = cls.extract_field_with_evidence(
            p1,
            [r"fx\s*(?:adjustment)?\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)", r"effect\s*of\s*exchange\s*rate\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.90
        )
        net_change = cls.extract_field_with_evidence(
            p1,
            [r"net\s*(?:increase|decrease)\s*in\s*cash\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)", r"net\s*change\s*in\s*cash\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.98
        )
        opening_cash = cls.extract_field_with_evidence(
            p1,
            [r"opening\s*cash\s*(?:and\s*cash\s*equivalents)?\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)", r"cash\s*at\s*beginning\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.98
        )
        closing_cash = cls.extract_field_with_evidence(
            p1,
            [r"closing\s*cash\s*(?:and\s*cash\s*equivalents)?\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)", r"cash\s*at\s*end\s*:?\s*[\$₹€£]?\s*([\d,\(\)]+\.?\d*)"],
            1, 0.98
        )

        line_items = cls._extract_statement_rows(text)

        return {
            "period": period,
            "currency": currency if currency["value"] else {"value": "USD", "confidence": 0.90, "page_number": 1, "evidence": None},
            "operating_cash_flow": operating_cf,
            "investing_cash_flow": investing_cf,
            "financing_cash_flow": financing_cf,
            "fx_adjustment": fx_adj if fx_adj["value"] is not None else {"value": 0.0, "confidence": 0.90, "page_number": 1, "evidence": None},
            "net_change_in_cash": net_change,
            "opening_cash": opening_cash,
            "closing_cash": closing_cash,
            "statement_line_items": line_items
        }

    @classmethod
    def _extract_generic(cls, ocr_pages: List[Dict[str, Any]], text: str) -> Dict[str, Any]:
        return {
            "full_text_snippet": text[:500],
            "line_count": len(text.splitlines())
        }

    @classmethod
    def _extract_statement_rows(cls, text: str) -> List[Dict[str, Any]]:
        rows = []
        for line in text.split("\n"):
            # Match line item description followed by numbers (e.g., "Cash & Bank Balances 1,234.00 (500.00)")
            m = re.search(r"^([A-Za-z0-9\s\-_&,\.]{3,50})\s+([\d,\(\)]+\.?\d*)\s*([\d,\(\)]+\.?\d*)?", line.strip())
            if m:
                desc = m.group(1).strip()
                val1 = cls.parse_number(m.group(2))
                val2 = cls.parse_number(m.group(3)) if m.group(3) else None
                if val1 is not None:
                    rows.append({
                        "description": desc,
                        "current_period_value": val1,
                        "previous_period_value": val2
                    })
        return rows[:25]  # Cap at top visible rows

    @classmethod
    def _extract_with_llm(cls, document_type: str, full_text: str) -> Optional[Dict[str, Any]]:
        """Call external LLM API if key is set"""
        # Placeholder for external LLM integration if user provides GEMINI_API_KEY or OPENAI_API_KEY
        return None
