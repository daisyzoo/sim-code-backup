#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
LEROBOT_ROOT="${REPO_ROOT}/unitree_lerobot/lerobot"
VLA_ROOT="/media/igs/EAGET/syh/vla"

DATASET_REPO_ID="local/g1_23_right_hand_rag_reach_11d"
DATASET_ROOT="/home/igs/Desktop/project/vla/data/local/g1_23_right_hand_rag_reach_11d"

HF_HOME="${VLA_ROOT}/.hf_home"
HF_DATASETS_CACHE="${VLA_ROOT}/.hf_datasets_cache"
HF_HUB_CACHE="${VLA_ROOT}/.hf_hub_cache"

JOB_NAME="groot_g1_23_rag_reach"
RUN_ID="$(date +%Y%m%d_%H%M%S)"
RUN_OUTPUT_DIR="${VLA_ROOT}/outputs/${JOB_NAME}_${RUN_ID}"

mkdir -p "${VLA_ROOT}/outputs" "${HF_HOME}" "${HF_DATASETS_CACHE}" "${HF_HUB_CACHE}"

export PYTHONPATH="${REPO_ROOT}"
export HF_HOME
export HF_DATASETS_CACHE
export HF_HUB_CACHE
export TOKENIZERS_PARALLELISM=false

cd "${LEROBOT_ROOT}"

python src/lerobot/scripts/lerobot_train.py \
  --dataset.repo_id="${DATASET_REPO_ID}" \
  --dataset.root="${DATASET_ROOT}" \
  --policy.type=groot \
  --policy.base_model_path=nvidia/GR00T-N1.5-3B \
  --policy.tokenizer_assets_repo=lerobot/eagle2hg-processor-groot-n1p5 \
  --policy.embodiment_tag=new_embodiment \
  --policy.push_to_hub=false \
  --policy.tune_llm=false \
  --policy.tune_visual=false \
  --policy.tune_projector=true \
  --policy.tune_diffusion_model=true \
  --policy.lora_rank=16 \
  --policy.lora_alpha=32 \
  --policy.lora_dropout=0.05 \
  --policy.use_bf16=true \
  --policy.max_state_dim=16 \
  --policy.max_action_dim=16 \
  --batch_size=1 \
  --steps=10000 \
  --save_freq=1000 \
  --log_freq=20 \
  --eval_freq=0 \
  --num_workers=2 \
  --output_dir="${RUN_OUTPUT_DIR}" \
  --job_name="${JOB_NAME}"
