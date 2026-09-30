#!/usr/bin/env bash
set -Eeuo pipefail
WORKSPACE=/home/user/Documents/zoo/sim
ROOT="$WORKSPACE/SimFoundry"
RUN="$ROOT/demo/spatial_generalization_20260928_r1"
CFG="$ROOT/scripts/pi05_paired_spatial_pilot40_20260928.env"
status() { python3 - "$RUN/STATUS.json" "$1" <<'PY'
import sys,json,datetime
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':sys.argv[2],'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
PY
}
trap 'status failed_runtime_or_gate' ERR
python3 - "$WORKSPACE" <<'PY'
import json,hashlib,shutil,sys
from pathlib import Path
r=Path(sys.argv[1]);ds=r/'lerobot/lerobot_sim_paired_spatial_pilot40_20260928';out=r/'SimFoundry/demo/spatial_generalization_20260928_r1'
a=json.loads((ds/'meta/paired_export_audit.json').read_text())
assert a['training_ready'] and a['frames']==5320 and a['train_frames']==4540
p=json.loads((ds/'meta/paired_provenance.json').read_text());assert p['variant']=='short' and len(p['records'])==40
for row in p['records']:assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['hash']
groups={row.get('geometry_group') for row in p['records'] if row['task_id']!='wait_no_package'};assert None not in groups and len(groups)==7
s=json.loads((ds/'meta/train_validation_split.json').read_text());assert len(s['train'])==34 and len(s['validation'])==6
selection=json.loads((out/'RAW_SELECTION.json').read_text())
assert set(s['validation_layouts'])==set(selection['validation_layouts'])
assert selection['selected_episodes']==40 and len(selection['selected_train_groups'])==6
assert groups==set(selection['selected_groups'])
assert not (r/'lerobot/outputs/paired_spatial_pilot40_20260928').exists()
assert shutil.disk_usage(r).free>25*2**30
(out/'INPUT_AUDIT.json').write_text(json.dumps({'passed':True,'same_episode_frame_budget':True,'hashes_verified':40,'geometry_groups':sorted(groups)},indent=2))
PY
status training
PI05_LOCAL_CONFIG="$CFG" bash "$WORKSPACE/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/train_pi05_package_sorting_local.sh" > "$RUN/train.log" 2>&1
python3 - "$WORKSPACE" "$RUN" <<'PY'
import sys,json
from pathlib import Path
r,out=map(Path,sys.argv[1:]);runs=list((r/'lerobot/outputs/paired_spatial_pilot40_20260928').glob('package_sorting_pi05_*'));assert len(runs)==1
run=runs[0];a=json.loads((run/'trainable_parameters.json').read_text());assert not any('lora_' in x['name'] for x in a['trainable'])
v=[json.loads(x) for x in (run/'validation.jsonl').read_text().splitlines()];assert v[-1]['step']==7240 and v[-1]['validation/frames']==780
cp=(run/'checkpoints/last/pretrained_model').resolve();assert (cp/'model.safetensors').is_file()
(out/'checkpoint.txt').write_text(str(cp)+'\n')
PY
status trained_evaluation_required
