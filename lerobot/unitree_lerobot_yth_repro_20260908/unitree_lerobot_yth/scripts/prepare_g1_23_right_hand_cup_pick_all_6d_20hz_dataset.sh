#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
PYTHON_BIN="${PYTHON_BIN:-/home/igs/miniconda3/envs/unitree_lerobot/bin/python}"

PREPARE_SCRIPT="${REPO_ROOT}/scripts/prepare_weighted_multisource_json_dataset.py"
CONVERT_SCRIPT="${REPO_ROOT}/unitree_lerobot/utils/convert_unitree_json_to_lerobot.py"

SOURCE_ROOT="${SOURCE_ROOT:-/media/igs/EAGET/syh/dataset/cup_pick}"
SPEC_PATH="${SPEC_PATH:-${REPO_ROOT}/data/raw/g1_23_right_hand_cup_pick_all_6d_20hz_spec.generated.json}"
RAW_JSON_ROOT="${RAW_JSON_ROOT:-${REPO_ROOT}/data/raw/g1_23_right_hand_cup_pick_all_6d_20hz_json}"
DATASET_REPO_ID="${DATASET_REPO_ID:-local/g1_23_right_hand_cup_pick_all_rightarm5_waist1_6d_20hz}"
DATASET_ROOT="${DATASET_ROOT:-${REPO_ROOT}/data/local/g1_23_right_hand_cup_pick_all_rightarm5_waist1_6d_20hz}"
ROBOT_TYPE="${ROBOT_TYPE:-Unitree_G1_23Dof_RightArm5_Waist1}"
MEDIA_MODE="${MEDIA_MODE:-symlink}"
REPEAT="${REPEAT:-1}"

GOAL="${GOAL:-Pick up the cup with the right hand.}"
DESC="${DESC:-Teach a right-hand cup pickup slot, then replay a smooth ready-to-slot motion and save one episode.}"
STEPS_TEXT="${STEPS_TEXT:-step1: move both arms to the ready pose; step2: grasp the cup with the right hand during teaching; step3: lift the cup and save the slot; step4: replay ready to slot and record the episode;}"

mkdir -p "${REPO_ROOT}/data/raw" "${REPO_ROOT}/data/local" "$(dirname "${SPEC_PATH}")"

if [[ ! -d "${SOURCE_ROOT}" ]]; then
  echo "Source root does not exist: ${SOURCE_ROOT}" >&2
  exit 1
fi

export SOURCE_ROOT SPEC_PATH RAW_JSON_ROOT MEDIA_MODE REPEAT GOAL DESC STEPS_TEXT
"${PYTHON_BIN}" - <<'PY'
import json
import os
from pathlib import Path

source_root = Path(os.environ["SOURCE_ROOT"])
spec_path = Path(os.environ["SPEC_PATH"])
raw_json_root = Path(os.environ["RAW_JSON_ROOT"])


def has_episode_data(path: Path) -> bool:
    return any(child.is_dir() and child.name.startswith("episode_") and (child / "data.json").is_file() for child in path.iterdir())


source_dirs: list[Path] = []
if has_episode_data(source_root):
    source_dirs.append(source_root)

for child in sorted(source_root.iterdir()):
    if child.is_dir() and has_episode_data(child):
        source_dirs.append(child)

if not source_dirs:
    raise SystemExit(f"No episode directories found under {source_root}")

spec = {
    "output_root": str(raw_json_root),
    "media_mode": os.environ["MEDIA_MODE"],
    "overwrite": True,
    "tasks": [
        {
            "name": "right_hand_cup_pick_all",
            "output_task_dir": "right_hand_cup_pick",
            "source_dirs": [str(path) for path in source_dirs],
            "goal": os.environ["GOAL"],
            "desc": os.environ["DESC"],
            "steps": os.environ["STEPS_TEXT"],
            "repeat": int(os.environ["REPEAT"]),
        }
    ],
}

spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
print(f"Wrote spec: {spec_path}")
print(f"Discovered source dirs: {len(source_dirs)}")
for path in source_dirs:
    print(f"  {path}")
PY

PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" "${PREPARE_SCRIPT}" \
  --spec-path "${SPEC_PATH}"

PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" "${CONVERT_SCRIPT}" \
  --raw-dir "${RAW_JSON_ROOT}" \
  --repo-id "${DATASET_REPO_ID}" \
  --robot-type "${ROBOT_TYPE}" \
  --root "${DATASET_ROOT}"
