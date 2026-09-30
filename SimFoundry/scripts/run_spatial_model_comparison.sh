#!/usr/bin/env bash
# Frozen h10 comparison. Completion means numeric artifacts exist; image review is separate.
set -Eeuo pipefail
WORKSPACE=/home/user/Documents/zoo/sim
ROOT="$WORKSPACE/SimFoundry"
RUN="$ROOT/demo/spatial_generalization_20260928_r1"
OUT="$ROOT/demo/spatial_model_comparison_20260928_r1"
OLD="$WORKSPACE/lerobot/outputs/paired_ordinary_pilot40_20260928/package_sorting_pi05_1gpu_20260928_102242/checkpoints/last/pretrained_model"
NEW="$(cat "$RUN/checkpoint.txt")"
[[ -f "$OLD/model.safetensors" && -f "$NEW/model.safetensors" ]]
[[ ! -e "$OUT" ]]
mkdir "$OUT"
status() { python3 - "$OUT/STATUS.json" "$1" <<'CHECK'
import sys,json,datetime
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':sys.argv[2],'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'visual_review':'pending','goal_complete':False},indent=2))
CHECK
}
trap 'status runtime_or_artifact_failure' ERR
for model in spatial; do
 if [[ "$model" == spatial ]]; then cp="$NEW"; else cp="$OLD"; fi
 cfg="$ROOT/scripts/pi05_paired_${model}_pilot40_20260928.env"
 /home/user/Desktop/project/vla/env/.venv/bin/python "$ROOT/scripts/audit_checkpoint_training_stats.py" --checkpoint "$cp" --dataset "$WORKSPACE/lerobot/lerobot_sim_paired_${model}_pilot40_20260928" --out "$OUT/CHECKPOINT_STATS_${model}.json"
 eval_roots=()
 for seed in 0 1 2; do
  status "evaluating_${model}_spatial_seed${seed}"
  dir="$OUT/${model}_spatial_seed${seed}"
  PI05_LOCAL_CONFIG="$cfg" PI05_POLICY_PATH="$cp" PI05_RECORD_DIR="$dir" PI05_EVAL_SEED="$seed" PI05_SPATIAL_PROTOCOL="$RUN/heldout_protocol.json" \
   bash "$ROOT/scripts/run_pi05_spatial_sim.sh" > "$OUT/${model}_spatial_seed${seed}.log" 2>&1
  for lid in 58000 58001 58002 58003 58004 58005; do eval_roots+=("$dir/layout_$lid"); done
  eval_roots+=("$dir/wait")
 done
 python3 "$ROOT/scripts/summarize_paired_evaluation.py" --roots "${eval_roots[@]}" --output "$OUT/EVALUATION_${model}_spatial.json"
done
original_roots=()
for seed in 0 1 2; do
 status "evaluating_spatial_original_seed${seed}"
 dir="$OUT/spatial_original_seed${seed}"
 PI05_LOCAL_CONFIG="$ROOT/scripts/pi05_paired_spatial_pilot40_20260928.env" PI05_POLICY_PATH="$NEW" PI05_RECORD_DIR="$dir" PI05_EVAL_SEED="$seed" \
  bash "$ROOT/scripts/run_pi05_paired_sim.sh" --policy-max-action-step 0 > "$OUT/spatial_original_seed${seed}.log" 2>&1
 original_roots+=("$dir/rollouts")
done
python3 "$ROOT/scripts/summarize_paired_evaluation.py" --roots "${original_roots[@]}" --output "$OUT/EVALUATION_spatial_original.json"
# Recompute previous ordinary original21 summary from original artifacts, not from a copied score.
old_original=()
for seed in 0 1 2; do old_original+=("$ROOT/demo/recovery_comparison_20260928_r1/ordinary_seed${seed}/rollouts"); done
python3 "$ROOT/scripts/summarize_paired_evaluation.py" --roots "${old_original[@]}" --output "$OUT/EVALUATION_ordinary_original.json"
# Reuse the independently completed old-model spatial baseline; never silently omit it.
BASELINE="$ROOT/demo/spatial_baseline_heldout_20260928_r1"
python3 - "$BASELINE" "$RUN/heldout_protocol.json" <<'CHECK'
import json,sys
from pathlib import Path
r,protocol=map(Path,sys.argv[1:]);assert json.loads((r/'STATUS.json').read_text())['stage'] in ('numeric_complete_actual_visual_review_required','complete_reviewed')
for seed in range(3):assert (r/f'seed{seed}'/'evaluation_protocol.json').read_bytes()==protocol.read_bytes()
CHECK
baseline_roots=()
for seed in 0 1 2; do
 for lid in 58000 58001 58002 58003 58004 58005; do baseline_roots+=("$BASELINE/seed${seed}/layout_$lid"); done
 baseline_roots+=("$BASELINE/seed${seed}/wait")
done
python3 "$ROOT/scripts/summarize_paired_evaluation.py" --roots "${baseline_roots[@]}" --output "$OUT/EVALUATION_ordinary_spatial.json"
python3 "$ROOT/scripts/compare_spatial_evaluations.py" --root "$OUT" --protocol "$RUN/heldout_protocol.json"
status numeric_complete_actual_visual_review_required
