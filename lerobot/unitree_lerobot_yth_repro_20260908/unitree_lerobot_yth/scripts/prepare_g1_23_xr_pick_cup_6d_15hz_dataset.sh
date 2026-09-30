#!/usr/bin/env bash

# Prepare the flat XR pick-cup recordings and convert them to a LeRobot dataset.
#
# Source data is never modified. One or more source directories are merged into
# one prepared dataset, then converted into one LeRobot dataset. The preparation stage:
#   1. rewrites the incorrect "pick up cube" task text;
#   2. wraps episodes in the task/episode layout expected by the converter;
#   3. renumbers all episodes from episode_0000;
#   4. preserves the recorded 15 Hz sampling rate.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

PYTHON_BIN="${PYTHON_BIN:-/home/igs/miniconda3/envs/unitree_lerobot/bin/python}"
# For a multi-directory merge, set SOURCE_ROOTS as a colon-separated list, e.g.
# SOURCE_ROOTS="/data/pick_cup_0804:/data/pick_cup_0805". SOURCE_ROOT remains
# supported for the original single-directory invocation.
SOURCE_ROOT="${SOURCE_ROOT:-/media/igs/EAGET/syh/dataset/xr_data/pick_cup}"
SOURCE_ROOTS="${SOURCE_ROOTS:-}"

SPEC_PATH="${SPEC_PATH:-${REPO_ROOT}/data/raw/g1_23_xr_pick_cup_6d_15hz_spec.generated.json}"
RAW_JSON_ROOT="${RAW_JSON_ROOT:-${REPO_ROOT}/data/raw/g1_23_xr_pick_cup_6d_15hz_json}"
DATASET_REPO_ID="${DATASET_REPO_ID:-local/g1_23_xr_pick_cup_rightarm5_waist1_6d_15hz}"
DATASET_ROOT="${DATASET_ROOT:-/media/igs/EAGET/syh/dataset/lerobot/g1_23_xr_pick_cup_rightarm5_waist1_6d_15hz}"

ROBOT_TYPE="${ROBOT_TYPE:-Unitree_G1_23Dof_RightArm5_Waist1}"
TASK_DIR="${TASK_DIR:-right_hand_cup_pick}"
MEDIA_MODE="${MEDIA_MODE:-symlink}"
DATA_MODE="${DATA_MODE:-video}"
PREPARE_ONLY="${PREPARE_ONLY:-false}"

GOAL="${GOAL:-Pick up the cup with the right hand.}"
DESC="${DESC:-Use the right hand to approach, grasp, and lift the cup.}"
STEPS_TEXT="${STEPS_TEXT:-step1: approach the cup with the right hand; step2: grasp the cup; step3: lift the cup.}"

PREPARE_SCRIPT="${REPO_ROOT}/scripts/prepare_weighted_multisource_json_dataset.py"
CONVERT_SCRIPT="${REPO_ROOT}/unitree_lerobot/utils/convert_unitree_json_to_lerobot.py"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Python executable does not exist or is not executable: ${PYTHON_BIN}" >&2
  exit 1
fi
if [[ ! -f "${PREPARE_SCRIPT}" || ! -f "${CONVERT_SCRIPT}" ]]; then
  echo "Preparation or conversion script is missing under: ${REPO_ROOT}" >&2
  exit 1
fi
if [[ "${MEDIA_MODE}" != "symlink" && "${MEDIA_MODE}" != "copy" ]]; then
  echo "MEDIA_MODE must be 'symlink' or 'copy', got: ${MEDIA_MODE}" >&2
  exit 1
fi
if [[ "${DATA_MODE}" != "video" && "${DATA_MODE}" != "image" ]]; then
  echo "DATA_MODE must be 'video' or 'image', got: ${DATA_MODE}" >&2
  exit 1
fi

mkdir -p "$(dirname -- "${SPEC_PATH}")" "$(dirname -- "${RAW_JSON_ROOT}")" "$(dirname -- "${DATASET_ROOT}")"

export SOURCE_ROOT SOURCE_ROOTS SPEC_PATH RAW_JSON_ROOT MEDIA_MODE TASK_DIR
export GOAL DESC STEPS_TEXT
"${PYTHON_BIN}" - <<'PY'
import json
import os
from pathlib import Path

source_roots_value = os.environ.get("SOURCE_ROOTS", "").strip()
source_roots = [
    Path(value).expanduser().resolve()
    for value in source_roots_value.split(":")
    if value.strip()
]
if not source_roots:
    source_roots = [Path(os.environ["SOURCE_ROOT"]).expanduser().resolve()]

if len(set(source_roots)) != len(source_roots):
    raise SystemExit(f"Duplicate source directory supplied: {source_roots}")

spec_path = Path(os.environ["SPEC_PATH"]).expanduser().resolve()
raw_json_root = Path(os.environ["RAW_JSON_ROOT"]).expanduser().resolve()

fps_values = set()
source_episode_counts = []
total_episodes = 0
for source_root in source_roots:
    if not source_root.is_dir():
        raise SystemExit(f"Source root does not exist: {source_root}")

    episode_dirs = sorted(
        path
        for path in source_root.glob("episode_*")
        if path.is_dir() and (path / "data.json").is_file()
    )
    if not episode_dirs:
        raise SystemExit(f"No episode_*/data.json files found under: {source_root}")

    for episode_dir in episode_dirs:
        payload = json.loads((episode_dir / "data.json").read_text(encoding="utf-8"))
        fps_values.add(float(payload.get("info", {}).get("image", {}).get("fps")))

    source_episode_counts.append((source_root, len(episode_dirs)))
    total_episodes += len(episode_dirs)

if fps_values != {15.0}:
    raise SystemExit(f"Expected this dataset to be uniformly 15 Hz, found: {sorted(fps_values)}")

spec = {
    "output_root": str(raw_json_root),
    "media_mode": os.environ["MEDIA_MODE"],
    "overwrite": True,
    "tasks": [
        {
            "name": "g1_23_xr_right_hand_cup_pick",
            "output_task_dir": os.environ["TASK_DIR"],
            "source_dirs": [str(source_root) for source_root in source_roots],
            "goal": os.environ["GOAL"],
            "desc": os.environ["DESC"],
            "steps": os.environ["STEPS_TEXT"],
            "repeat": 1,
        }
    ],
}

spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote generated spec: {spec_path}")
for source_root, episode_count in source_episode_counts:
    print(f"Source: {source_root} ({episode_count} episodes)")
print(f"Source directories:    {len(source_roots)}")
print(f"Source episodes:       {total_episodes}")
print(f"Prepared episodes:     {total_episodes}")
print(f"Recorded FPS:          {next(iter(fps_values))}")
PY

echo "Preparing relabeled Unitree JSON dataset..."
PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" "${PREPARE_SCRIPT}" \
  --spec-path "${SPEC_PATH}"

if [[ "${PREPARE_ONLY,,}" =~ ^(1|true|yes|on)$ ]]; then
  echo "PREPARE_ONLY=${PREPARE_ONLY}; skipping LeRobot conversion."
  echo "Prepared JSON root: ${RAW_JSON_ROOT}"
  exit 0
fi

echo "Converting prepared data to LeRobot (${ROBOT_TYPE}, ${DATA_MODE}, 15 Hz)..."
PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" "${CONVERT_SCRIPT}" \
  --raw-dir "${RAW_JSON_ROOT}" \
  --repo-id "${DATASET_REPO_ID}" \
  --robot-type "${ROBOT_TYPE}" \
  --root "${DATASET_ROOT}" \
  --mode "${DATA_MODE}"

if [[ ! -f "${DATASET_ROOT}/meta/info.json" ]]; then
  echo "Conversion finished but meta/info.json was not found: ${DATASET_ROOT}" >&2
  exit 1
fi

echo "LeRobot dataset ready:"
echo "  repo_id: ${DATASET_REPO_ID}"
echo "  root:    ${DATASET_ROOT}"
echo "  robot:   ${ROBOT_TYPE}"
echo "  fps:     15"
