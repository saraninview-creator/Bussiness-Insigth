import torch
import os
import sys
from pathlib import Path

# Assume the user has the Wan2.1 repository in their path or root
sys.path.append(os.getcwd())

def run_test_inference(prompt, lora_path, base_model_path="./Wan2.1-T2V-1.3B"):
    """
    Loads Wan2.1 base model, injects LoRA weights, and generates a test video.
    """
    print(f"Loading base model from: {base_model_path}")
    print(f"Applying LoRA weights from: {lora_path}")

    # 1. Imports from the local Wan2.1 repository
    # (These become available after the user clones/sets up the Wan2.1 repo)
    try:
        from scripts.generate import WanGenerator # Example internal class name
    except ImportError:
        print("Error: Could not find Wan2.1 generation logic. Ensure you are running this from the Wan2.1 root directory.")
        return

    # 2. Setup Generator with LoRA
    # In a typical setup, we pass the lora_path to the model loader
    generator = WanGenerator(
        model_path=base_model_path,
        lora_path=lora_path,
        device="cuda",
        offload_model=True,
        t5_cpu=True
    )

    # 3. Generate
    print(f"Generating test video for prompt: '{prompt}'")
    output_file = "test_finetuned_output.mp4"
    
    generator.generate(
        prompt=prompt,
        size="832*480",
        output_path=output_file,
        sample_shift=8,
        sample_guide_scale=6
    )

    print(f"Success! Test video saved to: {output_file}")

if __name__ == "__main__":
    TEST_PROMPT = "A professional dashboard showing a neon blue line chart rising, cinematic lighting, high quality"
    LORA_WEIGHTS = "./wan2.1_output_lora"
    
    if not os.path.exists(LORA_WEIGHTS):
        print(f"Warning: LoRA weights not found at {LORA_WEIGHTS}. Run the training script first.")
    else:
        run_test_inference(TEST_PROMPT, LORA_WEIGHTS)
