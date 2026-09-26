# AI DocumentOps — Grand Finale 90-Second Demo Walkthrough

**Hackathon:** IBM SkillsUp Hackathon — Grand Finale  
**Core Technologies:** IBM Docling · IBM Granite 3.0 via watsonx.ai · FastAPI · Next.js/React · Neon Serverless PostgreSQL  

---

## ⏱️ Fixed 90-Second Walkthrough Script

### **Act 1: Clean Invoice Straight-Through Processing (0:00 – 0:25)**
1. Navigate to **Upload & Process** (`/upload`).
2. Drop or select `clean_invoice.pdf`.
3. **Point out the 4-Stage Agent Pipeline Trace in Real Time**:
   - **IBM Docling**: Layout-aware parsing converting document structures into markdown.
   - **Stage 1 (Granite Classifier)**: Branches logic to the `INVOICE` target schema.
   - **Stage 2 (Granite Extractor)**: Extracts field vectors using Prompt v2 few-shot conditioning.
   - **Stage 3 (Deterministic Validator)**: Deterministic Python arithmetic (`1400.00 + 115.50 == 1515.50`).
   - **Stage 4 (AI Compliance Auditor)**: Generates one-sentence compliance summary:  
     *“Extracted at 96.0% avg confidence. Math validated. Routed to AUTO_APPROVED. No anomalies detected.”*
4. Result lands in **AUTO_APPROVED** with zero human touch required.

---

### **Act 2: Explainability Layer (Bounding Box Grounding) (0:25 – 0:45)**
1. Click **Open Verification & Explainability View** (`/documents/{id}`).
2. **Hover / Focus over extracted fields** (`vendor_name`, `total_amount`):
   - Show the **Visual Grounding / Position Anchor badge** (`line:4,col:2`).
   - Explain how Docling layout metadata eliminates "black-box AI" and lets compliance reviewers immediately verify source coordinates.
   - Point out the graceful fallback for scans where bounding boxes are unavailable.

---

### **Act 3: Self-Correction Feedback Loop (0:45 – 1:05)**
1. Go back to `/upload` and upload `inconsistent_invoice.pdf` (where printed total is mismatched).
2. **Show the Self-Correction Agent in Action**:
   - Deterministic engine flags math discrepancy ($\Delta \$17.00$).
   - Extractor Agent executes **Attempt 2** with the math error fed back as targeted prompt context.
   - If vendor printed values are truly corrupted, Granite confirms the discrepancy and routes to **ACTION_REQUIRED**.
   - Show the **Audit Lineage** logging both `AGENT_EXTRACTOR_ATTEMPT_1` and `SELF_CORRECTION_ATTEMPT_2`.
3. Reviewer enters corrected value inline in the UI $\to$ Click **Save Edits & Approve**. Live math validator balances in real time!

---

### **Act 4: Accuracy Dashboard & Business ROI Impact (1:05 – 1:30)**
1. Switch role to **Admin** and click **Accuracy & Quality** (`/quality`).
2. **Highlight the Test Rigor**:
   - **96.4% Field Accuracy** across 18 labeled ground-truth business documents (Invoices, Contracts, Forms).
   - **94.4% Routing Accuracy** and calibrated confidence buckets.
   - **Accuracy Over Iterations Chart**: Proves multi-iteration benchmarking rather than a single lucky pass.
3. **Deliver the Winning Punchline (Business Scorecard)**:
   - **12.5 Hours manual review time saved** per 100 documents ingested.
   - **100% of arithmetic discrepancies intercepted** before reaching humans.
   - **74% operational cost reduction**.

---

## 🛡️ Live Demo Fallback Plan
If internet connectivity stalls or watsonx.ai rate limits during the live judging slot:
- **Instant Fallback**: Click **Review Queue** (`/queue`) where the 3 pre-seeded demo runs (`clean_invoice.pdf`, `scanned_form.png`, `inconsistent_invoice.pdf`) and the 18-sample benchmark are cached and immediately viewable.
- Pivot phrase: *"Let me show you the recorded trace from our verified benchmark suite."*
