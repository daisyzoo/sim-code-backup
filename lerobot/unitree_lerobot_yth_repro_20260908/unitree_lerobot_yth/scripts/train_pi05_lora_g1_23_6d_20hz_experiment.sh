#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
LEROBOT_ROOT="${REPO_ROOT}/unitree_lerobot/lerobot"
VLA_ROOT="/media/igs/EAGET/syh/vla"
LOCAL_PI05_BASE="/home/igs/Desktop/project/vla/data/.hf_hub_cache/models--lerobot--pi05_base/snapshots/9e55186ad36e66b95cda57bc47818d9e6237ae30"
PYTHON_BIN="${PYTHON_BIN:-/home/igs/miniconda3/envs/unitree_lerobot/bin/python}"
OVERRIDE_DIR="${REPO_ROOT}/logs/runtime_overrides"
LOCAL_PALIGEMMA_TOKENIZER="${LOCAL_PALIGEMMA_TOKENIZER:-/media/igs/EAGET/yxf/model/paligemma-3b-pt-224}"

DATASET_REPO_ID="${DATASET_REPO_ID:?DATASET_REPO_ID is required}"
DATASET_ROOT="${DATASET_ROOT:?DATASET_ROOT is required}"
JOB_NAME="${JOB_NAME:?JOB_NAME is required}"

HF_HOME="${VLA_ROOT}/.hf_home"
HF_DATASETS_CACHE="${VLA_ROOT}/.hf_datasets_cache"
HF_HUB_CACHE="${VLA_ROOT}/.hf_hub_cache"
OUTPUT_ROOT="${OUTPUT_ROOT:-${VLA_ROOT}/outputs}"
LOG_ROOT_BASE="${LOG_ROOT_BASE:-${VLA_ROOT}/experiment_logs}"
RUN_GROUP="${RUN_GROUP:-default}"

DEVICE="${PI05_DEVICE:-cuda}"
STEPS="${PI05_TRAIN_STEPS:-10000}"
BATCH_SIZE="${PI05_BATCH_SIZE:-2}"
SAVE_FREQ="${PI05_SAVE_FREQ:-1000}"
LOG_FREQ="${PI05_LOG_FREQ:-20}"
NUM_WORKERS="${PI05_NUM_WORKERS:-2}"
POLICY_DTYPE="${POLICY_DTYPE:-float32}"
POLICY_GRADIENT_CHECKPOINTING="${POLICY_GRADIENT_CHECKPOINTING:-false}"
POLICY_USE_AMP="${POLICY_USE_AMP:-false}"
PI05_LORA_TARGET_LANGUAGE_MODEL="${PI05_LORA_TARGET_LANGUAGE_MODEL:-true}"
PI05_LORA_TARGET_ACTION_EXPERT="${PI05_LORA_TARGET_ACTION_EXPERT:-true}"
PYTORCH_CUDA_ALLOC_CONF_VALUE="${PYTORCH_CUDA_ALLOC_CONF_VALUE:-expandable_segments:True}"

STATE_NORM="${STATE_NORM:-QUANTILES}"
ACTION_NORM="${ACTION_NORM:-MIN_MAX}"
VISUAL_NORM="${VISUAL_NORM:-IDENTITY}"

ENABLE_IMAGE_TRANSFORMS="${ENABLE_IMAGE_TRANSFORMS:-false}"
IMAGE_TRANSFORMS_MAX_NUM="${IMAGE_TRANSFORMS_MAX_NUM:-2}"
IMAGE_TRANSFORMS_RANDOM_ORDER="${IMAGE_TRANSFORMS_RANDOM_ORDER:-false}"

if [[ -z "${PI05_BATCH_SIZE:-}" ]] && [[ -f "${OVERRIDE_DIR}/PI05_BATCH_SIZE" ]]; then
  BATCH_SIZE="$(tr -d '[:space:]' < "${OVERRIDE_DIR}/PI05_BATCH_SIZE")"
fi

mkdir -p "${OUTPUT_ROOT}" "${HF_HOME}" "${HF_DATASETS_CACHE}" "${HF_HUB_CACHE}"

if [[ ! -d "${DATASET_ROOT}" ]]; then
  echo "Dataset root does not exist: ${DATASET_ROOT}" >&2
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
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF_VALUE}"
export LEROBOT_TOKENIZER_NAME_OVERRIDE="${LEROBOT_TOKENIZER_NAME_OVERRIDE:-${LOCAL_PALIGEMMA_TOKENIZER}}"
export LEROBOT_TOKENIZER_LOCAL_FILES_ONLY_OVERRIDE="${LEROBOT_TOKENIZER_LOCAL_FILES_ONLY_OVERRIDE:-true}"

cd "${LEROBOT_ROOT}"

RUN_NAME="${JOB_NAME}_$(date +%Y%m%d_%H%M%S)"
RUN_OUTPUT_DIR="${OUTPUT_ROOT}/${RUN_NAME}"
RUN_LOG_DIR="${LOG_ROOT_BASE}/${RUN_GROUP}/${RUN_NAME}"
LOG_FILE_TMP="${RUN_LOG_DIR}/train.launch.log"
NORMALIZATION_MAPPING="{\"ACTION\":\"${ACTION_NORM}\",\"STATE\":\"${STATE_NORM}\",\"VISUAL\":\"${VISUAL_NORM}\"}"

mkdir -p "${RUN_LOG_DIR}"

ARGS=(
  "src/lerobot/scripts/lerobot_train.py"
  "--dataset.repo_id=${DATASET_REPO_ID}"
  "--dataset.root=${DATASET_ROOT}"
  "--policy.type=pi05"
  "--policy.pretrained_path=${POLICY_PRETRAINED_PATH}"
  "--policy.push_to_hub=false"
  "--policy.device=${DEVICE}"
  "--policy.dtype=${POLICY_DTYPE}"
  "--policy.gradient_checkpointing=${POLICY_GRADIENT_CHECKPOINTING}"
  "--policy.use_amp=${POLICY_USE_AMP}"
  "--policy.lora_rank=16"
  "--policy.lora_alpha=16"
  "--policy.lora_dropout=0.05"
  "--policy.lora_target_language_model=${PI05_LORA_TARGET_LANGUAGE_MODEL}"
  "--policy.lora_target_action_expert=${PI05_LORA_TARGET_ACTION_EXPERT}"
  "--policy.normalization_mapping=${NORMALIZATION_MAPPING}"
  "--output_dir=${RUN_OUTPUT_DIR}"
  "--job_name=${RUN_NAME}"
  "--steps=${STEPS}"
  "--batch_size=${BATCH_SIZE}"
  "--save_freq=${SAVE_FREQ}"
  "--log_freq=${LOG_FREQ}"
  "--num_workers=${NUM_WORKERS}"
)

if [[ "${ENABLE_IMAGE_TRANSFORMS}" == "true" ]]; then
  ARGS+=(
    "--dataset.image_transforms.enable=true"
    "--dataset.image_transforms.max_num_transforms=${IMAGE_TRANSFORMS_MAX_NUM}"
    "--dataset.image_transforms.random_order=${IMAGE_TRANSFORMS_RANDOM_ORDER}"
  )
fi

exec > >(tee -a "${LOG_FILE_TMP}") 2>&1

"${PYTHON_BIN}" "${ARGS[@]}"

if [[ -d "${RUN_OUTPUT_DIR}" ]]; then
  cp "${LOG_FILE_TMP}" "${RUN_OUTPUT_DIR}/train.launch.log"
fi
