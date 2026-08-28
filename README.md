# AI DocumentOps

**Enterprise Document Intelligence & Compliance Audit Engine**  
Powered by **IBM watsonx.ai** & **IBM Docling**

AI DocumentOps is an automated document processing platform that ingests unstructured business documents (invoices, forms, contracts), extracts key data with layout-aware AI, validates mathematical integrity, and enforces confidence-based human-in-the-loop review.

---

## Key Features & IBM Stack

- **IBM Docling Parser**: Layout-aware document parsing that retains visual structure, tables, and hierarchy into clean Markdown (with fallback OCR).
- **IBM Granite 3.0 via watsonx.ai**: Structured JSON extraction for target fields (`currency`, `dates`, `totals`, `vendor`) with field-level confidence vectors (0.00–1.00).
- **Deterministic Math Audit Engine**: Executes strict arithmetic checks (`subtotal + tax = total`) prior to posting to database.
- **Confidence-Based Routing**: Auto-approves high-confidence extractions, queues uncertain fields for review, and forces verification on mathematical mismatches.
- **Side-by-Side Review Interface**: Interactive document viewer alongside extracted form fields with real-time confidence indicators and error alerts.
- **Immutable Audit Lineage**: Timestamped tracking of every system extraction, confidence score, rule validation, and human correction[cite: 1].

---

## Core Architecture

frontend/   Next.js / React + Tailwind CSS + Recharts + Framer Motion + Lucide UI[cite: 1]
backend/    FastAPI (Python) + Neon Serverless PostgreSQL[cite: 1]
ai_stack/   IBM Docling + IBM Granite 3.0 (watsonx.ai)[cite: 1]
### 7-Stage Pipeline Flow

| Stage | Module / Component | Behaviour |
| --- | --- | --- |
| **1. Upload & Store** | `services/documents.py` | Validates file constraints (PDF, PNG, JPG, DOCX), generates unique Document ID[cite: 1]. |
| **2. Layout Parsing** | `extraction.py` | **IBM Docling** converts document to structured Markdown + layout metadata[cite: 1]. |
| **3. Structured Extraction** | `field_extractor.py` | **IBM Granite 3.0 (watsonx.ai)** extracts schema fields with per-field confidence scores[cite: 1]. |
| **4. Math Engine** | `validation.py` | Validates `subtotal + tax = total`. If invalid, flags discrepancy and lowers field scores[cite: 1]. |
| **5. Smart Routing** | `routing.py` | `≥90%` AUTO_APPROVED \| `70–89%` NEEDS_REVIEW \| `<70%` or Rule Failure → ACTION_REQUIRED[cite: 1]. |
| **6. Persistence** | PostgreSQL (Neon) | Stores document entities, extracted values, status flags, and reviewer edits[cite: 1]. |
| **7. Audit Lineage** | `runner.py` | Records every transition, rule trigger, score update, and edit to immutable audit logs[cite: 1]. |

---

## Routing Thresholds

- **`AUTO_APPROVED` (Confidence $\ge$ 90% & Math Valid)**: Written directly to the database without human touch[cite: 1].
- **`NEEDS_REVIEW` (Confidence 70–89% & Math Valid)**: Queued for human verification with lowest confidence fields highlighted[cite: 1].
- **`ACTION_REQUIRED` (Confidence < 70% OR Math Mismatch)**: Forced manual review. Math mismatches route here regardless of overall confidence score[cite: 1].

---

## Local Setup

### Prerequisites
- Python 3.10+
- Node.js 20+
- PostgreSQL (or Neon DB account)
- IBM Cloud Account with watsonx.ai access[cite: 1]

## Environment Variables
Create a `.env` file inside the `backend/` directory:

```env
WATSONX_APIKEY=your_ibm_cloud_api_key
WATSONX_PROJECT_ID=your_watsonx_project_id
DOCOPS_DATABASE_URL=postgresql://user:password@localhost:5432/documentops
```
## Running the Application

### 1. Backend Service (FastAPI)
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Seed initial demo data (optional)
python -m app.seed

# Start development server
uvicorn app.main:app --reload --port 8000
```
## 2.Frontend Setup (Next.js)

### Quick Start
```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

## API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/documents` | Upload and process a document through the 7-stage engine |
| `GET` | `/api/documents` | Fetch all documents (optional status filtering) |
| `GET` | `/api/documents/{id}` | Detailed document extraction, confidence breakdown, and audit log |
| `GET` | `/api/documents/{id}/file` | Fetch original file for side-by-side viewer |
| `POST` | `/api/documents/{id}/review` | Submit human reviewer corrections and approve/reject |
| `POST` | `/api/documents/{id}/reprocess` | Re-run document through extraction & validation rules |
| `GET` | `/api/metrics` | Executive dashboard aggregate metrics |
| `GET` | `/api/quality` | Field accuracy trends and evaluation metrics |

## Demo
<img width="1910" height="903" alt="Screenshot 2026-08-26 005214" src="https://github.com/user-attachments/assets/ba998074-de33-45e7-8520-2504aea108ac" />
<img width="1912" height="905" alt="Screenshot 2026-08-26 004841" src="https://github.com/user-attachments/assets/89b6c3a4-253f-452c-8c8e-ffbc5c971d7c" />
<img width="1905" height="912" alt="Screenshot 2026-08-26 004950" src="https://github.com/user-attachments/assets/dd8d6576-11d4-468b-a79a-31bc67c19f36" />
<img width="1908" height="911" alt="Screenshot 2026-08-26 005844" src="https://github.com/user-attachments/assets/8b061809-e353-43b1-83d4-00f267265117" />
<img width="1902" height="902" alt="Screenshot 2026-08-26 005947" src="https://github.com/user-attachments/assets/8dd91f0f-8f1d-47de-90e9-296bf001382f" />
<img width="1911" height="907" alt="Screenshot 2026-08-26 010024" src="https://github.com/user-attachments/assets/359580e5-f1fb-4a16-9637-04f070fb7b84" />
<img width="1907" height="907" alt="Screenshot 2026-08-26 005049" src="https://github.com/user-attachments/assets/c8b98b41-e816-4f2d-bf22-b73d7a4f0beb" />
<img width="1902" height="903" alt="Screenshot 2026-08-26 005133" src="https://github.com/user-attachments/assets/5f397c65-2dde-4107-a096-8e368e315e2e" />





