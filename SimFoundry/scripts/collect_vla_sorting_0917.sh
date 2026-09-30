#!/usr/bin/env bash
# 0917 last-pass contact-sweep collect. New tree; never --wipe 0911/0912/0914/0915.
# $3 = max-attempts (smoke: 10, not 80 lottery).
set -euo pipefail
source ~/miniconda3/etc/profile.d/conda.sh
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1 PYTHONUNBUFFERED=1
cd /home/user/Documents/zoo/sim/IsaacLab

MIX="${1:-push_box_to_bin:2,nudge_mailer_to_bin:2,wait_no_package:1}"
TAG="${2:-0917_smoke}"
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
  --max-attempts "${ATTEMPTS}" \
  --out-dir "${NPZ_OUT}" \
  --unitree-out "${UNITREE_OUT}" \
  2>&1 | tee "${LOG}"

echo "done: $(ls -d ${UNITREE_OUT}/episode_* 2>/dev/null | wc -l) episodes in ${UNITREE_OUT}"
