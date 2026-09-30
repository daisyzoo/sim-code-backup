#!/usr/bin/env bash
set -Eeuo pipefail
WORKSPACE=/home/user/Documents/zoo/sim
SIM_ROOT="$WORKSPACE/SimFoundry"
CONTRACT="$SIM_ROOT/demo/recovery_training_protocol_20260928_r1/recovery_pilot_contract.json"
python3 - "$CONTRACT" <<'PY'
import json,sys
assert json.load(open(sys.argv[1]))['approved_for_pilot'] is True
PY
source /home/user/miniconda3/etc/profile.d/conda.sh
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1 PYTHONUNBUFFERED=1
cd "$WORKSPACE/IsaacLab"
./isaaclab.sh -p "$SIM_ROOT/scripts/collect_paired_sorting.py" --device cuda --viz none --newton-contacts --role pilot --layout-start 50 --layouts 2 --wait-episodes 4 --wait-layout-start 31000 --out-dir "$SIM_ROOT/demo/ordinary_pilot8_20260928_r1"
./isaaclab.sh -p "$SIM_ROOT/scripts/collect_paired_sorting.py" --device cuda --viz none --newton-contacts --role pilot --layout-start 50 --layouts 2 --push-force-n 40 --recovery-pilot-contract "$CONTRACT" --out-dir "$SIM_ROOT/demo/recovery_push4_20260928_r1"
for spec in '31000 40 both 20' '31001 80 both 5' '31002 80 left 20' '31003 80 right 20'; do
 read -r layout force side start <<< "$spec"
 ./isaaclab.sh -p "$SIM_ROOT/scripts/collect_paired_sorting.py" --device cuda --viz none --newton-contacts --role pilot --layouts 0 --wait-episodes 1 --wait-layout-start "$layout" --wait-force-n "$force" --wait-force-side "$side" --wait-force-start "$start" --recovery-pilot-contract "$CONTRACT" --out-dir "$SIM_ROOT/demo/recovery_wait_${layout}_20260928_r1"
done
