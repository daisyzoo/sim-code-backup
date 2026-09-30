#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
TRAIN_SCRIPT="${REPO_ROOT}/scripts/train_pi05_lora_g1_23_6d_20hz_experiment.sh"

DATASET_REPO_ID="${DATASET_REPO_ID:-local/g1_23_right_hand_cup_pick_background_rightarm5_waist1_6d_20hz}"
DATASET_ROOT="${DATASET_ROOT:-${REPO_ROOT}/data/local/g1_23_right_hand_cup_pick_background_rightarm5_waist1_6d_20hz}"
JOB_NAME="${JOB_NAME:-pi05_lora_g1_23_right_hand_cup_pick_background_6d_20hz}"

exec env \
  DATASET_REPO_ID="${DATASET_REPO_ID}" \
  DATASET_ROOT="${DATASET_ROOT}" \
  JOB_NAME="${JOB_NAME}" \
  PI05_TRAIN_STEPS="${PI05_TRAIN_STEPS:-20000}" \
  PI05_BATCH_SIZE="${PI05_BATCH_SIZE:-2}" \
  POLICY_DTYPE="${POLICY_DTYPE:-float32}" \
  POLICY_GRADIENT_CHECKPOINTING="${POLICY_GRADIENT_CHECKPOINTING:-false}" \
  POLICY_USE_AMP="${POLICY_USE_AMP:-false}" \
  ACTION_NORM="${ACTION_NORM:-MIN_MAX}" \
  STATE_NORM="${STATE_NORM:-QUANTILES}" \
  VISUAL_NORM="${VISUAL_NORM:-IDENTITY}" \
  ENABLE_IMAGE_TRANSFORMS="${ENABLE_IMAGE_TRANSFORMS:-false}" \
  IMAGE_TRANSFORMS_MAX_NUM="${IMAGE_TRANSFORMS_MAX_NUM:-2}" \
  IMAGE_TRANSFORMS_RANDOM_ORDER="${IMAGE_TRANSFORMS_RANDOM_ORDER:-false}" \
  "${TRAIN_SCRIPT}"
