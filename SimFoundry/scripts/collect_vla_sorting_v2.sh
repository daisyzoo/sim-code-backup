#!/usr/bin/env bash
# Re-collection entry after the 2026-09-16 scene/quality overhaul.
# Usage: collect_vla_sorting_v2.sh MIX TAG [MAX_ATTEMPTS]
set -euo pipefail
source ~/miniconda3/etc/profile.d/conda.sh
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1 PYTHONUNBUFFERED=1
cd /home/user/Documents/zoo/sim/IsaacLab

MIX="${1:-push_box_to_bin:2,nudge_mailer_to_bin:2,wait_no_package:1}"
TAG="${2:-v2_smoke_20260916}"
ATTEMPTS="${3:-10}"
NPZ_OUT="../SimFoundry/datasets/sorting_station_g1_23_vla_${TAG}"
UNITREE_OUT="../SimFoundry/datasets/sorting_station_g1_23_unitree_vla_${TAG}"
LOG="/tmp/collect_vla_${TAG}.log"

./isaaclab.sh -p ../SimFoundry/scripts/collect_seed.py \
  --scene-id sorting_station_g1_23 \
  --task-mix "${MIX}" \
  --device cuda \
  --viz none \
  --unitree \
  --quality-gate \
  --sorting-expert cartesian \
  --max-attempts "${ATTEMPTS}" \
  --out-dir "${NPZ_OUT}" \
  --unitree-out "${UNITREE_OUT}" \
  2>&1 | tee "${LOG}"

echo "done: $(find "${UNITREE_OUT}" -mindepth 1 -maxdepth 1 -type d -name 'episode_*' | wc -l) episodes in ${UNITREE_OUT}"
