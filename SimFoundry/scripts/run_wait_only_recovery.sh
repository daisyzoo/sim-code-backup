#!/usr/bin/env bash
set -Eeuo pipefail
cd /home/user/Documents/zoo/sim
ROOT="$PWD/SimFoundry"
RUN_DIR="${WAITONLY_RUN_DIR:?Set a fresh experiment directory}"
[[ ! -e "$RUN_DIR" ]] || { echo 'Refusing overwrite' >&2; exit 1; }
python3 - <<'PY'
import json,hashlib
from pathlib import Path
r=Path('SimFoundry/demo/recovery_comparison_20260928_r1')
assert json.loads((r/'STATUS.json').read_text())['stage']=='evaluation_reviewed_screen_failed'
for v in ['ordinary','recovery','baseline']:
 assert json.loads((r/f'failure_review/{v}_visual_review.json').read_text())['reviewed']
 assert len(json.loads((r/f'EVALUATION_{v}.json').read_text())['rows'])==21
for p in ['lerobot/outputs/paired_waitonly_pilot40_20260928']:
 assert not Path(p).exists()
PY
mkdir -p "$RUN_DIR/source_snapshot"
status() {
 python3 - "$RUN_DIR/STATUS.json" "$1" <<'PY'
import json,sys,datetime
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':sys.argv[2],'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
PY
}
trap 'status failed_runtime_or_gate' ERR
status checking_inputs
python3 - "$RUN_DIR" <<'PY'
from pathlib import Path
import json,hashlib,sys,shutil
out=Path(sys.argv[1]);variants=['ordinary','recovery','waitonly'];prov={};splits={}
for v in variants:
 root=Path(f'lerobot/lerobot_sim_paired_{v}_pilot40_20260928')
 a=json.loads((root/'meta/paired_export_audit.json').read_text())
 assert a['training_ready'] and a['frames']==5320 and a['train_frames']==4540 and a['episodes']==40
 prov[v]=json.loads((root/'meta/paired_provenance.json').read_text())['records']
 splits[v]=json.loads((root/'meta/train_validation_split.json').read_text())
assert splits['ordinary']==splits['recovery']==splits['waitonly']
for ordinary,recovery,current in zip(*(prov[v] for v in variants)):
 assert (ordinary['layout_id'],ordinary['task_id'])==(recovery['layout_id'],recovery['task_id'])==(current['layout_id'],current['task_id'])
 expected=recovery if current['layout_id'] in range(31000,31004) else ordinary
 assert current['hash']==expected['hash']
 assert hashlib.sha256(Path(current['path']).read_bytes()).hexdigest()==current['hash']
def config(v):return dict(x.split('=',1) for x in Path(f'SimFoundry/scripts/pi05_paired_{v}_pilot40_20260928.env').read_text().splitlines() if x and not x.startswith('#'))
a,b=config('ordinary'),config('waitonly');allowed={'DATASET_V30_ROOT','SHARED_SPLIT_FILE','PI05_SHARED_SPLIT_FILE','PI05_TRAIN_STATS_FILE','PI05_OUTPUT_ROOT','DATASET_REPO_ID','WANDB_PROJECT_PI05'}
assert {k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}<=allowed
files=['scripts/run_wait_only_recovery.sh','scripts/pi05_paired_waitonly_pilot40_20260928.env','scripts/collect_paired_sorting.py','scripts/run_pi05_paired_sim.sh','simfoundry/data/paired_sorting.py','simfoundry/data/recovery_protocol.py']
sha={}
for f in files:
 p=Path('SimFoundry')/f;sha[f]=hashlib.sha256(p.read_bytes()).hexdigest();dest=out/'source_snapshot'/f;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
shutil.copy2('SimFoundry/demo/wait_only_recovery_protocol_20260928_r1/protocol.json',out/'protocol.json')
(out/'INPUT_AUDIT.json').write_text(json.dumps({'passed':True,'exact_data_substitution_verified':True,'same_config_except_data_paths':True,'source_sha256':sha},indent=2))
PY
CFG="$ROOT/scripts/pi05_paired_waitonly_pilot40_20260928.env"
status training_waitonly
PI05_LOCAL_CONFIG="$CFG" bash "$PWD/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/train_pi05_package_sorting_local.sh" > "$RUN_DIR/train_waitonly.log" 2>&1
python3 - "$RUN_DIR" <<'PY'
import json,sys
from pathlib import Path
runs=list(Path('lerobot/outputs/paired_waitonly_pilot40_20260928').glob('package_sorting_pi05_*'));assert len(runs)==1
run=runs[0];val=[json.loads(x) for x in (run/'validation.jsonl').read_text().splitlines()];assert val[-1]['step']==7240 and val[-1]['validation/frames']==780
cp=(run/'checkpoints/last/pretrained_model').resolve();assert (cp/'model.safetensors').is_file();(Path(sys.argv[1])/'checkpoint_waitonly.txt').write_text(str(cp)+'\n')
PY
POLICY="$(cat "$RUN_DIR/checkpoint_waitonly.txt")"
for seed in 0 1 2; do
 status "evaluating_waitonly_seed${seed}"
 PI05_LOCAL_CONFIG="$CFG" PI05_POLICY_PATH="$POLICY" PI05_RECORD_DIR="$RUN_DIR/waitonly_seed${seed}" PI05_EVAL_SEED="$seed" PI05_PROMPT_VARIANT=short bash "$ROOT/scripts/run_pi05_paired_sim.sh" --policy-max-action-step 0 > "$RUN_DIR/eval_waitonly_seed${seed}.log" 2>&1
done
python3 "$ROOT/scripts/summarize_paired_evaluation.py" --roots "$RUN_DIR/waitonly_seed0/rollouts" "$RUN_DIR/waitonly_seed1/rollouts" "$RUN_DIR/waitonly_seed2/rollouts" --output "$RUN_DIR/EVALUATION_waitonly.json"
status numeric_complete_visual_review_pending
