#!/usr/bin/env bash

# Real-robot, single-task PI0.5 evaluation for the 2026-08-06 15 Hz cup-pick
# checkpoint. Uses the existing LeRobot-aligned RTC runtime in this repository;
# it does not enable the paper-faithful full-Jacobian variant discussed later.
set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot_yth"
LEROBOT_ROOT="${REPO_ROOT}/unitree_lerobot/lerobot"
CONDA_SH="/home/igs/miniconda3/etc/profile.d/conda.sh"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-vla_eval}"

LOCAL_HF_HUB_CACHE="${LOCAL_HF_HUB_CACHE:-/home/igs/Desktop/project/vla/data/.hf_hub_cache}"
LOCAL_HF_HOME="${LOCAL_HF_HOME:-/media/igs/EAGET/syh/vla/cache/hf_home}"
LOCAL_HF_DATASETS_CACHE="${LOCAL_HF_DATASETS_CACHE:-/media/igs/EAGET/syh/vla/cache/hf_datasets}"
TOKENIZER_PATH="${TOKENIZER_PATH:-/media/igs/EAGET/syh/train_output/tokenizer}"

# Default model switched on 2026-09-02:
# - PI0.5 expert-only, FP32, 20,000 training steps;
# - trained with the expanded 0804-0805 + 0813 + 0817 cup-pick dataset;
# - 6-DoF layout: right arm 5 + waist yaw 1.
# Previous default (kept here for an explicit POLICY_PATH rollback):
# /media/igs/EAGET/syh/vla/outputs/pi05_expert_only_pick_up_6d_15hz_0804_0805_20260806_151401/checkpoints/last
POLICY_PATH_DEFAULT="/media/igs/EAGET/syh/vla/outputs/iwork_train_pi05_expert_only_pick_cup_6d_15hz_0804_0805_0813_0817_fp32"
POLICY_PATH_INPUT="${POLICY_PATH:-${POLICY_PATH_DEFAULT}}"
if [[ -d "${POLICY_PATH_INPUT}/pretrained_model" ]]; then
  POLICY_PATH="${POLICY_PATH_INPUT}/pretrained_model"
else
  POLICY_PATH="${POLICY_PATH_INPUT}"
fi

DATASET_REPO_ID="${DATASET_REPO_ID:-local/lerobot_pick_up_15hz_0804_0805_0813_0817}"
DATASET_ROOT="${DATASET_ROOT:-/media/igs/EAGET/syh/dataset/xr_data/lerobot_pick_up_15hz_0804_0805_0813_0817}"
TASK_OVERRIDE="${TASK_OVERRIDE:-Pick up the cup with the right hand.}"

IMAGE_HOST="${IMAGE_HOST:-192.168.123.164}"
NETWORK_INTERFACE="${NETWORK_INTERFACE:-eno1}"
EPISODE_INDEX="${EPISODE_INDEX:-0}"
FREQUENCY="${FREQUENCY:-15}"
NUM_INFERENCE_STEPS="${PI05_NUM_INFERENCE_STEPS:-10}"
VISUALIZATION="${VISUALIZATION:-false}"

# Continuous RTC rollout: neither action count nor wall time ends the run.
# The operator's runtime q is the normal stop condition.
EPISODE_DURATION_S="${EPISODE_DURATION_S:-0}"
MAX_EPISODE_WALL_TIME_S="${MAX_EPISODE_WALL_TIME_S:-0}"
RETURN_TO_ZERO_DURATION_S="${RETURN_TO_ZERO_DURATION_S:-2}"
HANDOVER_WAIT_SECONDS="${HANDOVER_WAIT_SECONDS:-0.8}"
PRE_HANDOVER_WAIT_SECONDS="${PRE_HANDOVER_WAIT_SECONDS:-0.8}"
MOTION="${MOTION:-true}"
ARM_TAU_MODE="${ARM_TAU_MODE:-gravity}"
CONSTANT_TARGET_DURATION_S="${CONSTANT_TARGET_DURATION_S:-0}"
# Final 6-DoF command smoothing and rate limiting. Set false to reproduce the
# unfiltered policy-action path without changing any other RTC setting.
ACTION_SMOOTHING_ENABLED="${ACTION_SMOOTHING_ENABLED:-true}"
ACTION_SMOOTHING_ARM_CUTOFF_HZ="${ACTION_SMOOTHING_ARM_CUTOFF_HZ:-1.5}"
ACTION_SMOOTHING_WAIST_CUTOFF_HZ="${ACTION_SMOOTHING_WAIST_CUTOFF_HZ:-1.0}"
ACTION_SMOOTHING_CHUNK_BLEND_FRAMES="${ACTION_SMOOTHING_CHUNK_BLEND_FRAMES:-5}"
ACTION_VELOCITY_LIMITS="${ACTION_VELOCITY_LIMITS:-0.90,0.50,0.80,1.20,1.50,0.18}"
ACTION_ACCELERATION_LIMITS="${ACTION_ACCELERATION_LIMITS:-4.00,2.50,3.50,5.00,8.00,0.80}"
SEND_REAL_ROBOT="${SEND_REAL_ROBOT:-true}"
ARM_CONTROLLER_PROCESS="${ARM_CONTROLLER_PROCESS:-true}"
LEFT_ARM_READY_POSE_DEG="${LEFT_ARM_READY_POSE_DEG:-0,0,14,0,0}"
USE_DATASET="${USE_DATASET:-}"
if [[ -z "${USE_DATASET}" ]]; then
  if [[ "${SEND_REAL_ROBOT,,}" == "true" ]]; then
    USE_DATASET=false
  else
    USE_DATASET=true
  fi
fi

# Keep the RTC horizon beyond the actions that can execute during inference.
# At 15 Hz, a 20-frame execution cap is ~1.33 s; horizon=25 leaves a five-frame
# exponential guidance tail for the newly generated actions that actually take
# over after the inferred-delay prefix is discarded.
RTC_ENABLED="${RTC_ENABLED:-true}"
# Set false for the async-chunking-only ablation: retain the action queue and
# consumed-frame handover, but bypass all RTC flow-matching/Jacobian guidance.
RTC_GUIDANCE_ENABLED="${RTC_GUIDANCE_ENABLED:-true}"
RTC_USE_AUTOGRAD_JACOBIAN="${RTC_USE_AUTOGRAD_JACOBIAN:-true}"
RTC_EXECUTION_HORIZON="${RTC_EXECUTION_HORIZON:-25}"
RTC_MAX_GUIDANCE_WEIGHT="${RTC_MAX_GUIDANCE_WEIGHT:-10.0}"
RTC_PREFIX_ATTENTION_SCHEDULE="${RTC_PREFIX_ATTENTION_SCHEDULE:-exp}"
RTC_QUEUE_THRESHOLD="${RTC_QUEUE_THRESHOLD:-30}"
RTC_MAX_ACTIONS_DURING_INFERENCE="${RTC_MAX_ACTIONS_DURING_INFERENCE:-20}"
RTC_INFERENCE_TIMEOUT_S="${RTC_INFERENCE_TIMEOUT_S:-120}"
RTC_LATENCY_WINDOW="${RTC_LATENCY_WINDOW:-100}"
RTC_SNAPSHOT_DIR="${RTC_SNAPSHOT_DIR:-${REPO_ROOT}/outputs/rtc_inference_snapshots/pi05_expert_only_pick_up_15hz}"
RTC_EXECUTION_LOG_PATH="${RTC_EXECUTION_LOG_PATH:-${REPO_ROOT}/outputs/rtc_execution_logs/pi05_expert_only_pick_up_15hz_$(date +%Y%m%d_%H%M%S).jsonl}"

# With RTC disabled, PI0.5 uses its native synchronous action queue: block for
# one inference, execute its 50 actions, then block again for the next chunk.
# ``RUN_UNTIL_Q=true`` keeps this loop running until the operator presses q.
RUN_UNTIL_Q="${RUN_UNTIL_Q:-true}"
SYNC_EPISODE_DURATION_S="${SYNC_EPISODE_DURATION_S:-60}"
if [[ "${RTC_ENABLED,,}" != "true" && "${RUN_UNTIL_Q,,}" != "true" ]]; then
  if [[ "${EPISODE_DURATION_S}" == "0" || "${EPISODE_DURATION_S}" == "0.0" ]]; then
    EPISODE_DURATION_S="${SYNC_EPISODE_DURATION_S}"
  fi
  echo "RTC is disabled: using native synchronous chunks for ${EPISODE_DURATION_S}s; each chunk is inferred while holding the last target, then all 50 actions execute at ${FREQUENCY}Hz."
elif [[ "${RTC_ENABLED,,}" != "true" ]]; then
  echo "RTC is disabled: running native synchronous chunks continuously; press q to stop the current run."
fi

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

echo "Using policy path: ${POLICY_PATH}"
echo "Using dataset root: ${DATASET_ROOT}"
echo "Task: ${TASK_OVERRIDE}"
echo "Interactive controls: at menu s=start q=quit; during execution q=stop current run"
echo "REAL ROBOT=${SEND_REAL_ROBOT} arm_controller_process=${ARM_CONTROLLER_PROCESS} frequency=${FREQUENCY}Hz run_until_q=${RUN_UNTIL_Q} episode_duration_s=${EPISODE_DURATION_S} use_dataset=${USE_DATASET}"
echo "Action smoothing enabled=${ACTION_SMOOTHING_ENABLED} arm_cutoff=${ACTION_SMOOTHING_ARM_CUTOFF_HZ}Hz waist_cutoff=${ACTION_SMOOTHING_WAIST_CUTOFF_HZ}Hz blend_frames=${ACTION_SMOOTHING_CHUNK_BLEND_FRAMES} velocity_limits=${ACTION_VELOCITY_LIMITS} acceleration_limits=${ACTION_ACCELERATION_LIMITS}"
echo "RTC enabled=${RTC_ENABLED} guidance_enabled=${RTC_GUIDANCE_ENABLED} autograd_jacobian=${RTC_USE_AUTOGRAD_JACOBIAN} horizon=${RTC_EXECUTION_HORIZON} guidance=${RTC_MAX_GUIDANCE_WEIGHT} schedule=${RTC_PREFIX_ATTENTION_SCHEDULE} queue_threshold=${RTC_QUEUE_THRESHOLD} max_actions_during_inference=${RTC_MAX_ACTIONS_DURING_INFERENCE}"
echo "RTC inference snapshots: ${RTC_SNAPSHOT_DIR}"
echo "RTC per-frame execution log: ${RTC_EXECUTION_LOG_PATH}"

EVAL_MODULE="unitree_lerobot.eval_robot.eval_g1_rtc"
if [[ "${PERSISTENT_DEBUG:-false}" == "true" ]]; then
  EVAL_MODULE="unitree_lerobot.eval_robot.persistent_rtc_debug"
fi

PYTHONNOUSERSITE=1 python -m "${EVAL_MODULE}" \
  --policy.path="${POLICY_PATH}" \
  --policy.num_inference_steps="${NUM_INFERENCE_STEPS}" \
  --repo_id="${DATASET_REPO_ID}" \
  --root="${DATASET_ROOT}" \
  --episodes="${EPISODE_INDEX}" \
  --frequency="${FREQUENCY}" \
  --episode_duration_s="${EPISODE_DURATION_S}" \
  --max_episode_wall_time_s="${MAX_EPISODE_WALL_TIME_S}" \
  --run_until_q="${RUN_UNTIL_Q}" \
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
  --interactive_single_task=true \
  --task_override="${TASK_OVERRIDE}" \
  --tokenizer_name_override="${TOKENIZER_PATH}" \
  --arm_tau_mode="${ARM_TAU_MODE}" \
  --constant_target_duration_s="${CONSTANT_TARGET_DURATION_S}" \
  --action_smoothing_enabled="${ACTION_SMOOTHING_ENABLED}" \
  --action_smoothing_arm_cutoff_hz="${ACTION_SMOOTHING_ARM_CUTOFF_HZ}" \
  --action_smoothing_waist_cutoff_hz="${ACTION_SMOOTHING_WAIST_CUTOFF_HZ}" \
  --action_smoothing_chunk_blend_frames="${ACTION_SMOOTHING_CHUNK_BLEND_FRAMES}" \
  --action_velocity_limits="${ACTION_VELOCITY_LIMITS}" \
  --action_acceleration_limits="${ACTION_ACCELERATION_LIMITS}" \
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
  --send_real_robot="${SEND_REAL_ROBOT}" \
  --arm_controller_process="${ARM_CONTROLLER_PROCESS}"
