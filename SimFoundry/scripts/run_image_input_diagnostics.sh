#!/usr/bin/env bash
set -Eeuo pipefail
cd /home/user/Documents/zoo/sim
ROOT="$PWD/SimFoundry"
OUT="${IMAGE_DIAGNOSTIC_DIR:?Set a fresh directory}"
[[ ! -e "$OUT" ]] || { echo 'Refusing overwrite' >&2; exit 1; }
python3 - <<'PY'
import json
from pathlib import Path
r=Path('SimFoundry/demo/wait_only_recovery_comparison_20260928_r1')
assert json.loads((r/'STATUS.json').read_text())['stage']=='evaluation_reviewed_screen_failed'
assert json.loads((r/'failure_review/waitonly_visual_review.json').read_text())['reviewed']
PY
mkdir -p "$OUT"
status() {
 python3 - "$OUT/STATUS.json" "$1" <<'PY'
from pathlib import Path
import json,sys,datetime
Path(sys.argv[1]).write_text(json.dumps({'stage':sys.argv[2],'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
PY
}
trap 'status failed' ERR
set -a
source "$ROOT/scripts/pi05_paired_pilot32_b_20260924.env"
set +a
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export HF_HOME="$HF_HOME_ROOT/pi05" CUDA_VISIBLE_DEVICES=0 PYTHONUNBUFFERED=1
export LEROBOT_TOKENIZER_NAME_OVERRIDE="$PI05_TOKENIZER_ROOT" LEROBOT_TOKENIZER_LOCAL_FILES_ONLY_OVERRIDE=true
export PYTHONPATH="$PI05_PROJECT_ROOT/unitree_lerobot/lerobot/src:$ROOT:$ROOT/scripts"
cp "$ROOT/scripts/probe_baseline_image_repeatability.py" "$ROOT/scripts/probe_training_encoding_gap.py" "$OUT/"
status baseline_same_input_and_image_swap
"$PI05_PYTHON" "$ROOT/scripts/probe_baseline_image_repeatability.py" --out "$OUT/baseline_image_repeatability.json" > "$OUT/repeatability.log" 2>&1
status training_encoding_gap
"$PI05_PYTHON" "$ROOT/scripts/probe_training_encoding_gap.py" --out "$OUT/training_encoding_gap.json" > "$OUT/encoding.log" 2>&1
status complete_analysis_pending
