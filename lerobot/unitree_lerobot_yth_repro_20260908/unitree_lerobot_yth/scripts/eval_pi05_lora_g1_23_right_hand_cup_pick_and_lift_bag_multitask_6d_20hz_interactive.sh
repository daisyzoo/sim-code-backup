#!/usr/bin/env bash

# Non-MCP interactive evaluation for the cup-pick / bag-lift multitask PI0.5 policy.
# The model is loaded once. Press s for cup pick, r for bag lift, or q to quit.
set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot_yth"
LEROBOT_ROOT="${REPO_ROOT}/unitree_lerobot/lerobot"
CONDA_SH="/home/igs/miniconda3/etc/profile.d/conda.sh"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-vla_eval}"
LOCAL_HF_HUB_CACHE="${LOCAL_HF_HUB_CACHE:-/home/igs/Desktop/project/vla/data/.hf_hub_cache}"
LOCAL_HF_HOME="${LOCAL_HF_HOME:-/media/igs/EAGET/syh/vla/cache/hf_home}"
LOCAL_HF_DATASETS_CACHE="${LOCAL_HF_DATASETS_CACHE:-/media/igs/EAGET/syh/vla/cache/hf_datasets}"
TOKENIZER_PATH="${TOKENIZER_PATH:-/media/igs/EAGET/syh/train_output/tokenizer}"

# POLICY_PATH may point either to pretrained_model itself or to its parent checkpoint.
POLICY_PATH_DEFAULT="/media/igs/EAGET/syh/train_output/pretrained_model"
POLICY_PATH_INPUT="${POLICY_PATH:-${POLICY_PATH_DEFAULT}}"
if [[ -d "${POLICY_PATH_INPUT}/pretrained_model" ]]; then
  POLICY_PATH="${POLICY_PATH_INPUT}/pretrained_model"
else
  POLICY_PATH="${POLICY_PATH_INPUT}"
fi

DATASET_REPO_ID="${DATASET_REPO_ID:-local/g1_23_right_hand_cup_pick_and_lift_bag_current_rightarm5_waist1_6d_20hz}"
DATASET_ROOT="${DATASET_ROOT:-/home/igs/Desktop/project/vla/unitree_lerobot/data/local/g1_23_right_hand_cup_pick_and_lift_bag_current_rightarm5_waist1_6d_20hz}"

CUP_PICK_TASK_TEXT="${CUP_PICK_TASK_TEXT:-Task: cup_pick. Pick up the cup with the right hand by grasping around the cup body.}"
LIFT_BAG_TASK_TEXT="${LIFT_BAG_TASK_TEXT:-Task: lift_bag. Use the right hand to hook the handbag handle and lift the handbag.}"

IMAGE_HOST="${IMAGE_HOST:-192.168.123.164}"
NETWORK_INTERFACE="${NETWORK_INTERFACE:-eno1}"
EPISODE_INDEX="${EPISODE_INDEX:-0}"
FREQUENCY="${FREQUENCY:-20}"
NUM_INFERENCE_STEPS="${PI05_NUM_INFERENCE_STEPS:-10}"
VISUALIZATION="${VISUALIZATION:-false}"
EPISODE_DURATION_S="${EPISODE_DURATION_S:-2.5}"
RETURN_TO_ZERO_DURATION_S="${RETURN_TO_ZERO_DURATION_S:-2}"
HANDOVER_WAIT_SECONDS="${HANDOVER_WAIT_SECONDS:-0.8}"
PRE_HANDOVER_WAIT_SECONDS="${PRE_HANDOVER_WAIT_SECONDS:-0.8}"
MOTION="${MOTION:-true}"
ARM_TAU_MODE="${ARM_TAU_MODE:-gravity}"
CONSTANT_TARGET_DURATION_S="${CONSTANT_TARGET_DURATION_S:-0}"
SEND_REAL_ROBOT="${SEND_REAL_ROBOT:-true}"
LEFT_ARM_READY_POSE_DEG="${LEFT_ARM_READY_POSE_DEG:-0,0,14,0,0}"

source "${CONDA_SH}"
conda activate "${CONDA_ENV_NAME}"

unset CYCLONEDDS_URI
unset RMW_IMPLEMENTATION
unset ROS_DOMAIN_ID

export PYTHONPATH="${LEROBOT_ROOT}/src:${REPO_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
export HF_HOME="${LOCAL_HF_HOME}"
export HF_HUB_CACHE="${LOCAL_HF_HUB_CACHE}"
export HF_DATASETS_CACHE="${LOCAL_HF_DATASETS_CACHE}"
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
export HF_DATASETS_OFFLINE=1

cd "${REPO_ROOT}"

if [[ ! -d "${POLICY_PATH}" ]]; then
  echo "Policy path does not exist: ${POLICY_PATH}" >&2
  exit 1
fi

if [[ ! -d "${DATASET_ROOT}" ]]; then
  echo "Dataset root does not exist: ${DATASET_ROOT}" >&2
  exit 1
fi

if [[ ! -d "${TOKENIZER_PATH}" ]]; then
  echo "Tokenizer path does not exist: ${TOKENIZER_PATH}" >&2
  exit 1
fi

echo "Using policy path: ${POLICY_PATH}"
echo "Using dataset root: ${DATASET_ROOT}"
echo "Using tokenizer path: ${TOKENIZER_PATH}"
echo "Interactive controls: s=cup pick, r=lift bag, q=quit"
echo "send_real_robot=${SEND_REAL_ROBOT} frequency=${FREQUENCY}"

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
  --arm=G1_23_RightArm5 \
  --ee='' \
  --image_host="${IMAGE_HOST}" \
  --network_interface="${NETWORK_INTERFACE}" \
  --motion="${MOTION}" \
  --visualization="${VISUALIZATION}" \
  --interactive_task_selection=true \
  --task_s_text="'${CUP_PICK_TASK_TEXT}'" \
  --task_r_text="'${LIFT_BAG_TASK_TEXT}'" \
  --tokenizer_name_override="${TOKENIZER_PATH}" \
  --arm_tau_mode="${ARM_TAU_MODE}" \
  --constant_target_duration_s="${CONSTANT_TARGET_DURATION_S}" \
  --left_arm_ready_pose_deg="${LEFT_ARM_READY_POSE_DEG}" \
  --send_real_robot="${SEND_REAL_ROBOT}"
