#!/usr/bin/env bash
# Guarded, serial A/B training and h10 evaluation. Does not collect more data.
set -Eeuo pipefail
SIM_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE="$(dirname -- "$SIM_ROOT")"
RUN_DIR="${PAIRED_RUN_DIR:?Set PAIRED_RUN_DIR to a fresh experiment directory}"
[[ ! -e "$RUN_DIR" ]] || { echo "Refusing to overwrite $RUN_DIR" >&2; exit 1; }
mkdir -p "$RUN_DIR"
status() {
  python3 - "$RUN_DIR/STATUS.json" "$1" <<'PY'
import json,sys,datetime
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':sys.argv[2],'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
PY
}
trap 'status failed_runtime_or_gate' ERR
status verifying_ab_inputs
python3 - "$WORKSPACE" "$RUN_DIR" <<'PY'
from pathlib import Path
import json,hashlib,sys
ws,out=map(Path,sys.argv[1:])
roots=[ws/f'lerobot/lerobot_sim_paired_zero_pilot32_{v}_20260924' for v in ('a','b')]
metas=[]
for root in roots:
 audit=json.loads((root/'meta/paired_export_audit.json').read_text())
 assert audit['training_ready'] and audit['episodes']==32 and audit['frames']==4400 and audit['train_frames']==3620
 metas.append(json.loads((root/'meta/paired_provenance.json').read_text()))
assert metas[0]['variant']=='unified_ablation' and metas[1]['variant']=='short'
assert [r['hash'] for r in metas[0]['records']]==[r['hash'] for r in metas[1]['records']]
for name in ('train_validation_split.json','train_only_stats.json'):
 assert (roots[0]/'meta'/name).read_bytes()==(roots[1]/'meta'/name).read_bytes(),name
videos=[]
for root in roots:
 videos.append({str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'videos').rglob('*.mp4'))})
assert videos[0] and videos[0]==videos[1], 'A/B encoded images differ'
assert len({r['exported_prompt'] for r in metas[0]['records']})==1
assert len({r['exported_prompt'] for r in metas[1]['records']})==3
(out/'AB_INPUT_AUDIT.json').write_text(json.dumps({'passed':True,'same_raw_hashes':True,'same_split_and_training_stats':True,'same_encoded_video_hashes':True,'episode_count':32,'frames':4400,'training_steps_each':7240,'seed_each':42},indent=2))
PY
for variant in a b; do
  cfg="$SIM_ROOT/scripts/pi05_paired_pilot32_${variant}_20260924.env"
  output_root="$WORKSPACE/lerobot/outputs/paired_zero_pilot32_${variant}_20260924"
  [[ ! -e "$output_root" ]] || { echo "Output root already exists: $output_root" >&2; exit 1; }
  status "training_${variant}"
  PI05_LOCAL_CONFIG="$cfg" bash "$WORKSPACE/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/train_pi05_package_sorting_local.sh" > "$RUN_DIR/train_${variant}.log" 2>&1
  python3 - "$output_root" "$RUN_DIR/checkpoint_${variant}.txt" <<'PY'
from pathlib import Path
import json,sys
root=Path(sys.argv[1]);runs=list(root.glob('package_sorting_pi05_*'))
assert len(runs)==1,runs
run=runs[0];val=[json.loads(x) for x in (run/'validation.jsonl').read_text().splitlines()]
assert val[-1]['step']==7240 and val[-1]['validation/frames']==780
path=run/'checkpoints/last/pretrained_model'
assert (path/'model.safetensors').is_file()
Path(sys.argv[2]).write_text(str(path.resolve())+'\n')
PY
done
for variant in a b; do
  cfg="$SIM_ROOT/scripts/pi05_paired_pilot32_${variant}_20260924.env"
  policy_path="$(cat "$RUN_DIR/checkpoint_${variant}.txt")"
  text_variant=short
  if [[ "$variant" == a ]]; then text_variant=unified_ablation; fi
  for seed in 0 1 2; do
    status "evaluating_${variant}_seed_${seed}"
    PI05_LOCAL_CONFIG="$cfg" PI05_POLICY_PATH="$policy_path" PI05_RECORD_DIR="$RUN_DIR/${variant}_seed${seed}" PI05_EVAL_SEED="$seed" PI05_PROMPT_VARIANT="$text_variant" bash "$SIM_ROOT/scripts/run_pi05_paired_sim.sh" > "$RUN_DIR/eval_${variant}_seed${seed}.log" 2>&1
  done
done
python3 "$SIM_ROOT/scripts/summarize_paired_evaluation.py" --roots "$RUN_DIR"/{a,b}_seed{0,1,2}/rollouts --output "$RUN_DIR/EVALUATION.json"
status numeric_evaluation_complete_visual_review_pending
