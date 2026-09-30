#!/usr/bin/env bash
set -Eeuo pipefail
WORKSPACE=/home/user/Documents/zoo/sim
ROOT="$WORKSPACE/SimFoundry"
RUN="$ROOT/demo/state_relative_chunk10_20260929_r1"
CFG="$ROOT/scripts/pi05_paired_relative_chunk10_20260929.env"
PYTHON=/home/user/Desktop/project/vla/env/.venv/bin/python
OUT="$RUN/evaluation"
PROTOCOL="$ROOT/demo/spatial_generalization_20260928_r1/heldout_protocol.json"
export PI05_POLICY_PORT=18777
status() { python3 - "$RUN/STATUS.json" "$1" <<'PY'
import sys,json,datetime
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':sys.argv[2],'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'goal_complete':False},indent=2))
PY
}
trap 'status failed_runtime_or_gate' ERR
export PYTHONPATH="$WORKSPACE/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HOME="$WORKSPACE/lerobot/hf_home/pi05"
export LEROBOT_TOKENIZER_NAME_OVERRIDE="$WORKSPACE/lerobot/models/paligemma-3b-pt-224" LEROBOT_TOKENIZER_LOCAL_FILES_ONLY_OVERRIDE=true PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
SAVED_RUN="$WORKSPACE/lerobot/outputs/paired_relative_chunk10_20260929/package_sorting_pi05_1gpu_20260929_015655"
"$PYTHON" "$ROOT/scripts/validate_saved_relative_checkpoint.py" --checkpoint "$SAVED_RUN/checkpoints/014480/pretrained_model" --out "$SAVED_RUN/validation.jsonl" > "$RUN/recovered_validation.log" 2>&1
python3 - "$WORKSPACE" "$RUN" <<'PY'
import json,sys
from pathlib import Path
w,r=map(Path,sys.argv[1:]);runs=list((w/'lerobot/outputs/paired_relative_chunk10_20260929').glob('package_sorting_pi05_*'));assert len(runs)==1;run=runs[0]
old=list((w/'lerobot/outputs/paired_coverage_chunk10_20260928').glob('package_sorting_pi05_*'))[0]
assert json.loads((run/'trainable_parameters.json').read_text())==json.loads((old/'trainable_parameters.json').read_text())
a=json.loads((run/'prefix_sampling_audit.json').read_text());assert a['passed'] and a['training_frames']==9080
assert a['per_episode']==json.loads((old/'prefix_sampling_audit.json').read_text())['per_episode']
v=[json.loads(l) for l in (run/'validation.jsonl').read_text().splitlines()];assert v[-1]['step']==14480 and v[-1]['validation/frames']==1560
cp=(run/'checkpoints/last/pretrained_model').resolve();assert (cp/'model.safetensors').is_file();(r/'checkpoint.txt').write_text(str(cp)+'\n')
c=json.loads((cp/'config.json').read_text());assert c['chunk_size']==c['n_action_steps']==10 and c['joint_action_representation']=='state_relative_arm10'
PY
CP="$(cat "$RUN/checkpoint.txt")"
export PYTHONPATH="$WORKSPACE/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HOME="$WORKSPACE/lerobot/hf_home/pi05"
export LEROBOT_TOKENIZER_NAME_OVERRIDE="$WORKSPACE/lerobot/models/paligemma-3b-pt-224" LEROBOT_TOKENIZER_LOCAL_FILES_ONLY_OVERRIDE=true PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
status auditing_trained_checkpoint
"$PYTHON" "$ROOT/scripts/audit_checkpoint_training_stats.py" --checkpoint "$CP" --dataset "$WORKSPACE/lerobot/lerobot_sim_paired_coverage80_20260928" --stats "$RUN/label_preflight/train_only_relative_stats.json" --out "$RUN/CHECKPOINT_STATS.json"
"$PYTHON" "$ROOT/scripts/audit_effective_action_chunks.py" --checkpoint "$CP" --out "$RUN/EFFECTIVE_SOURCE_ACTION_CHUNKS_AUDIT.json"
status teacher_forced_replanning
"$PYTHON" "$ROOT/scripts/audit_demonstration_replanning.py" --checkpoint "$CP" --dataset "$WORKSPACE/lerobot/lerobot_sim_paired_coverage80_20260928" --groups candidate_07_center candidate_14_center --out "$RUN/demonstration_replanning_audit" > "$RUN/replanning_audit.log" 2>&1
python3 - "$WORKSPACE" "$RUN" <<'PY'
import json,shutil,sys
from pathlib import Path
w,r=map(Path,sys.argv[1:]);budget=json.loads((r/'STORAGE_PREFLIGHT.json').read_text());assert shutil.disk_usage(w).free>budget['reference_evaluation_bytes']*1.25+2*2**30
PY
mkdir "$OUT"
spatial_roots=()
for seed in 0 1 2; do
 status "evaluating_relative10_spatial_seed${seed}"
 dir="$OUT/relative10_spatial_seed${seed}"
 PI05_LOCAL_CONFIG="$CFG" PI05_POLICY_PATH="$CP" PI05_RECORD_DIR="$dir" PI05_EVAL_SEED="$seed" PI05_SPATIAL_PROTOCOL="$PROTOCOL" bash "$ROOT/scripts/run_pi05_spatial_sim.sh" > "$OUT/relative10_spatial_seed${seed}.log" 2>&1
 for lid in 58000 58001 58002 58003 58004 58005; do spatial_roots+=("$dir/layout_$lid"); done
 spatial_roots+=("$dir/wait")
 /home/user/miniconda3/envs/env_isaaclab/bin/python "$ROOT/scripts/make_rollout_review.py" --root "$dir" --out "$OUT/visual_materials/relative10_spatial_seed${seed}"
done
python3 "$ROOT/scripts/summarize_paired_evaluation.py" --roots "${spatial_roots[@]}" --output "$OUT/EVALUATION_relative10_spatial.json"
original_roots=()
for seed in 0 1 2; do
 status "evaluating_relative10_original_seed${seed}"
 dir="$OUT/relative10_original_seed${seed}"
 PI05_LOCAL_CONFIG="$CFG" PI05_POLICY_PATH="$CP" PI05_RECORD_DIR="$dir" PI05_EVAL_SEED="$seed" bash "$ROOT/scripts/run_pi05_paired_sim.sh" --policy-max-action-step 0 > "$OUT/relative10_original_seed${seed}.log" 2>&1
 original_roots+=("$dir/rollouts")
 /home/user/miniconda3/envs/env_isaaclab/bin/python "$ROOT/scripts/make_rollout_review.py" --root "$dir" --out "$OUT/visual_materials/relative10_original_seed${seed}"
done
python3 "$ROOT/scripts/summarize_paired_evaluation.py" --roots "${original_roots[@]}" --output "$OUT/EVALUATION_relative10_original.json"
status numeric_complete_actual_visual_review_required
