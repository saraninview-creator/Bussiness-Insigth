import subprocess
import os
import shutil
import glob
from pathlib import Path
from typing import List, Dict

def generate_video_from_storyboard(scenes: List[Dict[str, str]], output_path: str):
    """
    Sequential video compiler: Generates individual scenes and stitches them into a final asset.
    """
    base_execution_dir = os.getcwd()
    wan_dir = os.path.join(base_execution_dir, "Wan2.1")
    if not os.path.exists(wan_dir):
        wan_dir = os.path.abspath(os.path.join(base_execution_dir, "..", "Wan2.1"))

    temp_results = []
    print(f"[Video Engine] Starting multi-scene compilation for {len(scenes)} segments...")

    for i, scene in enumerate(scenes):
        scene_prompt = scene["visual_prompt"]
        
        # Generation command with LoRA + FP8 optimizations
        cmd = [
            "python", "generate.py",
            "--task", "t2v-1.3B",
            "--size", "832*480",
            "--ckpt_dir", "./Wan2.1-T2V-1.3B",
            "--offload_model", "True",
            "--t5_cpu",
            "--dtype", "fp8",
            "--sample_shift", "8",
            "--sample_guide_scale", "6",
            "--sample_steps", "25",
            "--frame_num", "81", # ~10-12s scenes
            "--prompt", scene_prompt
        ]
        
        print(f"--- Compiling Scene {i+1}: {scene_prompt[:60]}... ---")
        
        try:
            subprocess.run(cmd, cwd=wan_dir, check=True, capture_output=True)
            
            # Locate result in Wan2.1 results dir
            files = glob.glob(os.path.join(wan_dir, "**", "*.mp4"), recursive=True)
            if files:
                latest = max(files, key=os.path.getctime)
                chunk_dest = os.path.join(base_execution_dir, f"segment_{i}.mp4")
                shutil.move(latest, chunk_dest)
                temp_results.append(chunk_dest)
        except Exception as e:
            print(f"Scene compilation failed: {e}")

    # Final FFmpeg Stitching
    if temp_results:
        print("[Video Engine] Finalizing broadcast sequence...")
        list_file = os.path.join(base_execution_dir, "manifest.txt")
        with open(list_file, "w") as f:
            for ch in temp_results:
                f.write(f"file '{ch.replace('\\', '/')}'\n")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        concat_cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", list_file, "-c", "copy", output_path
        ]
        
        try:
            subprocess.run(concat_cmd, check=True, capture_output=True)
            print(f"COMPLETE: Optimized video saved to {output_path}")
            # Cleanup
            os.remove(list_file)
            for ch in temp_results: os.remove(ch)
            return True
        except Exception: return False
            
    return False


def generate_video_via_wan(prompt_text: str, output_path: str = None):
    # Compatibility wrapper for single-string legacy calls
    from modules.nlp_engine import nlp_engine
    storyboard = nlp_engine.storyboard(prompt_text)
    return generate_video_from_storyboard(storyboard, output_path)
