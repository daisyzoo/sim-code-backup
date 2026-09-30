#!/usr/bin/env bash
set -Eeuo pipefail
WORKSPACE=/home/user/Documents/zoo/sim
ROOT="$WORKSPACE/SimFoundry"
RUN="$ROOT/demo/spatial_generalization_20260928_r1"
PYTHON=/home/user/Desktop/project/vla/env/.venv/bin/python
DATASET="$WORKSPACE/lerobot/lerobot_sim_paired_spatial_pilot40_20260928"
python3 - "$RUN/RAW_SELECTION.json" "$RUN" <<'PY'
import json,sys
from pathlib import Path
p,out=map(Path,sys.argv[1:]);s=json.loads(p.read_text());assert s['stage']=='selected_raw_requires_conversion_audit'
assert s['selected_episodes']==40 and s['selected_frames']==5320 and len(s['source_roots'])==15
(out/'selected_sources.txt').write_text('\n'.join(s['source_roots'])+'\n')
(out/'selected_validation_ids.txt').write_text(','.join(map(str,s['validation_layouts']))+'\n')
PY
mapfile -t sources < "$RUN/selected_sources.txt"
validation_ids="$(cat "$RUN/selected_validation_ids.txt")"
"$PYTHON" "$ROOT/scripts/prepare_paired_sorting_lerobot.py" \
 --source "${sources[@]}" --out-root "$DATASET" --repo-id local/paired_spatial_pilot40_20260928 \
 --validation-layouts "$validation_ids" --variant short > "$RUN/convert.log" 2>&1
"$PYTHON" "$ROOT/scripts/audit_paired_lerobot.py" --dataset "$DATASET" --repo-id local/paired_spatial_pilot40_20260928 > "$RUN/export_audit.log" 2>&1
python3 - "$DATASET" "$RUN/RAW_SELECTION.json" <<'PY'
import json,sys
from pathlib import Path
r,selection=map(Path,sys.argv[1:]);a=json.loads((r/'meta/paired_export_audit.json').read_text())
assert a['training_ready'] and a['frames']==5320 and a['train_frames']==4540
(r/'meta/spatial_selection.json').write_bytes(selection.read_bytes())
print(json.dumps(a,indent=2))
PY
