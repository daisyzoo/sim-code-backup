#!/usr/bin/env bash
set -Eeuo pipefail
cd /home/user/Documents/zoo/sim
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
PYTHON=/home/user/Desktop/project/vla/env/.venv/bin/python
DATASET=lerobot/lerobot_sim_paired_waitonly_pilot40_20260928
REPO=local/paired_waitonly_pilot40_20260928
"$PYTHON" SimFoundry/scripts/prepare_paired_sorting_lerobot.py --source SimFoundry/demo/paired_zero_push24_release_20260924_r1 SimFoundry/demo/paired_zero_wait8_20260924_r2 SimFoundry/demo/ordinary_push4_release_20260928_r1 SimFoundry/demo/recovery_wait_31000_20260928_r1 SimFoundry/demo/recovery_wait_31001_20260928_r1 SimFoundry/demo/recovery_wait_31002_20260928_r1 SimFoundry/demo/recovery_wait_31003_20260928_r1 --out-root "$DATASET" --repo-id "$REPO" --validation-layouts 20,21,10006,10007 --variant short
"$PYTHON" SimFoundry/scripts/audit_paired_lerobot.py --dataset "$DATASET" --repo-id "$REPO"
