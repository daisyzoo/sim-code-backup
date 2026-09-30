#!/usr/bin/env bash
# Resume 0910b: 7 paper-box episodes already on disk (do not --wipe).
# Target: 12 box + 12 mailer + 4 wait. Remaining = 5 + 12 + 4.
set -euo pipefail
source ~/miniconda3/etc/profile.d/conda.sh
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1
cd /home/user/Documents/zoo/sim/IsaacLab

NPZ_OUT="../SimFoundry/datasets/sorting_station_g1_23_vla_0910b"
UNITREE_OUT="../SimFoundry/datasets/sorting_station_g1_23_unitree_vla_0910b"
LOG="/tmp/collect_vla_0910b.log"

./isaaclab.sh -p ../SimFoundry/scripts/collect_seed.py \
  --scene-id sorting_station_g1_23 \
  --task-mix push_box_to_bin:5,nudge_mailer_to_bin:12,wait_no_package:4 \
  --device cuda \
  --viz none \
  --unitree \
  --quality-gate \
  --max-attempts 80 \
  --out-dir "${NPZ_OUT}" \
  --unitree-out "${UNITREE_OUT}" \
  2>&1 | tee "${LOG}"

echo "done: $(ls -d ${UNITREE_OUT}/episode_* 2>/dev/null | wc -l) episodes in ${UNITREE_OUT}"
