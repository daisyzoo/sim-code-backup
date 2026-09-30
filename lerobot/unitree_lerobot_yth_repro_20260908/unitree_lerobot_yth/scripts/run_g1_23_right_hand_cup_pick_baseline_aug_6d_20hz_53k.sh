#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
VLA_ROOT="/media/igs/EAGET/syh/vla"

PREPARE_ALL_SCRIPT="${REPO_ROOT}/scripts/prepare_g1_23_right_hand_cup_pick_all_6d_20hz_dataset.sh"
PREPARE_WEIGHTED_SCRIPT="${REPO_ROOT}/scripts/prepare_weighted_multisource_json_dataset.py"
CONVERT_SCRIPT="${REPO_ROOT}/unitree_lerobot/utils/convert_unitree_json_to_lerobot.py"
TRAIN_SCRIPT="${REPO_ROOT}/scripts/train_pi05_lora_g1_23_6d_20hz_experiment.sh"

ACTION="${ACTION:-all}"           # prepare | train | all
EXPERIMENTS="${EXPERIMENTS:-all}" # all | baseline | resample_x1 or comma-separated
RUN_GROUP="${RUN_GROUP:-g1_23_right_hand_cup_pick_baseline_aug_6d_20hz_53k_$(date +%Y%m%d_%H%M%S)}"

SOURCE_ROOT="${SOURCE_ROOT:-/media/igs/EAGET/syh/dataset/cup_pick}"
OUTPUT_ROOT="${OUTPUT_ROOT:-${VLA_ROOT}/outputs}"
LOG_ROOT_BASE="${LOG_ROOT_BASE:-${VLA_ROOT}/experiment_logs}"
RUN_LOG_ROOT="${LOG_ROOT_BASE}/${RUN_GROUP}/orchestrator"

BASELINE_RAW_JSON_ROOT="${BASELINE_RAW_JSON_ROOT:-${REPO_ROOT}/data/raw/g1_23_right_hand_cup_pick_all_baseline_53k_6d_20hz_json}"
BASELINE_DATASET_REPO_ID="${BASELINE_DATASET_REPO_ID:-local/g1_23_right_hand_cup_pick_all_baseline_53k_rightarm5_waist1_6d_20hz}"
BASELINE_DATASET_ROOT="${BASELINE_DATASET_ROOT:-${REPO_ROOT}/data/local/g1_23_right_hand_cup_pick_all_baseline_53k_rightarm5_waist1_6d_20hz}"
BASELINE_JOB_NAME="${BASELINE_JOB_NAME:-pi05_lora_g1_23_right_hand_cup_pick_all_baseline_aug_6d_20hz_53k}"

RESAMPLE_SPEC_PATH="${RESAMPLE_SPEC_PATH:-${REPO_ROOT}/data/raw/g1_23_right_hand_cup_pick_resample_x1_extra_53k_6d_20hz_spec.generated.json}"
RESAMPLE_RAW_JSON_ROOT="${RESAMPLE_RAW_JSON_ROOT:-${REPO_ROOT}/data/raw/g1_23_right_hand_cup_pick_resample_x1_extra_53k_6d_20hz_json}"
RESAMPLE_DATASET_REPO_ID="${RESAMPLE_DATASET_REPO_ID:-local/g1_23_right_hand_cup_pick_resample_x1_extra_53k_rightarm5_waist1_6d_20hz}"
RESAMPLE_DATASET_ROOT="${RESAMPLE_DATASET_ROOT:-${REPO_ROOT}/data/local/g1_23_right_hand_cup_pick_resample_x1_extra_53k_rightarm5_waist1_6d_20hz}"
RESAMPLE_JOB_NAME="${RESAMPLE_JOB_NAME:-pi05_lora_g1_23_right_hand_cup_pick_resample_x1_extra_aug_6d_20hz_53k}"

GOAL="${GOAL:-Pick up the cup with the right hand.}"
DESC="${DESC:-Teach a right-hand cup pickup slot, then replay a smooth ready-to-slot motion and save one episode.}"
STEPS_TEXT="${STEPS_TEXT:-step1: move both arms to the ready pose; step2: grasp the cup with the right hand during teaching; step3: lift the cup and save the slot; step4: replay ready to slot and record the episode;}"

RESAMPLE_TARGET_DIRS="${RESAMPLE_TARGET_DIRS:-g1_23_right_hand_cup_pick_background_hold_cup,g1_23_right_hand_cup_pick_backgroud_hold,right_hand_cup_pick_blue_background}"

MEDIA_MODE="${MEDIA_MODE:-symlink}"
ROBOT_TYPE="${ROBOT_TYPE:-Unitree_G1_23Dof_RightArm5_Waist1}"

usage() {
  cat <<EOF
Usage:
  ${0}
  ACTION=prepare ${0}
  ACTION=train ${0}
  EXPERIMENTS=baseline,resample_x1 ${0}

Defaults:
  SOURCE_ROOT=${SOURCE_ROOT}
  BASELINE_DATASET_ROOT=${BASELINE_DATASET_ROOT}
  BASELINE_DATASET_REPO_ID=${BASELINE_DATASET_REPO_ID}
  RESAMPLE_DATASET_ROOT=${RESAMPLE_DATASET_ROOT}
  RESAMPLE_DATASET_REPO_ID=${RESAMPLE_DATASET_REPO_ID}
  PI05_TRAIN_STEPS=${PI05_TRAIN_STEPS:-53000}
  PI05_SAVE_FREQ=${PI05_SAVE_FREQ:-5000}
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || "${1:-}" == "help" ]]; then
  usage
  exit 0
fi

case "${ACTION}" in
  prepare|train|all) ;;
  *)
    echo "Unsupported ACTION=${ACTION}. Use prepare, train, or all." >&2
    usage >&2
    exit 1
    ;;
esac

mkdir -p "${REPO_ROOT}/data/raw" "${REPO_ROOT}/data/local" "${RUN_LOG_ROOT}" "${OUTPUT_ROOT}"

run_logged() {
  local experiment="$1"
  local step_name="$2"
  shift 2

  local log_dir="${RUN_LOG_ROOT}/${experiment}"
  local log_file="${log_dir}/${step_name}.log"
  mkdir -p "${log_dir}"

  echo "[$(date '+%F %T')] start ${experiment} ${step_name}" | tee -a "${log_file}"
  (
    set -euo pipefail
    "$@"
  ) 2>&1 | tee -a "${log_file}"
  echo "[$(date '+%F %T')] done ${experiment} ${step_name}" | tee -a "${log_file}"
}

should_run_experiment() {
  local experiment="$1"
  if [[ "${EXPERIMENTS}" == "all" ]]; then
    return 0
  fi
  [[ ",${EXPERIMENTS}," == *",${experiment},"* ]]
}

generate_resample_spec() {
  export SOURCE_ROOT RESAMPLE_SPEC_PATH RESAMPLE_RAW_JSON_ROOT MEDIA_MODE GOAL DESC STEPS_TEXT RESAMPLE_TARGET_DIRS
  "${PYTHON_BIN:-/home/igs/miniconda3/envs/unitree_lerobot/bin/python}" - <<'PY'
import json
import os
from pathlib import Path

source_root = Path(os.environ["SOURCE_ROOT"])
spec_path = Path(os.environ["RESAMPLE_SPEC_PATH"])
raw_json_root = Path(os.environ["RESAMPLE_RAW_JSON_ROOT"])
target_names = {name for name in os.environ["RESAMPLE_TARGET_DIRS"].split(",") if name}

if not source_root.is_dir():
    raise SystemExit(f"Source root does not exist: {source_root}")


def has_episode_data(path: Path) -> bool:
    return any(
        child.is_dir()
        and child.name.startswith("episode_")
        and (child / "data.json").is_file()
        for child in path.iterdir()
    )


source_dirs: list[Path] = []
if has_episode_data(source_root):
    source_dirs.append(source_root)

for child in sorted(source_root.iterdir()):
    if child.is_dir() and has_episode_data(child):
        source_dirs.append(child)

if not source_dirs:
    raise SystemExit(f"No episode directories found under {source_root}")

source_by_name = {path.name: path for path in source_dirs}
missing_targets = sorted(target_names - set(source_by_name))
if missing_targets:
    raise SystemExit(f"Resample target dirs were not found: {missing_targets}")

# Keep all source folders once, then add one extra copy of the selected folders.
weighted_source_dirs = source_dirs + [source_by_name[name] for name in sorted(target_names)]

spec = {
    "output_root": str(raw_json_root),
    "media_mode": os.environ["MEDIA_MODE"],
    "overwrite": True,
    "tasks": [
        {
            "name": "right_hand_cup_pick_resample_x1_extra_53k",
            "output_task_dir": "right_hand_cup_pick",
            "source_dirs": [str(path) for path in weighted_source_dirs],
            "goal": os.environ["GOAL"],
            "desc": os.environ["DESC"],
            "steps": os.environ["STEPS_TEXT"],
            "repeat": 1,
        }
    ],
}

spec_path.parent.mkdir(parents=True, exist_ok=True)
spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")

print(f"Wrote spec: {spec_path}")
print(f"Base source dirs: {len(source_dirs)}")
print(f"Weighted source dirs: {len(weighted_source_dirs)}")
for path in weighted_source_dirs:
    tag = " extra" if path.name in target_names and weighted_source_dirs.count(path) > 1 else ""
    print(f"  {path}{tag}")
PY
}

prepare_baseline() {
  env \
    SOURCE_ROOT="${SOURCE_ROOT}" \
    RAW_JSON_ROOT="${BASELINE_RAW_JSON_ROOT}" \
    DATASET_REPO_ID="${BASELINE_DATASET_REPO_ID}" \
    DATASET_ROOT="${BASELINE_DATASET_ROOT}" \
    ROBOT_TYPE="${ROBOT_TYPE}" \
    MEDIA_MODE="${MEDIA_MODE}" \
    REPEAT=1 \
    "${PREPARE_ALL_SCRIPT}"
}

prepare_resample_x1() {
  generate_resample_spec

  PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN:-/home/igs/miniconda3/envs/unitree_lerobot/bin/python}" "${PREPARE_WEIGHTED_SCRIPT}" \
    --spec-path "${RESAMPLE_SPEC_PATH}"

  PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN:-/home/igs/miniconda3/envs/unitree_lerobot/bin/python}" "${CONVERT_SCRIPT}" \
    --raw-dir "${RESAMPLE_RAW_JSON_ROOT}" \
    --repo-id "${RESAMPLE_DATASET_REPO_ID}" \
    --robot-type "${ROBOT_TYPE}" \
    --root "${RESAMPLE_DATASET_ROOT}"
}

train_dataset() {
  local dataset_repo_id="$1"
  local dataset_root="$2"
  local job_name="$3"

  env \
    DATASET_REPO_ID="${dataset_repo_id}" \
    DATASET_ROOT="${dataset_root}" \
    JOB_NAME="${job_name}" \
    RUN_GROUP="${RUN_GROUP}" \
    OUTPUT_ROOT="${OUTPUT_ROOT}" \
    LOG_ROOT_BASE="${LOG_ROOT_BASE}" \
    PI05_TRAIN_STEPS="${PI05_TRAIN_STEPS:-53000}" \
    PI05_SAVE_FREQ="${PI05_SAVE_FREQ:-5000}" \
    ACTION_NORM="${ACTION_NORM:-MIN_MAX}" \
    STATE_NORM="${STATE_NORM:-QUANTILES}" \
    VISUAL_NORM="${VISUAL_NORM:-IDENTITY}" \
    ENABLE_IMAGE_TRANSFORMS="${ENABLE_IMAGE_TRANSFORMS:-true}" \
    IMAGE_TRANSFORMS_MAX_NUM="${IMAGE_TRANSFORMS_MAX_NUM:-2}" \
    IMAGE_TRANSFORMS_RANDOM_ORDER="${IMAGE_TRANSFORMS_RANDOM_ORDER:-false}" \
    PI05_BATCH_SIZE="${PI05_BATCH_SIZE:-2}" \
    POLICY_DTYPE="${POLICY_DTYPE:-float32}" \
    POLICY_GRADIENT_CHECKPOINTING="${POLICY_GRADIENT_CHECKPOINTING:-false}" \
    POLICY_USE_AMP="${POLICY_USE_AMP:-false}" \
    PI05_LORA_TARGET_LANGUAGE_MODEL="${PI05_LORA_TARGET_LANGUAGE_MODEL:-true}" \
    PI05_LORA_TARGET_ACTION_EXPERT="${PI05_LORA_TARGET_ACTION_EXPERT:-true}" \
    LEROBOT_ENABLE_PER_TASK_LOSS_METRICS="${LEROBOT_ENABLE_PER_TASK_LOSS_METRICS:-false}" \
    "${TRAIN_SCRIPT}"
}

echo "run_group=${RUN_GROUP}"
echo "action=${ACTION}"
echo "experiments=${EXPERIMENTS}"
echo "source_root=${SOURCE_ROOT}"
echo "baseline_raw_json_root=${BASELINE_RAW_JSON_ROOT}"
echo "baseline_dataset_repo_id=${BASELINE_DATASET_REPO_ID}"
echo "baseline_dataset_root=${BASELINE_DATASET_ROOT}"
echo "resample_raw_json_root=${RESAMPLE_RAW_JSON_ROOT}"
echo "resample_dataset_repo_id=${RESAMPLE_DATASET_REPO_ID}"
echo "resample_dataset_root=${RESAMPLE_DATASET_ROOT}"
echo "output_root=${OUTPUT_ROOT}"
echo "log_root=${RUN_LOG_ROOT}"
echo "train_steps=${PI05_TRAIN_STEPS:-53000}"
echo "save_freq=${PI05_SAVE_FREQ:-5000}"
echo "image_transforms=${ENABLE_IMAGE_TRANSFORMS:-true}"
echo "per_task_loss_metrics=${LEROBOT_ENABLE_PER_TASK_LOSS_METRICS:-false}"

if should_run_experiment baseline; then
  if [[ "${ACTION}" == "prepare" || "${ACTION}" == "all" ]]; then
    run_logged baseline prepare prepare_baseline
  fi
  if [[ "${ACTION}" == "train" || "${ACTION}" == "all" ]]; then
    run_logged baseline train train_dataset \
      "${BASELINE_DATASET_REPO_ID}" \
      "${BASELINE_DATASET_ROOT}" \
      "${BASELINE_JOB_NAME}"
  fi
fi

if should_run_experiment resample_x1; then
  if [[ "${ACTION}" == "prepare" || "${ACTION}" == "all" ]]; then
    run_logged resample_x1 prepare prepare_resample_x1
  fi
  if [[ "${ACTION}" == "train" || "${ACTION}" == "all" ]]; then
    run_logged resample_x1 train train_dataset \
      "${RESAMPLE_DATASET_REPO_ID}" \
      "${RESAMPLE_DATASET_ROOT}" \
      "${RESAMPLE_JOB_NAME}"
  fi
fi
