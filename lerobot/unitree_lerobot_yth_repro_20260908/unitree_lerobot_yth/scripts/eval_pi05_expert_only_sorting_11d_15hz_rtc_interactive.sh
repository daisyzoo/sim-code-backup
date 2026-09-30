#!/usr/bin/env bash

# Interactive real-robot PI0.5 + RTC evaluation for the 15 Hz, 11-DoF
# dual-arm package-sorting task.
#
# Action/state order (from the dataset metadata):
#   left arm 5 + right arm 5 + waist yaw 1 = 11 DoF.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
LEROBOT_ROOT="${REPO_ROOT}/unitree_lerobot/lerobot"
CONDA_SH="${CONDA_SH:-/home/igs/miniconda3/etc/profile.d/conda.sh}"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-vla_eval}"

LOCAL_HF_HUB_CACHE="${LOCAL_HF_HUB_CACHE:-/home/igs/Desktop/project/vla/data/.hf_hub_cache}"
LOCAL_HF_HOME="${LOCAL_HF_HOME:-/media/igs/EAGET/syh/vla/cache/hf_home}"
LOCAL_HF_DATASETS_CACHE="${LOCAL_HF_DATASETS_CACHE:-/media/igs/EAGET/syh/vla/cache/hf_datasets}"
TOKENIZER_PATH="${TOKENIZER_PATH:-/home/igs/Desktop/project/vla/data/.hf_hub_cache/models--google--paligemma-3b-pt-224/snapshots/35e4f46485b4d07967e7e9935bc3786aad50687c}"

# The archive may be extracted directly into this directory, into a
# pretrained_model child, or with the normal checkpoints/last layout.
POLICY_PATH_INPUT="${POLICY_PATH:-/skydata/model/sorting_0828}"
POLICY_PATH=""
for candidate in \
  "${POLICY_PATH_INPUT}/pretrained_model" \
  "${POLICY_PATH_INPUT}/checkpoints/last/pretrained_model" \
  "${POLICY_PATH_INPUT}/checkpoints/last" \
  "${POLICY_PATH_INPUT}"; do
  if [[ -f "${candidate}/config.json" ]]; then
    POLICY_PATH="${candidate}"
    break
  fi
done
if [[ -z "${POLICY_PATH}" ]]; then
  POLICY_PATH="${POLICY_PATH_INPUT}"
fi

DATASET_REPO_ID="${DATASET_REPO_ID:-xr/pick_cup_sorting_0824}"
DATASET_ROOT="${DATASET_ROOT:-/skydata/syh/InternVLA-A-series/.cache/huggingface/lerobot/xr/pick_cup_sorting_0824}"
TASK_OVERRIDE="${TASK_OVERRIDE:-Sort packages: place black bags on the left and boxes on the right.}"

IMAGE_HOST="${IMAGE_HOST:-192.168.123.164}"
NETWORK_INTERFACE="${NETWORK_INTERFACE:-eno1}"
EPISODE_INDEX="${EPISODE_INDEX:-0}"
FREQUENCY="${FREQUENCY:-15}"
NUM_INFERENCE_STEPS="${PI05_NUM_INFERENCE_STEPS:-10}"
VISUALIZATION="${VISUALIZATION:-false}"

# Continuous rollout. Press q during execution to stop the current sorting run.
EPISODE_DURATION_S="${EPISODE_DURATION_S:-0}"
MAX_EPISODE_WALL_TIME_S="${MAX_EPISODE_WALL_TIME_S:-0}"
RUN_UNTIL_Q="${RUN_UNTIL_Q:-true}"
RETURN_TO_ZERO_DURATION_S="${RETURN_TO_ZERO_DURATION_S:-2}"
HANDOVER_WAIT_SECONDS="${HANDOVER_WAIT_SECONDS:-0.8}"
PRE_HANDOVER_WAIT_SECONDS="${PRE_HANDOVER_WAIT_SECONDS:-0.8}"
MOTION="${MOTION:-true}"
ARM_TAU_MODE="${ARM_TAU_MODE:-gravity}"
CONSTANT_TARGET_DURATION_S="${CONSTANT_TARGET_DURATION_S:-0}"
SEND_REAL_ROBOT="${SEND_REAL_ROBOT:-true}"
ARM_CONTROLLER_PROCESS="${ARM_CONTROLLER_PROCESS:-true}"
USE_DATASET="${USE_DATASET:-}"
if [[ -z "${USE_DATASET}" ]]; then
  if [[ "${SEND_REAL_ROBOT,,}" == "true" ]]; then
    USE_DATASET=false
  else
    USE_DATASET=true
  fi
fi

# Safety filtering for 10 arm joints followed by one waist joint. The five arm
# limits are mirrored because the dataset controls the same five joints on both sides.
ACTION_SMOOTHING_ENABLED="${ACTION_SMOOTHING_ENABLED:-true}"
ACTION_SMOOTHING_ARM_CUTOFF_HZ="${ACTION_SMOOTHING_ARM_CUTOFF_HZ:-1.5}"
ACTION_SMOOTHING_WAIST_CUTOFF_HZ="${ACTION_SMOOTHING_WAIST_CUTOFF_HZ:-1.0}"
ACTION_SMOOTHING_CHUNK_BLEND_FRAMES="${ACTION_SMOOTHING_CHUNK_BLEND_FRAMES:-5}"
ACTION_VELOCITY_LIMITS="${ACTION_VELOCITY_LIMITS:-0.90,0.50,0.80,1.20,1.50,0.90,0.50,0.80,1.20,1.50,0.18}"
ACTION_ACCELERATION_LIMITS="${ACTION_ACCELERATION_LIMITS:-4.00,2.50,3.50,5.00,8.00,4.00,2.50,3.50,5.00,8.00,0.80}"

RTC_ENABLED="${RTC_ENABLED:-true}"
RTC_GUIDANCE_ENABLED="${RTC_GUIDANCE_ENABLED:-true}"
RTC_USE_AUTOGRAD_JACOBIAN="${RTC_USE_AUTOGRAD_JACOBIAN:-true}"
RTC_EXECUTION_HORIZON="${RTC_EXECUTION_HORIZON:-25}"
RTC_MAX_GUIDANCE_WEIGHT="${RTC_MAX_GUIDANCE_WEIGHT:-10.0}"
RTC_PREFIX_ATTENTION_SCHEDULE="${RTC_PREFIX_ATTENTION_SCHEDULE:-exp}"
RTC_QUEUE_THRESHOLD="${RTC_QUEUE_THRESHOLD:-30}"
RTC_MAX_ACTIONS_DURING_INFERENCE="${RTC_MAX_ACTIONS_DURING_INFERENCE:-20}"
RTC_INFERENCE_TIMEOUT_S="${RTC_INFERENCE_TIMEOUT_S:-120}"
RTC_LATENCY_WINDOW="${RTC_LATENCY_WINDOW:-100}"
RTC_SNAPSHOT_DIR="${RTC_SNAPSHOT_DIR:-${REPO_ROOT}/outputs/rtc_inference_snapshots/pi05_sorting_11d_15hz}"
RTC_EXECUTION_LOG_PATH="${RTC_EXECUTION_LOG_PATH:-${REPO_ROOT}/outputs/rtc_execution_logs/pi05_sorting_11d_15hz_$(date +%Y%m%d_%H%M%S).jsonl}"

if [[ ! -f "${CONDA_SH}" ]]; then
  echo "Conda activation script does not exist: ${CONDA_SH}" >&2
  exit 1
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

if [[ ! -d "${DATASET_ROOT}" ]]; then
  echo "Dataset root does not exist: ${DATASET_ROOT}" >&2
  exit 1
fi
if [[ ! -f "${DATASET_ROOT}/meta/info.json" ]]; then
  echo "Dataset metadata does not exist: ${DATASET_ROOT}/meta/info.json" >&2
  exit 1
fi

# Refuse to drive the robot if the selected dataset does not have the exact
# state/action layout expected by this script.
DATASET_ROOT="${DATASET_ROOT}" python - <<'PY'
import json
import os
from pathlib import Path

info_path = Path(os.environ["DATASET_ROOT"]) / "meta" / "info.json"
info = json.loads(info_path.read_text(encoding="utf-8"))
expected = [
    "left_arm_0", "left_arm_1", "left_arm_2", "left_arm_3", "left_arm_4",
    "right_arm_0", "right_arm_1", "right_arm_2", "right_arm_3", "right_arm_4",
    "waist_yaw",
]
for feature_name in ("observation.state", "action"):
    feature = info.get("features", {}).get(feature_name, {})
    if feature.get("shape") != [11]:
        raise SystemExit(f"{feature_name} must have shape [11], got {feature.get('shape')}")
    names = feature.get("names", {}).get("motors")
    if names != expected:
        raise SystemExit(f"Unexpected {feature_name} motor order: {names}; expected: {expected}")
if float(info.get("fps", 0)) != 15.0:
    raise SystemExit(f"Dataset must be 15 Hz, got: {info.get('fps')}")
print("Dataset layout verified: left_arm5 + right_arm5 + waist1, 15 Hz")
PY

if [[ ! -d "${POLICY_PATH}" ]]; then
  echo "Policy directory does not exist yet: ${POLICY_PATH}" >&2
  echo "Extract the model under ${POLICY_PATH_INPUT}, or set POLICY_PATH explicitly." >&2
  exit 1
fi
for required_file in config.json policy_preprocessor.json policy_postprocessor.json; do
  if [[ ! -f "${POLICY_PATH}/${required_file}" ]]; then
    echo "Required checkpoint file does not exist: ${POLICY_PATH}/${required_file}" >&2
    exit 1
  fi
done
if [[ ! -f "${POLICY_PATH}/model.safetensors" && ! -f "${POLICY_PATH}/model.safetensors.index.json" ]]; then
  echo "No model.safetensors or model.safetensors.index.json found under: ${POLICY_PATH}" >&2
  exit 1
fi
if [[ ! -d "${TOKENIZER_PATH}" ]]; then
  echo "Tokenizer path does not exist: ${TOKENIZER_PATH}" >&2
  echo "Set TOKENIZER_PATH to the local PI0.5 tokenizer directory." >&2
  exit 1
fi

echo "Using policy path: ${POLICY_PATH}"
echo "Using dataset root: ${DATASET_ROOT}"
echo "Task: ${TASK_OVERRIDE}"
echo "Action layout: left_arm[0:5], right_arm[5:10], waist_yaw[10]"
echo "Camera rename: observation.images.cam_high -> observation.images.color_0"
echo "Interactive controls: at menu s=start q=quit; during execution q=stop current run"
echo "REAL ROBOT=${SEND_REAL_ROBOT} arm=G1_23 frequency=${FREQUENCY}Hz run_until_q=${RUN_UNTIL_Q} use_dataset=${USE_DATASET}"
echo "RTC enabled=${RTC_ENABLED} guidance_enabled=${RTC_GUIDANCE_ENABLED} autograd_jacobian=${RTC_USE_AUTOGRAD_JACOBIAN} horizon=${RTC_EXECUTION_HORIZON} queue_threshold=${RTC_QUEUE_THRESHOLD}"

EVAL_MODULE="unitree_lerobot.eval_robot.eval_g1_rtc"
if [[ "${PERSISTENT_DEBUG:-false}" == "true" ]]; then
  EVAL_MODULE="unitree_lerobot.eval_robot.persistent_rtc_debug"
fi
PERSISTENT_CONFIRM_AFTER_READY="${PERSISTENT_CONFIRM_AFTER_READY:-true}"

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
  --persistent_confirm_after_ready="${PERSISTENT_CONFIRM_AFTER_READY}" \
  --return_to_zero_duration_s="${RETURN_TO_ZERO_DURATION_S}" \
  --handover_wait_seconds="${HANDOVER_WAIT_SECONDS}" \
  --pre_handover_wait_seconds="${PRE_HANDOVER_WAIT_SECONDS}" \
  --arm=G1_23 \
  --ee='' \
  --image_host="${IMAGE_HOST}" \
  --network_interface="${NETWORK_INTERFACE}" \
  --motion="${MOTION}" \
  --visualization="${VISUALIZATION}" \
  --use_dataset="${USE_DATASET}" \
  --interactive_single_task=true \
  --task_override="${TASK_OVERRIDE}" \
  --tokenizer_name_override="${TOKENIZER_PATH}" \
  --rename_map='{"observation.images.cam_high":"observation.images.color_0"}' \
  --arm_tau_mode="${ARM_TAU_MODE}" \
  --constant_target_duration_s="${CONSTANT_TARGET_DURATION_S}" \
  --action_smoothing_enabled="${ACTION_SMOOTHING_ENABLED}" \
  --action_smoothing_arm_cutoff_hz="${ACTION_SMOOTHING_ARM_CUTOFF_HZ}" \
  --action_smoothing_waist_cutoff_hz="${ACTION_SMOOTHING_WAIST_CUTOFF_HZ}" \
  --action_smoothing_chunk_blend_frames="${ACTION_SMOOTHING_CHUNK_BLEND_FRAMES}" \
  --action_velocity_limits="${ACTION_VELOCITY_LIMITS}" \
  --action_acceleration_limits="${ACTION_ACCELERATION_LIMITS}" \
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
