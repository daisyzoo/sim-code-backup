#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
TRAIN_SCRIPT="${REPO_ROOT}/scripts/train_pi05_lora_g1_23_6d_20hz_experiment.sh"

exec env \
  DATASET_REPO_ID="${DATASET_REPO_ID:-local/g1_23_right_hand_lift_bag_control_all5_rightarm5_waist1_righteepose_13d_20hz}" \
  DATASET_ROOT="${DATASET_ROOT:-/media/igs/EAGET/syh/vla/data/local/g1_23_right_hand_lift_bag_control_all5_rightarm5_waist1_righteepose_13d_20hz}" \
  JOB_NAME="${JOB_NAME:-pi05_lora_g1_23_right_hand_lift_bag_all5_eepose_minmax_aug_13d_20hz_40k}" \
  PI05_TRAIN_STEPS="${PI05_TRAIN_STEPS:-40000}" \
  PI05_SAVE_FREQ="${PI05_SAVE_FREQ:-2000}" \
  PI05_BATCH_SIZE="${PI05_BATCH_SIZE:-2}" \
  POLICY_DTYPE="${POLICY_DTYPE:-float32}" \
  POLICY_GRADIENT_CHECKPOINTING="${POLICY_GRADIENT_CHECKPOINTING:-false}" \
  POLICY_USE_AMP="${POLICY_USE_AMP:-false}" \
  ACTION_NORM="${ACTION_NORM:-MIN_MAX}" \
  STATE_NORM="${STATE_NORM:-QUANTILES}" \
  VISUAL_NORM="${VISUAL_NORM:-IDENTITY}" \
  ENABLE_IMAGE_TRANSFORMS="${ENABLE_IMAGE_TRANSFORMS:-true}" \
  IMAGE_TRANSFORMS_MAX_NUM="${IMAGE_TRANSFORMS_MAX_NUM:-2}" \
  IMAGE_TRANSFORMS_RANDOM_ORDER="${IMAGE_TRANSFORMS_RANDOM_ORDER:-false}" \
  "${TRAIN_SCRIPT}"
