#!/usr/bin/env bash
set -Eeuo pipefail
WORKSPACE=/home/user/Documents/zoo/sim
ROOT="$WORKSPACE/SimFoundry"
OUT="$ROOT/demo/natural_layout_feasibility_20260928_r1"
# Run only after the previous diagnostic batch finishes, without competing for GPU.
while kill -0 3941739 2>/dev/null; do sleep 5; done
python3 - "$ROOT/demo/spatial_diversity_feasibility_20260928_r1/STATUS.json" <<'CHECK'
import json,sys
from pathlib import Path
assert json.loads(Path(sys.argv[1]).read_text())['stage']=='numeric_complete_visual_review_pending', 'Previous batch did not finish normally; inspect before proceeding'
CHECK
source /home/user/miniconda3/etc/profile.d/conda.sh
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1 PYTHONUNBUFFERED=1
cd "$WORKSPACE/IsaacLab"
for lid in 51000 51001 51002 51003 51004 51005; do
 python - "$OUT/STATUS.json" "$lid" <<'PY'
from pathlib import Path
import json,sys
Path(sys.argv[1]).write_text(json.dumps({'stage':'collecting_diagnostics','layout_id':int(sys.argv[2]),'training_ready':False}))
PY
 set +e
 ./isaaclab.sh -p "$ROOT/scripts/collect_paired_sorting.py" --device cuda --viz none --newton-contacts --role diagnostic --layout-start "$lid" --layouts 1 --wait-episodes 0 --steps 160 --diagnostic-layout-json "$OUT/layout_${lid}.json" --out-dir "$OUT/case_${lid}" > "$OUT/case_${lid}.log" 2>&1
 rc=$?
 set -e
 # Proceed to next predeclared geometry only for a completed pair failing quality.
 # No resampling, retries, acceptance filtering, or continuation after runtime errors.
 python - "$OUT/case_${lid}" "$rc" <<'PY'
from pathlib import Path
import json,sys
r=Path(sys.argv[1]);rc=int(sys.argv[2])
if rc:
 s=json.loads((r/'STATUS.json').read_text());assert s.get('error')=='Quality gate failed. Stop; no retries or training export. See manifest.json.',s
assert len(list(r.glob('layout_*/quality.json')))==2
PY
done
python - "$OUT/STATUS.json" <<'PY'
from pathlib import Path
import json,sys
Path(sys.argv[1]).write_text(json.dumps({'stage':'numeric_complete_visual_review_pending','training_ready':False}))
PY
