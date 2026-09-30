#!/usr/bin/env bash
set -Eeuo pipefail
WORKSPACE=/home/user/Documents/zoo/sim
ROOT="$WORKSPACE/SimFoundry"
OUT="$ROOT/demo/crossed_approach8_20260929_r1"
status() { python3 - "$OUT/STATUS.json" "$1" <<'PY'
import sys,json,datetime
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':sys.argv[2],'training_ready':False,'goal_complete':False,'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
PY
}
trap 'status failed_runtime_or_integrity' ERR
source /home/user/miniconda3/etc/profile.d/conda.sh
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1 PYTHONUNBUFFERED=1
cd "$WORKSPACE/IsaacLab"
while IFS=$'\t' read -r case lid layout endpoint; do
 status "collecting_${case}"
 python - "$OUT" "$lid" "$layout" "$case" <<'PY'
import sys,json,hashlib,shutil
from pathlib import Path
out=Path(sys.argv[1]);p=Path(sys.argv[3]);r=next(r for r in json.loads((out/'PROTOCOL.json').read_text())['layouts'] if r['layout_id']==int(sys.argv[2]));assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'];assert not (out/sys.argv[4]).exists();assert shutil.disk_usage(out).free>20.12*2**30
PY
 set +e
 ./isaaclab.sh -p "$ROOT/scripts/collect_paired_sorting.py" --device cuda --viz none --newton-contacts --role diagnostic --layout-start "$lid" --layouts 1 --wait-episodes 0 --steps 160 --diagnostic-layout-json "$layout" --expert-staging-z .92 --expert-contact-offset -.13 --expert-far-contact-offset -.11 --expert-exit-y "$endpoint" --expert-crossed-contact-offset -.04 --out-dir "$OUT/${case}" > "$OUT/${case}.log" 2>&1
 rc=$?
 set -e
 python - "$OUT/${case}" "$rc" <<'PY'
import sys,json,hashlib
from pathlib import Path
import numpy as np
p=Path(sys.argv[1]);s=json.loads((p/'STATUS.json').read_text());raws=sorted(p.glob('layout_*/raw.npz'));assert len(raws)==2
if s['status']=='blocked_quality_or_runtime':assert s['error']=='Quality gate failed. Stop; no retries or training export. See manifest.json.',s
else:assert s['status']=='numeric_pass_visual_review_pending',s
rows=[]
for raw in raws:
 with np.load(raw) as z:
  m=json.loads(str(z['collect_meta']));assert len(z['q'])==160 and abs(z['q'][0,12:]).max()<1e-4 and abs(z['action'][0,12:]).max()<1e-4;assert np.all(z['action'][:,12]==0) and m['assist_frames']==0
 q=json.loads((raw.parent/'quality.json').read_text());assert not q['training_ready'];rows.append({'path':str(raw),'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'passed':q['passed'],'reasons':q['reasons']})
(p/'INTEGRITY.json').write_text(json.dumps({'rows':rows,'launcher_exit_code':int(sys.argv[2]),'training_ready':False},indent=2));print(p.name,[r['passed'] for r in rows],flush=True)
PY
done < "$OUT/case_inputs.tsv"
status numeric_complete_actual_visual_and_trace_review_required
