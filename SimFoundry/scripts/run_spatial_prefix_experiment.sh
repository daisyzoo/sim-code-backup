#!/usr/bin/env bash
# Explicitly gated single-factor experiment; never approve its own visual review.
set -Eeuo pipefail
WORKSPACE=/home/user/Documents/zoo/sim
ROOT="$WORKSPACE/SimFoundry"
RUN="$ROOT/demo/spatial_prefix_experiment_20260928_r1"
BASELINE="$ROOT/demo/spatial_model_comparison_20260928_r1"
PROTOCOL="$ROOT/demo/spatial_generalization_20260928_r1/heldout_protocol.json"
CFG="$ROOT/scripts/pi05_paired_spatial_prefix40_20260928.env"
POLICY="$RUN/prefix_sampling_policy.json"
PYTHON=/home/user/Desktop/project/vla/env/.venv/bin/python
OUT="$RUN/evaluation"
status() { python3 - "$RUN/STATUS.json" "$1" <<'PY'
import sys,json,datetime
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':sys.argv[2],'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'goal_complete':False},indent=2))
PY
}
# Preflight before installing error trap: a non-approved draft stays a draft.
python3 - "$WORKSPACE" "$RUN" "$BASELINE" "$POLICY" <<'PY'
import sys,json,hashlib,shutil
from pathlib import Path
w,r,b,p=map(Path,sys.argv[1:]);policy=json.loads(p.read_text());assert policy['approved_for_training'] is True
assert json.loads((b/'STATUS.json').read_text())['stage']=='complete_reviewed'
assert (b/'NUMERIC_COMPARISON.json').is_file()
for kind,n in [('spatial',13),('original',7)]:
 for seed in range(3):
  review=json.loads((b/f'visual_materials/spatial_{kind}_seed{seed}/review.json').read_text());assert review['reviewed'] and len(review['episodes'])==n
  for path,digest in review['episodes'].items():assert hashlib.sha256((b/path).read_bytes()).hexdigest()==digest
assert not (w/'lerobot/outputs/paired_spatial_prefix40_20260928').exists()
assert not (r/'evaluation').exists() and shutil.disk_usage(w).free>25*2**30
ds=w/'lerobot/lerobot_sim_paired_spatial_pilot40_20260928';audit=json.loads((ds/'meta/paired_export_audit.json').read_text());assert audit['training_ready'] and audit['train_frames']==4540
records=json.loads((ds/'meta/paired_provenance.json').read_text())['records'];assert len(records)==40
for row in records:assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['hash']
(r/'INPUT_AUDIT.json').write_text(json.dumps({'passed':True,'raw_hashes_verified':40,'baseline_review_hashes_verified':60,'policy_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'train_frames':4540},indent=2))
PY
trap 'status failed_runtime_or_gate' ERR
status training
PI05_PREFIX_SAMPLER_POLICY="$POLICY" PI05_LOCAL_CONFIG="$CFG" bash "$WORKSPACE/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/train_pi05_package_sorting_local.sh" > "$RUN/train.log" 2>&1
python3 - "$WORKSPACE" "$RUN" <<'PY'
import sys,json
from pathlib import Path
w,r=map(Path,sys.argv[1:]);runs=list((w/'lerobot/outputs/paired_spatial_prefix40_20260928').glob('package_sorting_pi05_*'));assert len(runs)==1
run=runs[0];sampler=json.loads((run/'prefix_sampling_audit.json').read_text());assert sampler['passed'] and sampler['preserves_exact_episode_and_task_draw_counts']
old=list((w/'lerobot/outputs/paired_spatial_pilot40_20260928').glob('package_sorting_pi05_*'))[0]
assert json.loads((run/'trainable_parameters.json').read_text())==json.loads((old/'trainable_parameters.json').read_text())
v=[json.loads(x) for x in (run/'validation.jsonl').read_text().splitlines()];assert v[-1]['step']==7240 and v[-1]['validation/frames']==780
cp=(run/'checkpoints/last/pretrained_model').resolve();assert (cp/'model.safetensors').is_file();(r/'checkpoint.txt').write_text(str(cp)+'\n')
PY
CP="$(cat "$RUN/checkpoint.txt")"
mkdir "$OUT"
"$PYTHON" "$ROOT/scripts/audit_checkpoint_training_stats.py" --checkpoint "$CP" --dataset "$WORKSPACE/lerobot/lerobot_sim_paired_spatial_pilot40_20260928" --out "$RUN/CHECKPOINT_STATS.json"
status initial_branch_diagnostic
export PYTHONPATH="$WORKSPACE/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src:${PYTHONPATH:-}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HOME="$WORKSPACE/lerobot/hf_home/pi05"
export LEROBOT_TOKENIZER_NAME_OVERRIDE="$WORKSPACE/lerobot/models/paligemma-3b-pt-224" LEROBOT_TOKENIZER_LOCAL_FILES_ONLY_OVERRIDE=true
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
"$PYTHON" "$ROOT/scripts/audit_initial_visual_branch.py" --checkpoint "$CP" --dataset "$WORKSPACE/lerobot/lerobot_sim_paired_spatial_pilot40_20260928" --out "$RUN/initial_visual_branch_audit" > "$RUN/initial_branch.log" 2>&1
"$PYTHON" "$ROOT/scripts/audit_demonstrated_branch_phase.py" --frame 30 --checkpoint "$CP" --dataset "$WORKSPACE/lerobot/lerobot_sim_paired_spatial_pilot40_20260928" --out "$RUN/demonstrated_frame30_branch_audit" > "$RUN/frame30_branch.log" 2>&1
for audit in initial_visual_branch_audit demonstrated_frame30_branch_audit; do
 /home/user/miniconda3/envs/env_isaaclab/bin/python "$ROOT/scripts/summarize_branch_task_choice.py" --audit "$RUN/$audit" --out "$RUN/$audit/TASK_CHOICE.json"
done
spatial_roots=()
for seed in 0 1 2; do
 status "evaluating_prefix_spatial_seed${seed}"
 dir="$OUT/prefix_spatial_seed${seed}"
 PI05_LOCAL_CONFIG="$CFG" PI05_POLICY_PATH="$CP" PI05_RECORD_DIR="$dir" PI05_EVAL_SEED="$seed" PI05_SPATIAL_PROTOCOL="$PROTOCOL" bash "$ROOT/scripts/run_pi05_spatial_sim.sh" > "$OUT/prefix_spatial_seed${seed}.log" 2>&1
 for lid in 58000 58001 58002 58003 58004 58005; do spatial_roots+=("$dir/layout_$lid"); done
 spatial_roots+=("$dir/wait")
 /home/user/miniconda3/envs/env_isaaclab/bin/python "$ROOT/scripts/make_rollout_review.py" --root "$dir" --out "$OUT/visual_materials/prefix_spatial_seed${seed}"
done
python3 "$ROOT/scripts/summarize_paired_evaluation.py" --roots "${spatial_roots[@]}" --output "$OUT/EVALUATION_prefix_spatial.json"
original_roots=()
for seed in 0 1 2; do
 status "evaluating_prefix_original_seed${seed}"
 dir="$OUT/prefix_original_seed${seed}"
 PI05_LOCAL_CONFIG="$CFG" PI05_POLICY_PATH="$CP" PI05_RECORD_DIR="$dir" PI05_EVAL_SEED="$seed" bash "$ROOT/scripts/run_pi05_paired_sim.sh" --policy-max-action-step 0 > "$OUT/prefix_original_seed${seed}.log" 2>&1
 original_roots+=("$dir/rollouts")
 /home/user/miniconda3/envs/env_isaaclab/bin/python "$ROOT/scripts/make_rollout_review.py" --root "$dir" --out "$OUT/visual_materials/prefix_original_seed${seed}"
done
python3 "$ROOT/scripts/summarize_paired_evaluation.py" --roots "${original_roots[@]}" --output "$OUT/EVALUATION_prefix_original.json"
python3 "$ROOT/scripts/compare_sampling_evaluations.py" --baseline-root "$BASELINE" --candidate-root "$OUT" --protocol "$PROTOCOL" --out "$RUN/NUMERIC_COMPARISON.json"
status numeric_complete_actual_visual_review_required
