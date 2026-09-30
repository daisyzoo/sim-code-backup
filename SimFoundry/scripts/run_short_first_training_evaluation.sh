#!/usr/bin/env bash
# Prepared orchestration: actual export/label approval is required before launch.
set -Eeuo pipefail
WORKSPACE=/home/user/Documents/zoo/sim
ROOT="$WORKSPACE/SimFoundry"
RUN="$ROOT/demo/short_first_model40_20260929_r1"
DATASET="$WORKSPACE/lerobot/lerobot_sim_short_first_pilot40_20260929"
CFG="$ROOT/scripts/pi05_short_first_relative_chunk10_20260929.env"
BASELINE_CFG="$ROOT/scripts/pi05_paired_relative_chunk10_20260929.env"
BASELINE_CP="$WORKSPACE/lerobot/outputs/paired_relative_chunk10_20260929/package_sorting_pi05_1gpu_20260929_015655/checkpoints/014480/pretrained_model"
PYTHON=/home/user/Desktop/project/vla/env/.venv/bin/python
OUT="$RUN/evaluation"
LOCAL_PROTOCOL="$ROOT/demo/short_first_test_protocol_20260929_r1/heldout_protocol.json"
ORIGINAL_SPATIAL_PROTOCOL="$ROOT/demo/spatial_generalization_20260928_r1/heldout_protocol.json"
export PI05_POLICY_PORT=18778
status() { python3 - "$RUN/STATUS.json" "$1" <<'PY'
import sys,json,datetime
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps(dict(stage=sys.argv[2],updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),goal_complete=False),indent=2))
PY
}
# Fail before writing status or starting a trainer if data preparation is incomplete.
python3 - "$WORKSPACE" "$RUN" "$DATASET" <<'PY'
import hashlib,json,shutil,sys
from pathlib import Path
w,r,d=map(Path,sys.argv[1:]);decision=json.loads((r/'DECISION.json').read_text());assert decision['approved_for_training']
assert not (w/'lerobot/outputs/short_first_relative_chunk10_20260929').exists() and not (r/'evaluation').exists()
audit=json.loads((d/'meta/paired_export_audit.json').read_text());assert audit['training_ready'] and audit['episodes']==40 and audit['train_frames']==8380 and audit['train_episodes']==34 and audit['validation_episodes']==6
labels=json.loads((r/'label_preflight/REPORT.json').read_text());assert labels['passed'] and labels['training_frames']==8380 and labels['validation_episodes_queried']==[]
assert Path(labels['dataset']).resolve()==d.resolve()
records=json.loads((d/'meta/paired_provenance.json').read_text())['records'];assert len(records)==40
assert not {70014,70015}&{x['layout_id'] for x in records}
for row in records:assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['hash']
for name,digest in decision['source_sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest
assert shutil.disk_usage(w).free>json.loads((r/'STORAGE_PREFLIGHT.json').read_text())['required_bytes']
PY
trap 'status failed_runtime_or_gate' ERR
status training
PI05_PREFIX_SAMPLER_POLICY="$RUN/prefix_sampling_policy.json" PI05_LOCAL_CONFIG="$CFG" bash "$WORKSPACE/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/train_pi05_package_sorting_local.sh" > "$RUN/train.log" 2>&1
python3 - "$WORKSPACE" "$RUN" "$BASELINE_CP" <<'PY'
import json,sys
from pathlib import Path
w,r,base=map(Path,sys.argv[1:]);runs=list((w/'lerobot/outputs/short_first_relative_chunk10_20260929').glob('package_sorting_pi05_*'));assert len(runs)==1;run=runs[0]
assert json.loads((run/'trainable_parameters.json').read_text())==json.loads((base.parents[2]/'trainable_parameters.json').read_text())
a=json.loads((run/'prefix_sampling_audit.json').read_text());assert a['passed'] and a['training_frames']==8380
v=[json.loads(line) for line in (run/'validation.jsonl').read_text().splitlines()];assert v[-1]['step']==14480 and v[-1]['validation/frames']==1420
cp=(run/'checkpoints/last/pretrained_model').resolve();assert (cp/'model.safetensors').is_file();c=json.loads((cp/'config.json').read_text());assert c['chunk_size']==c['n_action_steps']==10 and c['joint_action_representation']=='state_relative_arm10'
(r/'checkpoint.txt').write_text(str(cp)+'\n')
PY
CP="$(cat "$RUN/checkpoint.txt")"
export PYTHONPATH="$WORKSPACE/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HOME="$WORKSPACE/lerobot/hf_home/pi05"
export LEROBOT_TOKENIZER_NAME_OVERRIDE="$WORKSPACE/lerobot/models/paligemma-3b-pt-224" LEROBOT_TOKENIZER_LOCAL_FILES_ONLY_OVERRIDE=true PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
status auditing_trained_checkpoint
"$PYTHON" "$ROOT/scripts/audit_checkpoint_training_stats.py" --checkpoint "$CP" --dataset "$DATASET" --stats "$RUN/label_preflight/train_only_relative_stats.json" --out "$RUN/CHECKPOINT_STATS.json"
"$PYTHON" "$ROOT/scripts/audit_effective_action_chunks.py" --checkpoint "$CP" --out "$RUN/EFFECTIVE_SOURCE_ACTION_CHUNKS_AUDIT.json"
python3 - "$WORKSPACE" "$RUN" <<'PY'
import json,shutil,sys
from pathlib import Path
w,r=map(Path,sys.argv[1:]);assert shutil.disk_usage(w).free>json.loads((r/'STORAGE_PREFLIGHT.json').read_text())['evaluation_budget_bytes']+2*2**30
PY
mkdir "$OUT"
# Each model uses its own original config/dataset/serialized processor statistics.
for variant in baseline new; do
 if [[ "$variant" == baseline ]]; then eval_cfg="$BASELINE_CFG";eval_cp="$BASELINE_CP";else eval_cfg="$CFG";eval_cp="$CP";fi
 local_roots=()
 for seed in 0 1 2; do
  status "evaluating_${variant}_local320_seed${seed}"
  dir="$OUT/${variant}_local320_seed${seed}"
  PI05_LOCAL_CONFIG="$eval_cfg" PI05_POLICY_PATH="$eval_cp" PI05_RECORD_DIR="$dir" PI05_EVAL_SEED="$seed" PI05_SPATIAL_PROTOCOL="$LOCAL_PROTOCOL" bash "$ROOT/scripts/run_pi05_short_first_sim.sh" > "$OUT/${variant}_local320_seed${seed}.log" 2>&1
  local_roots+=("$dir/layout_70014" "$dir/layout_70015" "$dir/wait")
  /home/user/miniconda3/envs/env_isaaclab/bin/python "$ROOT/scripts/make_rollout_review.py" --root "$dir" --out "$OUT/visual_materials/${variant}_local320_seed${seed}"
 done
 python3 "$ROOT/scripts/summarize_paired_evaluation.py" --roots "${local_roots[@]}" --output "$OUT/EVALUATION_${variant}_local320.json"
done
spatial_roots=()
for seed in 0 1 2; do
 status "evaluating_new_original_spatial160_seed${seed}"
 dir="$OUT/new_spatial160_seed${seed}"
 PI05_LOCAL_CONFIG="$CFG" PI05_POLICY_PATH="$CP" PI05_RECORD_DIR="$dir" PI05_EVAL_SEED="$seed" PI05_SPATIAL_PROTOCOL="$ORIGINAL_SPATIAL_PROTOCOL" bash "$ROOT/scripts/run_pi05_spatial_sim.sh" > "$OUT/new_spatial160_seed${seed}.log" 2>&1
 for lid in 58000 58001 58002 58003 58004 58005;do spatial_roots+=("$dir/layout_$lid");done
 spatial_roots+=("$dir/wait")
 /home/user/miniconda3/envs/env_isaaclab/bin/python "$ROOT/scripts/make_rollout_review.py" --root "$dir" --out "$OUT/visual_materials/new_spatial160_seed${seed}"
done
python3 "$ROOT/scripts/summarize_paired_evaluation.py" --roots "${spatial_roots[@]}" --output "$OUT/EVALUATION_new_spatial160.json"
original_roots=()
for seed in 0 1 2;do
 status "evaluating_new_original160_seed${seed}"
 dir="$OUT/new_original160_seed${seed}"
 PI05_LOCAL_CONFIG="$CFG" PI05_POLICY_PATH="$CP" PI05_RECORD_DIR="$dir" PI05_EVAL_SEED="$seed" bash "$ROOT/scripts/run_pi05_paired_sim.sh" --policy-max-action-step 0 > "$OUT/new_original160_seed${seed}.log" 2>&1
 original_roots+=("$dir/rollouts")
 /home/user/miniconda3/envs/env_isaaclab/bin/python "$ROOT/scripts/make_rollout_review.py" --root "$dir" --out "$OUT/visual_materials/new_original160_seed${seed}"
done
python3 "$ROOT/scripts/summarize_paired_evaluation.py" --roots "${original_roots[@]}" --output "$OUT/EVALUATION_new_original160.json"
status numeric_complete_actual_visual_review_required
