#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
TRAIN_SCRIPT="${REPO_ROOT}/scripts/train_pi05_lora_g1_23_right_hand_cup_pick_baseline_6d_20hz.sh"

exec env \
  JOB_NAME="${JOB_NAME:-pi05_lora_g1_23_right_hand_cup_pick_baseline_aug_6d_20hz}" \
  ENABLE_IMAGE_TRANSFORMS="${ENABLE_IMAGE_TRANSFORMS:-true}" \
  IMAGE_TRANSFORMS_MAX_NUM="${IMAGE_TRANSFORMS_MAX_NUM:-2}" \
  IMAGE_TRANSFORMS_RANDOM_ORDER="${IMAGE_TRANSFORMS_RANDOM_ORDER:-false}" \
  "${TRAIN_SCRIPT}"
