from app.models import DocStatus, DocType
from app.pipeline import classifier, routing, validation
from app.pipeline.auditor import generate_audit_summary
from app.pipeline.field_extractor import extract_fields, parse_money
from app.pipeline.schemas_extraction import FieldCandidate, get_field_bbox
from app.pipeline.validation import should_run_math_validation, validate
from app.pipeline.watsonx import clean_json_response

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

CONTRACT_TEXT = """
MASTER SERVICES AGREEMENT
Party A: Alpha Corp
Party B: Beta Technologies Inc
Effective Date: 2026-03-01
Term: 24 months
Contract Value: $120,000.00
Governing Law: State of New York
Termination: 30 days written notice.
"""

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


def test_clean_json_response_strips_fences_and_prose():
    fenced = "```json\n{\n  \"doc_type\": \"INVOICE\",\n  \"confidence\": 0.98\n}\n```"
    assert clean_json_response(fenced) == {"doc_type": "INVOICE", "confidence": 0.98}

    prose = "Here is the extraction result: {\"status\": \"ok\", \"count\": 5} Hope that helps!"
    assert clean_json_response(prose) == {"status": "ok", "count": 5}


def test_missing_bbox_fallback_never_crashes():
    assert get_field_bbox(None) is None
    assert get_field_bbox({}) is None
    assert get_field_bbox({"bbox": "line:4,col:2"}) == "line:4,col:2"
    assert get_field_bbox({"bounding_box": {"x": 10.0, "y": 20.0, "width": 100.0, "height": 30.0}}) == "10.0,20.0,100.0,30.0"


def test_classifier_detects_all_types():
    assert classifier.classify(INVOICE_TEXT)[0] is DocType.INVOICE
    assert classifier.classify(CONTRACT_TEXT)[0] is DocType.CONTRACT
    assert classifier.classify(FORM_TEXT)[0] is DocType.FORM


def test_contract_and_form_skip_math_validation():
    assert not should_run_math_validation(DocType.CONTRACT, {"contract_value": "1000"})
    assert not should_run_math_validation(DocType.FORM, {"applicant_name": "John"})
    assert should_run_math_validation(DocType.INVOICE, {"subtotal": "100", "tax_amount": "10", "total_amount": "110"})
    assert not should_run_math_validation(DocType.INVOICE, {"total_amount": "110"})


def test_invoice_extraction_does_not_confuse_subtotal_with_total():
    values = field_map(INVOICE_TEXT, DocType.INVOICE)
    assert values["invoice_number"] == "INV-2024-00871"
    assert values["subtotal"] == "1400.00"
    assert values["tax_amount"] == "115.50"
    assert values["total_amount"] == "1515.50"


def test_contract_extraction():
    values = field_map(CONTRACT_TEXT, DocType.CONTRACT)
    assert values["party_a"] == "Alpha Corp"
    assert values["party_b"] == "Beta Technologies Inc"
    assert values["effective_date"] == "2026-03-01"
    assert values["term_months"] == "24"
    assert values["contract_value"] == "120000.00"


def test_clean_invoice_auto_approves():
    candidates, _ = extract_fields(INVOICE_TEXT, DocType.INVOICE, 0.98)
    result = validate(candidates, DocType.INVOICE)
    assert result.issues == []
    assert result.math_result.status == "passed"
    confidence = routing.overall_confidence(result.candidates, 0.95)
    assert routing.route(confidence, result.has_errors) is DocStatus.AUTO_APPROVED


def test_math_mismatch_forces_action_required():
    candidates, _ = extract_fields(BAD_MATH_TEXT, DocType.INVOICE, 0.98)
    result = validate(candidates, DocType.INVOICE)
    assert any(issue.rule == "invoice_math" for issue in result.issues)
    assert result.math_result.status == "mismatched"
    confidence = routing.overall_confidence(result.candidates, 0.95)
    assert routing.route(confidence, result.has_errors) is DocStatus.ACTION_REQUIRED


def test_audit_summary_generation():
    candidates, _ = extract_fields(INVOICE_TEXT, DocType.INVOICE, 0.98)
    result = validate(candidates, DocType.INVOICE)
    summary = generate_audit_summary(
        doc_type=DocType.INVOICE,
        overall_confidence=0.96,
        status=DocStatus.AUTO_APPROVED,
        math_result=result.math_result,
        issues=result.issues,
    )
    assert "96.0% avg confidence" in summary
    assert "Math validated" in summary
    assert "Routed to AUTO_APPROVED" in summary


def test_math_check_decision_enum():
    from app.pipeline.validation import MathCheckDecision, decide_math_validation

    # Contract -> skip wrong doc type
    assert decide_math_validation(DocType.CONTRACT, {}) == MathCheckDecision.SKIP_WRONG_DOC_TYPE
    assert decide_math_validation("FORM", {}) == MathCheckDecision.SKIP_WRONG_DOC_TYPE

    # Invoice with missing math fields -> skip fields missing (triggers self-correction)
    assert decide_math_validation(DocType.INVOICE, {"total_amount": "100.00"}) == MathCheckDecision.SKIP_FIELDS_MISSING

    # Invoice with all math fields -> run
    assert (
        decide_math_validation(
            DocType.INVOICE,
            {"subtotal": "100.00", "tax_amount": "10.00", "total_amount": "110.00"},
        )
        == MathCheckDecision.RUN
    )


def test_granite_budget_guard_enforces_limit_and_reset():
    import pytest
    from app.pipeline.watsonx import GraniteBudgetGuard

    guard = GraniteBudgetGuard(max_calls_per_session=3)
    assert guard.remaining == 3
    guard.check_and_increment()
    guard.check_and_increment()
    guard.check_and_increment()
    assert guard.remaining == 0

    with pytest.raises(RuntimeError, match="budget exhausted"):
        guard.check_and_increment()

    guard.reset()
    assert guard.remaining == 3
    assert guard.call_count == 0
