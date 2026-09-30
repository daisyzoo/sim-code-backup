#!/usr/bin/env bash
set -Eeuo pipefail
WORKSPACE=/home/user/Documents/zoo/sim
ROOT="$WORKSPACE/SimFoundry"
RUN="$ROOT/demo/coverage_model80_20260928_r1"
PYTHON=/home/user/Desktop/project/vla/env/.venv/bin/python
python3 - "$RUN" <<'PY'
import json,time,sys
from pathlib import Path
root=Path(sys.argv[1]);deadline=time.monotonic()+3600
while not (root/'checkpoint.txt').exists():
    status=json.loads((root/'STATUS.json').read_text())['stage']
    if status=='failed_runtime_or_gate':
        raise RuntimeError('Main training workflow failed; do not continue audits')
    if time.monotonic()>deadline:
        raise TimeoutError('Checkpoint wait exceeded one hour')
    time.sleep(10)
checkpoint=Path((root/'checkpoint.txt').read_text().strip())
config=json.loads((checkpoint/'train_config.json').read_text())
assert config['steps']==14480
assert Path(config['dataset']['root']).name=='lerobot_sim_paired_coverage80_20260928'
(root/'POSTTRAIN_AUDIT_STATUS.json').write_text(json.dumps({'stage':'checking_effective_action_windows','goal_complete':False}))
PY
CP="$(cat "$RUN/checkpoint.txt")"
export PYTHONPATH="$WORKSPACE/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HOME="$WORKSPACE/lerobot/hf_home/pi05"
export LEROBOT_TOKENIZER_NAME_OVERRIDE="$WORKSPACE/lerobot/models/paligemma-3b-pt-224" LEROBOT_TOKENIZER_LOCAL_FILES_ONLY_OVERRIDE=true PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
"$PYTHON" "$ROOT/scripts/audit_effective_action_chunks.py" --checkpoint "$CP" --out "$RUN/EFFECTIVE_ACTION_CHUNKS_AUDIT.json"
python3 - "$RUN/POSTTRAIN_AUDIT_STATUS.json" <<'PY'
import json,sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':'teacher_forced_replanning','goal_complete':False}))
PY
"$PYTHON" "$ROOT/scripts/audit_demonstration_replanning.py" --checkpoint "$CP" --dataset "$WORKSPACE/lerobot/lerobot_sim_paired_coverage80_20260928" --groups candidate_07_center candidate_14_center --out "$RUN/demonstration_replanning_audit"
python3 - "$RUN/POSTTRAIN_AUDIT_STATUS.json" <<'PY'
import json,sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':'complete_requires_interpretation','goal_complete':False}))
PY
