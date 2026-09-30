#!/usr/bin/env bash
set -euo pipefail

BUNDLE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${BUNDLE_DIR}/bundle.env"

if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  echo "ERROR: 请先创建并激活 venv，再运行本脚本。" >&2
  echo "示例: python${EXPECTED_PYTHON} -m venv /path/to/venv && source /path/to/venv/bin/activate" >&2
  exit 2
fi

ACTUAL_PREFIX="$(python -c 'import sys; print(sys.prefix)')"
if [[ "$(readlink -f "${ACTUAL_PREFIX}")" != "$(readlink -f "${VIRTUAL_ENV}")" ]]; then
  echo "ERROR: 当前 python 不属于 VIRTUAL_ENV=${VIRTUAL_ENV}" >&2
  exit 2
fi

ACTUAL_PYTHON="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "${ACTUAL_PYTHON}" != "${EXPECTED_PYTHON}" ]]; then
  echo "ERROR: ${BUNDLE_NAME} 要求 Python ${EXPECTED_PYTHON}，当前是 ${ACTUAL_PYTHON}。" >&2
  exit 2
fi
if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "x86_64" ]]; then
  echo "ERROR: 该离线包只支持 Linux x86_64。" >&2
  exit 2
fi

export TMPDIR="${TMPDIR:-${BUNDLE_DIR}/tmp}"
export PIP_CACHE_DIR="${PIP_CACHE_DIR:-${BUNDLE_DIR}/pip-cache}"
mkdir -p "${TMPDIR}" "${PIP_CACHE_DIR}"

# Some minimal/container Python builds intentionally omit ensurepip.  Reuse pip
# when the venv already has it; otherwise bootstrap pip from the bundled wheel.
if ! python -m pip --version >/dev/null 2>&1; then
  PIP_WHEEL="${BUNDLE_DIR}/wheelhouse/pip-25.3-py3-none-any.whl"
  if [[ ! -f "${PIP_WHEEL}" ]]; then
    echo "ERROR: 当前 venv 没有 pip，且离线 pip wheel 不存在: ${PIP_WHEEL}" >&2
    exit 2
  fi
  PYTHONPATH="${PIP_WHEEL}" python -m pip install \
    --no-index \
    --no-deps \
    "${PIP_WHEEL}"
fi
python -m pip --version
python -m pip install \
  --no-index \
  --find-links "${BUNDLE_DIR}/wheelhouse" \
  --no-deps \
  -r "${BUNDLE_DIR}/requirements.lock"
python -m pip install \
  --no-index \
  --find-links "${BUNDLE_DIR}/wheelhouse" \
  --no-build-isolation \
  --no-deps \
  -e "${BUNDLE_DIR}/${PROJECT_RELATIVE_PATH}"

python "${BUNDLE_DIR}/verify_environment.py"

echo
echo "安装完成: ${BUNDLE_NAME}"
echo "venv: ${VIRTUAL_ENV}"
echo "项目: ${BUNDLE_DIR}/${PROJECT_RELATIVE_PATH}"
echo "GPU 验证: python ${BUNDLE_DIR}/verify_environment.py --require-gpu"
