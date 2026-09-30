#!/usr/bin/env bash
set -Eeuo pipefail
WORKSPACE=/home/user/Documents/zoo/sim
ROOT="$WORKSPACE/SimFoundry"
CONTRACT="$ROOT/demo/spatial_generalization_20260928_r1/candidate_pool_protocol/contract.json"
OUT="$ROOT/demo/spatial_candidate_pool72_20260928_r1"
python3 - "$CONTRACT" "$OUT" <<'PY'
import json,sys,shutil
from pathlib import Path
c=json.loads(Path(sys.argv[1]).read_text());out=Path(sys.argv[2]);assert c['collection_kind']=='pre_registered_candidate_pool' and c['approved_for_pilot'] is True
assert len(c['layouts'])==30 and len(c['wait_layouts'])==12
assert shutil.disk_usage(out.parent).free>30*2**30
out.mkdir(exist_ok=False);(out/'contract.json').write_bytes(Path(sys.argv[1]).read_bytes());(out/'STATUS.json').write_text(json.dumps({'stage':'prepared','training_ready':False}))
PY
status() { python3 - "$OUT/STATUS.json" "$1" <<'PY'
import sys,json,datetime
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':sys.argv[2],'training_ready':False,'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
PY
}
trap 'status failed_runtime_or_unregistered_gate' ERR
source /home/user/miniconda3/etc/profile.d/conda.sh
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1 PYTHONUNBUFFERED=1
cd "$WORKSPACE/IsaacLab"
for lid in $(seq 62000 62029); do
 status "collecting_candidate_${lid}"
 # Do not rely on the Isaac launcher exit code; inspect child artifacts below.
 ./isaaclab.sh -p "$ROOT/scripts/collect_paired_sorting.py" \
   --device cuda --viz none --newton-contacts --role pilot --layout-start "$lid" --layouts 1 --steps 160 \
   --spatial-pilot-contract "$CONTRACT" --expert-staging-z .92 --expert-contact-offset -.13 --expert-far-contact-offset -.11 \
   --out-dir "$OUT/case_${lid}" > "$OUT/case_${lid}.log" 2>&1
 python - "$OUT/case_${lid}" "$ROOT" <<'PY'
import sys,json
from pathlib import Path
r=Path(sys.argv[1]);sys.path.insert(0,str(Path(sys.argv[2])/'scripts'));from check_collection_quality import check
s=json.loads((r/'STATUS.json').read_text())
if s.get('status')=='numeric_pass_visual_review_pending':
 result=check(r,2);result['candidate_numeric_pass']=True
else:
 assert s.get('status')=='blocked_quality_or_runtime' and s.get('error')=='Quality gate failed. Stop; no retries or training export. See manifest.json.',s
 q=list(r.glob('layout_*/quality.json'));assert len(q)==2 and all((p.parent/'raw.npz').is_file() for p in q)
 m=json.loads((r/'manifest.json').read_text());assert len(m)==1 and len(m[0]['episodes'])==2
 assert not m[0]['pair']['passed'] or not all(x['passed'] for x in m[0]['episodes'])
 result={'candidate_numeric_pass':False,'training_ready':False,'disposition':'Reject entire geometry group if either assignment fails; continue other preregistered candidates, no retry.'}
(r/'candidate_result.json').write_text(json.dumps(result,indent=2));print(r.name,result,flush=True)
PY
done
status collecting_waits
./isaaclab.sh -p "$ROOT/scripts/collect_paired_sorting.py" \
  --device cuda --viz none --newton-contacts --role pilot --layouts 0 --wait-episodes 12 --wait-layout-start 63000 \
  --out-dir "$OUT/waits" > "$OUT/waits.log" 2>&1
python "$ROOT/scripts/check_collection_quality.py" --root "$OUT/waits" --episodes 12
status numeric_complete_group_selection_and_visual_review_required
