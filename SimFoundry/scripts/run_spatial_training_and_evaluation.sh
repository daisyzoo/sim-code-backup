#!/usr/bin/env bash
# Run only after actual raw review, selection, conversion and export audit.
set -Eeuo pipefail
ROOT=/home/user/Documents/zoo/sim/SimFoundry
RUN="$ROOT/demo/spatial_generalization_20260928_r1"
BASELINE="$ROOT/demo/spatial_baseline_heldout_20260928_r1"
python3 - "$RUN" <<'PY'
import json,sys
from pathlib import Path
r=Path(sys.argv[1]);ds=r.parents[2]/'lerobot/lerobot_sim_paired_spatial_pilot40_20260928'
# r.parents[2] is workspace sim.
a=json.loads((ds/'meta/paired_export_audit.json').read_text());assert a['training_ready'] and a['frames']==5320
(r/'STATUS.json').write_text(json.dumps({'stage':'waiting_baseline_release_before_training','training_ready':True,'goal_complete':False},indent=2))
PY
while true; do
 stage="$(python3 - "$BASELINE/STATUS.json" <<'PY'
import json,sys
from pathlib import Path
s=json.loads(Path(sys.argv[1]).read_text())['stage']
assert s in ['evaluating_seed0','evaluating_seed1','evaluating_seed2','numeric_complete_actual_visual_review_required','complete_reviewed'],s
print(s)
PY
)"
 if [[ "$stage" == numeric_complete_actual_visual_review_required || "$stage" == complete_reviewed ]]; then break; fi
 sleep 15
done
bash "$ROOT/scripts/train_spatial_pilot.sh"
bash "$ROOT/scripts/run_spatial_model_comparison.sh"
