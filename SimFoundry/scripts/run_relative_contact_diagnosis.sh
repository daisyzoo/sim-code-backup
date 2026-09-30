#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=/home/user/Documents/zoo/sim/SimFoundry
OUT="$ROOT/demo/relative_contact_diagnosis_20260929_r1"
export PI05_LOCAL_CONFIG="$ROOT/scripts/pi05_paired_relative_chunk10_20260929.env"
export PI05_POLICY_PATH="$(cat "$ROOT/demo/state_relative_chunk10_20260929_r1/checkpoint.txt")"
export PI05_POLICY_PORT=18777
export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1 PYTHONUNBUFFERED=1
status() { python3 - "$OUT/STATUS.json" "$1" <<'PY'
import json,sys,datetime
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':sys.argv[2],'training_ready':False,'goal_complete':False,'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
PY
}
trap 'status failed_runtime' ERR
status original100_seed2
PI05_RECORD_DIR="$OUT/original100_seed2" PI05_EVAL_SEED=2 bash "$ROOT/scripts/run_pi05_paired_sim.sh" --layout-start 100 --layouts 1 --wait-episodes 0 --trace-episode-contacts --policy-max-action-step 0 > "$OUT/original100_seed2.log" 2>&1
status spatial58004_seed1
PI05_RECORD_DIR="$OUT/spatial58004_seed1" PI05_EVAL_SEED=1 bash "$ROOT/scripts/run_pi05_paired_sim.sh" --layout-start 58004 --layouts 1 --wait-episodes 0 --diagnostic-layout-json "$ROOT/demo/spatial_generalization_20260928_r1/heldout_layouts/layout_58004.json" --trace-episode-contacts --policy-max-action-step 0 > "$OUT/spatial58004_seed1.log" 2>&1
status collected_parity_and_actual_review_required
