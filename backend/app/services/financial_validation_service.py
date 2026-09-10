import math
from typing import Dict, Any, List
from backend.app.core.config import settings
from backend.app.schemas.extraction import FinancialCheck, FinancialValidationResult
from backend.app.core.logging import logger

class FinancialValidationService:

    @classmethod
    def validate(cls, document_type: str, extracted_data: Dict[str, Any]) -> FinancialValidationResult:
        logger.info(f"Performing financial validation checks for document_type '{document_type}'")
        
        checks: List[FinancialCheck] = []
        
        if document_type == "invoice":
            checks = cls._validate_invoice(extracted_data)
        elif document_type == "balance_sheet":
            checks = cls._validate_balance_sheet(extracted_data)
        elif document_type == "profit_and_loss":
            checks = cls._validate_profit_and_loss(extracted_data)
        elif document_type == "cash_flow_statement":
            checks = cls._validate_cash_flow(extracted_data)
        else:
            checks = []

        # Determine overall status
        failed_checks = [c for c in checks if c.status == "FAIL"]
        overall_status = "FAIL" if failed_checks else ("PASS" if checks else "NOT_APPLICABLE")
        
        issues = [f"Validation check '{c.name}' failed: calculated {c.calculated_value} vs reported {c.reported_value} (variance: {c.variance})" for c in failed_checks]

        return FinancialValidationResult(
            checks=checks,
            overall_status=overall_status,
            issues=issues
        )

    @classmethod
    def _extract_val(cls, item: Any) -> Any:
        """Helper to extract raw scalar float/int value from ExtractedField dict or direct value"""
        if isinstance(item, dict):
            return item.get("value")
        return item

    @classmethod
    def _is_within_tolerance(cls, calculated: float, reported: float) -> bool:
        diff = abs(calculated - reported)
        if diff <= settings.FINANCIAL_TOLERANCE_ABSOLUTE:
            return True
        if reported != 0:
            rel_diff = diff / abs(reported)
            return rel_diff <= settings.FINANCIAL_TOLERANCE_PERCENT
        return False

    @classmethod
    def _validate_invoice(cls, data: Dict[str, Any]) -> List[FinancialCheck]:
        checks = []

        subtotal = cls._extract_val(data.get("subtotal"))
        tax_amount = cls._extract_val(data.get("tax_amount"))
        discount = cls._extract_val(data.get("discount"))
        total_amount = cls._extract_val(data.get("total_amount"))
        cash_paid = cls._extract_val(data.get("cash_paid"))
        change = cls._extract_val(data.get("change"))
        line_items = data.get("line_items", [])

        # 1. Line Item Quantity x Unit Price = Amount
        if line_items:
            for idx, item in enumerate(line_items):
                qty = item.get("quantity")
                uprice = item.get("unit_price")
                amt = item.get("amount")
                if qty is not None and uprice is not None and amt is not None:
                    calc_amt = round(float(qty) * float(uprice), 2)
                    reported_amt = round(float(amt), 2)
                    var = round(abs(calc_amt - reported_amt), 2)
                    status = "PASS" if cls._is_within_tolerance(calc_amt, reported_amt) else "FAIL"
                    checks.append(FinancialCheck(
                        name=f"line_item_{idx+1}_math",
                        formula="quantity * unit_price",
                        operands={"quantity": qty, "unit_price": uprice},
                        calculated_value=calc_amt,
                        reported_value=reported_amt,
                        variance=var,
                        status=status,
                        details=f"Item {idx+1}: {item.get('description', '')}"
                    ))

        # 2. Line Items Sum = Subtotal
        if line_items and subtotal is not None:
            sum_lines = round(sum(float(item.get("amount", 0)) for item in line_items), 2)
            rep_sub = round(float(subtotal), 2)
            var = round(abs(sum_lines - rep_sub), 2)
            status = "PASS" if cls._is_within_tolerance(sum_lines, rep_sub) else "FAIL"
            checks.append(FinancialCheck(
                name="subtotal_reconciliation_check",
                formula="sum(line_item_amounts)",
                operands={"line_items_count": len(line_items)},
                calculated_value=sum_lines,
                reported_value=rep_sub,
                variance=var,
                status=status
            ))

        # 3. Invoice Total Check: Subtotal + Tax - Discount = Total
        if subtotal is not None and total_amount is not None:
            tax_val = float(tax_amount) if tax_amount is not None else 0.0
            disc_val = float(discount) if discount is not None else 0.0
            sub_val = float(subtotal)
            tot_val = float(total_amount)

            calc_tot = round(sub_val + tax_val - disc_val, 2)
            var = round(abs(calc_tot - tot_val), 2)
            status = "PASS" if cls._is_within_tolerance(calc_tot, tot_val) else "FAIL"

            checks.append(FinancialCheck(
                name="invoice_total_check",
                formula="subtotal + tax_amount - discount",
                operands={"subtotal": sub_val, "tax_amount": tax_val, "discount": disc_val},
                calculated_value=calc_tot,
                reported_value=tot_val,
                variance=var,
                status=status
            ))
        elif total_amount is None:
            checks.append(FinancialCheck(
                name="invoice_total_check",
                formula="subtotal + tax_amount - discount",
                operands={"subtotal": subtotal, "tax_amount": tax_amount, "discount": discount},
                calculated_value=None,
                reported_value=None,
                variance=None,
                status="NOT_APPLICABLE",
                details="Required total_amount field not present in source document."
            ))

        # 4. Cash Paid - Total = Change
        if cash_paid is not None and change is not None and total_amount is not None:
            c_paid = float(cash_paid)
            tot = float(total_amount)
            rep_change = float(change)
            calc_change = round(c_paid - tot, 2)
            var = round(abs(calc_change - rep_change), 2)
            status = "PASS" if cls._is_within_tolerance(calc_change, rep_change) else "FAIL"
            checks.append(FinancialCheck(
                name="cash_change_check",
                formula="cash_paid - total_amount",
                operands={"cash_paid": c_paid, "total_amount": tot},
                calculated_value=calc_change,
                reported_value=rep_change,
                variance=var,
                status=status
            ))

        return checks

    @classmethod
    def _validate_balance_sheet(cls, data: Dict[str, Any]) -> List[FinancialCheck]:
        checks = []

        total_assets = cls._extract_val(data.get("total_assets"))
        total_liabilities = cls._extract_val(data.get("total_liabilities"))
        total_equity = cls._extract_val(data.get("total_equity"))

        # Accounting Equation: Total Capital & Liabilities = Total Assets
        if total_assets is not None and (total_liabilities is not None or total_equity is not None):
            rep_assets = float(total_assets)
            liab_val = float(total_liabilities) if total_liabilities is not None else 0.0
            eq_val = float(total_equity) if total_equity is not None else 0.0
            
            # If total_liabilities already represents Total Capital & Liabilities
            if liab_val > 0 and abs(liab_val - rep_assets) < abs((liab_val + eq_val) - rep_assets):
                calc_tot = liab_val
                operands = {"total_capital_and_liabilities": liab_val}
            else:
                calc_tot = liab_val + eq_val
                operands = {"total_liabilities": liab_val, "total_equity": eq_val}

            var = round(abs(calc_tot - rep_assets), 2)
            status = "PASS" if cls._is_within_tolerance(calc_tot, rep_assets) else "FAIL"

            checks.append(FinancialCheck(
                name="balance_sheet_identity_check",
                formula="Total Capital & Liabilities = Total Assets",
                operands=operands,
                calculated_value=calc_tot,
                reported_value=rep_assets,
                variance=var,
                status=status
            ))
        else:
            checks.append(FinancialCheck(
                name="balance_sheet_identity_check",
                formula="Total Capital & Liabilities = Total Assets",
                operands={"total_assets": total_assets, "total_liabilities": total_liabilities, "total_equity": total_equity},
                calculated_value=None,
                reported_value=None,
                variance=None,
                status="NOT_APPLICABLE",
                details="Missing total_assets or total_liabilities/equity fields for reconciliation."
            ))

        return checks

    @classmethod
    def _validate_profit_and_loss(cls, data: Dict[str, Any]) -> List[FinancialCheck]:
        checks = []

        rev = cls._extract_val(data.get("revenue"))
        interest_earned = cls._extract_val(data.get("interest_earned"))
        other_income = cls._extract_val(data.get("other_income"))
        tot_income = cls._extract_val(data.get("total_income"))

        cogs = cls._extract_val(data.get("cost_of_sales"))
        op_exp = cls._extract_val(data.get("operating_expenses"))
        tot_exp = cls._extract_val(data.get("total_expenditure"))

        net_profit = cls._extract_val(data.get("net_profit"))
        tax = cls._extract_val(data.get("tax"))

        # 1. Total Income Check
        if (interest_earned is not None or other_income is not None) and tot_income is not None:
            ie = float(interest_earned) if interest_earned is not None else 0.0
            oi = float(other_income) if other_income is not None else 0.0
            r_val = float(rev) if rev is not None else 0.0
            
            calc_inc = ie + oi if (ie > 0 or oi > 0) else r_val + oi
            rep_inc = float(tot_income)
            var = round(abs(calc_inc - rep_inc), 2)
            status = "PASS" if cls._is_within_tolerance(calc_inc, rep_inc) else "FAIL"

            checks.append(FinancialCheck(
                name="total_income_reconciliation_check",
                formula="Interest Earned + Other Income = Total Income",
                operands={"interest_earned": ie, "other_income": oi},
                calculated_value=calc_inc,
                reported_value=rep_inc,
                variance=var,
                status=status
            ))

        # 2. Total Expenditure Check
        if (cogs is not None or op_exp is not None) and tot_exp is not None:
            c_val = float(cogs) if cogs is not None else 0.0
            o_val = float(op_exp) if op_exp is not None else 0.0
            calc_exp = c_val + o_val
            rep_exp = float(tot_exp)
            var = round(abs(calc_exp - rep_exp), 2)
            status = "PASS" if cls._is_within_tolerance(calc_exp, rep_exp) else "FAIL"

            checks.append(FinancialCheck(
                name="total_expenditure_reconciliation_check",
                formula="COGS + Operating Expenses = Total Expenditure",
                operands={"cogs": c_val, "operating_expenses": o_val},
                calculated_value=calc_exp,
                reported_value=rep_exp,
                variance=var,
                status=status
            ))

        # 3. Net Profit Check: Total Income - Total Expenditure = Net Profit
        if tot_income is not None and tot_exp is not None and net_profit is not None:
            inc = float(tot_income)
            exp = float(tot_exp)
            rep_np = float(net_profit)
            tax_val = float(tax) if tax is not None else 0.0
            
            calc_np = round(inc - exp - tax_val, 2)
            var = round(abs(calc_np - rep_np), 2)
            status = "PASS" if cls._is_within_tolerance(calc_np, rep_np) else "FAIL"

            checks.append(FinancialCheck(
                name="net_profit_reconciliation_check",
                formula="Total Income - Total Expenditure - Tax = Net Profit",
                operands={"total_income": inc, "total_expenditure": exp, "tax": tax_val},
                calculated_value=calc_np,
                reported_value=rep_np,
                variance=var,
                status=status
            ))
        elif net_profit is None:
            checks.append(FinancialCheck(
                name="net_profit_reconciliation_check",
                formula="Total Income - Total Expenditure = Net Profit",
                operands={"total_income": tot_income, "total_expenditure": tot_exp},
                calculated_value=None,
                reported_value=None,
                variance=None,
                status="NOT_APPLICABLE",
                details="Missing net_profit or total income/expenditure fields."
            ))

        return checks

    @classmethod
    def _validate_cash_flow(cls, data: Dict[str, Any]) -> List[FinancialCheck]:
        checks = []

        op_cf = cls._extract_val(data.get("operating_cash_flow"))
        inv_cf = cls._extract_val(data.get("investing_cash_flow"))
        fin_cf = cls._extract_val(data.get("financing_cash_flow"))
        fx_adj = cls._extract_val(data.get("fx_adjustment"))
        net_change = cls._extract_val(data.get("net_change_in_cash"))
        opening_cash = cls._extract_val(data.get("opening_cash"))
        closing_cash = cls._extract_val(data.get("closing_cash"))

        # 1. Operating + Investing + Financing + FX = Net Change in Cash
        if op_cf is not None and inv_cf is not None and fin_cf is not None and net_change is not None:
            o_val = float(op_cf)
            i_val = float(inv_cf)
            f_val = float(fin_cf)
            fx_val = float(fx_adj) if fx_adj is not None else 0.0

            calc_change = round(o_val + i_val + f_val + fx_val, 2)
            rep_change = float(net_change)
            var = round(abs(calc_change - rep_change), 2)
            status = "PASS" if cls._is_within_tolerance(calc_change, rep_change) else "FAIL"

            checks.append(FinancialCheck(
                name="net_cash_flow_check",
                formula="Operating CF + Investing CF + Financing CF + FX = Net Change in Cash",
                operands={"operating_cf": o_val, "investing_cf": i_val, "financing_cf": f_val, "fx_adjustment": fx_val},
                calculated_value=calc_change,
                reported_value=rep_change,
                variance=var,
                status=status
            ))

        # 2. Opening Cash + Net Increase = Closing Cash
        if opening_cash is not None and net_change is not None and closing_cash is not None:
            open_val = float(opening_cash)
            chg_val = float(net_change)
            rep_close = float(closing_cash)

            calc_close = round(open_val + chg_val, 2)
            var = round(abs(calc_close - rep_close), 2)
            status = "PASS" if cls._is_within_tolerance(calc_close, rep_close) else "FAIL"

            checks.append(FinancialCheck(
                name="cash_reconciliation_check",
                formula="Opening Cash + Net Change in Cash = Closing Cash",
                operands={"opening_cash": open_val, "net_change_in_cash": chg_val},
                calculated_value=calc_close,
                reported_value=rep_close,
                variance=var,
                status=status
            ))
        elif closing_cash is None or opening_cash is None:
            checks.append(FinancialCheck(
                name="cash_reconciliation_check",
                formula="Opening Cash + Net Change in Cash = Closing Cash",
                operands={"opening_cash": opening_cash, "net_change_in_cash": net_change},
                calculated_value=None,
                reported_value=None,
                variance=None,
                status="NOT_APPLICABLE",
                details="Missing opening_cash or closing_cash fields."
            ))

        return checks
