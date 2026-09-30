#!/usr/bin/env bash
# Fixed-data four-epoch diagnostic; never mixes or generates training samples.
set -Eeuo pipefail
SIM_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE="$(dirname -- "$SIM_ROOT")"
RUN_DIR="${PAIRED_C4_RUN_DIR:?Set a fresh C4 experiment directory}"
CFG="$SIM_ROOT/scripts/pi05_paired_pilot32_c4_20260924.env"
[[ ! -e "$RUN_DIR" ]] || { echo "Refusing overwrite: $RUN_DIR" >&2; exit 1; }
mkdir -p "$RUN_DIR"
status() {
 python3 - "$RUN_DIR/STATUS.json" "$1" <<'PY'
import json,sys,datetime
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':sys.argv[2],'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
PY
}
trap 'status failed_runtime_or_gate' ERR
status checking_frozen_inputs
python3 - "$SIM_ROOT" "$RUN_DIR" <<'PY'
import json,sys,hashlib,shutil
from pathlib import Path
sim,out=map(Path,sys.argv[1:]);ws=sim.parent
root=ws/'lerobot/lerobot_sim_paired_zero_pilot32_b_20260924'
audit=json.loads((root/'meta/paired_export_audit.json').read_text())
assert audit['training_ready'] and audit['train_frames']==3620 and audit['frames']==4400
provenance=json.loads((root/'meta/paired_provenance.json').read_text());assert provenance['variant']=='short'
for r in provenance['records']:
 assert hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['hash']
def env(name):
 return dict(line.split('=',1) for line in (sim/'scripts'/name).read_text().splitlines() if line and not line.startswith('#'))
b=env('pi05_paired_pilot32_b_20260924.env');c=env('pi05_paired_pilot32_c4_20260924.env')
diff={k:[b.get(k),c.get(k)] for k in b.keys()|c.keys() if b.get(k)!=c.get(k)}
assert set(diff)=={'PI05_STEPS','PI05_OUTPUT_ROOT','WANDB_PROJECT_PI05'}
assert int(c['PI05_STEPS'])==4*audit['train_frames']
assert not Path(c['PI05_OUTPUT_ROOT']).exists()
(out/'INPUT_AUDIT.json').write_text(json.dumps({'passed':True,'config_differences':diff,'raw_hashes_unchanged':True,'note':'Total steps doubles; cosine decay endpoint follows steps. Same base, seed, data, sampling and raw h10 controller. Fixed previous test layouts are regression benchmarks, not fresh generalization evidence.'},indent=2))
for name in ('scripts/run_paired_c4_experiment.sh','scripts/pi05_paired_pilot32_c4_20260924.env','scripts/collect_paired_sorting.py','scripts/pi05_policy_server.py','scripts/run_pi05_paired_sim.sh','scripts/diagnose_paired_policy.py','simfoundry/data/paired_sorting.py'):
 target=out/'source_snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(sim/name,target)
PY
status training_c4
PI05_LOCAL_CONFIG="$CFG" bash "$WORKSPACE/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/train_pi05_package_sorting_local.sh" > "$RUN_DIR/train.log" 2>&1
python3 - "$WORKSPACE/lerobot/outputs/paired_zero_pilot32_c4_20260924" "$RUN_DIR/checkpoint.txt" <<'PY'
from pathlib import Path
import sys,json
runs=list(Path(sys.argv[1]).glob('package_sorting_pi05_*'));assert len(runs)==1
run=runs[0];val=[json.loads(x) for x in (run/'validation.jsonl').read_text().splitlines()]
assert val[-1]['step']==14480 and val[-1]['validation/frames']==780
cp=run/'checkpoints/last/pretrained_model';assert (cp/'model.safetensors').is_file()
Path(sys.argv[2]).write_text(str(cp.resolve())+'\n')
PY
POLICY="$(cat "$RUN_DIR/checkpoint.txt")"
status offline_probes
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1 PYTHONPATH="$WORKSPACE/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src" /home/user/Desktop/project/vla/env/.venv/bin/python "$SIM_ROOT/scripts/diagnose_paired_policy.py" --experiment "$SIM_ROOT/demo/paired_zero_ab_experiment_20260924_r1" --checkpoint "$POLICY" --out-dir "$RUN_DIR/offline_probes" > "$RUN_DIR/offline_probes.log" 2>&1
for seed in 0 1 2; do
 status "evaluating_seed_${seed}"
 PI05_LOCAL_CONFIG="$CFG" PI05_POLICY_PATH="$POLICY" PI05_RECORD_DIR="$RUN_DIR/seed${seed}" PI05_EVAL_SEED="$seed" PI05_PROMPT_VARIANT=short bash "$SIM_ROOT/scripts/run_pi05_paired_sim.sh" --policy-max-action-step 0 > "$RUN_DIR/eval_seed${seed}.log" 2>&1
done
python3 "$SIM_ROOT/scripts/summarize_paired_evaluation.py" --roots "$RUN_DIR"/seed{0,1,2}/rollouts --output "$RUN_DIR/EVALUATION.json"
status numeric_evaluation_complete_visual_review_pending
