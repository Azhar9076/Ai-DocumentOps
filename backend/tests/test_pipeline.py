from app.models import DocStatus, DocType
from app.pipeline import classifier, routing
from app.pipeline.field_extractor import extract_fields, parse_money
from app.pipeline.validation import validate

INVOICE_TEXT = """
ACME INDUSTRIAL SUPPLY CO.
INVOICE
Invoice Number: INV-2024-00871
Vendor: ACME Industrial Supply Co.
Invoice Date: 2026-08-04
Due Date: 2026-09-03
Bill To: Northwind Logistics LLC
Subtotal: 1400.00
Sales Tax (8.25%): 115.50
Total Due: 1515.50
Currency: USD
"""

BAD_MATH_TEXT = INVOICE_TEXT.replace("Total Due: 1515.50", "Total Due: 135.00")

FORM_TEXT = """
PATIENT INTAKE APPLICATION FORM
Form No: FRM-2291
Applicant Name: Marcus T. Halloway
Date of Birth: 1988-07-14
Email: m.halloway@example.com
Phone: 415-555-0182
"""


def field_map(text: str, doc_type: DocType, quality: float = 0.98) -> dict[str, str]:
    candidates, _ = extract_fields(text, doc_type, quality)
    return {c.field_key: c.field_value for c in candidates}


def test_parse_money_handles_symbols_and_separators():
    assert parse_money("$1,515.50") == 1515.50
    assert parse_money("abc") is None


def test_classifier_detects_invoice_and_form():
    assert classifier.classify(INVOICE_TEXT)[0] is DocType.INVOICE
    assert classifier.classify(FORM_TEXT)[0] is DocType.FORM


def test_invoice_extraction_does_not_confuse_subtotal_with_total():
    values = field_map(INVOICE_TEXT, DocType.INVOICE)
    assert values["invoice_number"] == "INV-2024-00871"
    assert values["subtotal"] == "1400.00"
    assert values["tax_amount"] == "115.50"
    assert values["total_amount"] == "1515.50"


def test_clean_invoice_auto_approves():
    candidates, _ = extract_fields(INVOICE_TEXT, DocType.INVOICE, 0.98)
    result = validate(candidates, DocType.INVOICE)
    assert result.issues == []
    confidence = routing.overall_confidence(result.candidates, 0.95)
    assert routing.route(confidence, result.has_errors) is DocStatus.AUTO_APPROVED


def test_math_mismatch_forces_action_required_and_penalises_confidence():
    candidates, _ = extract_fields(BAD_MATH_TEXT, DocType.INVOICE, 0.98)
    result = validate(candidates, DocType.INVOICE)
    assert any(issue.rule == "invoice_math" for issue in result.issues)
    penalised = {c.field_key: c.confidence_score for c in result.candidates}
    original = {c.field_key: c.confidence_score for c in candidates}
    assert penalised["total_amount"] < original["total_amount"]
    confidence = routing.overall_confidence(result.candidates, 0.95)
    assert routing.route(confidence, result.has_errors) is DocStatus.ACTION_REQUIRED


def test_ambiguous_ocr_values_lose_confidence_and_need_review():
    noisy = FORM_TEXT.replace("Marcus T. Halloway", "Marc?us T. Halloway")
    candidates, _ = extract_fields(noisy, DocType.FORM, 0.86)
    scores = {c.field_key: c.confidence_score for c in candidates}
    assert scores["applicant_name"] < scores["email"]
    result = validate(candidates, DocType.FORM)
    confidence = routing.overall_confidence(result.candidates, 0.9)
    assert routing.route(confidence, result.has_errors) is DocStatus.NEEDS_REVIEW


def test_missing_required_field_is_flagged():
    result = validate(*[extract_fields("Invoice\nVendor: X", DocType.INVOICE, 0.9)[0], DocType.INVOICE])
    assert {issue.rule for issue in result.issues} == {"required_field"}
    assert result.has_errors
