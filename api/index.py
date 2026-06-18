"""
Vercel serverless entrypoint — DataNarrate API.

Vercel Python runtime discovers `app` from api/index.py automatically.

Architecture note:
  - /api/* routes  → this serverless function (Supabase read/write)
  - Heavy pipeline  → must run on a self-hosted backend (Railway / Render / VPS)
                      Set VITE_API_URL in Vercel env-vars to point to it.

When SUPABASE_URL + SUPABASE_KEY are set, this function:
  • Accepts CSV/Excel uploads → stores raw file in Supabase Storage
  • Creates a job record    → Supabase `jobs` table
  • Returns status/results  → polled by the frontend

When those env-vars are absent the function returns 503 with a helpful message.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Supabase (optional) ───────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
supabase_client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except ImportError:
        pass  # supabase package not installed in this runtime


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="DataNarrate API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _require_supabase() -> None:
    """Raise 503 if Supabase is not configured."""
    if not supabase_client:
        raise HTTPException(
            status_code=503,
            detail=(
                "Database not configured. "
                "Add SUPABASE_URL and SUPABASE_KEY to Vercel environment variables. "
                "For local development use the self-hosted backend at http://localhost:8000."
            ),
        )


def _get_status(job_id: str) -> dict | None:
    if not supabase_client:
        return None
    try:
        res = (
            supabase_client.table("jobs")
            .select("status, error")
            .eq("id", job_id)
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception:
        return None


def _get_result(job_id: str) -> dict | None:
    if not supabase_client:
        return None
    try:
        res = (
            supabase_client.table("jobs")
            .select("findings, video_url, status")
            .eq("id", job_id)
            .execute()
        )
        if res.data and res.data[0].get("findings"):
            return {
                "findings": res.data[0]["findings"],
                "video_url": res.data[0].get("video_url"),
            }
    except Exception:
        pass
    return None


def _upsert_job(job_id: str, status: str, error: str = "") -> None:
    if not supabase_client:
        return
    try:
        supabase_client.table("jobs").upsert(
            {"id": job_id, "status": status, "error": error}
        ).execute()
    except Exception as e:
        print("Supabase upsert error:", e)


# ── Routes (/api/* prefix — matched by vercel.json) ───────────────────────────

@app.get("/health")
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "supabase": "connected" if supabase_client else "not configured",
    }


@app.post("/upload")
@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    explanation_level: str = Form("concise_21s"),
):
    """
    Accept a CSV/Excel upload → store in Supabase Storage → create job record.
    The actual analysis pipeline runs on the self-hosted backend which polls
    for queued jobs and updates the Supabase `jobs` table when complete.
    """
    _require_supabase()

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    job_id = str(uuid.uuid4())
    content = await file.read()

    # Store raw CSV/Excel in Supabase Storage bucket "datanarrate"
    try:
        supabase_client.storage.from_("datanarrate").upload(
            file=content,
            path=f"{job_id}/upload{ext}",
            file_options={"content-type": "application/octet-stream"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {e}")

    # Create job record (status=queued)
    _upsert_job(job_id, "queued")

    return JSONResponse({"job_id": job_id})


@app.get("/status/{job_id}")
@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """Poll pipeline stage from Supabase."""
    _require_supabase()
    state = _get_status(job_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JSONResponse(state)


@app.get("/result/{job_id}")
@app.get("/api/result/{job_id}")
async def get_job_result(job_id: str):
    """Return findings + video URL once the job is done."""
    _require_supabase()

    state = _get_status(job_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if state.get("status") == "error":
        raise HTTPException(
            status_code=500, detail=state.get("error", "Pipeline error")
        )
    if state.get("status") != "done":
        raise HTTPException(
            status_code=202,
            detail=f"Job still in progress: {state.get('status')}",
        )

    result = _get_result(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not available yet")

    return JSONResponse(result)
