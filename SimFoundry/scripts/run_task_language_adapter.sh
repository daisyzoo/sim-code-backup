#!/usr/bin/env bash
set -Eeuo pipefail
cd /home/user/Documents/zoo/sim
ROOT="$PWD/SimFoundry"
RUN="$ROOT/demo/task_language_adapter_20260928_r1"
CFG="$ROOT/scripts/pi05_paired_language_adapter_pilot40_20260928.env"
status() { python3 - "$RUN/STATUS.json" "$1" <<'PY'
import sys,json,datetime
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':sys.argv[2],'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
PY
}
trap 'status failed_runtime_or_gate' ERR
status checking_inputs
python3 - <<'PY'
import json,hashlib,shutil
from pathlib import Path
r=Path('/home/user/Documents/zoo/sim'); ds=r/'lerobot/lerobot_sim_paired_ordinary_pilot40_20260928';out=r/'SimFoundry/demo/task_language_adapter_20260928_r1'
a=json.loads((ds/'meta/paired_export_audit.json').read_text());assert a['training_ready'] and a['frames']==5320 and a['train_frames']==4540
p=json.loads((ds/'meta/paired_provenance.json').read_text());assert p['variant']=='short'
for row in p['records']:assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['hash']
def cfg(n):return dict(x.split('=',1) for x in (r/'SimFoundry/scripts'/n).read_text().splitlines() if x and not x.startswith('#'))
b=cfg('pi05_paired_ordinary_pilot40_20260928.env');c=cfg('pi05_paired_language_adapter_pilot40_20260928.env')
changed={k for k in b.keys()|c.keys() if b.get(k)!=c.get(k)}
assert changed=={'PI05_OUTPUT_ROOT','PI05_TRAIN_EXPERT_ONLY','PI05_REQUIRE_EXPERT_ONLY','PI05_LORA_RANK','PI05_LORA_DROPOUT','PI05_LORA_TARGET_ACTION_EXPERT','WANDB_PROJECT_PI05','PI05_TRAIN_EXPERT_WITH_LANGUAGE_LORA','PI05_REQUIRE_LANGUAGE_ADAPTER'},changed
assert not Path(c['PI05_OUTPUT_ROOT']).exists()
assert shutil.disk_usage(r).free>25*2**30
(out/'INPUT_AUDIT.json').write_text(json.dumps({'passed':True,'source_hashes_verified':len(p['records']),'same_data_split_stats_and_budget':True,'configuration_diff':{k:{'baseline':b.get(k),'candidate':c.get(k)} for k in sorted(changed)}},indent=2))
PY
status training
PI05_LOCAL_CONFIG="$CFG" bash "$PWD/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/train_pi05_package_sorting_local.sh" > "$RUN/train.log" 2>&1
python3 - "$PWD" "$RUN" <<'PY'
import sys,json
from pathlib import Path
r,out=map(Path,sys.argv[1:]);runs=list((r/'lerobot/outputs/paired_language_adapter_pilot40_20260928').glob('package_sorting_pi05_*'));assert len(runs)==1
run=runs[0];a=json.loads((run/'trainable_parameters.json').read_text());assert any('language_model' in x['name'] and 'lora_' in x['name'] for x in a['trainable'])
v=[json.loads(x) for x in (run/'validation.jsonl').read_text().splitlines()];assert v[-1]['step']==7240 and v[-1]['validation/frames']==780
cp=(run/'checkpoints/last/pretrained_model').resolve();assert (cp/'model.safetensors').is_file()
(out/'checkpoint.txt').write_text(str(cp)+'\n')
PY
POLICY="$(cat "$RUN/checkpoint.txt")"
for seed in 0 1 2; do
 status "evaluating_seed${seed}"
 PI05_LOCAL_CONFIG="$CFG" PI05_POLICY_PATH="$POLICY" PI05_RECORD_DIR="$RUN/language_seed${seed}" PI05_EVAL_SEED="$seed" PI05_PROMPT_VARIANT=short bash "$ROOT/scripts/run_pi05_paired_sim.sh" --policy-max-action-step 0 > "$RUN/eval_seed${seed}.log" 2>&1
done
python3 "$ROOT/scripts/summarize_paired_evaluation.py" --roots "$RUN/language_seed0/rollouts" "$RUN/language_seed1/rollouts" "$RUN/language_seed2/rollouts" --output "$RUN/EVALUATION.json"
status numeric_complete_visual_review_pending
