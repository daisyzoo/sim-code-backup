#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
VLA_ROOT="/media/igs/EAGET/syh/vla"

PREPARE_SCRIPT="${REPO_ROOT}/scripts/prepare_g1_23_right_hand_cup_pick_all_6d_20hz_dataset.sh"
TRAIN_SCRIPT="${REPO_ROOT}/scripts/train_pi05_lora_g1_23_6d_20hz_experiment.sh"

ACTION="${ACTION:-all}"  # prepare | train | all
RUN_GROUP="${RUN_GROUP:-g1_23_right_hand_cup_pick_all_6d_20hz_minmax_aug_40k_$(date +%Y%m%d_%H%M%S)}"

SOURCE_ROOT="${SOURCE_ROOT:-/media/igs/EAGET/syh/dataset/cup_pick}"
RAW_JSON_ROOT="${RAW_JSON_ROOT:-${REPO_ROOT}/data/raw/g1_23_right_hand_cup_pick_all_6d_20hz_json}"
DATASET_REPO_ID="${DATASET_REPO_ID:-local/g1_23_right_hand_cup_pick_all_rightarm5_waist1_6d_20hz}"
DATASET_ROOT="${DATASET_ROOT:-${REPO_ROOT}/data/local/g1_23_right_hand_cup_pick_all_rightarm5_waist1_6d_20hz}"
JOB_NAME="${JOB_NAME:-pi05_lora_g1_23_right_hand_cup_pick_all_6d_20hz_minmax_aug_40k}"

OUTPUT_ROOT="${OUTPUT_ROOT:-${VLA_ROOT}/outputs}"
LOG_ROOT_BASE="${LOG_ROOT_BASE:-${VLA_ROOT}/experiment_logs}"
LOG_DIR="${LOG_ROOT_BASE}/${RUN_GROUP}/orchestrator"
mkdir -p "${LOG_DIR}"

run_logged() {
  local step_name="$1"
  shift

  local log_file="${LOG_DIR}/${step_name}.log"
  echo "[$(date '+%F %T')] start ${step_name}" | tee -a "${log_file}"
  (
    set -euo pipefail
    "$@"
  ) 2>&1 | tee -a "${log_file}"
  echo "[$(date '+%F %T')] done ${step_name}" | tee -a "${log_file}"
}

case "${ACTION}" in
  prepare|train|all) ;;
  *)
    echo "Unsupported ACTION=${ACTION}. Use prepare, train, or all." >&2
    exit 1
    ;;
esac

echo "run_group=${RUN_GROUP}"
echo "action=${ACTION}"
echo "source_root=${SOURCE_ROOT}"
echo "dataset_repo_id=${DATASET_REPO_ID}"
echo "dataset_root=${DATASET_ROOT}"
echo "raw_json_root=${RAW_JSON_ROOT}"
echo "output_root=${OUTPUT_ROOT}"
echo "log_dir=${LOG_DIR}"

if [[ "${ACTION}" == "prepare" || "${ACTION}" == "all" ]]; then
  run_logged prepare env \
    SOURCE_ROOT="${SOURCE_ROOT}" \
    RAW_JSON_ROOT="${RAW_JSON_ROOT}" \
    DATASET_REPO_ID="${DATASET_REPO_ID}" \
    DATASET_ROOT="${DATASET_ROOT}" \
    "${PREPARE_SCRIPT}"
fi

if [[ "${ACTION}" == "train" || "${ACTION}" == "all" ]]; then
  run_logged train env \
    DATASET_REPO_ID="${DATASET_REPO_ID}" \
    DATASET_ROOT="${DATASET_ROOT}" \
    JOB_NAME="${JOB_NAME}" \
    RUN_GROUP="${RUN_GROUP}" \
    OUTPUT_ROOT="${OUTPUT_ROOT}" \
    LOG_ROOT_BASE="${LOG_ROOT_BASE}" \
    PI05_TRAIN_STEPS="${PI05_TRAIN_STEPS:-40000}" \
    ACTION_NORM="${ACTION_NORM:-MIN_MAX}" \
    STATE_NORM="${STATE_NORM:-QUANTILES}" \
    VISUAL_NORM="${VISUAL_NORM:-IDENTITY}" \
    ENABLE_IMAGE_TRANSFORMS="${ENABLE_IMAGE_TRANSFORMS:-true}" \
    IMAGE_TRANSFORMS_MAX_NUM="${IMAGE_TRANSFORMS_MAX_NUM:-2}" \
    IMAGE_TRANSFORMS_RANDOM_ORDER="${IMAGE_TRANSFORMS_RANDOM_ORDER:-false}" \
    PI05_BATCH_SIZE="${PI05_BATCH_SIZE:-2}" \
    POLICY_DTYPE="${POLICY_DTYPE:-float32}" \
    POLICY_GRADIENT_CHECKPOINTING="${POLICY_GRADIENT_CHECKPOINTING:-false}" \
    POLICY_USE_AMP="${POLICY_USE_AMP:-false}" \
    "${TRAIN_SCRIPT}"
fi
