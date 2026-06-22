#!/bin/bash

# ==============================================================================
# Wan2.1-T2V-1.3B LoRA Fine-Tuning Execution Script
# ==============================================================================

# 1. Environment Configuration
export DATASET_NAME="./datasets/my_custom_dataset/"
export DATASET_META_NAME="./datasets/my_custom_dataset/metadata.json"
export MODEL_PATH="./Wan2.1-T2V-1.3B"
export OUTPUT_DIR="./wan2.1_output_lora"

# 2. Training Execution
# Note: Ensure you are in the environment with Wan2.1 requirements installed.
# We utilize deepspeed or torch.distributed for scaling if available.

echo "Starting Wan2.1 LoRA SFT..."

python scripts/train_lora.py \
  --model_path "$MODEL_PATH" \
  --dataset_name "$DATASET_NAME" \
  --dataset_meta_name "$DATASET_META_NAME" \
  --output_dir "$OUTPUT_DIR" \
  --mixed_precision "bf16" \
  --lora_rank 16 \
  --lora_alpha 32 \
  --learning_rate 2e-5 \
  --train_batch_size 1 \
  --gradient_accumulation_steps 4 \
  --max_train_steps 1500 \
  --checkpointing_steps 500 \
  --offload_model True \
  --t5_cpu \
  --seed 42 \
  --resume_from_checkpoint "latest" \
  --report_to "tensorboard"

echo "Training sequence complete. Check $OUTPUT_DIR for adapter weights."
