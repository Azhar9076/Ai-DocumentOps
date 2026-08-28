# AI DocumentOps

Document automation platform that turns unstructured business documents (invoices, forms, contracts)
into validated structured data with field-level confidence scoring and human-in-the-loop review.

## Architecture

```
frontend/  React 19 + Vite + Tailwind + Recharts + Framer Motion + Lucide
backend/   FastAPI + SQLAlchemy + PostgreSQL, Pydantic extraction schemas, OCR via Tesseract
```

Pipeline (`backend/app/pipeline/`):

| Stage | Module | Behaviour |
| --- | --- | --- |
| File validation & storage | `services/documents.py` | Type/size checks, per-document storage folder |
| Text & visual extraction | `extraction.py` | PDF text layer, OCR fallback (Tesseract), DOCX parsing, OCR quality score |
| Classification | `classifier.py` | Weighted keyword scoring → `INVOICE` / `FORM` / `CONTRACT` |
| Structured extraction | `field_extractor.py` | Regex extraction into strict Pydantic schemas, per-field confidence 0.00–1.00 |
| Validation engine | `validation.py` | Deterministic rules (subtotal + tax = total, formats, required fields) that penalise confidence |
| Routing | `routing.py` | ≥90% `AUTO_APPROVED`, 70–89% `NEEDS_REVIEW`, <70% or rule failure `ACTION_REQUIRED` |
| Audit trail | `runner.py` | Every transition, score and reviewer edit appended to `audit_logs` |

Tables: `documents`, `extracted_fields`, `reviews`, `audit_logs`.

## Local setup

Requirements: Python 3.10+, Node 22 (`.nvmrc`), PostgreSQL 14+, `tesseract-ocr`, `poppler-utils`.

```bash
sudo apt-get install -y postgresql tesseract-ocr poppler-utils
sudo -u postgres psql -c "CREATE USER docops WITH PASSWORD 'docops' SUPERUSER;"
sudo -u postgres psql -c "CREATE DATABASE documentops OWNER docops;"

# backend
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m app.seed                      # three synthetic demo runs
.venv/bin/uvicorn app.main:app --reload --port 8000

# frontend
cd ../frontend
npm install && npm run dev                        # http://localhost:5173
```

Configuration is environment-driven with the `DOCOPS_` prefix, e.g.
`DOCOPS_DATABASE_URL`, `DOCOPS_AUTO_APPROVE_THRESHOLD`, `DOCOPS_REVIEW_THRESHOLD`.
The frontend reads `VITE_API_BASE` (defaults to `http://localhost:8000`).

## Seeded demo runs

`python -m app.seed` generates real files and pushes them through the real pipeline:

| Document | Result |
| --- | --- |
| `clean_invoice.pdf` | 96% confidence → `AUTO_APPROVED` |
| `scanned_form.png` (OCR) | ~71% with two ambiguous handwriting fields → `NEEDS_REVIEW` |
| `inconsistent_invoice.pdf` | Subtotal 100 + Tax 18 ≠ Total 135 → `ACTION_REQUIRED` with a math validation alert |

## API

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/documents` | Upload and process a document |
| GET | `/api/documents` | List documents (optional `?status=`) |
| GET | `/api/documents/{id}` | Detail with fields, issues, reviews and audit trail |
| GET | `/api/documents/{id}/file` | Original file for the viewer |
| POST | `/api/documents/{id}/review` | Submit edits and approve/reject |
| POST | `/api/documents/{id}/reprocess` | Re-run the pipeline |
| GET | `/api/metrics` | Dashboard metrics |
| GET | `/api/quality` | Accuracy and quality evaluation |

## Checks

The suite runs against an isolated `documentops_test` database
(`sudo -u postgres createdb -O docops documentops_test`), so the demo data is never touched.

```bash
cd backend && .venv/bin/ruff check . && .venv/bin/python -m pytest
cd frontend && npm run lint && npm run build
```
## Demo
<img width="1910" height="903" alt="Screenshot 2026-08-26 005214" src="https://github.com/user-attachments/assets/ba998074-de33-45e7-8520-2504aea108ac" />
<img width="1912" height="905" alt="Screenshot 2026-08-26 004841" src="https://github.com/user-attachments/assets/89b6c3a4-253f-452c-8c8e-ffbc5c971d7c" />
<img width="1905" height="912" alt="Screenshot 2026-08-26 004950" src="https://github.com/user-attachments/assets/dd8d6576-11d4-468b-a79a-31bc67c19f36" />
<img width="1908" height="911" alt="Screenshot 2026-08-26 005844" src="https://github.com/user-attachments/assets/8b061809-e353-43b1-83d4-00f267265117" />
<img width="1902" height="902" alt="Screenshot 2026-08-26 005947" src="https://github.com/user-attachments/assets/8dd91f0f-8f1d-47de-90e9-296bf001382f" />
<img width="1911" height="907" alt="Screenshot 2026-08-26 010024" src="https://github.com/user-attachments/assets/359580e5-f1fb-4a16-9637-04f070fb7b84" />
<img width="1907" height="907" alt="Screenshot 2026-08-26 005049" src="https://github.com/user-attachments/assets/c8b98b41-e816-4f2d-bf22-b73d7a4f0beb" />
<img width="1902" height="903" alt="Screenshot 2026-08-26 005133" src="https://github.com/user-attachments/assets/5f397c65-2dde-4107-a096-8e368e315e2e" />





