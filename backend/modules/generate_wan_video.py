import subprocess
import os
import shutil
import glob
from pathlib import Path

def generate_video_via_wan(prompt_text: str, output_path: str = None):
    """
    Programmatically trigger the local Wan2.1 CLI pipeline.
    
    Args:
        prompt_text: The AI-generated summary/prompt to visualize.
        output_path: Absolute path where the final .mp4 should be saved.
                    If None, it will be placed in the current directory as 'summary_video.mp4'.
    """
    # 1. Resolve Wan2.1 directory relative to execution root
    base_execution_dir = os.getcwd()
    
    # We assume 'Wan2.1' is in the root of the project.
    # If we are starting from /app or /insight, it should be there.
    wan_dir = os.path.join(base_execution_dir, "Wan2.1")
    
    # Path resolution fallback (like in our pipeline logic)
    if not os.path.exists(wan_dir):
        # Try one level up if we are executing from within /backend
        wan_dir = os.path.abspath(os.path.join(base_execution_dir, "..", "Wan2.1"))

    # 2. Construct the CLI command from the user's provided snippet
    cmd = [
        "python", "generate.py",
        "--task", "t2v-1.3B",
        "--size", "832*480",
        "--ckpt_dir", "./Wan2.1-T2V-1.3B",
        "--offload_model", "True",
        "--t5_cpu",
        "--sample_shift", "8",
        "--sample_guide_scale", "6",
        "--prompt", prompt_text
    ]

    print(f"[Wan2.1 Migration] Triggering generation...")
    print(f"[Wan2.1 Migration] CWD: {wan_dir}")
    print(f"[Wan2.1 Migration] CMD: {' '.join(cmd)}")

    if not os.path.exists(wan_dir):
        print(f"WARNING: Wan2.1 directory not found at {wan_dir}. Video generation may fail.")
    
    try:
        # Run the generation process
        # Note: We use shell=False for security as per previous patterns
        result = subprocess.run(
            cmd,
            cwd=wan_dir,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"[Wan2.1 Migration] Generation successful.")
        
        # 3. Handle output file moving to the static assets directory
        # Wan2.1 typically saves to a results/ directory by default.
        # We need to find the generated file and move it to output_path.
        if output_path:
            # Look for the most recently created .mp4 in the wan_dir or wan_dir/results
            search_pattern = os.path.join(wan_dir, "**", "*.mp4")
            files = glob.glob(search_pattern, recursive=True)
            if files:
                # Get the latest file
                latest_file = max(files, key=os.path.getctime)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                shutil.move(latest_file, output_path)
                print(f"[Wan2.1 Migration] Video moved to: {output_path}")
            else:
                print(f"[Wan2.1 Migration] Error: No output video found in {wan_dir}")
                
        return True

    except subprocess.CalledProcessError as e:
        print(f"[Wan2.1 Migration] Generation failed (Exit {e.returncode})")
        print(f"[Wan2.1 Migration] Error: {e.stderr}")
        return False
    except Exception as e:
        print(f"[Wan2.1 Migration] Unexpected error: {str(e)}")
        return False
