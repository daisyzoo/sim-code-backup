#!/usr/bin/env bash
# Fresh exact-contract collection. Any quality/runtime failure stops this batch.
set -Eeuo pipefail
WORKSPACE=/home/user/Documents/zoo/sim
ROOT="$WORKSPACE/SimFoundry"
CONTRACT="${SPATIAL_PILOT_CONTRACT:?Set the approved contract path}"
OUT="${SPATIAL_PILOT_OUT:?Set a fresh output root}"
python3 - "$CONTRACT" "$OUT" <<'PY'
import json,sys,shutil
from pathlib import Path
p,out=map(Path,sys.argv[1:]);c=json.loads(p.read_text())
assert c['approved_for_pilot'] is True
assert len(c['layouts'])==14 and len(c['wait_layouts'])==12
assert c['wait_layouts']==list(range(c['wait_layouts'][0],c['wait_layouts'][0]+12))
assert c['expert']['steps']==160
assert shutil.disk_usage(out.parent).free>30*2**30
out.mkdir(exist_ok=False)
(out/'contract.json').write_bytes(p.read_bytes())
(out/'layout_ids.txt').write_text('\n'.join(str(d['layout_id']) for d in c['layouts'])+'\n')
(out/'expert_settings.txt').write_text(f"{c['expert']['staging_z']} {c['expert']['contact_offset']} {c['expert'].get('far_contact_offset',0.)} {c['wait_layouts'][0]}\n")
(out/'STATUS.json').write_text(json.dumps({'stage':'prepared','training_ready':False}))
PY
status() { python3 - "$OUT/STATUS.json" "$1" <<'PY'
import sys,json,datetime
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':sys.argv[2],'training_ready':False,'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
PY
}
trap 'status failed_quality_or_runtime' ERR
mapfile -t layout_ids < "$OUT/layout_ids.txt"
read -r staging_z contact_offset far_contact_offset wait_start < "$OUT/expert_settings.txt"
source /home/user/miniconda3/etc/profile.d/conda.sh
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1 PYTHONUNBUFFERED=1
cd "$WORKSPACE/IsaacLab"
for lid in "${layout_ids[@]}"; do
 status "collecting_layout_${lid}"
 ./isaaclab.sh -p "$ROOT/scripts/collect_paired_sorting.py" \
   --device cuda --viz none --newton-contacts --role pilot --layout-start "$lid" --layouts 1 --steps 160 \
   --spatial-pilot-contract "$CONTRACT" --expert-staging-z "$staging_z" --expert-contact-offset "$contact_offset" --expert-far-contact-offset "$far_contact_offset" \
   --out-dir "$OUT/case_${lid}" > "$OUT/case_${lid}.log" 2>&1
 python "$ROOT/scripts/check_collection_quality.py" --root "$OUT/case_${lid}" --episodes 2
done
status collecting_waits
./isaaclab.sh -p "$ROOT/scripts/collect_paired_sorting.py" \
   --device cuda --viz none --newton-contacts --role pilot --layouts 0 --wait-episodes 12 --wait-layout-start "$wait_start" \
   --out-dir "$OUT/waits" > "$OUT/waits.log" 2>&1
python "$ROOT/scripts/check_collection_quality.py" --root "$OUT/waits" --episodes 12
status numeric_complete_visual_review_pending
