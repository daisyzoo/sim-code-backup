#!/usr/bin/env bash
set -Eeuo pipefail
WORKSPACE=/home/user/Documents/zoo/sim
ROOT="$WORKSPACE/SimFoundry"
RUN="$ROOT/demo/coverage_chunk10_20260928_r1"
CFG="$ROOT/scripts/pi05_paired_coverage_chunk10_20260928.env"
POLICY="$RUN/prefix_sampling_policy.json"
PROTOCOL="$ROOT/demo/spatial_generalization_20260928_r1/heldout_protocol.json"
PYTHON=/home/user/Desktop/project/vla/env/.venv/bin/python
OUT="$RUN/evaluation"
export PI05_POLICY_PORT=18776
status() { python3 - "$RUN/STATUS.json" "$1" <<'PY'
import json,sys,datetime
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':sys.argv[2],'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'goal_complete':False},indent=2))
PY
}
python3 - "$WORKSPACE" "$RUN" <<'PY'
import json,sys,hashlib,shutil
from pathlib import Path
w,r=map(Path,sys.argv[1:]);b=w/'SimFoundry/demo/spatial_prefix_experiment_20260928_r1';assert json.loads((b/'STATUS.json').read_text())['stage']=='complete_reviewed'
v=json.loads((b/'visual_review.json').read_text());assert v['reviewed'] and len(v['episodes'])==60
for p,h in v['episodes'].items():assert hashlib.sha256((Path(v['root'])/p).read_bytes()).hexdigest()==h
assert json.loads((r/'DECISION.json').read_text())['approved_for_training']
preflight=json.loads((r/'PREFLIGHT_ACTION_CHUNKS.json').read_text());assert preflight['passed'] and preflight['labels_per_chunk']==10 and preflight['training_frames_checked']==9080
continuity=json.loads((w/'SimFoundry/demo/coverage_model80_20260928_r1/demonstration_replanning_audit/REPORT.json').read_text());assert len(continuity['rows'])==24 and all(row['events'] for row in continuity['rows'])
ds=w/'lerobot/lerobot_sim_paired_coverage80_20260928';a=json.loads((ds/'meta/paired_export_audit.json').read_text());assert a['training_ready'] and a['frames']==10640 and a['train_frames']==9080
records=json.loads((ds/'meta/paired_provenance.json').read_text())['records'];assert len(records)==80
for row in records:assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['hash']
split=json.loads((ds/'meta/train_validation_split.json').read_text());assert len(split['train'])==68 and len(split['validation'])==12 and not set(split['train'])&set(split['validation'])
assert not (w/'lerobot/outputs/paired_coverage_chunk10_20260928').exists() and not (r/'evaluation').exists()
assert shutil.disk_usage(w).free>25*2**30
(r/'INPUT_AUDIT.json').write_text(json.dumps({'passed':True,'verified_raw_hashes':80,'prior_model_reviewed':60,'train_frames':9080,'all_existing_partitions_preserved':True},indent=2))
PY
trap 'status failed_runtime_or_gate' ERR
status training
PI05_PREFIX_SAMPLER_POLICY="$POLICY" PI05_LOCAL_CONFIG="$CFG" bash "$WORKSPACE/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/train_pi05_package_sorting_local.sh" > "$RUN/train.log" 2>&1
python3 - "$WORKSPACE" "$RUN" <<'PY'
import sys,json
from pathlib import Path
w,r=map(Path,sys.argv[1:]);runs=list((w/'lerobot/outputs/paired_coverage_chunk10_20260928').glob('package_sorting_pi05_*'));assert len(runs)==1;run=runs[0]
a=json.loads((run/'prefix_sampling_audit.json').read_text());assert a['passed'] and a['training_frames']==9080
old=list((w/'lerobot/outputs/paired_coverage80_20260928').glob('package_sorting_pi05_*'))[0];assert json.loads((run/'trainable_parameters.json').read_text())==json.loads((old/'trainable_parameters.json').read_text())
v=[json.loads(l) for l in (run/'validation.jsonl').read_text().splitlines()];assert v[-1]['step']==14480 and v[-1]['validation/frames']==1560
cp=(run/'checkpoints/last/pretrained_model').resolve();assert (cp/'model.safetensors').is_file();(r/'checkpoint.txt').write_text(str(cp)+'\n')
config=json.loads((cp/'config.json').read_text());assert config['chunk_size']==config['n_action_steps']==10
PY
CP="$(cat "$RUN/checkpoint.txt")"
mkdir "$OUT"
"$PYTHON" "$ROOT/scripts/audit_checkpoint_training_stats.py" --checkpoint "$CP" --dataset "$WORKSPACE/lerobot/lerobot_sim_paired_coverage80_20260928" --out "$RUN/CHECKPOINT_STATS.json"
status auditing_trained_action_windows
export PYTHONPATH="$WORKSPACE/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HOME="$WORKSPACE/lerobot/hf_home/pi05"
export LEROBOT_TOKENIZER_NAME_OVERRIDE="$WORKSPACE/lerobot/models/paligemma-3b-pt-224" LEROBOT_TOKENIZER_LOCAL_FILES_ONLY_OVERRIDE=true PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
"$PYTHON" "$ROOT/scripts/audit_effective_action_chunks.py" --checkpoint "$CP" --out "$RUN/EFFECTIVE_ACTION_CHUNKS_AUDIT.json"
status teacher_forced_replanning
"$PYTHON" "$ROOT/scripts/audit_demonstration_replanning.py" --checkpoint "$CP" --dataset "$WORKSPACE/lerobot/lerobot_sim_paired_coverage80_20260928" --groups candidate_07_center candidate_14_center --out "$RUN/demonstration_replanning_audit" > "$RUN/replanning_audit.log" 2>&1
status trained_waiting_for_coverage80_review
python3 - "$ROOT/demo/coverage_model80_20260928_r1" <<'PYWAIT'
import json,sys,time,hashlib
from pathlib import Path
root=Path(sys.argv[1]);deadline=time.monotonic()+7200
while True:
    stage=json.loads((root/'STATUS.json').read_text())['stage']
    if stage=='complete_reviewed':
        break
    if stage=='failed_runtime_or_gate':
        raise RuntimeError('Coverage80 baseline evaluation failed; preserve new checkpoint and stop comparison')
    if time.monotonic()>deadline:
        raise TimeoutError('Two-hour baseline review wait exceeded')
    time.sleep(10)
review=json.loads((root/'visual_review.json').read_text())
assert review['reviewed'] and len(review['episodes'])==60
for path,digest in review['episodes'].items():
    assert hashlib.sha256((Path(review['root'])/path).read_bytes()).hexdigest()==digest
PYWAIT
spatial_roots=()
for seed in 0 1 2; do
 status "evaluating_chunk10_spatial_seed${seed}"
 dir="$OUT/chunk10_spatial_seed${seed}"
 PI05_LOCAL_CONFIG="$CFG" PI05_POLICY_PATH="$CP" PI05_RECORD_DIR="$dir" PI05_EVAL_SEED="$seed" PI05_SPATIAL_PROTOCOL="$PROTOCOL" bash "$ROOT/scripts/run_pi05_spatial_sim.sh" > "$OUT/chunk10_spatial_seed${seed}.log" 2>&1
 for lid in 58000 58001 58002 58003 58004 58005; do spatial_roots+=("$dir/layout_$lid"); done
 spatial_roots+=("$dir/wait")
 /home/user/miniconda3/envs/env_isaaclab/bin/python "$ROOT/scripts/make_rollout_review.py" --root "$dir" --out "$OUT/visual_materials/chunk10_spatial_seed${seed}"
done
python3 "$ROOT/scripts/summarize_paired_evaluation.py" --roots "${spatial_roots[@]}" --output "$OUT/EVALUATION_chunk10_spatial.json"
original_roots=()
for seed in 0 1 2; do
 status "evaluating_chunk10_original_seed${seed}"
 dir="$OUT/chunk10_original_seed${seed}"
 PI05_LOCAL_CONFIG="$CFG" PI05_POLICY_PATH="$CP" PI05_RECORD_DIR="$dir" PI05_EVAL_SEED="$seed" bash "$ROOT/scripts/run_pi05_paired_sim.sh" --policy-max-action-step 0 > "$OUT/chunk10_original_seed${seed}.log" 2>&1
 original_roots+=("$dir/rollouts")
 /home/user/miniconda3/envs/env_isaaclab/bin/python "$ROOT/scripts/make_rollout_review.py" --root "$dir" --out "$OUT/visual_materials/chunk10_original_seed${seed}"
done
python3 "$ROOT/scripts/summarize_paired_evaluation.py" --roots "${original_roots[@]}" --output "$OUT/EVALUATION_chunk10_original.json"
python3 "$ROOT/scripts/compare_chunk_length_evaluations.py" --baseline-root "$ROOT/demo/coverage_model80_20260928_r1/evaluation" --candidate-root "$OUT" --protocol "$PROTOCOL" --out "$RUN/NUMERIC_COMPARISON.json"
status numeric_complete_actual_visual_review_required
