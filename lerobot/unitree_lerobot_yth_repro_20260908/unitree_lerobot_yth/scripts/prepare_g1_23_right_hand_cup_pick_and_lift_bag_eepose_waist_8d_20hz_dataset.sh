#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
PYTHON_BIN="${PYTHON_BIN:-/home/igs/miniconda3/envs/unitree_lerobot/bin/python}"

SPEC_PATH="${SPEC_PATH:-${REPO_ROOT}/scripts/g1_23_right_hand_cup_pick_and_lift_bag_eepose_waist_8d_20hz_spec.json}"
RAW_JSON_ROOT="${RAW_JSON_ROOT:-${REPO_ROOT}/data/raw/g1_23_right_hand_cup_pick_and_lift_bag_multitask_8d_20hz_json}"
DATASET_REPO_ID="${DATASET_REPO_ID:-local/g1_23_right_hand_cup_pick_and_lift_bag_multitask_righteepose7_waist1_8d_20hz}"
DATASET_ROOT="${DATASET_ROOT:-${REPO_ROOT}/data/local/g1_23_right_hand_cup_pick_and_lift_bag_multitask_righteepose7_waist1_8d_20hz}"
ROBOT_TYPE="${ROBOT_TYPE:-Unitree_G1_23Dof_RightEePose_Waist1}"
FILL_MISSING_EEPOSE="${FILL_MISSING_EEPOSE:-true}"

mkdir -p "${REPO_ROOT}/data/raw" "${REPO_ROOT}/data/local"

PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" scripts/prepare_multisource_multitask_json_dataset.py \
  --spec-path "${SPEC_PATH}" \
  --output-root "${RAW_JSON_ROOT}"

if [[ "${FILL_MISSING_EEPOSE}" == "true" ]]; then
  PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" scripts/fill_g1_23_right_ee_pose_from_fk.py \
    --raw-dir "${RAW_JSON_ROOT}" \
    --overwrite-existing \
    --use-waist-yaw
fi

PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" unitree_lerobot/utils/convert_unitree_json_to_lerobot.py \
  --raw-dir "${RAW_JSON_ROOT}" \
  --repo-id "${DATASET_REPO_ID}" \
  --robot-type "${ROBOT_TYPE}" \
  --root "${DATASET_ROOT}"
