#!/usr/bin/env bash
set -Eeuo pipefail
cd /home/user/Documents/zoo/sim
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
PYTHON=/home/user/Desktop/project/vla/env/.venv/bin/python
PUSH=SimFoundry/demo/paired_zero_push24_release_20260924_r1
WAIT=SimFoundry/demo/paired_zero_wait8_20260924_r2
variants=("$@")
if [[ ${#variants[@]} -eq 0 ]]; then variants=(ordinary recovery); fi
for variant in "${variants[@]}"; do
 [[ "$variant" == ordinary || "$variant" == recovery ]] || exit 2
 if [[ "$variant" == ordinary ]]; then
  sources=(SimFoundry/demo/ordinary_pilot8_20260928_r1)
 else
  sources=(SimFoundry/demo/recovery_push4_20260928_r1 SimFoundry/demo/recovery_wait_31000_20260928_r1 SimFoundry/demo/recovery_wait_31001_20260928_r1 SimFoundry/demo/recovery_wait_31002_20260928_r1 SimFoundry/demo/recovery_wait_31003_20260928_r1)
 fi
 dataset="lerobot/lerobot_sim_paired_${variant}_pilot40_20260928"
 repo="local/paired_${variant}_pilot40_20260928"
 "$PYTHON" SimFoundry/scripts/prepare_paired_sorting_lerobot.py --source "$PUSH" "$WAIT" "${sources[@]}" --out-root "$dataset" --repo-id "$repo" --validation-layouts 20,21,10006,10007 --variant short
 "$PYTHON" SimFoundry/scripts/audit_paired_lerobot.py --dataset "$dataset" --repo-id "$repo"
done
