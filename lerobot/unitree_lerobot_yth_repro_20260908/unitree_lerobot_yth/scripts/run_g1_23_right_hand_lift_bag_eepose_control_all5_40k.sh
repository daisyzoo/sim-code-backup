#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
PYTHON_BIN="${PYTHON_BIN:-/home/igs/miniconda3/envs/unitree_lerobot/bin/python}"
PREPARE_JSON_SCRIPT="${REPO_ROOT}/scripts/prepare_weighted_multisource_json_dataset.py"
FILL_EEPOSE_SCRIPT="${REPO_ROOT}/scripts/fill_g1_23_right_ee_pose_from_fk.py"
CONVERT_SCRIPT="${REPO_ROOT}/unitree_lerobot/utils/convert_unitree_json_to_lerobot.py"
TRAIN_SCRIPT="${REPO_ROOT}/scripts/train_pi05_lora_g1_23_6d_20hz_experiment.sh"

SPEC_PATH="${SPEC_PATH:-${REPO_ROOT}/scripts/g1_23_right_hand_lift_bag_control_all5_20hz_spec.json}"
RAW_JSON_ROOT="${RAW_JSON_ROOT:-/media/igs/EAGET/syh/dataset/processed/g1_23_right_hand_lift_bag_control_all5_20hz_json}"
DATA_ROOT="${DATA_ROOT:-/media/igs/EAGET/syh/vla/data/local}"
RUN_GROUP="${RUN_GROUP:-g1_23_right_hand_lift_bag_eepose_control_all5_40k}"

BASELINE_DATASET_REPO_ID="${BASELINE_DATASET_REPO_ID:-local/g1_23_right_hand_lift_bag_control_all5_rightarm5_waist1_6d_20hz}"
BASELINE_DATASET_ROOT="${BASELINE_DATASET_ROOT:-${DATA_ROOT}/g1_23_right_hand_lift_bag_control_all5_rightarm5_waist1_6d_20hz}"
BASELINE_ROBOT_TYPE="${BASELINE_ROBOT_TYPE:-Unitree_G1_23Dof_RightArm5_Waist1}"
BASELINE_JOB_NAME="${BASELINE_JOB_NAME:-pi05_lora_g1_23_right_hand_lift_bag_all5_baseline_minmax_aug_6d_20hz_40k}"

EEPOSE_DATASET_REPO_ID="${EEPOSE_DATASET_REPO_ID:-local/g1_23_right_hand_lift_bag_control_all5_rightarm5_waist1_righteepose_13d_20hz}"
EEPOSE_DATASET_ROOT="${EEPOSE_DATASET_ROOT:-${DATA_ROOT}/g1_23_right_hand_lift_bag_control_all5_rightarm5_waist1_righteepose_13d_20hz}"
EEPOSE_ROBOT_TYPE="${EEPOSE_ROBOT_TYPE:-Unitree_G1_23Dof_RightArm5_Waist1_RightEePose}"
EEPOSE_JOB_NAME="${EEPOSE_JOB_NAME:-pi05_lora_g1_23_right_hand_lift_bag_all5_eepose_minmax_aug_13d_20hz_40k}"

RUN_PREPARE="${RUN_PREPARE:-true}"
FILL_MISSING_EEPOSE="${FILL_MISSING_EEPOSE:-true}"
RUN_TRAIN_BASELINE="${RUN_TRAIN_BASELINE:-true}"
RUN_TRAIN_EEPOSE="${RUN_TRAIN_EEPOSE:-true}"

PI05_TRAIN_STEPS="${PI05_TRAIN_STEPS:-40000}"
PI05_BATCH_SIZE="${PI05_BATCH_SIZE:-2}"
PI05_SAVE_FREQ="${PI05_SAVE_FREQ:-2000}"
PI05_LOG_FREQ="${PI05_LOG_FREQ:-20}"
PI05_NUM_WORKERS="${PI05_NUM_WORKERS:-2}"
POLICY_DTYPE="${POLICY_DTYPE:-float32}"
POLICY_GRADIENT_CHECKPOINTING="${POLICY_GRADIENT_CHECKPOINTING:-false}"
POLICY_USE_AMP="${POLICY_USE_AMP:-false}"
ACTION_NORM="${ACTION_NORM:-MIN_MAX}"
STATE_NORM="${STATE_NORM:-QUANTILES}"
VISUAL_NORM="${VISUAL_NORM:-IDENTITY}"
ENABLE_IMAGE_TRANSFORMS="${ENABLE_IMAGE_TRANSFORMS:-true}"
IMAGE_TRANSFORMS_MAX_NUM="${IMAGE_TRANSFORMS_MAX_NUM:-2}"
IMAGE_TRANSFORMS_RANDOM_ORDER="${IMAGE_TRANSFORMS_RANDOM_ORDER:-false}"

prepare_dataset() {
  echo "==> Preparing relabeled JSON dataset"
  PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" "${PREPARE_JSON_SCRIPT}" \
    --spec-path "${SPEC_PATH}"

  if [[ "${FILL_MISSING_EEPOSE}" == "true" ]]; then
    echo "==> Filling missing right_ee.qpos with G1-23 FK"
    PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" "${FILL_EEPOSE_SCRIPT}" \
      --raw-dir "${RAW_JSON_ROOT}"
  fi

  echo "==> Converting baseline 6d LeRobot dataset"
  PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" "${CONVERT_SCRIPT}" \
    --raw-dir "${RAW_JSON_ROOT}" \
    --repo-id "${BASELINE_DATASET_REPO_ID}" \
    --robot-type "${BASELINE_ROBOT_TYPE}" \
    --root "${BASELINE_DATASET_ROOT}"

  echo "==> Converting eepose 13d LeRobot dataset"
  PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" "${CONVERT_SCRIPT}" \
    --raw-dir "${RAW_JSON_ROOT}" \
    --repo-id "${EEPOSE_DATASET_REPO_ID}" \
    --robot-type "${EEPOSE_ROBOT_TYPE}" \
    --root "${EEPOSE_DATASET_ROOT}"
}

train_one() {
  local dataset_repo_id="$1"
  local dataset_root="$2"
  local job_name="$3"

  env \
    DATASET_REPO_ID="${dataset_repo_id}" \
    DATASET_ROOT="${dataset_root}" \
    JOB_NAME="${job_name}" \
    RUN_GROUP="${RUN_GROUP}" \
    PI05_TRAIN_STEPS="${PI05_TRAIN_STEPS}" \
    PI05_BATCH_SIZE="${PI05_BATCH_SIZE}" \
    PI05_SAVE_FREQ="${PI05_SAVE_FREQ}" \
    PI05_LOG_FREQ="${PI05_LOG_FREQ}" \
    PI05_NUM_WORKERS="${PI05_NUM_WORKERS}" \
    POLICY_DTYPE="${POLICY_DTYPE}" \
    POLICY_GRADIENT_CHECKPOINTING="${POLICY_GRADIENT_CHECKPOINTING}" \
    POLICY_USE_AMP="${POLICY_USE_AMP}" \
    ACTION_NORM="${ACTION_NORM}" \
    STATE_NORM="${STATE_NORM}" \
    VISUAL_NORM="${VISUAL_NORM}" \
    ENABLE_IMAGE_TRANSFORMS="${ENABLE_IMAGE_TRANSFORMS}" \
    IMAGE_TRANSFORMS_MAX_NUM="${IMAGE_TRANSFORMS_MAX_NUM}" \
    IMAGE_TRANSFORMS_RANDOM_ORDER="${IMAGE_TRANSFORMS_RANDOM_ORDER}" \
    "${TRAIN_SCRIPT}"
}

if [[ "${RUN_PREPARE}" == "true" ]]; then
  prepare_dataset
fi

if [[ "${RUN_TRAIN_BASELINE}" == "true" ]]; then
  echo "==> Training baseline 6d"
  train_one "${BASELINE_DATASET_REPO_ID}" "${BASELINE_DATASET_ROOT}" "${BASELINE_JOB_NAME}"
fi

if [[ "${RUN_TRAIN_EEPOSE}" == "true" ]]; then
  echo "==> Training eepose 13d"
  train_one "${EEPOSE_DATASET_REPO_ID}" "${EEPOSE_DATASET_ROOT}" "${EEPOSE_JOB_NAME}"
fi
