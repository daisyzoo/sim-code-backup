#!/usr/bin/env bash
# Requires completed reviewed conversion audits; no automatic data approval.
set -Eeuo pipefail
SIM_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE="$(dirname -- "$SIM_ROOT")"
RUN_DIR="${RECOVERY_RUN_DIR:?Set a fresh comparison directory}"
[[ ! -e "$RUN_DIR" ]] || { echo 'Refusing overwrite' >&2; exit 1; }
mkdir -p "$RUN_DIR"
status() {
 python3 - "$RUN_DIR/STATUS.json" "$1" <<'PY'
import json,sys,datetime
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':sys.argv[2],'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
PY
}
trap 'status failed_runtime_or_gate' ERR
status checking_inputs
python3 - "$WORKSPACE" "$RUN_DIR" <<'PY'
import json,sys,hashlib
from pathlib import Path
ws,out=map(Path,sys.argv[1:]);audits={};datasets={}
for variant in ('ordinary','recovery'):
 root=ws/f'lerobot/lerobot_sim_paired_{variant}_pilot40_20260928'
 audit=json.loads((root/'meta/paired_export_audit.json').read_text())
 assert audit['training_ready'] and audit['train_frames']==4540 and audit['frames']==5320 and audit['episodes']==40
 prov=json.loads((root/'meta/paired_provenance.json').read_text());assert prov['variant']=='short'
 for r in prov['records']:assert hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['hash']
 split=json.loads((root/'meta/train_validation_split.json').read_text())
 datasets[variant]=(prov,split)
 audits[variant]=audit
def config(name):
 return dict(line.split('=',1) for line in (ws/'SimFoundry/scripts'/name).read_text().splitlines() if line and not line.startswith('#'))
baseline=config('pi05_paired_pilot32_b_20260924.env')
allowed={'DATASET_V30_ROOT','SHARED_SPLIT_FILE','PI05_SHARED_SPLIT_FILE','PI05_TRAIN_STATS_FILE','PI05_OUTPUT_ROOT','DATASET_REPO_ID','WANDB_PROJECT_PI05'}
for variant in ('ordinary','recovery'):
 candidate=config(f'pi05_paired_{variant}_pilot40_20260928.env')
 assert {k for k in baseline.keys()|candidate.keys() if baseline.get(k)!=candidate.get(k)} <= allowed
 assert candidate['PI05_STEPS']=='7240' and candidate['PI05_SEED']=='42'
 assert not Path(candidate['PI05_OUTPUT_ROOT']).exists()
p0,s0=datasets['ordinary'];p1,s1=datasets['recovery'];assert s0==s1
assert [(r['layout_id'],r['task_id']) for r in p0['records']]==[(r['layout_id'],r['task_id']) for r in p1['records']]
for i in s0['validation']:assert p0['records'][i]['hash']==p1['records'][i]['hash']
for a,b in zip(p0['records'],p1['records']):
 if a['layout_id'] not in {50,51,31000,31001,31002,31003}:assert a['hash']==b['hash']
(out/'INPUT_AUDIT.json').write_text(json.dumps({'passed':True,'datasets':audits,'same_validation_and_original_raw':True,'same_added_frame_budget':920},indent=2))
PY
for variant in ordinary recovery; do
 CFG="$SIM_ROOT/scripts/pi05_paired_${variant}_pilot40_20260928.env"
 status "training_${variant}"
 PI05_LOCAL_CONFIG="$CFG" bash "$WORKSPACE/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/train_pi05_package_sorting_local.sh" > "$RUN_DIR/train_${variant}.log" 2>&1
 python3 - "$WORKSPACE/lerobot/outputs/paired_${variant}_pilot40_20260928" "$RUN_DIR/checkpoint_${variant}.txt" <<'PY'
from pathlib import Path
import sys,json
runs=list(Path(sys.argv[1]).glob('package_sorting_pi05_*'));assert len(runs)==1
run=runs[0];val=[json.loads(x) for x in (run/'validation.jsonl').read_text().splitlines()]
assert val[-1]['step']==7240 and val[-1]['validation/frames']==780
cp=run/'checkpoints/last/pretrained_model';assert (cp/'model.safetensors').is_file()
Path(sys.argv[2]).write_text(str(cp.resolve())+'\n')
PY
 POLICY="$(cat "$RUN_DIR/checkpoint_${variant}.txt")"
 for seed in 0 1 2; do
  status "evaluating_${variant}_seed${seed}"
  PI05_LOCAL_CONFIG="$CFG" PI05_POLICY_PATH="$POLICY" PI05_RECORD_DIR="$RUN_DIR/${variant}_seed${seed}" PI05_EVAL_SEED="$seed" PI05_PROMPT_VARIANT=short bash "$SIM_ROOT/scripts/run_pi05_paired_sim.sh" --policy-max-action-step 0 > "$RUN_DIR/eval_${variant}_seed${seed}.log" 2>&1
 done
 python3 "$SIM_ROOT/scripts/summarize_paired_evaluation.py" --roots "$RUN_DIR/${variant}_seed0/rollouts" "$RUN_DIR/${variant}_seed1/rollouts" "$RUN_DIR/${variant}_seed2/rollouts" --output "$RUN_DIR/EVALUATION_${variant}.json"
done
status rechecking_frozen_baseline
CFG="$SIM_ROOT/scripts/pi05_paired_pilot32_b_20260924.env"
POLICY="$(cat "$SIM_ROOT/demo/paired_zero_ab_experiment_20260924_r1/checkpoint_b.txt")"
for seed in 0 1 2; do
 status "evaluating_baseline_seed${seed}"
 PI05_LOCAL_CONFIG="$CFG" PI05_POLICY_PATH="$POLICY" PI05_RECORD_DIR="$RUN_DIR/baseline_seed${seed}" PI05_EVAL_SEED="$seed" PI05_PROMPT_VARIANT=short bash "$SIM_ROOT/scripts/run_pi05_paired_sim.sh" --policy-max-action-step 0 > "$RUN_DIR/eval_baseline_seed${seed}.log" 2>&1
done
python3 "$SIM_ROOT/scripts/summarize_paired_evaluation.py" --roots "$RUN_DIR/baseline_seed0/rollouts" "$RUN_DIR/baseline_seed1/rollouts" "$RUN_DIR/baseline_seed2/rollouts" --output "$RUN_DIR/EVALUATION_baseline.json"
status numeric_complete_visual_review_pending
