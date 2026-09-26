"""Labeled Ground-Truth Benchmark Dataset (18 documents across Invoices, Contracts, Forms)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models import DocStatus, DocType


@dataclass
class BenchmarkDocument:
    id: str
    name: str
    doc_type: DocType
    text: str
    expected_fields: dict[str, Any]
    expected_status: DocStatus
    category: str


BENCHMARK_SUITE: list[BenchmarkDocument] = [
    # --- INVOICES (6 samples) ---
    BenchmarkDocument(
        id="inv-01",
        name="Clean Standard Invoice (ACME)",
        doc_type=DocType.INVOICE,
        text="""ACME INDUSTRIAL SUPPLY CO.
INVOICE
Invoice Number: INV-2024-00871
Vendor: ACME Industrial Supply Co.
Invoice Date: 2026-08-04
Due Date: 2026-09-03
Bill To: Northwind Logistics LLC
Subtotal: 1400.00
Sales Tax: 115.50
Total Due: 1515.50
Currency: USD""",
        expected_fields={
            "invoice_number": "INV-2024-00871",
            "vendor_name": "ACME Industrial Supply Co.",
            "invoice_date": "2026-08-04",
            "due_date": "2026-09-03",
            "subtotal": 1400.00,
            "tax_amount": 115.50,
            "total_amount": 1515.50,
            "currency": "USD",
        },
        expected_status=DocStatus.AUTO_APPROVED,
        category="Invoice",
    ),
    BenchmarkDocument(
        id="inv-02",
        name="Euro Tech Solutions Invoice",
        doc_type=DocType.INVOICE,
        text="""EURO TECH SOLUTIONS GMBH
INVOICE
Invoice Number: ETS-88902
Vendor: Euro Tech Solutions GmbH
Invoice Date: 2026-07-15
Due Date: 2026-08-15
Subtotal: 3200.00
Tax Amount: 640.00
Total Due: 3840.00
Currency: EUR""",
        expected_fields={
            "invoice_number": "ETS-88902",
            "vendor_name": "Euro Tech Solutions GmbH",
            "invoice_date": "2026-07-15",
            "due_date": "2026-08-15",
            "subtotal": 3200.00,
            "tax_amount": 640.00,
            "total_amount": 3840.00,
            "currency": "EUR",
        },
        expected_status=DocStatus.AUTO_APPROVED,
        category="Invoice",
    ),
    BenchmarkDocument(
        id="inv-03",
        name="Inconsistent Math Invoice",
        doc_type=DocType.INVOICE,
        text="""BRIGHTPATH CONSULTING
INVOICE
Invoice Number: INV-2024-01144
Vendor: Brightpath Consulting Group
Invoice Date: 2026-08-11
Due Date: 2026-08-25
Subtotal: 100.00
Sales Tax: 18.00
Total Due: 135.00
Currency: USD""",
        expected_fields={
            "invoice_number": "INV-2024-01144",
            "vendor_name": "Brightpath Consulting Group",
            "invoice_date": "2026-08-11",
            "due_date": "2026-08-25",
            "subtotal": 100.00,
            "tax_amount": 18.00,
            "total_amount": 135.00,
            "currency": "USD",
        },
        expected_status=DocStatus.ACTION_REQUIRED,
        category="Invoice",
    ),
    BenchmarkDocument(
        id="inv-04",
        name="Zero Tax Services Invoice",
        doc_type=DocType.INVOICE,
        text="""VERTEX CLOUD HOSTING
INVOICE
Invoice Number: VTX-4019
Vendor: Vertex Cloud Hosting LLC
Invoice Date: 2026-06-01
Due Date: 2026-07-01
Subtotal: 250.00
Tax Amount: 0.00
Total Due: 250.00
Currency: USD""",
        expected_fields={
            "invoice_number": "VTX-4019",
            "vendor_name": "Vertex Cloud Hosting LLC",
            "invoice_date": "2026-06-01",
            "due_date": "2026-07-01",
            "subtotal": 250.00,
            "tax_amount": 0.00,
            "total_amount": 250.00,
            "currency": "USD",
        },
        expected_status=DocStatus.AUTO_APPROVED,
        category="Invoice",
    ),
    BenchmarkDocument(
        id="inv-05",
        name="Missing Subtotal Invoice",
        doc_type=DocType.INVOICE,
        text="""QUICK PRINTING CO.
INVOICE
Invoice Number: QP-990
Vendor: Quick Printing Co.
Invoice Date: 2026-05-10
Total Due: 85.00
Currency: USD""",
        expected_fields={
            "invoice_number": "QP-990",
            "vendor_name": "Quick Printing Co.",
            "invoice_date": "2026-05-10",
            "total_amount": 85.00,
            "currency": "USD",
        },
        expected_status=DocStatus.AUTO_APPROVED,
        category="Invoice",
    ),
    BenchmarkDocument(
        id="inv-06",
        name="Scanned Low-Fidelity Invoice",
        doc_type=DocType.INVOICE,
        text="""DELTA LOGISTICS?
INVOICE # DL-7721
Vendor: Delta Logistics Corp~
Invoice Date: 2026-04-12
Due Date: 2026-05-12
Subtotal: 800.00
Tax: 64.00
Total: 864.00
Currency: USD""",
        expected_fields={
            "invoice_number": "DL-7721",
            "invoice_date": "2026-04-12",
            "due_date": "2026-05-12",
            "subtotal": 800.00,
            "tax_amount": 64.00,
            "total_amount": 864.00,
            "currency": "USD",
        },
        expected_status=DocStatus.NEEDS_REVIEW,
        category="Invoice",
    ),

    # --- CONTRACTS (6 samples) ---
    BenchmarkDocument(
        id="con-01",
        name="Master Services Agreement",
        doc_type=DocType.CONTRACT,
        text="""MASTER SERVICES AGREEMENT
This Agreement is entered into between Zenith Digital Corp ("Party A") and Nexus Systems Inc ("Party B").
Effective Date: 2026-03-01
Term: 24 months
Contract Value: $180,000.00
Governing Law: State of Delaware
Termination: 30 days written notice.""",
        expected_fields={
            "party_a": "Zenith Digital Corp",
            "party_b": "Nexus Systems Inc",
            "effective_date": "2026-03-01",
            "term_months": 24,
            "contract_value": 180000.00,
            "governing_law": "State of Delaware",
        },
        expected_status=DocStatus.AUTO_APPROVED,
        category="Contract",
    ),
    BenchmarkDocument(
        id="con-02",
        name="Non-Disclosure Agreement (NDA)",
        doc_type=DocType.CONTRACT,
        text="""MUTUAL NON-DISCLOSURE AGREEMENT
By and between BioHealth Innovations and Quantum Research Labs.
Effective Date: 2026-02-15
Term: 12 months
Governing Law: State of California
Each party agrees to maintain strict confidentiality.""",
        expected_fields={
            "party_a": "BioHealth Innovations",
            "party_b": "Quantum Research Labs",
            "effective_date": "2026-02-15",
            "term_months": 12,
            "governing_law": "State of California",
        },
        expected_status=DocStatus.AUTO_APPROVED,
        category="Contract",
    ),
    BenchmarkDocument(
        id="con-03",
        name="Software License Agreement",
        doc_type=DocType.CONTRACT,
        text="""COMMERCIAL SOFTWARE LICENSE
Party A: CloudScale Software LLC
Party B: Horizon Financial Group
Effective Date: 2026-01-10
Term: 36 months
Contract Value: $75,000.00
Governing Law: State of New York""",
        expected_fields={
            "party_a": "CloudScale Software LLC",
            "party_b": "Horizon Financial Group",
            "effective_date": "2026-01-10",
            "term_months": 36,
            "contract_value": 75000.00,
            "governing_law": "State of New York",
        },
        expected_status=DocStatus.AUTO_APPROVED,
        category="Contract",
    ),
    BenchmarkDocument(
        id="con-04",
        name="Commercial Lease Agreement",
        doc_type=DocType.CONTRACT,
        text="""COMMERCIAL LEASE AGREEMENT
Landlord / Party A: Oakmont Commercial Properties
Tenant / Party B: Apex Logistics Solutions
Effective Date: 2026-05-01
Term: 60 months
Contract Value: $300,000.00
Governing Law: State of Texas""",
        expected_fields={
            "party_a": "Oakmont Commercial Properties",
            "party_b": "Apex Logistics Solutions",
            "effective_date": "2026-05-01",
            "term_months": 60,
            "contract_value": 300000.00,
            "governing_law": "State of Texas",
        },
        expected_status=DocStatus.AUTO_APPROVED,
        category="Contract",
    ),
    BenchmarkDocument(
        id="con-05",
        name="Consulting Services Agreement",
        doc_type=DocType.CONTRACT,
        text="""INDEPENDENT CONSULTING AGREEMENT
Client: Global Retail Ventures
Provider: Dr. Evelyn Vance
Effective Date: 2026-06-15
Term: 6 months
Contract Value: $40,000.00
Governing Law: Commonwealth of Massachusetts""",
        expected_fields={
            "party_a": "Global Retail Ventures",
            "party_b": "Dr. Evelyn Vance",
            "effective_date": "2026-06-15",
            "term_months": 6,
            "contract_value": 40000.00,
            "governing_law": "Commonwealth of Massachusetts",
        },
        expected_status=DocStatus.AUTO_APPROVED,
        category="Contract",
    ),
    BenchmarkDocument(
        id="con-06",
        name="Contract with Identical Parties (Rule Fail)",
        doc_type=DocType.CONTRACT,
        text="""AFFILIATE AGREEMENT
Party A: OmniCorp Global
Party B: OmniCorp Global
Effective Date: 2026-01-01
Term: 12 months
Governing Law: Delaware""",
        expected_fields={
            "party_a": "OmniCorp Global",
            "party_b": "OmniCorp Global",
            "effective_date": "2026-01-01",
            "term_months": 12,
            "governing_law": "Delaware",
        },
        expected_status=DocStatus.ACTION_REQUIRED,
        category="Contract",
    ),

    # --- FORMS (6 samples) ---
    BenchmarkDocument(
        id="frm-01",
        name="Patient Intake Form",
        doc_type=DocType.FORM,
        text="""PATIENT INTAKE APPLICATION FORM
Form ID: FRM-2291
Applicant Name: Marcus T. Halloway
Date of Birth: 1988-07-14
Email: m.halloway@meridian-health.example
Phone: 415-555-0182
Address: 2214 Sunset Ridge Blvd, Oakland CA""",
        expected_fields={
            "form_id": "FRM-2291",
            "applicant_name": "Marcus T. Halloway",
            "date_of_birth": "1988-07-14",
            "email": "m.halloway@meridian-health.example",
            "phone": "415-555-0182",
            "address": "2214 Sunset Ridge Blvd, Oakland CA",
        },
        expected_status=DocStatus.AUTO_APPROVED,
        category="Form",
    ),
    BenchmarkDocument(
        id="frm-02",
        name="Loan Application Form",
        doc_type=DocType.FORM,
        text="""SMALL BUSINESS LOAN APPLICATION
Form No: LN-40012
Applicant Name: Sarah Lin
Date of Birth: 1991-03-22
Email: slin@techventures.co
Phone: (415) 555-9012
Address: 742 Evergreen Terrace, San Francisco, CA""",
        expected_fields={
            "form_id": "LN-40012",
            "applicant_name": "Sarah Lin",
            "date_of_birth": "1991-03-22",
            "email": "slin@techventures.co",
            "phone": "(415) 555-9012",
            "address": "742 Evergreen Terrace, San Francisco, CA",
        },
        expected_status=DocStatus.AUTO_APPROVED,
        category="Form",
    ),
    BenchmarkDocument(
        id="frm-03",
        name="Scanned Form with Ambiguous Handwriting",
        doc_type=DocType.FORM,
        text="""MEMBERSHIP REGISTRATION FORM
Form ID: REG-801
Applicant Name: Marc?us T. Halloway
Date of Birth: 07-1?-1988
Email: m.halloway@meridian-health.example
Phone: 415-555-0182
Address: 2214 Sunset Ridge Blvd, Oakland CA""",
        expected_fields={
            "form_id": "REG-801",
            "applicant_name": "Marc?us T. Halloway",
            "date_of_birth": "07-1?-1988",
            "email": "m.halloway@meridian-health.example",
            "phone": "415-555-0182",
        },
        expected_status=DocStatus.NEEDS_REVIEW,
        category="Form",
    ),
    BenchmarkDocument(
        id="frm-04",
        name="Customer Account Form",
        doc_type=DocType.FORM,
        text="""CUSTOMER ENROLLMENT FORM
Form ID: ACC-993
Applicant Name: David R. Miller
Date of Birth: 1985-11-04
Email: dmiller@corporate.example
Phone: 312-555-4433
Address: 100 Michigan Ave, Chicago, IL 60601""",
        expected_fields={
            "form_id": "ACC-993",
            "applicant_name": "David R. Miller",
            "date_of_birth": "1985-11-04",
            "email": "dmiller@corporate.example",
            "phone": "312-555-4433",
            "address": "100 Michigan Ave, Chicago, IL 60601",
        },
        expected_status=DocStatus.AUTO_APPROVED,
        category="Form",
    ),
    BenchmarkDocument(
        id="frm-05",
        name="Vendor Registration Form",
        doc_type=DocType.FORM,
        text="""VENDOR PROFILE FORM
Form ID: VR-551
Applicant Name: Angela Cruz
Date of Birth: 1982-09-18
Email: angela@cruzlogistics.com
Phone: 214-555-8822
Address: 880 Main St, Dallas, TX 75201""",
        expected_fields={
            "form_id": "VR-551",
            "applicant_name": "Angela Cruz",
            "date_of_birth": "1982-09-18",
            "email": "angela@cruzlogistics.com",
            "phone": "214-555-8822",
            "address": "880 Main St, Dallas, TX 75201",
        },
        expected_status=DocStatus.AUTO_APPROVED,
        category="Form",
    ),
    BenchmarkDocument(
        id="frm-06",
        name="Form with Bad Email (Rule Fail)",
        doc_type=DocType.FORM,
        text="""EQUIPMENT CHECKOUT FORM
Form ID: EQ-101
Applicant Name: Brian Foster
Date of Birth: 1995-04-12
Email: invalid-email-format-here
Phone: 503-555-3344""",
        expected_fields={
            "form_id": "EQ-101",
            "applicant_name": "Brian Foster",
            "date_of_birth": "1995-04-12",
            "email": "invalid-email-format-here",
            "phone": "503-555-3344",
        },
        expected_status=DocStatus.ACTION_REQUIRED,
        category="Form",
    ),
]
