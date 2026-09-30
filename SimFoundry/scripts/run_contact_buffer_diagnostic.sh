#!/usr/bin/env bash
set -Eeuo pipefail
WORKSPACE=/home/user/Documents/zoo/sim
ROOT="$WORKSPACE/SimFoundry"
OUT="$ROOT/demo/contact_buffer_diagnostic_20260928_r1"
[[ ! -e "$OUT/expert" && ! -e "$OUT/model_seed0" ]] || { echo 'Refusing overwrite' >&2; exit 1; }
source /home/user/miniconda3/etc/profile.d/conda.sh
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1 PYTHONUNBUFFERED=1
cd "$WORKSPACE/IsaacLab"
./isaaclab.sh -p "$ROOT/scripts/collect_paired_sorting.py" --device cuda --viz none --newton-contacts --role diagnostic --layout-start 20 --layouts 1 --wait-episodes 0 --steps 160 --trace-episode-contacts --out-dir "$OUT/expert" > "$OUT/expert.log" 2>&1
PI05_LOCAL_CONFIG="$ROOT/scripts/pi05_paired_ordinary_pilot40_20260928.env" PI05_POLICY_PATH="$(cat "$ROOT/demo/recovery_comparison_20260928_r1/checkpoint_ordinary.txt")" PI05_RECORD_DIR="$OUT/model_seed0" PI05_EVAL_SEED=0 PI05_PROMPT_VARIANT=short bash "$ROOT/scripts/run_pi05_paired_sim.sh" --layout-start 20 --layouts 1 --wait-episodes 0 --trace-episode-contacts --policy-max-action-step 0 > "$OUT/model.log" 2>&1
