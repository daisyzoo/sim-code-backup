#!/usr/bin/env bash
set -Eeuo pipefail
WORKSPACE=/home/user/Documents/zoo/sim
ROOT="$WORKSPACE/SimFoundry"
OUT="$ROOT/demo/rotated_front_back_20260928_r1"
source /home/user/miniconda3/etc/profile.d/conda.sh
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1 PYTHONUNBUFFERED=1
cd "$WORKSPACE/IsaacLab"
for variant in rotated; do
 cap=0;offset=-.13
 if [[ "$variant" == forward_settled ]]; then cap=0;offset=-.13;fi
 for lid in 54000 54001; do
  python - "$OUT/STATUS.json" "$variant" "$lid" <<'PY'
import json,sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':'collecting_diagnostics','variant':sys.argv[2],'layout':int(sys.argv[3]),'training_ready':False}))
PY
  set +e
  ./isaaclab.sh -p "$ROOT/scripts/collect_paired_sorting.py" --device cuda --viz none --newton-contacts --role diagnostic --layout-start "$lid" --layouts 1 --steps 160 --diagnostic-layout-json "$OUT/layout_${lid}.json" --expert-staging-z .92 --expert-contact-offset "$offset" --expert-max-contact-x "$cap" --trace-episode-contacts --out-dir "$OUT/${variant}_${lid}" > "$OUT/${variant}_${lid}.log" 2>&1
  rc=$?
  set -e
  python - "$OUT/${variant}_${lid}" "$rc" <<'PY'
import json,sys
from pathlib import Path
r=Path(sys.argv[1])
if int(sys.argv[2]):
 s=json.loads((r/'STATUS.json').read_text());assert s.get('error')=='Quality gate failed. Stop; no retries or training export. See manifest.json.',s
assert len(list(r.glob('layout_*/quality.json')))==2
PY
 done
done
python - "$OUT/STATUS.json" <<'PY'
import json,sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':'numeric_complete_visual_review_pending','training_ready':False}))
PY
