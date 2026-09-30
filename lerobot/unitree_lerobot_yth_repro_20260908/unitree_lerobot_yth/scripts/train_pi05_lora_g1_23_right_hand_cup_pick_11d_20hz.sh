#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
LEROBOT_ROOT="${REPO_ROOT}/unitree_lerobot/lerobot"
VLA_ROOT="/media/igs/EAGET/syh/vla"
LOCAL_PI05_BASE="/home/igs/Desktop/project/vla/data/.hf_hub_cache/models--lerobot--pi05_base/snapshots/9e55186ad36e66b95cda57bc47818d9e6237ae30"
PYTHON_BIN="${PYTHON_BIN:-/home/igs/miniconda3/envs/unitree_lerobot/bin/python}"

DATASET_REPO_ID="${DATASET_REPO_ID:-local/g1_23_right_hand_cup_pick_11d_20hz}"
DATASET_ROOT="${DATASET_ROOT:-${REPO_ROOT}/data/local/g1_23_right_hand_cup_pick_11d_20hz}"
HF_HOME="${VLA_ROOT}/.hf_home"
HF_DATASETS_CACHE="${VLA_ROOT}/.hf_datasets_cache"
HF_HUB_CACHE="${VLA_ROOT}/.hf_hub_cache"

JOB_NAME="${JOB_NAME:-pi05_lora_g1_23_right_hand_cup_pick_11d_20hz}"

DEVICE="${PI05_DEVICE:-cuda}"
STEPS="${PI05_TRAIN_STEPS:-10000}"
BATCH_SIZE="${PI05_BATCH_SIZE:-2}"
SAVE_FREQ="${PI05_SAVE_FREQ:-1000}"
LOG_FREQ="${PI05_LOG_FREQ:-20}"
NUM_WORKERS="${PI05_NUM_WORKERS:-2}"

mkdir -p "${VLA_ROOT}/outputs" "${HF_HOME}" "${HF_DATASETS_CACHE}" "${HF_HUB_CACHE}"

if [[ ! -d "${DATASET_ROOT}" ]]; then
  echo "Dataset root does not exist: ${DATASET_ROOT}" >&2
  echo "Prepare it first with scripts/prepare_g1_23_right_hand_cup_pick_11d_20hz_dataset.sh" >&2
  exit 1
fi

if [[ -f "${LOCAL_PI05_BASE}/model.safetensors" ]]; then
  POLICY_PRETRAINED_PATH="${LOCAL_PI05_BASE}"
else
  POLICY_PRETRAINED_PATH="lerobot/pi05_base"
fi

export HF_HOME
export HF_DATASETS_CACHE
export HF_HUB_CACHE
export TOKENIZERS_PARALLELISM=false

cd "${LEROBOT_ROOT}"

RUN_NAME="${JOB_NAME}_$(date +%Y%m%d_%H%M%S)"
RUN_OUTPUT_DIR="${VLA_ROOT}/outputs/${RUN_NAME}"
LOG_FILE_TMP="${VLA_ROOT}/outputs/${RUN_NAME}.train.log"

exec > >(tee -a "${LOG_FILE_TMP}") 2>&1

"${PYTHON_BIN}" src/lerobot/scripts/lerobot_train.py \
  --dataset.repo_id="${DATASET_REPO_ID}" \
  --dataset.root="${DATASET_ROOT}" \
  --policy.type=pi05 \
  --policy.pretrained_path="${POLICY_PRETRAINED_PATH}" \
  --policy.push_to_hub=false \
  --policy.device="${DEVICE}" \
  --policy.lora_rank=16 \
  --policy.lora_alpha=16 \
  --policy.lora_dropout=0.05 \
  --output_dir="${RUN_OUTPUT_DIR}" \
  --job_name="${RUN_NAME}" \
  --steps="${STEPS}" \
  --batch_size="${BATCH_SIZE}" \
  --save_freq="${SAVE_FREQ}" \
  --log_freq="${LOG_FREQ}" \
  --num_workers="${NUM_WORKERS}"

if [[ -d "${RUN_OUTPUT_DIR}" ]]; then
  mv "${LOG_FILE_TMP}" "${RUN_OUTPUT_DIR}/train.log"
fi
