#!/usr/bin/env bash
# Small VLA-ready sorting batch: physics-only gate, unified English prompt, wait clips.
# Motion: known scene pose → inboard contact → press → sweep a known bin distance.
# Do not mix 0902 kinematic-assist data or the failed geom-P smokes.
set -euo pipefail
source ~/miniconda3/etc/profile.d/conda.sh
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1
cd /home/user/Documents/zoo/sim/IsaacLab

NPZ_OUT="../SimFoundry/datasets/sorting_station_g1_23_vla_0910"
UNITREE_OUT="../SimFoundry/datasets/sorting_station_g1_23_unitree_vla_0910"
LOG="/tmp/collect_vla_0910.log"

./isaaclab.sh -p ../SimFoundry/scripts/collect_seed.py \
  --scene-id sorting_station_g1_23 \
  --task-mix push_box_to_bin:12,nudge_mailer_to_bin:12,wait_no_package:8 \
  --device cuda \
  --viz none \
  --unitree \
  --quality-gate \
  --max-attempts 80 \
  --wipe \
  --out-dir "${NPZ_OUT}" \
  --unitree-out "${UNITREE_OUT}" \
  2>&1 | tee "${LOG}"

echo "done: $(ls -d ${UNITREE_OUT}/episode_* 2>/dev/null | wc -l) episodes in ${UNITREE_OUT}"
