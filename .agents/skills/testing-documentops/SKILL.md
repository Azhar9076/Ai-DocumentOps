---
name: testing-documentops
description: How to run and end-to-end test the AI DocumentOps app (FastAPI backend + Vite/React frontend) locally, including seeding, routes, and known gotchas.
---

# Testing AI DocumentOps locally

## Bring up the stack
- Postgres 14 local, db `documentops`, user/pass `docops`/`docops`.
- Backend: `backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend`
  (log to /tmp/api.log). Health-check with `curl -s localhost:8000/api/documents`.
- Re-seed if the DB is empty: `cd backend && .venv/bin/python -m app.seed` — creates
  clean_invoice.pdf (AUTO_APPROVED ~96%), scanned_form.png (NEEDS_REVIEW ~71%),
  inconsistent_invoice.pdf (ACTION_REQUIRED ~76%, invoice_math rule failure).
- Frontend requires **Node 22** (otherwise the rolldown native binding fails):
  `export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"; nvm use 22; npm --prefix frontend run dev -- --port 5173`
- Frontend talks to `VITE_API_BASE` or defaults to `http://localhost:8000`.

## Useful API shortcuts for building assertions before touching the UI
- `GET /api/metrics`, `GET /api/quality`, `GET /api/documents`, `GET /api/documents/{id}`
  give exact expected numbers (card values, chart buckets, field confidences) so UI
  assertions can be written with concrete values.
- Unknown id returns 404 `{"detail":"Document not found"}`; the UI renders an
  ErrorNotice ("Something went wrong" / detail + Retry) — good error-boundary check.

## UI routes
`/` dashboard, `/upload`, `/queue`, `/documents/:id` (HITL verify), `/workflow`, `/quality`.
Unknown routes redirect to `/`.

## Gotchas
- Uploading via the drop zone opens the native GTK file chooser: click the dashed zone,
  then just type the absolute path and press Return once. Pressing Return twice re-opens
  the dialog (the drop zone is a focused `role="button"`), press Escape to dismiss.
- The pipeline finishes in <1s, so the animated 6-step progress indicator jumps straight
  to all-complete; capturing a mid-run "active/spinner" step is generally not possible.
  Don't treat that as a failure; assert the final all-green state plus the result card.
- Every upload permanently adds a document, shifting dashboard/quality numbers. Snapshot
  expected values immediately before the assertion, or re-seed between runs.
- PDF preview: if the pane on `/documents/:id` is blank and Chrome shows a download bubble,
  check the header with `curl -D- -o /dev/null localhost:8000/api/documents/<id>/file`.
  `FileResponse(..., filename=...)` sets `Content-Disposition: attachment`, which stops Chrome
  from embedding the PDF in the `<object>`; passing
  `headers={"content-disposition": f'inline; filename="{name}"'}` instead makes it render.
  Images (`<img>`) render fine either way, so only PDFs expose this class of bug.
  When asserting the PDF actually rendered, click the embedded viewer's "+" zoom button a
  couple of times — the default fit-to-width render is too small for legible screenshot proof.

## Devin Secrets Needed
None — everything runs locally with the seeded Postgres credentials above.
