#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
PYTHON_BIN="${PYTHON_BIN:-/home/igs/miniconda3/envs/unitree_lerobot/bin/python}"

RAW_JSON_ROOT="${RAW_JSON_ROOT:-${REPO_ROOT}/data/raw/g1_23_right_hand_cup_pick_11d_20hz_json}"
DATASET_REPO_ID="${DATASET_REPO_ID:-local/g1_23_right_hand_cup_pick_rightarm5_waist1_6d_20hz}"
DATASET_ROOT="${DATASET_ROOT:-${REPO_ROOT}/data/local/g1_23_right_hand_cup_pick_rightarm5_waist1_6d_20hz}"
ROBOT_TYPE="${ROBOT_TYPE:-Unitree_G1_23Dof_RightArm5_Waist1}"

if [[ ! -d "${RAW_JSON_ROOT}" ]]; then
  echo "Raw JSON root does not exist: ${RAW_JSON_ROOT}" >&2
  echo "Prepare wrapped JSON first with scripts/prepare_g1_23_right_hand_cup_pick_11d_20hz_dataset.sh" >&2
  exit 1
fi

mkdir -p "${REPO_ROOT}/data/local"

PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" unitree_lerobot/utils/convert_unitree_json_to_lerobot.py \
  --raw-dir "${RAW_JSON_ROOT}" \
  --repo-id "${DATASET_REPO_ID}" \
  --robot-type "${ROBOT_TYPE}" \
  --root "${DATASET_ROOT}"
