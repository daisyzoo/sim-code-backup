#!/usr/bin/env bash
# Append 100 black-mailer clips into sorting_station_g1_23_unitree_0901 (no wipe).
set -euo pipefail
source ~/miniconda3/etc/profile.d/conda.sh
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1
cd /home/user/Documents/zoo/sim/IsaacLab
./isaaclab.sh -p ../SimFoundry/scripts/collect_seed.py \
  --scene-id sorting_station_g1_23 \
  --task-id nudge_mailer_to_bin \
  --num-episodes 100 \
  --device cuda \
  --unitree \
  --quality-gate \
  --max-attempts 80 \
  --out-dir ../SimFoundry/datasets/sorting_station_g1_23_0901_mailer \
  --unitree-out ../SimFoundry/datasets/sorting_station_g1_23_unitree_0901 \
  2>&1 | tee /tmp/collect_0901_mailer.log
echo "episodes now: $(ls -d ../SimFoundry/datasets/sorting_station_g1_23_unitree_0901/episode_* | wc -l)"
