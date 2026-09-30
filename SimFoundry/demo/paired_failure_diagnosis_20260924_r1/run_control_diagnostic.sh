#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=/home/user/Documents/zoo/sim/SimFoundry
EXPERIMENT="$ROOT/demo/paired_zero_ab_experiment_20260924_r1"
OUT="$ROOT/demo/paired_failure_diagnosis_20260924_r1"
POLICY="$(cat "$EXPERIMENT/checkpoint_b.txt")"
for mode in raw slew055; do
 cap=0
 if [[ "$mode" == slew055 ]]; then cap=.055; fi
 PI05_LOCAL_CONFIG="$ROOT/scripts/pi05_paired_pilot32_b_20260924.env" PI05_POLICY_PATH="$POLICY" PI05_RECORD_DIR="$OUT/validation20_${mode}_seed0" PI05_EVAL_SEED=0 PI05_PROMPT_VARIANT=short bash "$ROOT/scripts/run_pi05_paired_sim.sh" --layout-start 20 --layouts 1 --wait-episodes 1 --wait-layout-start 10006 --policy-max-action-step "$cap" > "$OUT/validation20_${mode}_seed0.log" 2>&1
done
