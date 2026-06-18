"""
FastAPI application — DataNarrate backend
Endpoints: POST /upload, GET /status/{job_id}, GET /result/{job_id}
"""
from __future__ import annotations

import threading
import uuid
from pathlib import Path

import aiofiles
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from pipeline import JOBS_DIR, get_result, get_status, job_dir, run_pipeline

app = FastAPI(title="DataNarrate API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve rendered videos
JOBS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/videos", StaticFiles(directory=str(JOBS_DIR)), name="videos")


ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    explanation_level: str = Form("concise_21s")
):
    """Accept a CSV/Excel upload, start the analysis pipeline, return job_id."""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    job_id = str(uuid.uuid4())
    jd = job_dir(job_id)
    upload_path = jd / f"upload{ext}"

    # Save the uploaded file
    async with aiofiles.open(upload_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # Launch pipeline in a background thread (non-blocking)
    def _run():
        run_pipeline(job_id, str(upload_path), explanation_level)

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    return JSONResponse({"job_id": job_id})


@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Return current pipeline stage for a job."""
    jd = job_dir(job_id)
    if not jd.exists():
        raise HTTPException(status_code=404, detail="Job not found")
    state = get_status(job_id)
    return JSONResponse(state)


@app.get("/result/{job_id}")
async def get_job_result(job_id: str):
    """Return findings + video URL when the job is done."""
    jd = job_dir(job_id)
    if not jd.exists():
        raise HTTPException(status_code=404, detail="Job not found")

    state = get_status(job_id)
    if state["status"] == "error":
        raise HTTPException(status_code=500, detail=state.get("error", "Pipeline error"))
    if state["status"] != "done":
        raise HTTPException(status_code=202, detail=f"Job still in progress: {state['status']}")

    result = get_result(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not available yet")

    return JSONResponse(result)


@app.get("/health")
async def health():
    return {"status": "ok"}
