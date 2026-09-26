"""Strict Pydantic target schemas per document type."""

from __future__ import annotations

from datetime import date
from typing import Any

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
        return value.strip() if isinstance(value, str) else ""


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
    termination_clause: str = ""


SCHEMA_BY_TYPE: dict[str, type[BaseModel]] = {
    "INVOICE": InvoiceSchema,
    "FORM": FormSchema,
    "CONTRACT": ContractSchema,
}


class FieldCandidate(BaseModel):
    field_key: str
    field_value: str = ""
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    bbox: str | None = None


def get_field_bbox(field_metadata: dict[str, Any] | Any) -> str | None:
    """Safely extract bounding box or positional anchor; returns None if unavailable rather than raising."""
    if not isinstance(field_metadata, dict):
        return None
    bbox = field_metadata.get("bbox") or field_metadata.get("bounding_box")
    if isinstance(bbox, str):
        return bbox
    if isinstance(bbox, dict) and all(k in bbox for k in ("x", "y", "width", "height")):
        return f"{bbox['x']:.1f},{bbox['y']:.1f},{bbox['width']:.1f},{bbox['height']:.1f}"
    return None


def today_iso() -> str:
    return date.today().isoformat()
