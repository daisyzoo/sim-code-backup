#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
PYTHON_BIN="${PYTHON_BIN:-/home/igs/miniconda3/envs/unitree_lerobot/bin/python}"

SOURCE_ROOT="${SOURCE_ROOT:-/media/igs/EAGET/syh/dataset/right_hand_cup_pick_50f}"
TASK_NAME="${TASK_NAME:-right_hand_cup_pick}"
WRAPPED_JSON_ROOT="${WRAPPED_JSON_ROOT:-${REPO_ROOT}/data/raw/g1_23_right_hand_cup_pick_11d_20hz_json}"
DATASET_REPO_ID="${DATASET_REPO_ID:-local/g1_23_right_hand_cup_pick_11d_20hz}"
DATASET_ROOT="${DATASET_ROOT:-${REPO_ROOT}/data/local/g1_23_right_hand_cup_pick_11d_20hz}"
ROBOT_TYPE="${ROBOT_TYPE:-Unitree_G1_23Dof_Arms5_Waist1}"
LINK_MODE="${LINK_MODE:-symlink}"

if [[ ! -d "${SOURCE_ROOT}" ]]; then
  echo "Source root does not exist: ${SOURCE_ROOT}" >&2
  exit 1
fi

mkdir -p "${REPO_ROOT}/data/raw" "${REPO_ROOT}/data/local"

PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" scripts/wrap_flat_unitree_json_dataset.py \
  --source-root "${SOURCE_ROOT}" \
  --output-root "${WRAPPED_JSON_ROOT}" \
  --task-name "${TASK_NAME}" \
  --mode "${LINK_MODE}" \
  --overwrite

PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" unitree_lerobot/utils/convert_unitree_json_to_lerobot.py \
  --raw-dir "${WRAPPED_JSON_ROOT}" \
  --repo-id "${DATASET_REPO_ID}" \
  --robot-type "${ROBOT_TYPE}" \
  --root "${DATASET_ROOT}"
