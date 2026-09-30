#!/usr/bin/env bash

# A/B counterpart of pi05_lora_g1_23_right_hand_cup_pick_all_baseline_aug_6d_20hz_50k.
# It keeps the 2026-07-01 baseline configuration and dataset fixed, while masking
# only the dataset-generated action padding from the PI0.5 training loss.
set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot_yth"
LEROBOT_ROOT="${REPO_ROOT}/unitree_lerobot/lerobot"
VLA_ROOT="/media/igs/EAGET/syh/vla"
LOCAL_PI05_BASE="/home/igs/Desktop/project/vla/data/.hf_hub_cache/models--lerobot--pi05_base/snapshots/9e55186ad36e66b95cda57bc47818d9e6237ae30"
LOCAL_PALIGEMMA_TOKENIZER="${LOCAL_PALIGEMMA_TOKENIZER:-/media/igs/EAGET/yxf/model/paligemma-3b-pt-224}"
PYTHON_BIN="${PYTHON_BIN:-/home/igs/miniconda3/envs/unitree_lerobot/bin/python}"

# Keep this dataset identical to the baseline run; do not re-convert or resample it.
DATASET_REPO_ID="${DATASET_REPO_ID:-local/g1_23_right_hand_cup_pick_all_rightarm5_waist1_6d_20hz}"
DATASET_ROOT="${DATASET_ROOT:-/home/igs/Desktop/project/vla/unitree_lerobot/data/local/g1_23_right_hand_cup_pick_all_rightarm5_waist1_6d_20hz}"
JOB_NAME="${JOB_NAME:-pi05_lora_g1_23_right_hand_cup_pick_all_baseline_aug_6d_20hz_50k_mask_action_padding}"

HF_HOME="${VLA_ROOT}/.hf_home"
HF_DATASETS_CACHE="${VLA_ROOT}/.hf_datasets_cache"
HF_HUB_CACHE="${VLA_ROOT}/.hf_hub_cache"
OUTPUT_ROOT="${OUTPUT_ROOT:-${VLA_ROOT}/outputs}"
LOG_ROOT_BASE="${LOG_ROOT_BASE:-${VLA_ROOT}/experiment_logs}"
RUN_GROUP="${RUN_GROUP:-action_padding_mask_$(date +%Y%m%d_%H%M%S)}"

# Values matched to the referenced baseline launch log.
DEVICE="${PI05_DEVICE:-cuda}"
STEPS="${PI05_TRAIN_STEPS:-50000}"
BATCH_SIZE="${PI05_BATCH_SIZE:-2}"
SAVE_FREQ="${PI05_SAVE_FREQ:-5000}"
LOG_FREQ="${PI05_LOG_FREQ:-20}"
NUM_WORKERS="${PI05_NUM_WORKERS:-2}"
SEED="${SEED:-1000}"
POLICY_DTYPE="${POLICY_DTYPE:-float32}"
POLICY_GRADIENT_CHECKPOINTING="${POLICY_GRADIENT_CHECKPOINTING:-false}"
POLICY_USE_AMP="${POLICY_USE_AMP:-false}"
STATE_NORM="${STATE_NORM:-QUANTILES}"
ACTION_NORM="${ACTION_NORM:-MIN_MAX}"
VISUAL_NORM="${VISUAL_NORM:-IDENTITY}"
ENABLE_IMAGE_TRANSFORMS="${ENABLE_IMAGE_TRANSFORMS:-true}"
IMAGE_TRANSFORMS_MAX_NUM="${IMAGE_TRANSFORMS_MAX_NUM:-2}"
IMAGE_TRANSFORMS_RANDOM_ORDER="${IMAGE_TRANSFORMS_RANDOM_ORDER:-false}"
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
# The conda environment has an editable lerobot install from the original repo.
# Put this checkout first so the new PI05Config field is visible to the CLI parser.
export PYTHONPATH="${LEROBOT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
export LEROBOT_TOKENIZER_NAME_OVERRIDE="${LEROBOT_TOKENIZER_NAME_OVERRIDE:-${LOCAL_PALIGEMMA_TOKENIZER}}"
export LEROBOT_TOKENIZER_LOCAL_FILES_ONLY_OVERRIDE="${LEROBOT_TOKENIZER_LOCAL_FILES_ONLY_OVERRIDE:-true}"
export LEROBOT_ENABLE_PER_TASK_LOSS_METRICS="${LEROBOT_ENABLE_PER_TASK_LOSS_METRICS:-false}"

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
  "--policy.lora_target_language_model=true"
  "--policy.lora_target_action_expert=true"
  "--policy.normalization_mapping=${NORMALIZATION_MAPPING}"
  "--policy.mask_action_padding=true"
  "--output_dir=${RUN_OUTPUT_DIR}"
  "--job_name=${RUN_NAME}"
  "--steps=${STEPS}"
  "--batch_size=${BATCH_SIZE}"
  "--save_freq=${SAVE_FREQ}"
  "--log_freq=${LOG_FREQ}"
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

echo "Baseline reference: pi05_lora_g1_23_right_hand_cup_pick_all_baseline_aug_6d_20hz_50k_20260701_210909"
echo "Only training change: --policy.mask_action_padding=true"
"${PYTHON_BIN}" "${ARGS[@]}"

if [[ -d "${RUN_OUTPUT_DIR}" ]]; then
  cp "${LOG_FILE_TMP}" "${RUN_OUTPUT_DIR}/train.launch.log"
fi
