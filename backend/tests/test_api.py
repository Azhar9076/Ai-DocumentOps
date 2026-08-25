import io

import pytest
from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from app.db import init_db
from app.main import app

INVOICE_LINES = [
    "INVOICE",
    "Invoice Number: INV-TEST-001",
    "Vendor: Testing Supplies Ltd",
    "Invoice Date: 2026-08-01",
    "Due Date: 2026-08-31",
    "Subtotal: 200.00",
    "Sales Tax (10%): 20.00",
    "Total Due: 220.00",
]


@pytest.fixture(scope="module")
def client() -> TestClient:
    init_db()
    with TestClient(app) as test_client:
        yield test_client


def invoice_pdf() -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=LETTER)
    pdf.setFont("Helvetica", 11)
    y = 720
    for line in INVOICE_LINES:
        pdf.drawString(64, y, line)
        y -= 18
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def test_health(client: TestClient):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_unsupported_file_type_is_rejected(client: TestClient):
    response = client.post(
        "/api/documents", files={"file": ("notes.exe", b"binary", "application/octet-stream")}
    )
    assert response.status_code == 415


def test_upload_extract_and_review_roundtrip(client: TestClient):
    response = client.post(
        "/api/documents", files={"file": ("invoice.pdf", invoice_pdf(), "application/pdf")}
    )
    assert response.status_code == 201
    document = response.json()
    assert document["doc_type"] == "INVOICE"
    assert document["status"] == "AUTO_APPROVED"
    values = {f["field_key"]: f["field_value"] for f in document["fields"]}
    assert values["total_amount"] == "220.00"
    assert {log["action"] for log in document["audit_logs"]} >= {
        "UPLOADED",
        "CLASSIFIED",
        "FIELDS_EXTRACTED",
        "RULES_VALIDATED",
    }

    reviewed = client.post(
        f"/api/documents/{document['id']}/review",
        json={
            "edits": [{"field_key": "vendor_name", "field_value": "Testing Supplies Limited"}],
            "decision": "APPROVE",
        },
    )
    assert reviewed.status_code == 200
    body = reviewed.json()
    assert body["status"] == "APPROVED"
    assert body["reviews"][0]["corrected_value"] == "Testing Supplies Limited"

    metrics = client.get("/api/metrics").json()
    assert metrics["documents_processed"] >= 1
    quality = client.get("/api/quality").json()
    assert quality["notice"].startswith("Metrics evaluated")


def test_missing_document_returns_404(client: TestClient):
    assert client.get("/api/documents/does-not-exist").status_code == 404
