#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
LEROBOT_ROOT="${REPO_ROOT}/unitree_lerobot/lerobot"
VLA_ROOT="/media/igs/EAGET/syh/vla"
LOCAL_PI05_BASE="/home/igs/Desktop/project/vla/data/.hf_hub_cache/models--lerobot--pi05_base/snapshots/9e55186ad36e66b95cda57bc47818d9e6237ae30"

DATASET_REPO_ID="local/g1_23_right_hand_rag_reach_11d"
DATASET_ROOT="/home/igs/Desktop/project/vla/data/local/g1_23_right_hand_rag_reach_11d"

HF_HOME="${VLA_ROOT}/.hf_home"
HF_DATASETS_CACHE="${VLA_ROOT}/.hf_datasets_cache"
HF_HUB_CACHE="${VLA_ROOT}/.hf_hub_cache"

JOB_NAME="pi05_lora_g1_23_rag_reach"
RUN_ID="$(date +%Y%m%d_%H%M%S)"
RUN_OUTPUT_DIR="${VLA_ROOT}/outputs/${JOB_NAME}_${RUN_ID}"
TRAIN_LOG_FILE="${RUN_OUTPUT_DIR}/train.log"
TRAIN_LOG_FILE_TMP="${VLA_ROOT}/outputs/${JOB_NAME}_${RUN_ID}.train.log"

mkdir -p "${VLA_ROOT}/outputs" "${HF_HOME}" "${HF_DATASETS_CACHE}" "${HF_HUB_CACHE}"

if [[ -f "${LOCAL_PI05_BASE}/model.safetensors" ]]; then
  POLICY_PRETRAINED_PATH="${LOCAL_PI05_BASE}"
else
  POLICY_PRETRAINED_PATH="lerobot/pi05_base"
fi

export PYTHONPATH="${REPO_ROOT}"
export HF_HOME
export HF_DATASETS_CACHE
export HF_HUB_CACHE
export TOKENIZERS_PARALLELISM=false

cd "${LEROBOT_ROOT}"

exec > >(tee -a "${TRAIN_LOG_FILE_TMP}") 2>&1

python src/lerobot/scripts/lerobot_train.py \
  --dataset.repo_id="${DATASET_REPO_ID}" \
  --dataset.root="${DATASET_ROOT}" \
  --policy.type=pi05 \
  --policy.pretrained_path="${POLICY_PRETRAINED_PATH}" \
  --policy.push_to_hub=false \
  --policy.dtype=bfloat16 \
  --policy.gradient_checkpointing=true \
  --policy.lora_rank=16 \
  --policy.lora_alpha=32 \
  --policy.lora_dropout=0.05 \
  --policy.lora_target_language_model=true \
  --policy.lora_target_action_expert=true \
  --policy.debug_numerics_once=true \
  --batch_size=2 \
  --steps=10000 \
  --save_freq=1000 \
  --log_freq=20 \
  --eval_freq=0 \
  --num_workers=2 \
  --output_dir="${RUN_OUTPUT_DIR}" \
  --job_name="${JOB_NAME}"

if [[ -d "${RUN_OUTPUT_DIR}" && -f "${TRAIN_LOG_FILE_TMP}" ]]; then
  mv "${TRAIN_LOG_FILE_TMP}" "${TRAIN_LOG_FILE}"
fi
