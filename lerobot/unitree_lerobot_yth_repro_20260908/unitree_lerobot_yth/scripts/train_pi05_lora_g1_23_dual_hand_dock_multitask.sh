#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
LEROBOT_ROOT="${REPO_ROOT}/unitree_lerobot/lerobot"
VLA_ROOT="/media/igs/EAGET/syh/vla"
LOCAL_PI05_BASE="/home/igs/Desktop/project/vla/data/.hf_hub_cache/models--lerobot--pi05_base/snapshots/9e55186ad36e66b95cda57bc47818d9e6237ae30"
PYTHON_BIN="${PYTHON_BIN:-/home/igs/miniconda3/envs/unitree_lerobot/bin/python}"

DATASET_REPO_ID="${DATASET_REPO_ID:-local/g1_23_dual_hand_dock_multitask_11d}"
DATASET_ROOT="${DATASET_ROOT:-/media/igs/EAGET/syh/vla/data/local/g1_23_dual_hand_dock_multitask_11d}"

HF_HOME="${VLA_ROOT}/.hf_home"
HF_DATASETS_CACHE="${VLA_ROOT}/.hf_datasets_cache"
HF_HUB_CACHE="${VLA_ROOT}/.hf_hub_cache"

JOB_NAME="${JOB_NAME:-pi05_lora_g1_23_dual_hand_dock_multitask}"
RUN_ID="$(date +%Y%m%d_%H%M%S)"
RUN_OUTPUT_DIR="${VLA_ROOT}/outputs/${JOB_NAME}_${RUN_ID}"
TRAIN_LOG_FILE="${RUN_OUTPUT_DIR}/train.log"
TRAIN_LOG_FILE_TMP="${VLA_ROOT}/outputs/${JOB_NAME}_${RUN_ID}.train.log"

STEPS="${PI05_TRAIN_STEPS:-10000}"
BATCH_SIZE="${PI05_BATCH_SIZE:-2}"
SAVE_FREQ="${PI05_SAVE_FREQ:-1000}"
LOG_FREQ="${PI05_LOG_FREQ:-20}"
NUM_WORKERS="${PI05_NUM_WORKERS:-2}"

mkdir -p "${VLA_ROOT}/outputs" "${HF_HOME}" "${HF_DATASETS_CACHE}" "${HF_HUB_CACHE}"

if [[ ! -d "${DATASET_ROOT}" ]]; then
  echo "Dataset root does not exist: ${DATASET_ROOT}" >&2
  exit 1
fi

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Python executable does not exist: ${PYTHON_BIN}" >&2
  exit 1
fi

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

"${PYTHON_BIN}" src/lerobot/scripts/lerobot_train.py \
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
  --batch_size="${BATCH_SIZE}" \
  --steps="${STEPS}" \
  --save_freq="${SAVE_FREQ}" \
  --log_freq="${LOG_FREQ}" \
  --eval_freq=0 \
  --num_workers="${NUM_WORKERS}" \
  --output_dir="${RUN_OUTPUT_DIR}" \
  --job_name="${JOB_NAME}"

if [[ -d "${RUN_OUTPUT_DIR}" && -f "${TRAIN_LOG_FILE_TMP}" ]]; then
  mv "${TRAIN_LOG_FILE_TMP}" "${TRAIN_LOG_FILE}"
fi
