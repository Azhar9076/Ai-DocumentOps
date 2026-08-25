"""Seed three synthetic demo runs through the real pipeline.

1. Clean invoice          -> AUTO_APPROVED (high confidence)
2. Scanned form (OCR)     -> NEEDS_REVIEW (ambiguous handwriting fields)
3. Inconsistent invoice   -> ACTION_REQUIRED (subtotal + tax != total)
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from sqlalchemy import delete

from app.config import settings
from app.db import SessionLocal, init_db
from app.models import AuditLog, DocStatus, Document, ExtractedField, Review
from app.pipeline.runner import log_audit, process_document_sync
from app.services.documents import store_upload

SAMPLES_DIR = settings.storage_dir.parent / "samples"

CLEAN_INVOICE = [
    "ACME INDUSTRIAL SUPPLY CO.",
    "INVOICE",
    "Invoice Number: INV-2024-00871",
    "Vendor: ACME Industrial Supply Co.",
    "Invoice Date: 2026-08-04",
    "Due Date: 2026-09-03",
    "Bill To: Northwind Logistics LLC",
    "",
    "Description                Qty      Rate       Amount",
    "Hydraulic couplings         40     18.50      740.00",
    "Steel brackets              25     22.00      550.00",
    "Freight                      1     110.00     110.00",
    "",
    "Subtotal: 1400.00",
    "Sales Tax (8.25%): 115.50",
    "Total Due: 1515.50",
    "Currency: USD",
    "Payment terms: Net 30. Remit to ACME Industrial Supply Co.",
]

INCONSISTENT_INVOICE = [
    "BRIGHTPATH CONSULTING",
    "INVOICE",
    "Invoice Number: INV-2024-01144",
    "Vendor: Brightpath Consulting Group",
    "Invoice Date: 2026-08-11",
    "Due Date: 2026-08-25",
    "Bill To: Vertex Manufacturing Inc.",
    "",
    "Advisory retainer                            100.00",
    "",
    "Subtotal: 100.00",
    "Sales Tax (18%): 18.00",
    "Total Due: 135.00",
    "Currency: USD",
]

SCANNED_FORM = [
    "PATIENT INTAKE APPLICATION FORM",
    "Form No: FRM-2291",
    "Applicant Name: Marc?us T. Halloway",
    "Date of Birth: 07-1?-1988",
    "Email: m.halloway@meridian-health.example",
    "Phone: 415-555-0182",
    "Address: 2214 Sunset Ridge Blvd, Oakland CA",
    "Please print clearly. Signature required below.",
]


def write_pdf(path: Path, lines: list[str]) -> None:
    pdf = canvas.Canvas(str(path), pagesize=LETTER)
    pdf.setFont("Helvetica", 11)
    y = 730
    for line in lines:
        pdf.drawString(64, y, line)
        y -= 18
    pdf.showPage()
    pdf.save()


def write_scan_png(path: Path, lines: list[str]) -> None:
    """Render a low-fidelity 'scanned' page so the OCR path is genuinely exercised."""
    image = Image.new("RGB", (1240, 720), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    except OSError:  # pragma: no cover - font fallback
        font = ImageFont.load_default()
    y = 60
    for line in lines:
        draw.text((60, y), line, fill=(35, 35, 45), font=font)
        y += 52
    image = image.rotate(0.4, fillcolor="white", resample=Image.BICUBIC)
    image.save(path, "PNG")


def reset(db) -> None:
    for model in (Review, AuditLog, ExtractedField, Document):
        db.execute(delete(model))
    db.commit()


def seed() -> None:
    init_db()
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    clean = SAMPLES_DIR / "clean_invoice.pdf"
    inconsistent = SAMPLES_DIR / "inconsistent_invoice.pdf"
    scan = SAMPLES_DIR / "scanned_form.png"
    write_pdf(clean, CLEAN_INVOICE)
    write_pdf(inconsistent, INCONSISTENT_INVOICE)
    write_scan_png(scan, SCANNED_FORM)

    db = SessionLocal()
    try:
        reset(db)
        results = []
        for path, mime in (
            (clean, "application/pdf"),
            (scan, "image/png"),
            (inconsistent, "application/pdf"),
        ):
            with path.open("rb") as handle:
                document = store_upload(db, path.name, mime, handle)
            outcome = process_document_sync(db, document)
            log_audit(db, document.id, "SEEDED", "Synthetic demo run created by seed script")
            db.commit()
            results.append((path.name, outcome.status, outcome.confidence, len(outcome.issues)))

        print("Seeded demo runs:")
        for name, status, confidence, issues in results:
            print(f"  {name:28} {status.value:16} confidence={confidence:.2%} issues={issues}")

        statuses = {status for _, status, _, _ in results}
        expected = {DocStatus.AUTO_APPROVED, DocStatus.NEEDS_REVIEW, DocStatus.ACTION_REQUIRED}
        missing = expected - statuses
        if missing:
            print(f"WARNING: demo data did not produce {sorted(s.value for s in missing)}", file=sys.stderr)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
