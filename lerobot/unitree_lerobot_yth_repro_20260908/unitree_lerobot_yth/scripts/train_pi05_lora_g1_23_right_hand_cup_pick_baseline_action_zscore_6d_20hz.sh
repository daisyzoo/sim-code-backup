#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
TRAIN_SCRIPT="${REPO_ROOT}/scripts/train_pi05_lora_g1_23_right_hand_cup_pick_baseline_6d_20hz.sh"

exec env \
  JOB_NAME="${JOB_NAME:-pi05_lora_g1_23_right_hand_cup_pick_baseline_action_zscore_6d_20hz}" \
  ACTION_NORM="${ACTION_NORM:-MEAN_STD}" \
  STATE_NORM="${STATE_NORM:-QUANTILES}" \
  VISUAL_NORM="${VISUAL_NORM:-IDENTITY}" \
  "${TRAIN_SCRIPT}"
