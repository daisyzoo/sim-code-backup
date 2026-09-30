#!/usr/bin/env bash
set -Eeuo pipefail
WORKSPACE=/home/user/Documents/zoo/sim
ROOT="$WORKSPACE/SimFoundry"
OUT="$ROOT/demo/contact_height_pause_20260928_r1"
source /home/user/miniconda3/etc/profile.d/conda.sh
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1 PYTHONUNBUFFERED=1
cd "$WORKSPACE/IsaacLab"
for variant in control z60; do
 extra=()
 if [[ "$variant" == z60 ]]; then extra=(--push-force-n 60 --push-force-axis z --push-force-start 70); fi
 ./isaaclab.sh -p "$ROOT/scripts/collect_paired_sorting.py" --device cuda --viz none --newton-contacts --role diagnostic --layout-start 60 --layouts 1 --wait-episodes 0 --steps 160 --trace-episode-contacts --recover-contact-height "${extra[@]}" --out-dir "$OUT/$variant" > "$OUT/$variant.log" 2>&1
done
