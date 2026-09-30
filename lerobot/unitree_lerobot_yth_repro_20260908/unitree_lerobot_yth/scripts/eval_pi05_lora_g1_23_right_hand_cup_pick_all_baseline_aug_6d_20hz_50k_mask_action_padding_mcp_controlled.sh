#!/usr/bin/env bash

# Controlled evaluation for the action-padding-mask PI0.5 checkpoint.
# Defaults to dry-run: no G1 arm commands are sent unless explicitly armed below.
set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot_yth"
LEROBOT_ROOT="${REPO_ROOT}/unitree_lerobot/lerobot"
CONDA_SH="/home/igs/miniconda3/etc/profile.d/conda.sh"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-vla_eval}"
LOCAL_HF_HUB_CACHE="${LOCAL_HF_HUB_CACHE:-/home/igs/Desktop/project/vla/data/.hf_hub_cache}"

POLICY_PATH_DEFAULT="/media/igs/EAGET/syh/vla/outputs/pi05_lora_g1_23_right_hand_cup_pick_all_baseline_aug_6d_20hz_50k_mask_action_padding_20260716_201827/checkpoints/050000"
POLICY_PATH_INPUT="${POLICY_PATH:-${POLICY_PATH_DEFAULT}}"
if [[ -d "${POLICY_PATH_INPUT}/pretrained_model" ]]; then
  POLICY_PATH="${POLICY_PATH_INPUT}/pretrained_model"
else
  POLICY_PATH="${POLICY_PATH_INPUT}"
fi

DATASET_REPO_ID="${DATASET_REPO_ID:-local/g1_23_right_hand_cup_pick_all_rightarm5_waist1_6d_20hz}"
DATASET_ROOT="${DATASET_ROOT:-/home/igs/Desktop/project/vla/unitree_lerobot/data/local/g1_23_right_hand_cup_pick_all_rightarm5_waist1_6d_20hz}"
IMAGE_HOST="${IMAGE_HOST:-192.168.123.164}"
NETWORK_INTERFACE="${NETWORK_INTERFACE:-eno1}"
EPISODE_INDEX="${EPISODE_INDEX:-0}"
FREQUENCY="${FREQUENCY:-20}"
NUM_INFERENCE_STEPS="${PI05_NUM_INFERENCE_STEPS:-10}"
VISUALIZATION="${VISUALIZATION:-false}"
TASK_OVERRIDE="${TASK_OVERRIDE:-}"
IDLE_PUBLISH_MODE="${IDLE_PUBLISH_MODE:-freeze}"
EPISODE_DURATION_S="${EPISODE_DURATION_S:-2.5}"
RETURN_TO_ZERO_DURATION_S="${RETURN_TO_ZERO_DURATION_S:-2}"
HANDOVER_WAIT_SECONDS="${HANDOVER_WAIT_SECONDS:-0.8}"
PRE_HANDOVER_WAIT_SECONDS="${PRE_HANDOVER_WAIT_SECONDS:-0.8}"
ARM_TAU_MODE="${ARM_TAU_MODE:-gravity}"
CONSTANT_TARGET_DURATION_S="${CONSTANT_TARGET_DURATION_S:-0}"
POST_ACTION_SHOULDER_ROLL_NUDGE_RAD="${POST_ACTION_SHOULDER_ROLL_NUDGE_RAD:-0.16}"
POST_ACTION_NUDGE_DURATION_S="${POST_ACTION_NUDGE_DURATION_S:-0.8}"
POST_ACTION_NUDGE_HOLD_S="${POST_ACTION_NUDGE_HOLD_S:-1.0}"
MCP_PORT="${MCP_PORT:-8765}"
VLA_BASE="${VLA_BASE:-http://localhost:${MCP_PORT}}"

# Safe by default. A real-robot run requires both explicit environment variables.
SEND_REAL_ROBOT="${SEND_REAL_ROBOT:-false}"
MOTION="${MOTION:-false}"
if [[ "${SEND_REAL_ROBOT}" == "true" && "${ALLOW_REAL_ROBOT:-false}" != "true" ]]; then
  echo "Refusing real-robot mode. Re-run with ALLOW_REAL_ROBOT=true SEND_REAL_ROBOT=true." >&2
  exit 2
fi

if [[ ! -d "${POLICY_PATH}" ]]; then
  echo "Policy path does not exist: ${POLICY_PATH}" >&2
  exit 1
fi
if [[ ! -d "${DATASET_ROOT}" ]]; then
  echo "Dataset root does not exist: ${DATASET_ROOT}" >&2
  exit 1
fi

source "${CONDA_SH}"
conda activate "${CONDA_ENV_NAME}"
unset CYCLONEDDS_URI RMW_IMPLEMENTATION ROS_DOMAIN_ID

# Prefer this checkout over the environment's editable install from the old repo.
export PYTHONPATH="${LEROBOT_ROOT}/src:${REPO_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
export HF_HUB_CACHE="${LOCAL_HF_HUB_CACHE}"
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 PYTHONUNBUFFERED=1

echo "Policy: ${POLICY_PATH}"
echo "Dataset: ${DATASET_ROOT}"
echo "send_real_robot=${SEND_REAL_ROBOT}; motion=${MOTION}"
echo "MCP endpoint: ${VLA_BASE}/mcp"

cd "${REPO_ROOT}"
PYTHONNOUSERSITE=1 python -m unitree_lerobot.eval_robot.vla_mcp_controlled_server \
  --vla-base="${VLA_BASE}" \
  --port="${MCP_PORT}" \
  --policy.path="${POLICY_PATH}" \
  --policy.num_inference_steps="${NUM_INFERENCE_STEPS}" \
  --repo_id="${DATASET_REPO_ID}" \
  --root="${DATASET_ROOT}" \
  --episodes="${EPISODE_INDEX}" \
  --frequency="${FREQUENCY}" \
  --episode_duration_s="${EPISODE_DURATION_S}" \
  --return_to_zero_duration_s="${RETURN_TO_ZERO_DURATION_S}" \
  --idle_publish_mode="${IDLE_PUBLISH_MODE}" \
  --handover_wait_seconds="${HANDOVER_WAIT_SECONDS}" \
  --pre_handover_wait_seconds="${PRE_HANDOVER_WAIT_SECONDS}" \
  --arm=G1_23_RightArm5 \
  --ee='' \
  --image_host="${IMAGE_HOST}" \
  --network_interface="${NETWORK_INTERFACE}" \
  --motion="${MOTION}" \
  --visualization="${VISUALIZATION}" \
  --task_override="${TASK_OVERRIDE}" \
  --arm_tau_mode="${ARM_TAU_MODE}" \
  --constant_target_duration_s="${CONSTANT_TARGET_DURATION_S}" \
  --post_action_shoulder_roll_nudge_rad="${POST_ACTION_SHOULDER_ROLL_NUDGE_RAD}" \
  --post_action_nudge_duration_s="${POST_ACTION_NUDGE_DURATION_S}" \
  --post_action_nudge_hold_s="${POST_ACTION_NUDGE_HOLD_S}" \
  --send_real_robot="${SEND_REAL_ROBOT}"
