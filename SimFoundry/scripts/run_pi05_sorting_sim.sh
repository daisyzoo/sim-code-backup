#!/usr/bin/env bash
# Start PI0.5 policy server (vla venv) then run SimFoundry Isaac closed-loop demo.
set -Eeuo pipefail

SIM_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
ISAACLAB="${ISAACLAB_PATH:-/home/user/Documents/zoo/sim/IsaacLab}"
ENV_FILE="${PI05_LOCAL_CONFIG:-/home/user/Documents/zoo/sim/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/pi05_package_sorting_local.env}"
PORT="${PI05_POLICY_PORT:-18765}"
RECORD_DIR="${PI05_RECORD_DIR:-${SIM_ROOT}/demo/preview_pi05_sorting}"

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

PROJECT_ROOT="${PI05_PROJECT_ROOT:?}"
PYTHON_BIN="${PI05_PYTHON:?}"
if [[ -f "${PROJECT_ROOT}/src/lerobot/scripts/lerobot_train.py" ]]; then
    LEROBOT_ROOT="${PROJECT_ROOT}"
elif [[ -f "${PROJECT_ROOT}/unitree_lerobot/lerobot/src/lerobot/scripts/lerobot_train.py" ]]; then
    LEROBOT_ROOT="${PROJECT_ROOT}/unitree_lerobot/lerobot"
else
    echo "Cannot locate lerobot src under ${PROJECT_ROOT}" >&2
    exit 1
fi

POLICY_PATH="${PI05_POLICY_PATH:-/home/user/Documents/zoo/sim/lerobot/outputs/package_sorting_pi05_1gpu_20260909_122124/checkpoints/028562/pretrained_model}"
TOKENIZER_ROOT="${PI05_TOKENIZER_ROOT:?}"
DATASET_ROOT="${DATASET_V30_ROOT:?}"

unset ALL_PROXY all_proxy || true
export HTTP_PROXY="${HTTP_PROXY:-http://127.0.0.1:7897}"
export HTTPS_PROXY="${HTTPS_PROXY:-http://127.0.0.1:7897}"
export OMNI_KIT_ACCEPT_EULA=yes
export DISPLAY="${DISPLAY:-:1}"
export CUDA_VISIBLE_DEVICES="${GPU_IDS:-0}"
export PYTHONUNBUFFERED=1
export HF_HOME="${HF_HOME_ROOT:?}/pi05"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export LEROBOT_TOKENIZER_NAME_OVERRIDE="${TOKENIZER_ROOT}"
export LEROBOT_TOKENIZER_LOCAL_FILES_ONLY_OVERRIDE=true
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

mkdir -p "${RECORD_DIR}"
SERVER_LOG="${RECORD_DIR}/policy_server.log"
ISAAC_LOG="${RECORD_DIR}/isaac.log"

cleanup() {
    if [[ -n "${SERVER_PID:-}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
        kill "${SERVER_PID}" 2>/dev/null || true
        wait "${SERVER_PID}" 2>/dev/null || true
    fi
}
trap cleanup EXIT

echo "Starting PI0.5 server on :${PORT}"
PYTHONPATH="${LEROBOT_ROOT}/src:${PYTHONPATH:-}" "${PYTHON_BIN}" "${SIM_ROOT}/scripts/pi05_policy_server.py" \
    --host 127.0.0.1 --port "${PORT}" \
    --policy-path "${POLICY_PATH}" \
    --dataset-root "${DATASET_ROOT}" \
    --tokenizer-path "${TOKENIZER_ROOT}" \
    --seed "${PI05_EVAL_SEED:-0}" \
    --device cuda:0 \
    >"${SERVER_LOG}" 2>&1 &
SERVER_PID=$!

ready=0
for _ in $(seq 1 180); do
    if grep -q "PI05_SERVER_READY" "${SERVER_LOG}" 2>/dev/null; then
        ready=1
        break
    fi
    if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
        echo "policy server died; see ${SERVER_LOG}" >&2
        tail -n 80 "${SERVER_LOG}" >&2 || true
        exit 1
    fi
    sleep 1
done
if [[ "${ready}" != 1 ]]; then
    echo "timeout waiting for PI05_SERVER_READY; see ${SERVER_LOG}" >&2
    tail -n 80 "${SERVER_LOG}" >&2 || true
    exit 1
fi
echo "policy server ready (pid ${SERVER_PID})"

if [[ -f "${HOME}/miniconda3/etc/profile.d/conda.sh" ]]; then
    # shellcheck disable=SC1091
    source "${HOME}/miniconda3/etc/profile.d/conda.sh"
elif [[ -f "${HOME}/anaconda3/etc/profile.d/conda.sh" ]]; then
    # shellcheck disable=SC1091
    source "${HOME}/anaconda3/etc/profile.d/conda.sh"
fi
conda activate env_isaaclab

cd "${ISAACLAB}"
./isaaclab.sh -p "${SIM_ROOT}/scripts/demo_pi05_sorting.py" \
    --num_envs 1 --device cuda --viz kit \
    --save-preview --realtime \
    --policy-host 127.0.0.1 --policy-port "${PORT}" \
    --record-dir "${RECORD_DIR}" \
    "$@" 2>&1 | tee "${ISAAC_LOG}"
