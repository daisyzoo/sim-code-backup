#!/usr/bin/env bash

# PI0.5 expert-only training for lerobot_pick_up_15hz_0804-0805.
# Dataset: 236 episodes, 61,547 frames, 6-D state/action, 15 Hz.
set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot_yth"
LEROBOT_ROOT="${REPO_ROOT}/unitree_lerobot/lerobot"
VLA_ROOT="/media/igs/EAGET/syh/vla"
LOCAL_PI05_BASE="/home/igs/Desktop/project/vla/data/.hf_hub_cache/models--lerobot--pi05_base/snapshots/9e55186ad36e66b95cda57bc47818d9e6237ae30"
LOCAL_PALIGEMMA_TOKENIZER="${LOCAL_PALIGEMMA_TOKENIZER:-/media/igs/EAGET/yxf/model/paligemma-3b-pt-224}"
PYTHON_BIN="${PYTHON_BIN:-/home/igs/miniconda3/envs/unitree_lerobot/bin/python}"

DATASET_REPO_ID="${DATASET_REPO_ID:-local/lerobot_pick_up_15hz_0804-0805}"
DATASET_ROOT="${DATASET_ROOT:-/media/igs/EAGET/syh/dataset/xr_data/lerobot_pick_up_15hz_0804-0805}"
JOB_NAME="${JOB_NAME:-pi05_expert_only_pick_up_6d_15hz_0804_0805}"

HF_HOME="${VLA_ROOT}/.hf_home"
HF_DATASETS_CACHE="${VLA_ROOT}/.hf_datasets_cache"
HF_HUB_CACHE="${VLA_ROOT}/.hf_hub_cache"
OUTPUT_ROOT="${OUTPUT_ROOT:-${VLA_ROOT}/outputs}"
LOG_ROOT_BASE="${LOG_ROOT_BASE:-${VLA_ROOT}/experiment_logs}"
RUN_GROUP="${RUN_GROUP:-pi05_expert_only_pick_up_15hz}"

DEVICE="${PI05_DEVICE:-cuda}"
# 61,547 frames / batch size 8 = ceil(7,693.375) steps per epoch;
# 20 epochs therefore require 153,880 optimizer steps on one process.
STEPS="${PI05_TRAIN_STEPS:-153880}"
BATCH_SIZE="${PI05_BATCH_SIZE:-8}"
SAVE_FREQ="${PI05_SAVE_FREQ:-30000}"
LOG_FREQ="${PI05_LOG_FREQ:-20}"
NUM_WORKERS="${PI05_NUM_WORKERS:-2}"
SEED="${SEED:-1000}"
# PI0.5 optimizer and cosine scheduler settings. Override these at launch when needed.
LEARNING_RATE="${PI05_LEARNING_RATE:-2.5e-5}"
SCHEDULER_DECAY_LR="${PI05_SCHEDULER_DECAY_LR:-2.5e-6}"
STATE_NORM="${STATE_NORM:-QUANTILES}"
ACTION_NORM="${ACTION_NORM:-MIN_MAX}"
VISUAL_NORM="${VISUAL_NORM:-IDENTITY}"
ENABLE_IMAGE_TRANSFORMS="${ENABLE_IMAGE_TRANSFORMS:-true}"
IMAGE_TRANSFORMS_MAX_NUM="${IMAGE_TRANSFORMS_MAX_NUM:-2}"
IMAGE_TRANSFORMS_RANDOM_ORDER="${IMAGE_TRANSFORMS_RANDOM_ORDER:-false}"
# This dataset has video/data timestamp offsets up to 0.0002 s; 1 ms remains
# far below a 15 Hz frame period (66.7 ms) while accommodating codec rounding.
DATASET_TOLERANCE_S="${DATASET_TOLERANCE_S:-0.001}"
PYTORCH_CUDA_ALLOC_CONF_VALUE="${PYTORCH_CUDA_ALLOC_CONF_VALUE:-expandable_segments:True}"

if [[ ! -d "${DATASET_ROOT}" ]]; then
  echo "Dataset root does not exist: ${DATASET_ROOT}" >&2
  exit 1
fi

if [[ -f "${LOCAL_PI05_BASE}/model.safetensors" ]]; then
  POLICY_PRETRAINED_PATH="${LOCAL_PI05_BASE}"
else
  POLICY_PRETRAINED_PATH="lerobot/pi05_base"
fi

mkdir -p "${OUTPUT_ROOT}" "${HF_HOME}" "${HF_DATASETS_CACHE}" "${HF_HUB_CACHE}"

export HF_HOME HF_DATASETS_CACHE HF_HUB_CACHE
export TOKENIZERS_PARALLELISM=false
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF_VALUE}"
export PYTHONPATH="${LEROBOT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
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
  "--dataset.tolerance_s=${DATASET_TOLERANCE_S}"
  "--policy.type=pi05"
  "--policy.pretrained_path=${POLICY_PRETRAINED_PATH}"
  "--policy.push_to_hub=false"
  "--policy.device=${DEVICE}"
  "--policy.dtype=bfloat16"
  "--policy.gradient_checkpointing=false"
  "--policy.use_amp=false"
  "--policy.lora_rank=0"
  "--policy.train_expert_only=true"
  "--policy.mask_action_padding=true"
  "--policy.normalization_mapping=${NORMALIZATION_MAPPING}"
  "--policy.optimizer_lr=${LEARNING_RATE}"
  "--policy.scheduler_decay_lr=${SCHEDULER_DECAY_LR}"
  "--output_dir=${RUN_OUTPUT_DIR}"
  "--job_name=${RUN_NAME}"
  "--steps=${STEPS}"
  "--batch_size=${BATCH_SIZE}"
  "--save_freq=${SAVE_FREQ}"
  "--log_freq=${LOG_FREQ}"
  "--eval_freq=0"
  "--num_workers=${NUM_WORKERS}"
  "--seed=${SEED}"
)

if [[ "${ENABLE_IMAGE_TRANSFORMS}" == "true" ]]; then
  ARGS+=(
    "--dataset.image_transforms.enable=true"
    "--dataset.image_transforms.max_num_transforms=${IMAGE_TRANSFORMS_MAX_NUM}"
    "--dataset.image_transforms.random_order=${IMAGE_TRANSFORMS_RANDOM_ORDER}"
  )
fi

exec > >(tee -a "${LOG_FILE_TMP}") 2>&1

echo "Dataset: ${DATASET_ROOT} (15 Hz, 6-D action)"
echo "Training mode: action expert and action projections only; VLM frozen; LoRA disabled."
"${PYTHON_BIN}" -m accelerate.commands.launch --mixed_precision=bf16 "${ARGS[@]}"

if [[ -d "${RUN_OUTPUT_DIR}" ]]; then
  cp "${LOG_FILE_TMP}" "${RUN_OUTPUT_DIR}/train.launch.log"
fi
