#!/usr/bin/env bash

# MCP-controlled, continuous RTC evaluation for the expert-only 15 Hz cup-pick model.
# Each vla_execute request may refill multiple PI0.5 action chunks until its requested
# duration, the server hard limit, or vla_stop terminates the task.
set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot_yth"
LEROBOT_ROOT="${REPO_ROOT}/unitree_lerobot/lerobot"
CONDA_SH="/home/igs/miniconda3/etc/profile.d/conda.sh"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-vla_eval}"

LOCAL_HF_HUB_CACHE="${LOCAL_HF_HUB_CACHE:-/home/igs/Desktop/project/vla/data/.hf_hub_cache}"
LOCAL_HF_HOME="${LOCAL_HF_HOME:-/media/igs/EAGET/syh/vla/cache/hf_home}"
LOCAL_HF_DATASETS_CACHE="${LOCAL_HF_DATASETS_CACHE:-/media/igs/EAGET/syh/vla/cache/hf_datasets}"
TOKENIZER_PATH="${TOKENIZER_PATH:-/media/igs/EAGET/syh/train_output/tokenizer}"

POLICY_PATH_DEFAULT="/media/igs/EAGET/syh/vla/outputs/pi05_expert_only_pick_up_6d_15hz_0804_0805_20260806_151401/checkpoints/last"
POLICY_PATH_INPUT="${POLICY_PATH:-${POLICY_PATH_DEFAULT}}"
if [[ -d "${POLICY_PATH_INPUT}/pretrained_model" ]]; then
  POLICY_PATH="${POLICY_PATH_INPUT}/pretrained_model"
else
  POLICY_PATH="${POLICY_PATH_INPUT}"
fi

DATASET_REPO_ID="${DATASET_REPO_ID:-local/lerobot_pick_up_15hz_0804-0805}"
DATASET_ROOT="${DATASET_ROOT:-/media/igs/EAGET/syh/dataset/xr_data/lerobot_pick_up_15hz_0804-0805}"
TASK_OVERRIDE="${TASK_OVERRIDE:-Pick up the cup with the right hand.}"

IMAGE_HOST="${IMAGE_HOST:-192.168.123.164}"
NETWORK_INTERFACE="${NETWORK_INTERFACE:-eno1}"
EPISODE_INDEX="${EPISODE_INDEX:-0}"
FREQUENCY="${FREQUENCY:-15}"
NUM_INFERENCE_STEPS="${PI05_NUM_INFERENCE_STEPS:-10}"
VISUALIZATION="${VISUALIZATION:-false}"

# Fixed per-request action limit. It is not exposed as an MCP tool argument and
# starts at the first action, after initial inference.
MAX_EPISODE_WALL_TIME_S="${MAX_EPISODE_WALL_TIME_S:-60}"
RETURN_TO_ZERO_DURATION_S="${RETURN_TO_ZERO_DURATION_S:-2}"
HANDOVER_WAIT_SECONDS="${HANDOVER_WAIT_SECONDS:-0.8}"
PRE_HANDOVER_WAIT_SECONDS="${PRE_HANDOVER_WAIT_SECONDS:-0.8}"
MOTION="${MOTION:-true}"
ARM_TAU_MODE="${ARM_TAU_MODE:-gravity}"
CONSTANT_TARGET_DURATION_S="${CONSTANT_TARGET_DURATION_S:-0}"
POST_ACTION_SHOULDER_ROLL_NUDGE_RAD="${POST_ACTION_SHOULDER_ROLL_NUDGE_RAD:-0}"
POST_ACTION_NUDGE_DURATION_S="${POST_ACTION_NUDGE_DURATION_S:-0.8}"
POST_ACTION_NUDGE_HOLD_S="${POST_ACTION_NUDGE_HOLD_S:-0}"
SEND_REAL_ROBOT="${SEND_REAL_ROBOT:-true}"
ARM_CONTROLLER_PROCESS="${ARM_CONTROLLER_PROCESS:-true}"
IDLE_PUBLISH_MODE="${IDLE_PUBLISH_MODE:-freeze}"
LEFT_ARM_READY_POSE_DEG="${LEFT_ARM_READY_POSE_DEG:-0,0,14,0,0}"
USE_DATASET="${USE_DATASET:-}"
if [[ -z "${USE_DATASET}" ]]; then
  if [[ "${SEND_REAL_ROBOT,,}" == "true" ]]; then
    USE_DATASET=false
  else
    USE_DATASET=true
  fi
fi

RTC_ENABLED="${RTC_ENABLED:-true}"
# Set false for the async-chunking-only ablation: retain the action queue and
# consumed-frame handover, but bypass all RTC flow-matching/Jacobian guidance.
RTC_GUIDANCE_ENABLED="${RTC_GUIDANCE_ENABLED:-true}"
RTC_USE_AUTOGRAD_JACOBIAN="${RTC_USE_AUTOGRAD_JACOBIAN:-true}"
# Keep the RTC horizon beyond the actions that can execute during inference.
# At 15 Hz, a 20-frame execution cap is ~1.33 s; horizon=25 leaves a five-frame
# exponential guidance tail for the newly generated actions that actually take
# over after the inferred-delay prefix is discarded.
RTC_EXECUTION_HORIZON="${RTC_EXECUTION_HORIZON:-25}"
RTC_MAX_GUIDANCE_WEIGHT="${RTC_MAX_GUIDANCE_WEIGHT:-10.0}"
RTC_PREFIX_ATTENTION_SCHEDULE="${RTC_PREFIX_ATTENTION_SCHEDULE:-exp}"
RTC_QUEUE_THRESHOLD="${RTC_QUEUE_THRESHOLD:-30}"
RTC_MAX_ACTIONS_DURING_INFERENCE="${RTC_MAX_ACTIONS_DURING_INFERENCE:-20}"
RTC_INFERENCE_TIMEOUT_S="${RTC_INFERENCE_TIMEOUT_S:-120}"
RTC_LATENCY_WINDOW="${RTC_LATENCY_WINDOW:-100}"
# Empty by default for long MCP sessions; set a directory to save inference images.
RTC_SNAPSHOT_DIR="${RTC_SNAPSHOT_DIR:-}"
RTC_EXECUTION_LOG_PATH="${RTC_EXECUTION_LOG_PATH:-${REPO_ROOT}/outputs/rtc_execution_logs/pi05_expert_only_pick_up_15hz_mcp_$(date +%Y%m%d_%H%M%S).jsonl}"

# Data-derived automatic completion: measured 5D right-arm + 1D waist state
# must remain inside the terminal region for the configured hold duration.
TERMINAL_JOINT_DETECTOR_ENABLED="${TERMINAL_JOINT_DETECTOR_ENABLED:-true}"
TERMINAL_JOINT_DETECTOR_CONFIG="${TERMINAL_JOINT_DETECTOR_CONFIG:-${REPO_ROOT}/unitree_lerobot/eval_robot/assets/g1/pick_cup_terminal_joint_pose_15hz.json}"

MCP_PORT="${MCP_PORT:-8765}"
VLA_BASE="${VLA_BASE:-http://localhost:${MCP_PORT}}"

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
export PYTHONUNBUFFERED=1

cd "${REPO_ROOT}"

for required_dir in "${POLICY_PATH}" "${DATASET_ROOT}" "${TOKENIZER_PATH}"; do
  if [[ ! -d "${required_dir}" ]]; then
    echo "Required directory does not exist: ${required_dir}" >&2
    exit 1
  fi
done

for required_file in config.json model.safetensors policy_preprocessor.json policy_postprocessor.json; do
  if [[ ! -f "${POLICY_PATH}/${required_file}" ]]; then
    echo "Required checkpoint file does not exist: ${POLICY_PATH}/${required_file}" >&2
    exit 1
  fi
done
if [[ "${TERMINAL_JOINT_DETECTOR_ENABLED,,}" == "true" && ! -f "${TERMINAL_JOINT_DETECTOR_CONFIG}" ]]; then
  echo "Terminal joint detector config does not exist: ${TERMINAL_JOINT_DETECTOR_CONFIG}" >&2
  exit 1
fi

echo "Using policy path: ${POLICY_PATH}"
echo "Using dataset root: ${DATASET_ROOT}"
echo "Task fallback: ${TASK_OVERRIDE}"
echo "MCP endpoint: ${VLA_BASE}/mcp"
echo "HTTP endpoints: ${VLA_BASE}/vla/execute ${VLA_BASE}/vla/stop ${VLA_BASE}/vla/status"
echo "REAL ROBOT=${SEND_REAL_ROBOT} arm_controller_process=${ARM_CONTROLLER_PROCESS} frequency=${FREQUENCY}Hz"
echo "Fixed MCP action duration=${MAX_EPISODE_WALL_TIME_S}s; inference_timeout=${RTC_INFERENCE_TIMEOUT_S}s"
echo "RTC guidance_enabled=${RTC_GUIDANCE_ENABLED} autograd_jacobian=${RTC_USE_AUTOGRAD_JACOBIAN} horizon=${RTC_EXECUTION_HORIZON} queue_threshold=${RTC_QUEUE_THRESHOLD} max_actions_during_inference=${RTC_MAX_ACTIONS_DURING_INFERENCE}"
echo "RTC per-frame execution log: ${RTC_EXECUTION_LOG_PATH}"
echo "Terminal joint detector=${TERMINAL_JOINT_DETECTOR_ENABLED} config=${TERMINAL_JOINT_DETECTOR_CONFIG}"

PYTHONNOUSERSITE=1 python -m unitree_lerobot.eval_robot.vla_rtc_mcp_controlled_server \
  --vla-base="${VLA_BASE}" \
  --port="${MCP_PORT}" \
  --policy.path="${POLICY_PATH}" \
  --policy.num_inference_steps="${NUM_INFERENCE_STEPS}" \
  --repo_id="${DATASET_REPO_ID}" \
  --root="${DATASET_ROOT}" \
  --episodes="${EPISODE_INDEX}" \
  --frequency="${FREQUENCY}" \
  --episode_duration_s="${MAX_EPISODE_WALL_TIME_S}" \
  --max_episode_wall_time_s="${MAX_EPISODE_WALL_TIME_S}" \
  --run_until_q=false \
  --return_to_zero_duration_s="${RETURN_TO_ZERO_DURATION_S}" \
  --handover_wait_seconds="${HANDOVER_WAIT_SECONDS}" \
  --pre_handover_wait_seconds="${PRE_HANDOVER_WAIT_SECONDS}" \
  --arm=G1_23_RightArm5 \
  --ee='' \
  --image_host="${IMAGE_HOST}" \
  --network_interface="${NETWORK_INTERFACE}" \
  --motion="${MOTION}" \
  --visualization="${VISUALIZATION}" \
  --use_dataset="${USE_DATASET}" \
  --interactive_single_task=false \
  --task_override="${TASK_OVERRIDE}" \
  --tokenizer_name_override="${TOKENIZER_PATH}" \
  --idle_publish_mode="${IDLE_PUBLISH_MODE}" \
  --arm_tau_mode="${ARM_TAU_MODE}" \
  --constant_target_duration_s="${CONSTANT_TARGET_DURATION_S}" \
  --post_action_shoulder_roll_nudge_rad="${POST_ACTION_SHOULDER_ROLL_NUDGE_RAD}" \
  --post_action_nudge_duration_s="${POST_ACTION_NUDGE_DURATION_S}" \
  --post_action_nudge_hold_s="${POST_ACTION_NUDGE_HOLD_S}" \
  --left_arm_ready_pose_deg="${LEFT_ARM_READY_POSE_DEG}" \
  --rtc_enabled="${RTC_ENABLED}" \
  --rtc_guidance_enabled="${RTC_GUIDANCE_ENABLED}" \
  --rtc_use_autograd_jacobian="${RTC_USE_AUTOGRAD_JACOBIAN}" \
  --rtc_execution_horizon="${RTC_EXECUTION_HORIZON}" \
  --rtc_max_guidance_weight="${RTC_MAX_GUIDANCE_WEIGHT}" \
  --rtc_prefix_attention_schedule="${RTC_PREFIX_ATTENTION_SCHEDULE}" \
  --rtc_queue_threshold="${RTC_QUEUE_THRESHOLD}" \
  --rtc_max_actions_during_inference="${RTC_MAX_ACTIONS_DURING_INFERENCE}" \
  --rtc_inference_timeout_s="${RTC_INFERENCE_TIMEOUT_S}" \
  --rtc_latency_window="${RTC_LATENCY_WINDOW}" \
  --rtc_snapshot_dir="${RTC_SNAPSHOT_DIR}" \
  --rtc_execution_log_path="${RTC_EXECUTION_LOG_PATH}" \
  --terminal_joint_detector_enabled="${TERMINAL_JOINT_DETECTOR_ENABLED}" \
  --terminal_joint_detector_config="${TERMINAL_JOINT_DETECTOR_CONFIG}" \
  --send_real_robot="${SEND_REAL_ROBOT}" \
  --arm_controller_process="${ARM_CONTROLLER_PROCESS}"
