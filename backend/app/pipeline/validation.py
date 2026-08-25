"""Deterministic business-rule validation engine with confidence penalties."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.models import DocType
from app.pipeline.field_extractor import parse_money
from app.pipeline.schemas_extraction import FieldCandidate

DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|[A-Z][a-z]{2,9} \d{1,2}, \d{4})$")
EMAIL_RE = re.compile(r"^[\w\.\-\+]+@[\w\-]+\.[\w\.\-]+$")
MATH_TOLERANCE = 0.01


@dataclass
class Issue:
    rule: str
    message: str
    severity: str = "error"
    fields: list[str] = field(default_factory=list)
    penalty: float = 0.35

    def as_dict(self) -> dict[str, object]:
        return {
            "rule": self.rule,
            "message": self.message,
            "severity": self.severity,
            "fields": self.fields,
        }


@dataclass
class ValidationResult:
    issues: list[Issue]
    candidates: list[FieldCandidate]

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)


def validate(candidates: list[FieldCandidate], doc_type: DocType) -> ValidationResult:
    values = {c.field_key: c.field_value for c in candidates}
    issues: list[Issue] = []

    required = REQUIRED_BY_TYPE.get(doc_type, ())
    for key in required:
        if not values.get(key):
            issues.append(
                Issue(
                    rule="required_field",
                    message=f"Required field '{key}' was not found in the document.",
                    fields=[key],
                    penalty=0.4,
                )
            )

    if doc_type is DocType.INVOICE:
        issues.extend(_invoice_rules(values))
    if doc_type is DocType.FORM:
        issues.extend(_form_rules(values))
    if doc_type is DocType.CONTRACT:
        issues.extend(_contract_rules(values))

    penalised = _apply_penalties(candidates, issues)
    return ValidationResult(issues=issues, candidates=penalised)


REQUIRED_BY_TYPE: dict[DocType, tuple[str, ...]] = {
    DocType.INVOICE: ("invoice_number", "total_amount"),
    DocType.FORM: ("applicant_name",),
    DocType.CONTRACT: ("party_a", "party_b"),
}


def _invoice_rules(values: dict[str, str]) -> list[Issue]:
    issues: list[Issue] = []
    subtotal = parse_money(values.get("subtotal", ""))
    tax = parse_money(values.get("tax_amount", ""))
    total = parse_money(values.get("total_amount", ""))

    if subtotal is not None and tax is not None and total is not None:
        expected = round(subtotal + tax, 2)
        if abs(expected - total) > MATH_TOLERANCE:
            issues.append(
                Issue(
                    rule="invoice_math",
                    message=(
                        f"Subtotal ({subtotal:.2f}) + Tax ({tax:.2f}) = {expected:.2f}, "
                        f"which does not match the stated Total ({total:.2f})."
                    ),
                    fields=["subtotal", "tax_amount", "total_amount"],
                    penalty=0.45,
                )
            )
    if total is not None and total <= 0:
        issues.append(
            Issue(
                rule="non_positive_total",
                message="Invoice total must be greater than zero.",
                fields=["total_amount"],
            )
        )
    for key in ("invoice_date", "due_date"):
        value = values.get(key, "")
        if value and not DATE_RE.match(value):
            issues.append(
                Issue(
                    rule="date_format",
                    message=f"'{key}' value '{value}' is not a recognised date format.",
                    severity="warning",
                    fields=[key],
                    penalty=0.2,
                )
            )
    return issues


def _form_rules(values: dict[str, str]) -> list[Issue]:
    issues: list[Issue] = []
    email = values.get("email", "")
    if email and not EMAIL_RE.match(email):
        issues.append(
            Issue(
                rule="email_format",
                message=f"Email '{email}' is not a valid address.",
                fields=["email"],
                penalty=0.3,
            )
        )
    dob = values.get("date_of_birth", "")
    if dob and not DATE_RE.match(dob):
        issues.append(
            Issue(
                rule="date_format",
                message=f"Date of birth '{dob}' is not a recognised date format.",
                severity="warning",
                fields=["date_of_birth"],
                penalty=0.2,
            )
        )
    return issues


def _contract_rules(values: dict[str, str]) -> list[Issue]:
    issues: list[Issue] = []
    term = parse_money(values.get("term_months", ""))
    if term is not None and (term <= 0 or term > 600):
        issues.append(
            Issue(
                rule="term_range",
                message=f"Contract term of {term:.0f} months is outside the accepted 1-600 range.",
                fields=["term_months"],
            )
        )
    if values.get("party_a") and values.get("party_a") == values.get("party_b"):
        issues.append(
            Issue(
                rule="distinct_parties",
                message="Party A and Party B must be different entities.",
                fields=["party_a", "party_b"],
            )
        )
    return issues


def _apply_penalties(
    candidates: list[FieldCandidate], issues: list[Issue]
) -> list[FieldCandidate]:
    penalty_by_key: dict[str, float] = {}
    for issue in issues:
        for key in issue.fields:
            penalty_by_key[key] = max(penalty_by_key.get(key, 0.0), issue.penalty)

    updated: list[FieldCandidate] = []
    for candidate in candidates:
        penalty = penalty_by_key.get(candidate.field_key, 0.0)
        score = round(max(0.02, candidate.confidence_score - penalty), 4)
        updated.append(
            candidate.model_copy(
                update={"confidence_score": score if penalty else candidate.confidence_score}
            )
        )
    return updated
