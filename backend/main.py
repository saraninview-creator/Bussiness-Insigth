"""
FastAPI application — DataNarrate backend
Endpoints: POST /upload, GET /status/{job_id}, GET /result/{job_id}
"""
from __future__ import annotations

import os
import threading
import uuid
from pathlib import Path

import json
import pandas as pd
from pydantic import BaseModel
import aiofiles
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from pipeline import JOBS_DIR, get_result, get_status, job_dir, run_pipeline
from modules.chatbot import HybridDataBot
from modules.generate_wan_video import generate_video_via_wan

class ChatRequest(BaseModel):
    query: str

app = FastAPI(title="DataNarrate API", version="1.0.0")

# Render backend explicitly configures CORS for the Vercel frontend
FRONTEND_URL = os.environ.get("FRONTEND_URL", "*")
allowed_origins = [FRONTEND_URL] if FRONTEND_URL != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
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


@app.post("/api/chat/{job_id}")
async def post_chat_query(job_id: str, request: ChatRequest, background_tasks: BackgroundTasks):
    jd = job_dir(job_id)
    if not jd.exists():
        raise HTTPException(status_code=404, detail="Job not found")

    # Locate the originally saved upload representation accurately.
    upload_file = None
    for ext in ALLOWED_EXTENSIONS:
        if (jd / f"upload{ext}").exists():
            upload_file = jd / f"upload{ext}"
            break
            
    if not upload_file:
        raise HTTPException(status_code=404, detail="Original dataset unrecoverable for active job.")

    # Derive analytics summary
    findings_summary = "No insights available."
    findings_path = jd / "findings.json"
    if findings_path.exists():
        try:
            findings = json.loads(findings_path.read_text(encoding="utf-8"))
            findings_summary = "\n".join([f"- {f.get('text', '')}" for f in findings])
        except Exception:
            pass

    # Read active DataFrame
    try:
        if str(upload_file).endswith('.csv'):
            df = pd.read_csv(upload_file)
        else:
            df = pd.read_excel(upload_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data parser error loading active dataset context: {str(e)}")

    # Instantiate hybrid conversational protocol
    try:
        bot = HybridDataBot(df, findings_summary)
        response = bot.ask(request.query)
        
        # Trigger Wan2.1 video generation in background if response is substantial
        if response and len(response) > 20:
            output_mp4 = str(jd / "summary_video.mp4")
            background_tasks.add_task(generate_video_via_wan, response, output_mp4)
            
        return JSONResponse({"response": response})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid Chatbot reasoning error: {str(e)}")


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    # Render requires binding to 0.0.0.0 and mapping to the dynamic PORT env var
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
