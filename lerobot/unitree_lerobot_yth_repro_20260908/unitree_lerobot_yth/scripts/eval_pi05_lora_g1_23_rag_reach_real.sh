#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
CONDA_SH="/home/igs/miniconda3/etc/profile.d/conda.sh"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-vla_eval}"

POLICY_PATH_DEFAULT="/media/igs/EAGET/syh/vla/outputs/pi05_lora_g1_23_rag_reach_20260520_210832/checkpoints/010000/pretrained_model"
POLICY_PATH="${POLICY_PATH:-${POLICY_PATH_DEFAULT}}"
DATASET_REPO_ID="${DATASET_REPO_ID:-local/g1_23_right_hand_rag_reach_11d}"
DATASET_ROOT="${DATASET_ROOT:-/home/igs/Desktop/project/vla/data/local/g1_23_right_hand_rag_reach_11d}"
IMAGE_HOST="${IMAGE_HOST:-192.168.123.164}"
NETWORK_INTERFACE="${NETWORK_INTERFACE:-eno1}"
EPISODE_INDEX="${EPISODE_INDEX:-0}"
FREQUENCY="${FREQUENCY:-20}"
NUM_INFERENCE_STEPS="${PI05_NUM_INFERENCE_STEPS:-1}"
VISUALIZATION="${VISUALIZATION:-false}"
TASK_OVERRIDE="${TASK_OVERRIDE:-}"
EPISODE_DURATION_S="${EPISODE_DURATION_S:-2.5}"
RETURN_TO_ZERO_DURATION_S="${RETURN_TO_ZERO_DURATION_S:-3}"
HANDOVER_WAIT_SECONDS="${HANDOVER_WAIT_SECONDS:-0.8}"
PRE_HANDOVER_WAIT_SECONDS="${PRE_HANDOVER_WAIT_SECONDS:-0.8}"
MOTION="${MOTION:-true}"
ARM_TAU_MODE="${ARM_TAU_MODE:-gravity}"
CONSTANT_TARGET_DURATION_S="${CONSTANT_TARGET_DURATION_S:-0}"

source "${CONDA_SH}"
conda activate "${CONDA_ENV_NAME}"

unset CYCLONEDDS_URI
unset RMW_IMPLEMENTATION
unset ROS_DOMAIN_ID

export PYTHONPATH="${REPO_ROOT}"

cd "${REPO_ROOT}"

PYTHONNOUSERSITE=1 python unitree_lerobot/eval_robot/eval_g1.py \
  --policy.path="${POLICY_PATH}" \
  --policy.num_inference_steps="${NUM_INFERENCE_STEPS}" \
  --repo_id="${DATASET_REPO_ID}" \
  --root="${DATASET_ROOT}" \
  --episodes="${EPISODE_INDEX}" \
  --frequency="${FREQUENCY}" \
  --episode_duration_s="${EPISODE_DURATION_S}" \
  --return_to_zero_duration_s="${RETURN_TO_ZERO_DURATION_S}" \
  --handover_wait_seconds="${HANDOVER_WAIT_SECONDS}" \
  --pre_handover_wait_seconds="${PRE_HANDOVER_WAIT_SECONDS}" \
  --arm=G1_23 \
  --ee='' \
  --image_host="${IMAGE_HOST}" \
  --network_interface="${NETWORK_INTERFACE}" \
  --motion="${MOTION}" \
  --visualization="${VISUALIZATION}" \
  --task_override="${TASK_OVERRIDE}" \
  --arm_tau_mode="${ARM_TAU_MODE}" \
  --constant_target_duration_s="${CONSTANT_TARGET_DURATION_S}" \
  --send_real_robot=true
