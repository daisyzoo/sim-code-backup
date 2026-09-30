#!/usr/bin/env bash
# Write frame-weight policy + launch weighted PI0.5 training on inactive-park 300_r2.
set -Eeuo pipefail

SIM_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
LEROBOT_SCRIPTS="/home/user/Documents/zoo/sim/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts"
# Always use the weighted env for this launcher (ignore inherited PI05_LOCAL_CONFIG).
ENV_FILE="${LEROBOT_SCRIPTS}/pi05_sim_sorting_vla_officialhand_inactivepark_300_r2_weighted_20260923.env"

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

PI05_PYTHON="${PI05_PYTHON:?}"
DATASET_ROOT="${DATASET_V30_ROOT:?}"
UNITREE_ROOT="${UNITREE_SOURCE_ROOT:?}"

echo "Writing sorting_frame_weight_policy.json ..."
"${PI05_PYTHON}" "${LEROBOT_SCRIPTS}/write_sorting_frame_weight_policy.py" \
    --lerobot-root "${DATASET_ROOT}" \
    --unitree-root "${UNITREE_ROOT}"

echo "Starting weighted PI0.5 training ..."
PI05_LOCAL_CONFIG="${ENV_FILE}" bash "${LEROBOT_SCRIPTS}/train_pi05_package_sorting_local.sh"
