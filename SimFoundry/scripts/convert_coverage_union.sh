#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=/home/user/Documents/zoo/sim/SimFoundry
RUN="$ROOT/demo/coverage_union80_20260928_r1"
DATASET=/home/user/Documents/zoo/sim/lerobot/lerobot_sim_paired_coverage80_20260928
PYTHON=/home/user/Desktop/project/vla/env/.venv/bin/python
status() { python3 - "$RUN/STATUS.json" "$1" <<'PY'
import json,sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'stage':sys.argv[2],'training_started':False,'goal_complete':False},indent=2))
PY
}
trap 'status failed_conversion_or_audit' ERR
python3 - "$RUN/SELECTION.json" "$DATASET" <<'PY'
import json,sys,shutil
from pathlib import Path
s=json.loads(Path(sys.argv[1]).read_text());assert s['approved_for_conversion'] and s['episodes']==80 and s['frames']==10640
assert not Path(sys.argv[2]).exists() and shutil.disk_usage(Path(sys.argv[2]).parent).free>15*2**30
PY
mapfile -t sources < "$RUN/selected_sources.txt"
validation_ids="$(cat "$RUN/selected_validation_ids.txt")"
status converting
"$PYTHON" "$ROOT/scripts/prepare_paired_sorting_lerobot.py" --source "${sources[@]}" --out-root "$DATASET" --repo-id local/paired_coverage80_20260928 --validation-layouts "$validation_ids" --variant short > "$RUN/convert.log" 2>&1
status auditing_export
"$PYTHON" "$ROOT/scripts/audit_paired_lerobot.py" --dataset "$DATASET" --repo-id local/paired_coverage80_20260928 > "$RUN/export_audit.log" 2>&1
python3 - "$DATASET" "$RUN" <<'PY'
import json,sys
from pathlib import Path
r,run=map(Path,sys.argv[1:]);a=json.loads((r/'meta/paired_export_audit.json').read_text());s=json.loads((run/'SELECTION.json').read_text());split=json.loads((r/'meta/train_validation_split.json').read_text());records=json.loads((r/'meta/paired_provenance.json').read_text())['records']
assert a['training_ready'] and a['frames']==10640 and a['train_frames']==9080
assert split==s['split'] and len(records)==80
for row,expected in zip(records,s['records']):assert row['hash']==expected['sha256']
(r/'meta/coverage_selection.json').write_bytes((run/'SELECTION.json').read_bytes())
(run/'EXPORT_REPORT.json').write_text(json.dumps({'passed':True,'episodes':80,'frames':10640,'train_frames':9080,'validation_frames':1560,'all_original_partitions_preserved':True,'full_spatial_groups_preserved':True,'training_started':False,'dataset':str(r)},indent=2))
print(json.dumps(a,indent=2))
PY
status converted_and_audited_not_trained
