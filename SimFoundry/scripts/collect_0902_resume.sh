#!/usr/bin/env bash
# Resume 0902: finish remaining mailer clips, then 100 wood-box clips (no wipe).
set -euo pipefail
source ~/miniconda3/etc/profile.d/conda.sh
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1
cd /home/user/Documents/zoo/sim/IsaacLab

UNITREE_OUT="../SimFoundry/datasets/sorting_station_g1_23_unitree_0902"
have=$(ls -d "${UNITREE_OUT}"/episode_* 2>/dev/null | wc -l)
mailer_need=$((100 - have))
if (( mailer_need < 0 )); then mailer_need=0; fi

echo "episodes already: ${have}; remaining mailer: ${mailer_need}"

if (( mailer_need > 0 )); then
  echo "=== Phase 1/2: ${mailer_need}× nudge_mailer_to_bin (left hand, black → left) ==="
  ./isaaclab.sh -p ../SimFoundry/scripts/collect_seed.py \
    --scene-id sorting_station_g1_23 \
    --task-id nudge_mailer_to_bin \
    --num-episodes "${mailer_need}" \
    --device cuda \
    --unitree \
    --quality-gate \
    --max-attempts 80 \
    --out-dir ../SimFoundry/datasets/sorting_station_g1_23_0902_mailer \
    --unitree-out "${UNITREE_OUT}" \
    2>&1 | tee -a /tmp/collect_0902_mailer.log
fi

echo "=== Phase 2/2: 100× push_box_to_bin (right hand, wood → right) ==="
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
