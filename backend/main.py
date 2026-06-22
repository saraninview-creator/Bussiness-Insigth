"""
DataNarrate API — Multi-Scene Video Architecture & Gemini 2.5 Flash Chat
"""
import os
import threading
import uuid
import json
import shutil
from pathlib import Path
from typing import Optional

import pandas as pd
import aiofiles
from pydantic import BaseModel
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from pipeline import JOBS_DIR, get_result, get_status, job_dir, run_pipeline
from modules.chatbot import HybridDataBot
from modules.generate_wan_video import generate_video_from_storyboard
from modules.nlp_engine import nlp_engine

# --- Configuration & App Init ---
app = FastAPI(title="DataNarrate API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/videos", StaticFiles(directory=str(JOBS_DIR)), name="videos")

class ChatRequest(BaseModel):
    query: str

# --- Global Orchestration State ---
video_jobs = {}

# --- Background Support Methods ---

def start_background_video_task(job_id: str, script_text: str, output_path: str):
    """
    Decoupled Scene Pipeline:
    1. NLP Segmenter (Semantic Storyboarding)
    2. Sequential Fast Inference (Wan2.1 Engines)
    3. Final FFmpeg Stitcher
    """
    try:
        video_jobs[job_id] = {"status": "processing", "progress": 10}
        
        # 1. Semantic Storyboarding
        storyboard = nlp_engine.storyboard(script_text)
        video_jobs[job_id]["progress"] = 30
        
        # 2. Sequential Generator & Compiler
        success = generate_video_from_storyboard(storyboard, output_path)
        
        if success:
            video_jobs[job_id] = {
                "status": "completed", 
                "url": f"/videos/{job_id}/summary_video.mp4", 
                "progress": 100
            }
        else:
            video_jobs[job_id] = {"status": "failed"}
    except Exception as e:
        video_jobs[job_id] = {"status": "error", "message": str(e)}

# --- Endpoints ---

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    explanation_level: str = Form("standard_65s")
):
    ext = Path(file.filename).suffix.lower()
    if ext not in {".csv", ".xlsx", ".xls"}:
        raise HTTPException(status_code=400, detail="Unsupported file format.")

    job_id = str(uuid.uuid4())
    jd = job_dir(job_id)
    jd.mkdir(parents=True, exist_ok=True)
    upload_path = jd / f"upload{ext}"

    async with aiofiles.open(upload_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    def _run():
        run_pipeline(job_id, str(upload_path), explanation_level)

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    return JSONResponse({"job_id": job_id})

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    state = get_status(job_id)
    return JSONResponse(state)

@app.get("/result/{job_id}")
async def get_job_result(job_id: str):
    res = get_result(job_id)
    if res is None:
        raise HTTPException(status_code=404, detail="Result not ready.")
    return JSONResponse(res)

@app.get("/api/video/status/{job_id}")
async def fetch_video_status(job_id: str):
    return JSONResponse(video_jobs.get(job_id, {"status": "not_started"}))

@app.post("/api/video/generate/{job_id}")
async def trigger_video_generation(job_id: str):
    """
    Decoupled Orchestrator:
    Starts the video compilation in a background thread.
    """
    jd = job_dir(job_id)
    findings_file = jd / "findings.json"
    if not findings_file.exists():
        raise HTTPException(status_code=400, detail="Wait for audit results to complete.")
    
    with open(findings_file, "r") as f:
        findings = json.load(f)
    
    # Slice script parts for stitching
    full_script = " ".join([f["text"] for f in findings])
    output_path = str(jd / "summary_video.mp4")
    
    thread = threading.Thread(
        target=start_background_video_task, 
        args=(job_id, full_script, output_path)
    )
    thread.daemon = True
    thread.start()
    
    return JSONResponse(status_code=202, content={"job_id": job_id, "status": "processing"})

@app.post("/api/chat/{job_id}")
async def post_chat_query(job_id: str, request: ChatRequest):
    jd = job_dir(job_id)
    if not jd.exists():
        raise HTTPException(status_code=404, detail="Job not found")

    # Locate dataset
    upload_file = None
    for ext in [".csv", ".xlsx", ".xls"]:
        if (jd / f"upload{ext}").exists():
            upload_file = jd / f"upload{ext}"
            break
            
    if not upload_file:
        raise HTTPException(status_code=404, detail="Dataset missing.")

    # Contextual Summary
    findings_summary = "No insights."
    findings_path = jd / "findings.json"
    if findings_path.exists():
        try:
            findings = json.loads(findings_path.read_text(encoding="utf-8"))
            findings_summary = "\n".join([f"- {f.get('text', '')}" for f in findings])
        except Exception: pass

    # Parser
    try:
        df = pd.read_csv(upload_file) if str(upload_file).endswith('.csv') else pd.read_excel(upload_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parser error: {str(e)}")

    bot = HybridDataBot(df, findings_summary)
    
    def stream_generator():
        for chunk in bot.ask_stream(request.query):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
