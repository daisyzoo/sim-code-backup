#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
PYTHON_BIN="${PYTHON_BIN:-/home/igs/miniconda3/envs/unitree_lerobot/bin/python}"

RAW_JSON_ROOT="${RAW_JSON_ROOT:-/media/igs/EAGET/syh/dataset/processed/g1_23_right_hand_lift_bag_20fps_json}"
DATASET_REPO_ID="${DATASET_REPO_ID:-local/g1_23_right_hand_lift_bag_rightarm5_waist1_6d_20hz}"
DATASET_ROOT="${DATASET_ROOT:-/media/igs/EAGET/syh/vla/data/local/g1_23_right_hand_lift_bag_rightarm5_waist1_6d_20hz}"
ROBOT_TYPE="${ROBOT_TYPE:-Unitree_G1_23Dof_RightArm5_Waist1}"

if [[ ! -d "${RAW_JSON_ROOT}" ]]; then
  echo "Raw JSON root does not exist: ${RAW_JSON_ROOT}" >&2
  exit 1
fi

PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" unitree_lerobot/utils/convert_unitree_json_to_lerobot.py \
  --raw-dir "${RAW_JSON_ROOT}" \
  --repo-id "${DATASET_REPO_ID}" \
  --robot-type "${ROBOT_TYPE}" \
  --root "${DATASET_ROOT}"
