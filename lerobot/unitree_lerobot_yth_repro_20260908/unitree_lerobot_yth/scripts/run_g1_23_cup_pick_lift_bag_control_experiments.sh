#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
PYTHON_BIN="${PYTHON_BIN:-/home/igs/miniconda3/envs/unitree_lerobot/bin/python}"
PREPARE_SCRIPT="${REPO_ROOT}/scripts/prepare_weighted_multisource_json_dataset.py"
TRAIN_SCRIPT="${REPO_ROOT}/scripts/train_pi05_lora_g1_23_6d_20hz_experiment.sh"
CONVERT_SCRIPT="${REPO_ROOT}/unitree_lerobot/utils/convert_unitree_json_to_lerobot.py"

ROBOT_TYPE="${ROBOT_TYPE:-Unitree_G1_23Dof_RightArm5_Waist1}"
RUN_GROUP="${RUN_GROUP:-g1_23_cup_pick_lift_bag_controls_$(date +%Y%m%d_%H%M%S)}"
ACTION="${ACTION:-all}"
EXPERIMENTS="${EXPERIMENTS:-all}"

CUP_GOAL_REPO_ID="${CUP_GOAL_REPO_ID:-local/g1_23_right_hand_cup_pick_all_rightarm5_waist1_6d_20hz}"
CUP_GOAL_DATASET_ROOT="${CUP_GOAL_DATASET_ROOT:-${REPO_ROOT}/data/local/g1_23_right_hand_cup_pick_all_rightarm5_waist1_6d_20hz}"
CUP_GOAL_SPEC_PATH="${CUP_GOAL_SPEC_PATH:-${REPO_ROOT}/scripts/g1_23_right_hand_cup_pick_all_6d_20hz_spec.json}"
CUP_GOAL_RAW_ROOT="${CUP_GOAL_RAW_ROOT:-${REPO_ROOT}/data/raw/g1_23_right_hand_cup_pick_all_6d_20hz_json}"

MULTITASK_REPO_ID="${MULTITASK_REPO_ID:-local/g1_23_right_hand_cup_pick_and_lift_bag_multitask_x2_rightarm5_waist1_6d_20hz}"
MULTITASK_DATASET_ROOT="${MULTITASK_DATASET_ROOT:-${REPO_ROOT}/data/local/g1_23_right_hand_cup_pick_and_lift_bag_multitask_x2_rightarm5_waist1_6d_20hz}"
MULTITASK_SPEC_PATH="${MULTITASK_SPEC_PATH:-${REPO_ROOT}/scripts/g1_23_right_hand_cup_pick_and_lift_bag_multitask_x2_6d_20hz_spec.json}"
MULTITASK_RAW_ROOT="${MULTITASK_RAW_ROOT:-${REPO_ROOT}/data/raw/g1_23_right_hand_cup_pick_and_lift_bag_multitask_x2_6d_20hz_json}"

BAG_REPO_ID="${BAG_REPO_ID:-local/g1_23_right_hand_lift_bag_all_rightarm5_waist1_6d_20hz}"
BAG_DATASET_ROOT="${BAG_DATASET_ROOT:-${REPO_ROOT}/data/local/g1_23_right_hand_lift_bag_all_rightarm5_waist1_6d_20hz}"
BAG_SPEC_PATH="${BAG_SPEC_PATH:-${REPO_ROOT}/scripts/g1_23_right_hand_lift_bag_all_6d_20hz_spec.json}"
BAG_RAW_ROOT="${BAG_RAW_ROOT:-${REPO_ROOT}/data/raw/g1_23_right_hand_lift_bag_all_6d_20hz_json}"

mkdir -p "${REPO_ROOT}/data/raw" "${REPO_ROOT}/data/local"

prepare_dataset() {
  local spec_path="$1"
  local raw_root="$2"
  local repo_id="$3"
  local dataset_root="$4"

  PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" "${PREPARE_SCRIPT}" \
    --spec-path "${spec_path}"

  PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" "${CONVERT_SCRIPT}" \
    --raw-dir "${raw_root}" \
    --repo-id "${repo_id}" \
    --robot-type "${ROBOT_TYPE}" \
    --root "${dataset_root}"
}

train_experiment() {
  local dataset_repo_id="$1"
  local dataset_root="$2"
  local job_name="$3"
  local steps="$4"

  env \
    DATASET_REPO_ID="${dataset_repo_id}" \
    DATASET_ROOT="${dataset_root}" \
    JOB_NAME="${job_name}" \
    RUN_GROUP="${RUN_GROUP}" \
    PI05_TRAIN_STEPS="${steps}" \
    ACTION_NORM="${ACTION_NORM:-MIN_MAX}" \
    STATE_NORM="${STATE_NORM:-QUANTILES}" \
    VISUAL_NORM="${VISUAL_NORM:-IDENTITY}" \
    ENABLE_IMAGE_TRANSFORMS="${ENABLE_IMAGE_TRANSFORMS:-true}" \
    IMAGE_TRANSFORMS_MAX_NUM="${IMAGE_TRANSFORMS_MAX_NUM:-2}" \
    IMAGE_TRANSFORMS_RANDOM_ORDER="${IMAGE_TRANSFORMS_RANDOM_ORDER:-false}" \
    POLICY_DTYPE="${POLICY_DTYPE:-float32}" \
    POLICY_GRADIENT_CHECKPOINTING="${POLICY_GRADIENT_CHECKPOINTING:-false}" \
    POLICY_USE_AMP="${POLICY_USE_AMP:-false}" \
    PI05_BATCH_SIZE="${PI05_BATCH_SIZE:-2}" \
    "${TRAIN_SCRIPT}"
}

should_run() {
  local experiment="$1"
  if [[ "${EXPERIMENTS}" == "all" ]]; then
    return 0
  fi
  [[ ",${EXPERIMENTS}," == *",${experiment},"* ]]
}

if [[ "${ACTION}" != "prepare" && "${ACTION}" != "train" && "${ACTION}" != "all" ]]; then
  echo "Unsupported ACTION=${ACTION}. Use prepare, train, or all." >&2
  exit 1
fi

if should_run baseline; then
  if [[ "${ACTION}" == "prepare" || "${ACTION}" == "all" ]]; then
    prepare_dataset "${CUP_GOAL_SPEC_PATH}" "${CUP_GOAL_RAW_ROOT}" "${CUP_GOAL_REPO_ID}" "${CUP_GOAL_DATASET_ROOT}"
  fi
  if [[ "${ACTION}" == "train" || "${ACTION}" == "all" ]]; then
    train_experiment \
      "${CUP_GOAL_REPO_ID}" \
      "${CUP_GOAL_DATASET_ROOT}" \
      "pi05_lora_g1_23_right_hand_cup_pick_all_baseline_aug_6d_20hz" \
      "${BASELINE_STEPS:-30000}"
  fi
fi

if should_run multitask; then
  if [[ "${ACTION}" == "prepare" || "${ACTION}" == "all" ]]; then
    prepare_dataset "${MULTITASK_SPEC_PATH}" "${MULTITASK_RAW_ROOT}" "${MULTITASK_REPO_ID}" "${MULTITASK_DATASET_ROOT}"
  fi
  if [[ "${ACTION}" == "train" || "${ACTION}" == "all" ]]; then
    train_experiment \
      "${MULTITASK_REPO_ID}" \
      "${MULTITASK_DATASET_ROOT}" \
      "pi05_lora_g1_23_right_hand_cup_pick_and_lift_bag_multitask_x2_6d_20hz" \
      "${MULTITASK_STEPS:-50000}"
  fi
fi

if should_run bag_single; then
  if [[ "${ACTION}" == "prepare" || "${ACTION}" == "all" ]]; then
    prepare_dataset "${BAG_SPEC_PATH}" "${BAG_RAW_ROOT}" "${BAG_REPO_ID}" "${BAG_DATASET_ROOT}"
  fi
  if [[ "${ACTION}" == "train" || "${ACTION}" == "all" ]]; then
    train_experiment \
      "${BAG_REPO_ID}" \
      "${BAG_DATASET_ROOT}" \
      "pi05_lora_g1_23_right_hand_lift_bag_single_task_6d_20hz" \
      "${BAG_SINGLE_STEPS:-10000}"
  fi
fi
