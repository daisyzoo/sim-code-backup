#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"

TRAIN_11D_SCRIPT="${REPO_ROOT}/scripts/train_pi05_lora_g1_23_right_hand_cup_pick_11d_20hz.sh"
TRAIN_6D_SCRIPT="${REPO_ROOT}/scripts/train_pi05_lora_g1_23_right_hand_cup_pick_6d_20hz.sh"

if [[ ! -x "${TRAIN_11D_SCRIPT}" ]]; then
  echo "11d train script is missing or not executable: ${TRAIN_11D_SCRIPT}" >&2
  exit 1
fi

if [[ ! -x "${TRAIN_6D_SCRIPT}" ]]; then
  echo "6d train script is missing or not executable: ${TRAIN_6D_SCRIPT}" >&2
  exit 1
fi

echo "Starting 11d 20hz training at $(date '+%F %T')"
"${TRAIN_11D_SCRIPT}"
echo "Finished 11d 20hz training at $(date '+%F %T')"

echo "Starting 6d 20hz training at $(date '+%F %T')"
"${TRAIN_6D_SCRIPT}"
echo "Finished 6d 20hz training at $(date '+%F %T')"
