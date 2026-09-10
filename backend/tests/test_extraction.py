import pytest
from backend.app.services.financial_validation_service import FinancialValidationService

def test_invoice_validation_pass():
    data = {
        "subtotal": 1000.00,
        "tax_amount": 100.00,
        "discount": 50.00,
        "total_amount": 1050.00,
        "line_items": [
            {"description": "Item A", "quantity": 2, "unit_price": 500.00, "amount": 1000.00}
        ]
    }
    res = FinancialValidationService.validate("invoice", data)
    assert res.overall_status == "PASS"
    assert len(res.checks) >= 2
    for c in res.checks:
        assert c.status == "PASS"

def test_invoice_validation_calculation_fail():
    data = {
        "subtotal": 1000.00,
        "tax_amount": 100.00,
        "discount": 50.00,
        "total_amount": 9999.00,  # Intentional calculation discrepancy!
        "line_items": []
    }
    res = FinancialValidationService.validate("invoice", data)
    assert res.overall_status == "FAIL"
    fail_check = [c for c in res.checks if c.name == "invoice_total_check"][0]
    assert fail_check.status == "FAIL"
    assert len(res.issues) >= 1

def test_missing_fields_not_applicable():
    data = {
        "vendor_name": "ABC Tech"
        # total_amount, subtotal missing
    }
    res = FinancialValidationService.validate("invoice", data)
    assert res.overall_status == "PASS"  # No failing checks, check returned NOT_APPLICABLE
    na_check = res.checks[0]
    assert na_check.status == "NOT_APPLICABLE"

def test_balance_sheet_validation():
    data = {
        "total_assets": 50000.00,
        "total_liabilities": 20000.00,
        "total_equity": 30000.00
    }
    res = FinancialValidationService.validate("balance_sheet", data)
    assert res.overall_status == "PASS"
    check = res.checks[0]
    assert check.status == "PASS"
    assert check.calculated_value == 50000.00

def test_cash_flow_validation_negative_numbers():
    data = {
        "operating_cash_flow": 12000.00,
        "investing_cash_flow": -4000.00,
        "financing_cash_flow": -2000.00,
        "fx_adjustment": 0.00,
        "net_change_in_cash": 6000.00,
        "opening_cash": 10000.00,
        "closing_cash": 16000.00
    }
    res = FinancialValidationService.validate("cash_flow_statement", data)
    assert res.overall_status == "PASS"
    assert len(res.checks) == 2
    for c in res.checks:
        assert c.status == "PASS"
