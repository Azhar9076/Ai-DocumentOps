# AI DocumentOps — Deployment Guide (Vercel & Render)

This guide provides step-by-step instructions for deploying **AI DocumentOps**:
- **Frontend (Vite + React)** on **Vercel**
- **Backend (FastAPI + IBM Granite 3.0)** on **Render**
- **Database (PostgreSQL)** on **Neon Serverless PostgreSQL** (or Render Postgres / SQLite fallback)

---

## Architecture Overview

```
+--------------------------------+          +--------------------------------+
|         Vercel (Frontend)      |  HTTP    |         Render (Backend)       |
|   React SPA + Tailwind CSS     | -------> |    FastAPI + IBM watsonx.ai    |
|   https://<app>.vercel.app     |  CORS    |  https://<app>.onrender.com    |
+--------------------------------+          +--------------------------------+
                                                            |
                                                            v
                                            +--------------------------------+
                                            |       Neon Serverless DB       |
                                            |       PostgreSQL Storage       |
                                            +--------------------------------+
```

---

## Step 1: Deploy Backend on Render

1. Log into your account at [render.com](https://render.com).
2. Click **New +** $\rightarrow$ **Web Service**.
3. Connect your GitHub repository (`Azhar9076/Ai-DocumentOps`).
4. Configure the service settings:
   - **Name**: `ai-documentops-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Region**: Select closest region (e.g., Singapore or US East)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Scroll to **Environment Variables** and add the following keys:

| Key | Example / Recommended Value | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require` | Neon PostgreSQL Connection URI |
| `DOCOPS_WATSONX_API_KEY` | `your-watsonx-api-key` | IBM watsonx.ai API Key for Granite 3.0 |
| `DOCOPS_WATSONX_PROJECT_ID` | `your-watsonx-project-id` | IBM watsonx.ai Project ID |
| `DOCOPS_WATSONX_URL` | `https://us-south.ml.cloud.ibm.com` | watsonx.ai Regional Endpoint |
| `DOCOPS_CORS_ORIGINS` | `*` | Allowed CORS origins (or comma-separated Vercel URL) |
| `PYTHON_VERSION` | `3.11.9` | Python runtime version |

6. Click **Create Web Service**.
7. Once deployed, copy your backend URL (e.g., `https://ai-documentops-backend.onrender.com`).
8. Test health endpoint in browser: `https://ai-documentops-backend.onrender.com/health`

---

## Step 2: Deploy Frontend on Vercel

1. Log into your account at [vercel.com](https://vercel.com).
2. Click **Add New...** $\rightarrow$ **Project**.
3. Import your GitHub repository (`Azhar9076/Ai-DocumentOps`).
4. In Project Settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Select `frontend` (or click Edit and choose `frontend`)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Expand **Environment Variables** and add:

| Key | Value |
|---|---|
| `VITE_API_BASE` | `https://ai-documentops-backend.onrender.com` (Your Render Backend URL) |

6. Click **Deploy**.
7. Once deployment completes, test opening your Vercel URL (e.g., `https://ai-documentops.vercel.app`).

---

## Step 3: Verify End-to-End Pipeline

1. **Health Check**: Open your Vercel URL $\rightarrow$ Navigate to **IBM Governance & Trust** tab to verify live Granite & API status.
2. **Document Upload**: Go to **Upload & Process** $\rightarrow$ Upload an invoice or contract $\rightarrow$ Confirm 3-agent pipeline execution.
3. **Approve & Learn**: Open document verification view $\rightarrow$ Modify a field $\rightarrow$ Click **Approve & Learn** to test benchmark cache update.
4. **Export Certificate**: Click **Audit PDF** in document header $\rightarrow$ Confirm PDF certificate downloads.
5. **Intake Stress-Tester**: Go to **Intake Stress-Test** $\rightarrow$ Click **Simulate High-Volume Intake** $\rightarrow$ Confirm concurrent processing.

---

## Troubleshooting & Tips

- **PostgreSQL / Supabase Connections on Render**: Render free tier instances do not support outbound IPv6. If using Supabase, replace direct connection port `5432` with the IPv4 Transaction Pooler host on port `6543` (e.g., `postgresql://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:6543/postgres`).
- **Automatic SQLite Fallback**: If `DATABASE_URL` is unreachable or misconfigured, the backend automatically logs a warning and initializes a resilient SQLite database in `./data/fallback_app.db` without crashing startup.
- **Cold Starts on Render Free Tier**: Render web services sleep after 15 minutes of inactivity. First request after sleep may take 30–50s.
- **CORS Issues**: Ensure `DOCOPS_CORS_ORIGINS` on Render is set to `*` or includes your exact Vercel deployment domain.
- **Neon Database**: Ensure your Neon connection string uses `sslmode=require`.
