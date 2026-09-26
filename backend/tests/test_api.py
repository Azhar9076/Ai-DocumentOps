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


def test_root_endpoint(client: TestClient):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "service" in data


def test_health(client: TestClient):
    res = client.get("/api/health").json()
    assert res["status"] == "ok"
    assert "service" in res


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
    assert "audit_summary" in document
    assert len(document["audit_summary"]) > 0

    values = {f["field_key"]: f["field_value"] for f in document["fields"]}
    assert values["total_amount"] == "220.00"

    actions = {log["action"] for log in document["audit_logs"]}
    assert "DOCLING_PARSED" in actions
    assert "AGENT_CLASSIFIER" in actions
    assert "AGENT_EXTRACTOR_ATTEMPT_1" in actions
    assert "AGENT_AUDITOR" in actions

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
    assert "roi_metrics" in metrics

    quality = client.get("/api/quality").json()
    assert quality["overall_accuracy"] >= 75.0
    assert "confidence_calibration" in quality
    assert "accuracy_iterations" in quality


def test_export_endpoints(client: TestClient):
    # Upload doc
    response = client.post(
        "/api/documents", files={"file": ("export_test.pdf", invoice_pdf(), "application/pdf")}
    )
    doc_id = response.json()["id"]

    json_exp = client.get(f"/api/documents/{doc_id}/export?format=json")
    assert json_exp.status_code == 200
    assert json_exp.json()["id"] == doc_id

    csv_exp = client.get(f"/api/documents/{doc_id}/export?format=csv")
    assert csv_exp.status_code == 200
    assert "Document ID" in csv_exp.text


def test_reprocess_and_cancel_endpoints(client: TestClient):
    response = client.post(
        "/api/documents", files={"file": ("reproc.pdf", invoice_pdf(), "application/pdf")}
    )
    doc_id = response.json()["id"]

    reproc = client.post(f"/api/documents/{doc_id}/reprocess")
    assert reproc.status_code == 200
    assert reproc.json()["status"] == "AUTO_APPROVED"

    cancel = client.post(f"/api/documents/{doc_id}/cancel")
    assert cancel.status_code == 200


def test_bulk_review_endpoint(client: TestClient):
    r1 = client.post("/api/documents", files={"file": ("b1.pdf", invoice_pdf(), "application/pdf")}).json()
    r2 = client.post("/api/documents", files={"file": ("b2.pdf", invoice_pdf(), "application/pdf")}).json()

    bulk_res = client.post(
        "/api/documents/bulk-review",
        json={"document_ids": [r1["id"], r2["id"]], "decision": "APPROVE"},
    )
    assert bulk_res.status_code == 200


def test_missing_document_returns_404(client: TestClient):
    assert client.get("/api/documents/does-not-exist").status_code == 404


def test_approve_and_learn_correct_endpoint(client: TestClient):
    res = client.post(
        "/api/documents", files={"file": ("correct_test.pdf", invoice_pdf(), "application/pdf")}
    )
    doc_id = res.json()["id"]

    correct_res = client.post(
        f"/api/documents/{doc_id}/correct",
        json={
            "field_name": "vendor_name",
            "corrected_value": "Acme Super Supply",
            "reviewer_id": "lead_reviewer@example.com",
        },
    )
    assert correct_res.status_code == 200
    data = correct_res.json()
    assert data["status"] == "corrected"
    assert "math_result" in data
    assert any(
        f["field_key"] == "vendor_name" and f["field_value"] == "Acme Super Supply"
        for f in data["document"]["fields"]
    )


def test_audit_pdf_and_csv_export_endpoint(client: TestClient):
    res = client.post(
        "/api/documents", files={"file": ("cert_test.pdf", invoice_pdf(), "application/pdf")}
    )
    doc_id = res.json()["id"]

    pdf_res = client.get(f"/api/documents/{doc_id}/export-audit?format=pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 500

    csv_res = client.get(f"/api/documents/{doc_id}/export-audit?format=csv")
    assert csv_res.status_code == 200
    assert "Document ID" in csv_res.text


def test_stress_test_and_status_endpoints(client: TestClient):
    stress_res = client.post("/api/demo/stress-test?sample_count=3")
    assert stress_res.status_code == 200
    data = stress_res.json()
    assert data["started"] == 3
    assert len(data["job_ids"]) == 3
    assert "budget_remaining" in data

    job_query = ",".join(data["job_ids"])
    status_res = client.get(f"/api/demo/stress-test/status?job_ids={job_query}")
    assert status_res.status_code == 200
    assert len(status_res.json()) >= 1


def test_admin_routing_thresholds_api(client: TestClient):
    get_res = client.get("/api/admin/thresholds")
    assert get_res.status_code == 200
    original = get_res.json()
    assert "auto_approved_min" in original
    assert "needs_review_min" in original

    put_res = client.put(
        "/api/admin/thresholds",
        json={"auto_approved_min": 0.88, "needs_review_min": 0.65},
    )
    assert put_res.status_code == 200
    updated = put_res.json()
    assert updated["auto_approved_min"] == 0.88
    assert updated["needs_review_min"] == 0.65

    # Restore
    client.put("/api/admin/thresholds", json=original)


def test_quality_compare_mode(client: TestClient):
    res = client.get("/api/quality?compare=true")
    assert res.status_code == 200
    data = res.json()
    assert data["v1_comparison"] is not None
    assert "prompt_v1" in data["v1_comparison"]
    assert "prompt_v2" in data["v1_comparison"]
    assert "delta" in data["v1_comparison"]


def test_db_fallback_resilience(monkeypatch):
    from unittest.mock import MagicMock
    import app.db as db_module

    mock_engine = MagicMock()
    mock_engine.connect.side_effect = Exception("Connection refused / Network is unreachable")
    
    with monkeypatch.context() as m:
        m.setattr(db_module, "engine", mock_engine)
        # Should not raise exception
        db_module.init_db()


