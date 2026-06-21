"""
Pipeline Orchestrator — runs the full analysis pipeline for a job.
Steps: parse → profile → findings → script → audio → video → done
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.dirname(__file__))



from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase_client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except ImportError:
        pass

from modules.chart_selector import enrich_findings
from modules.findings import generate_findings
from modules.profiler import profile_data
from modules.script_gen import generate_script
from modules.tts import concatenate_audio, synthesize_segments

JOBS_DIR = Path(__file__).parent / "jobs"
REMOTION_DIR = Path(__file__).parent.parent / "remotion"

# Print at module load — appears immediately in Render startup logs
print(f"[STARTUP] pipeline.py loaded from: {__file__}")
print(f"[STARTUP] REMOTION_DIR resolved to: {REMOTION_DIR.resolve()}")
print(f"[STARTUP] REMOTION_DIR exists: {REMOTION_DIR.exists()}")


def job_dir(job_id: str) -> Path:
    d = JOBS_DIR / job_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def set_status(job_id: str, status: str, error: str = "") -> None:
    state = {"status": status, "error": error}
    (job_dir(job_id) / "status.json").write_text(json.dumps(state), encoding="utf-8")
    
    if supabase_client:
        try:
            # Perform an upsert based on primary key 'id'
            data = {"id": job_id, "status": status, "error": error}
            supabase_client.table("jobs").upsert(data).execute()
        except Exception as e:
            print("Supabase update error:", e)


def get_status(job_id: str) -> dict[str, str]:
    if supabase_client:
        try:
            res = supabase_client.table("jobs").select("status, error").eq("id", job_id).execute()
            if res.data:
                return res.data[0]
        except Exception:
            pass
            
    p = job_dir(job_id) / "status.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"status": "queued", "error": ""}


def get_result(job_id: str) -> dict[str, Any] | None:
    if supabase_client:
        try:
            res = supabase_client.table("jobs").select("findings, video_url").eq("id", job_id).execute()
            if res.data and res.data[0].get("findings"):
                return {"findings": res.data[0]["findings"], "video_url": res.data[0].get("video_url")}
        except Exception:
            pass

    jd = job_dir(job_id)
    findings_path = jd / "findings.json"
    if not findings_path.exists():
        return None
    findings = json.loads(findings_path.read_text(encoding="utf-8"))
    video_path = jd / "video.mp4"
    video_url = f"/videos/{job_id}/video.mp4" if video_path.exists() else None
    return {"video_url": video_url, "findings": findings}


def run_pipeline(job_id: str, filepath: str, explanation_level: str = "concise_21s") -> None:
    """Run the full pipeline. Called in a background thread."""
    jd = job_dir(job_id)

    try:
        # ── Stage 1: Parsing ─────────────────────────────────────────────
        set_status(job_id, "parsing")
        if not Path(filepath).exists():
            raise FileNotFoundError(f"Upload not found: {filepath}")

        # ── Stage 2: Profiling ───────────────────────────────────────────
        set_status(job_id, "profiling")
        profile = profile_data(filepath)
        profile_path = jd / "profile.json"
        profile_path.write_text(json.dumps(profile, indent=2, default=str), encoding="utf-8")

        # ── Stage 3: Findings + Script ───────────────────────────────────
        set_status(job_id, "scripting")
        findings = generate_findings(filepath, profile, explanation_level)
        findings = enrich_findings(findings, profile)
        script = generate_script(findings, explanation_level)
        # Attach script info (timestamps will be filled after TTS)
        for f, seg in zip(findings, script):
            f["timestamp"] = 0  # placeholder, updated after TTS

        # ── Stage 4: Generate Audio ──────────────────────────────────────
        set_status(job_id, "generating_audio")
        audio_dir = str(jd / "audio")
        segments = synthesize_segments(script, audio_dir)
        
        # Convert local absolute paths into backend-hosted HTTP URLs for Remotion
        for seg in segments:
            base_name = Path(seg.get("audio_file", "")).name
            seg["audio_file"] = f"http://localhost:8000/videos/{job_id}/audio/{base_name}"

        # Update timestamps in findings
        for i, (f, seg) in enumerate(zip(findings, segments)):
            f["timestamp"] = round(seg.get("start_ms", 0) / 1000, 2)
            f["duration_seconds"] = round(seg.get("duration_ms", 5000) / 1000, 2)

        # Save enriched findings + script
        (jd / "findings.json").write_text(
            json.dumps(findings, indent=2, default=str), encoding="utf-8"
        )
        (jd / "script.json").write_text(
            json.dumps(segments, indent=2, default=str), encoding="utf-8"
        )

        # ── Stage 5: Assemble Video ──────────────────────────────────────
        set_status(job_id, "assembling_video")
        props = {
            "jobId": job_id,
            "findings": findings,
            "audioFile": "",
            "segments": segments,
        }
        props_path = jd / "props.json"
        props_path.write_text(json.dumps(props, default=str), encoding="utf-8")

        output_mp4 = str(jd / "video.mp4")
        _render_video(str(props_path), output_mp4)

        video_url = f"/videos/{job_id}/video.mp4"
        
        # ── Stage 6: Supabase Cloud Sync (Optional) ──────────────────────
        if supabase_client:
            try:
                with open(output_mp4, "rb") as f:
                    supabase_client.storage.from_("datanarrate").upload(
                        file=f,
                        path=f"{job_id}/video.mp4",
                        file_options={"content-type": "video/mp4"}
                    )
                # Get the public URL for the video
                video_url = supabase_client.storage.from_("datanarrate").get_public_url(f"{job_id}/video.mp4")
            except Exception as e:
                print("Supabase storage upload error:", e)

            # Update the DB with the final findings and video_url
            try:
                data = {"findings": findings, "video_url": video_url}
                supabase_client.table("jobs").update(data).eq("id", job_id).execute()
            except Exception as e:
                print("Supabase update findings error:", e)

        # ── Done ─────────────────────────────────────────────────────────
        set_status(job_id, "done")

    except Exception as exc:
        set_status(job_id, "error", str(exc))
        raise


import shutil

def _render_video(props_path: str, output_path: str) -> None:
    """Call Remotion CLI via Node to render the video securely."""
    # Use the module-level REMOTION_DIR constant which is anchored via Path(__file__).
    # This resolves correctly BOTH locally (C:\...\insight\remotion)
    # AND inside the Render container (/app/remotion) regardless of cwd.
    remotion_abs = str(REMOTION_DIR.resolve())

    # ── Runtime path validation (shows up in Render logs) ────────────────────
    print(f"[DEBUG] Python cwd         : {os.getcwd()}")
    print(f"[DEBUG] pipeline __file__  : {__file__}")
    print(f"[DEBUG] REMOTION_DIR       : {REMOTION_DIR}")
    print(f"[DEBUG] remotion_abs       : {remotion_abs}")
    print(f"[DEBUG] remotion exists    : {os.path.exists(remotion_abs)}")

    if not os.path.exists(remotion_abs):
        import glob
        nearby = glob.glob('/app/*') or glob.glob(str(Path(remotion_abs).parent / '*'))
        print(f"[CRITICAL ERROR] {remotion_abs} does not exist!")
        print(f"[CRITICAL ERROR] Contents of parent dir: {nearby}")
        raise FileNotFoundError(f"Remotion directory not found: {remotion_abs}")

    # Normalize paths for Remotion (forward slashes satisfy Remotion's CLI parser)
    props_abs = os.path.abspath(props_path).replace("\\", "/")
    output_abs = os.path.abspath(output_path).replace("\\", "/")

    # On Windows use 'npx.cmd'; on Linux/macOS (Render container) use 'npx'
    npx_exec = 'npx.cmd' if os.name == 'nt' else 'npx'

    cmd = [
        npx_exec,
        "--yes",
        "remotion",
        "render",
        "src/index.tsx",
        "DataNarrate",
        output_abs,
        f"--props={props_abs}",
        "--log=error"
    ]

    print(f"[Remotion] cwd={remotion_abs}")
    print(f"[Remotion] cmd={' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        cwd=remotion_abs,
        capture_output=True,
        timeout=600,
        shell=False,
    )

    if result.returncode != 0:
        err = result.stderr.decode('utf-8', errors='replace') if result.stderr else "Unknown Remotion Error"
        raise RuntimeError(f"Remotion render failed (exit {result.returncode}): {err}")
