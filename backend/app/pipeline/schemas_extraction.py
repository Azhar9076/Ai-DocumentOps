"""Strict Pydantic target schemas per document type."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator


class InvoiceSchema(BaseModel):
    invoice_number: str = ""
    vendor_name: str = ""
    invoice_date: str = ""
    due_date: str = ""
    subtotal: float | None = None
    tax_amount: float | None = None
    total_amount: float | None = None
    currency: str = "USD"

    @field_validator("invoice_date", "due_date")
    @classmethod
    def normalise_date(cls, value: str) -> str:
        return value.strip()


class FormSchema(BaseModel):
    applicant_name: str = ""
    date_of_birth: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    form_id: str = ""


class ContractSchema(BaseModel):
    party_a: str = ""
    party_b: str = ""
    effective_date: str = ""
    term_months: int | None = None
    contract_value: float | None = None
    governing_law: str = ""


SCHEMA_BY_TYPE = {
    "INVOICE": InvoiceSchema,
    "FORM": FormSchema,
    "CONTRACT": ContractSchema,
}


class FieldCandidate(BaseModel):
    field_key: str
    field_value: str = ""
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    bbox: str | None = None


def today_iso() -> str:
    return date.today().isoformat()
