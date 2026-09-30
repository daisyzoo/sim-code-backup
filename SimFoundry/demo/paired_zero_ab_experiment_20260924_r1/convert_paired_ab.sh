#!/usr/bin/env bash
set -Eeuo pipefail
cd /home/user/Documents/zoo/sim
PYTHON_BIN=/home/user/Desktop/project/vla/env/.venv/bin/python
SOURCE_PUSH=/home/user/Documents/zoo/sim/SimFoundry/demo/paired_zero_push24_release_20260924_r1
SOURCE_WAIT=/home/user/Documents/zoo/sim/SimFoundry/demo/paired_zero_wait8_20260924_r2
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
for variant in a b; do
  text_variant=short
  if [[ "$variant" == a ]]; then text_variant=unified_ablation; fi
  dataset="/home/user/Documents/zoo/sim/lerobot/lerobot_sim_paired_zero_pilot32_${variant}_20260924"
  repo="local/paired_zero_pilot32_${variant}"
  "$PYTHON_BIN" SimFoundry/scripts/prepare_paired_sorting_lerobot.py --source "$SOURCE_PUSH" "$SOURCE_WAIT" --out-root "$dataset" --repo-id "$repo" --validation-layouts 20,21,10006,10007 --variant "$text_variant"
  "$PYTHON_BIN" SimFoundry/scripts/audit_paired_lerobot.py --dataset "$dataset" --repo-id "$repo"
done
