#!/usr/bin/env bash
set -Eeuo pipefail
WORKSPACE=/home/user/Documents/zoo/sim
ROOT="$WORKSPACE/SimFoundry"
OUT="$ROOT/demo/tail_feedback_20260928_r1"
source /home/user/miniconda3/etc/profile.d/conda.sh
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1 PYTHONUNBUFFERED=1
cd "$WORKSPACE/IsaacLab"
for lid in 67300 67301 67302 67303; do
 python - "$OUT/STATUS.json" "$lid" <<'PY'
import json,sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':'collecting_diagnostic','layout':int(sys.argv[2]),'training_ready':False}))
PY
 set +e
 ./isaaclab.sh -p "$ROOT/scripts/collect_tail_feedback_diagnostic.py" --device cuda --viz none --newton-contacts --role diagnostic --layout-start "$lid" --layouts 1 --steps 160 --diagnostic-layout-json "$OUT/layout_${lid}.json" --expert-staging-z .92 --expert-contact-offset -.13 --expert-far-contact-offset -.11 --expert-object-feedback-lead .04 --trace-episode-contacts --out-dir "$OUT/case_${lid}" > "$OUT/case_${lid}.log" 2>&1
 rc=$?
 set -e
 python - "$OUT/case_${lid}" "$rc" <<'PY'
import json,sys
from pathlib import Path
r=Path(sys.argv[1]);qs=list(r.glob('layout_*/quality.json'));raw=list(r.glob('layout_*/raw.npz'))
assert len(qs)==len(raw)==2,(r,sys.argv[2],len(qs),len(raw))
print(r.name,[json.loads(q.read_text()).get('passed') for q in qs],flush=True)
PY
done
python - "$OUT/STATUS.json" <<'PY'
import json,sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':'numeric_complete_review_required','training_ready':False}))
PY
