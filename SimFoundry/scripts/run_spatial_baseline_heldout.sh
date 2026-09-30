#!/usr/bin/env bash
set -Eeuo pipefail
WORKSPACE=/home/user/Documents/zoo/sim
ROOT="$WORKSPACE/SimFoundry"
RUN="$ROOT/demo/spatial_generalization_20260928_r1"
OUT="$ROOT/demo/spatial_baseline_heldout_20260928_r1"
CP="$WORKSPACE/lerobot/outputs/paired_ordinary_pilot40_20260928/package_sorting_pi05_1gpu_20260928_102242/checkpoints/last/pretrained_model"
[[ ! -e "$OUT" ]]
mkdir "$OUT"
status() { python3 - "$OUT/STATUS.json" "$1" <<'PY'
import sys,json,datetime
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':sys.argv[2],'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'visual_review':'pending','goal_complete':False},indent=2))
PY
}
trap 'status failed_runtime_or_artifact' ERR
/home/user/Desktop/project/vla/env/.venv/bin/python "$ROOT/scripts/audit_checkpoint_training_stats.py" --checkpoint "$CP" --dataset "$WORKSPACE/lerobot/lerobot_sim_paired_ordinary_pilot40_20260928" --out "$OUT/CHECKPOINT_STATS.json"
roots=()
for seed in 0 1 2; do
 status "evaluating_seed${seed}"
 dir="$OUT/seed${seed}"
 PI05_LOCAL_CONFIG="$ROOT/scripts/pi05_paired_ordinary_pilot40_20260928.env" PI05_POLICY_PATH="$CP" PI05_RECORD_DIR="$dir" PI05_EVAL_SEED="$seed" PI05_POLICY_PORT=18775 PI05_SPATIAL_PROTOCOL="$RUN/heldout_protocol.json" \
  bash "$ROOT/scripts/run_pi05_spatial_sim.sh" > "$OUT/seed${seed}.log" 2>&1
 for lid in 58000 58001 58002 58003 58004 58005; do roots+=("$dir/layout_$lid"); done
 roots+=("$dir/wait")
done
python3 "$ROOT/scripts/summarize_paired_evaluation.py" --roots "${roots[@]}" --output "$OUT/EVALUATION.json"
status numeric_complete_actual_visual_review_required
