#!/usr/bin/env bash
# Supplemental wait-only320 evaluation; requires explicit collector --wait-steps support.
set -Eeuo pipefail

SIM_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
ISAACLAB="${ISAACLAB_PATH:-/home/user/Documents/zoo/sim/IsaacLab}"
ENV_FILE="${PI05_LOCAL_CONFIG:-/home/user/Documents/zoo/sim/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/pi05_package_sorting_local.env}"
PORT="${PI05_POLICY_PORT:-18774}"
RECORD_DIR="${PI05_RECORD_DIR:?Set PI05_RECORD_DIR to a fresh evaluation directory}"

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

POLICY_PATH="${PI05_POLICY_PATH:?Set PI05_POLICY_PATH to the exact paired experiment checkpoint}"
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

if [[ -e "${RECORD_DIR}" ]]; then
    echo "Refusing to overwrite ${RECORD_DIR}" >&2
    exit 1
fi
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
    --dataset-root "${DATASET_ROOT}" --repo-id "${DATASET_REPO_ID:?}" \
    --tokenizer-path "${TOKENIZER_ROOT}" \
    --seed "${PI05_EVAL_SEED:-0}" --num-inference-steps 10 \
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

# Protocol validation happens before the first inference rollout.
"${PYTHON_BIN}" - "${PI05_SPATIAL_PROTOCOL:?}" "${RECORD_DIR}" "${PI05_EVAL_SEED:-0}" <<'CHECK'
import json,hashlib,sys
from pathlib import Path
p,r=map(Path,sys.argv[1:3]);d=json.loads(p.read_text())
assert d['horizon']==10 and d['policy_action_step_cap']==0 and d['push_steps']==320 and d['wait_steps']==320 and d['solver_steps']==10 and d['scope']=='fresh_short_first_test_group'
assert int(sys.argv[3]) in d['eval_seeds']
lines=[]
for row in d['layout_files']:
 f=Path(row['path']);assert hashlib.sha256(f.read_bytes()).hexdigest()==row['sha256']
 lid=json.loads(f.read_text())['layout_id'];assert f.name==f'layout_{lid}.json'
 lines.append(str(f))
assert len(lines)==2 and len(set(lines))==2
(r/'layout_inputs.txt').write_text('\n'.join(lines)+'\n')
(r/'evaluation_protocol.json').write_bytes(p.read_bytes())
(r/'wait_layout.txt').write_text(str(d['wait_layout_id']))
CHECK
mapfile -t layout_files < "${RECORD_DIR}/layout_inputs.txt"
wait_layout="$(cat "${RECORD_DIR}/wait_layout.txt")"
cd "${ISAACLAB}"
eval_roots=()
./isaaclab.sh -p "${SIM_ROOT}/scripts/collect_paired_sorting.py" \
    --device cuda --viz none --newton-contacts --role diagnostic \
    --horizon 10 --steps 320 --wait-steps 320 --layouts 0 --wait-episodes 1 --wait-layout-start "${wait_layout}" \
    --policy-host 127.0.0.1 --policy-port "${PORT}" --policy-max-action-step 0 \
    --eval-seed "${PI05_EVAL_SEED:-0}" --prompt-variant short \
    --out-dir "${RECORD_DIR}/wait" > "${RECORD_DIR}/wait.log" 2>&1
python3 "${SIM_ROOT}/scripts/summarize_paired_evaluation.py" --roots "${eval_roots[@]}" "${RECORD_DIR}/wait" --output "${RECORD_DIR}/EVALUATION.json"

python3 - "${RECORD_DIR}/wait" <<'VERIFY_WAIT_DURATION'
from pathlib import Path
import json,sys,numpy as np
root=Path(sys.argv[1]);rows=list(root.glob('layout_*/raw.npz'));assert len(rows)==1
with np.load(rows[0]) as z:assert len(z['q'])==len(z['action'])==len(z['rgb'])==320
assert json.loads((rows[0].parent/'quality.json').read_text())['frames']==320
assert json.loads((root/'STATUS.json').read_text())['status']=='evaluation_complete'
print('Actual wait trajectory duration verified: 320 frames')
VERIFY_WAIT_DURATION
