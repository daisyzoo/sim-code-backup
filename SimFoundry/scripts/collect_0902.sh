#!/usr/bin/env bash
# 0902 batch: 100 left-hand black mailer + 100 right-hand wood box → unitree_0902
set -euo pipefail
source ~/miniconda3/etc/profile.d/conda.sh
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1
cd /home/user/Documents/zoo/sim/IsaacLab

UNITREE_OUT="../SimFoundry/datasets/sorting_station_g1_23_unitree_0902"

echo "=== Phase 1/2: 100× nudge_mailer_to_bin (left hand, black mailer → left) ==="
./isaaclab.sh -p ../SimFoundry/scripts/collect_seed.py \
  --scene-id sorting_station_g1_23 \
  --task-id nudge_mailer_to_bin \
  --num-episodes 100 \
  --device cuda \
  --unitree \
  --quality-gate \
  --max-attempts 80 \
  --wipe \
  --out-dir ../SimFoundry/datasets/sorting_station_g1_23_0902_mailer \
  --unitree-out "${UNITREE_OUT}" \
  2>&1 | tee /tmp/collect_0902_mailer.log

echo "=== Phase 2/2: 100× push_box_to_bin (right hand, wood box → right) ==="
./isaaclab.sh -p ../SimFoundry/scripts/collect_seed.py \
  --scene-id sorting_station_g1_23 \
  --task-id push_box_to_bin \
  --num-episodes 100 \
  --device cuda \
  --unitree \
  --quality-gate \
  --max-attempts 60 \
  --out-dir ../SimFoundry/datasets/sorting_station_g1_23_0902 \
  --unitree-out "${UNITREE_OUT}" \
  2>&1 | tee /tmp/collect_0902_box.log

echo "done: $(ls -d ../SimFoundry/datasets/sorting_station_g1_23_unitree_0902/episode_* | wc -l) episodes in ${UNITREE_OUT}"
