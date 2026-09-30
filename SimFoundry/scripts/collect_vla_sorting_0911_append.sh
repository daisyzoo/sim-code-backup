#!/usr/bin/env bash
# Append more feed-forward VLA-0911 clips. Never --wipe unitree_vla_0911.
# NPZ goes to a sidecar dir so ep000.npz from this run cannot overwrite 0911.
set -euo pipefail
source ~/miniconda3/etc/profile.d/conda.sh
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1 PYTHONUNBUFFERED=1
cd /home/user/Documents/zoo/sim/IsaacLab

MIX="${1:-push_box_to_bin:12,nudge_mailer_to_bin:12,wait_no_package:8}"
TAG="${2:-0911b}"
NPZ_OUT="../SimFoundry/datasets/sorting_station_g1_23_vla_${TAG}"
UNITREE_OUT="../SimFoundry/datasets/sorting_station_g1_23_unitree_vla_0911"
LOG="/tmp/collect_vla_${TAG}.log"

./isaaclab.sh -p ../SimFoundry/scripts/collect_seed.py \
  --scene-id sorting_station_g1_23 \
  --task-mix "${MIX}" \
  --device cuda \
  --viz none \
  --unitree \
  --quality-gate \
  --max-attempts 80 \
  --out-dir "${NPZ_OUT}" \
  --unitree-out "${UNITREE_OUT}" \
  2>&1 | tee "${LOG}"

echo "done: $(ls -d ${UNITREE_OUT}/episode_* 2>/dev/null | wc -l) episodes in ${UNITREE_OUT}"
