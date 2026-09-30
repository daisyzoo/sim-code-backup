#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
PYTHON_BIN="${PYTHON_BIN:-/home/igs/miniconda3/envs/unitree_lerobot/bin/python}"

SPEC_PATH="${SPEC_PATH:-${REPO_ROOT}/scripts/g1_23_right_hand_cup_pick_and_lift_bag_multitask_6d_20hz_spec.json}"
RAW_JSON_ROOT="${RAW_JSON_ROOT:-${REPO_ROOT}/data/raw/g1_23_right_hand_cup_pick_and_lift_bag_multitask_6d_20hz_json}"
DATASET_REPO_ID="${DATASET_REPO_ID:-local/g1_23_right_hand_cup_pick_and_lift_bag_multitask_rightarm5_waist1_6d_20hz}"
DATASET_ROOT="${DATASET_ROOT:-${REPO_ROOT}/data/local/g1_23_right_hand_cup_pick_and_lift_bag_multitask_rightarm5_waist1_6d_20hz}"
ROBOT_TYPE="${ROBOT_TYPE:-Unitree_G1_23Dof_RightArm5_Waist1}"

mkdir -p "${REPO_ROOT}/data/raw" "${REPO_ROOT}/data/local"

PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" scripts/prepare_multisource_multitask_json_dataset.py \
  --spec-path "${SPEC_PATH}"

PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" unitree_lerobot/utils/convert_unitree_json_to_lerobot.py \
  --raw-dir "${RAW_JSON_ROOT}" \
  --repo-id "${DATASET_REPO_ID}" \
  --robot-type "${ROBOT_TYPE}" \
  --root "${DATASET_ROOT}"
