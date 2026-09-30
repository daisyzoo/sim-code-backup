#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# Prefetch runtime weights that otherwise download on the first pipeline run:
#   rembg u2netp          (~5 MB, ~/.u2net or ~/.rembg)
#   Hunyuan hy3dgen       (~15 GB, ~/.cache/hy3dgen/tencent/Hunyuan3D-2.1)
#   facebook/dinov2-giant (paint backbone, same hy3dgen tree)
#
# Shape and paint share the hy3dgen directory so Hunyuan is not fetched twice.
# Does not put tokens on argv; huggingface_hub reads HF_TOKEN from the environment.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENV_SIMFOUNDRY="${ENV_SIMFOUNDRY:-simfoundry}"
ENV_HUNYUAN="${ENV_HUNYUAN:-hunyuan}"
SKIP_REMBG=0
SKIP_HUNYUAN=0
SKIP_DINO=0

usage() {
  cat <<'EOF'
Usage: scripts/installation/prefetch_runtime_weights.sh [options]

Options:
  --env-simfoundry NAME   Env with rembg (default: simfoundry)
  --env-hunyuan NAME      Env with huggingface_hub (default: hunyuan)
  --skip-rembg
  --skip-hunyuan
  --skip-dino
  -h, --help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-simfoundry) ENV_SIMFOUNDRY="$2"; shift 2 ;;
    --env-hunyuan) ENV_HUNYUAN="$2"; shift 2 ;;
    --skip-rembg) SKIP_REMBG=1; shift ;;
    --skip-hunyuan) SKIP_HUNYUAN=1; shift ;;
    --skip-dino) SKIP_DINO=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

export PYTHONPATH="${REPO_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
export HF_HUB_DISABLE_XET="${HF_HUB_DISABLE_XET:-1}"

run_in_env() {
  local env_name="$1"
  shift
  if command -v mamba >/dev/null 2>&1 && mamba env list | awk '{print $1}' | grep -Fxq "${env_name}"; then
    env -u LD_LIBRARY_PATH mamba run -n "${env_name}" "$@"
  else
    "$@"
  fi
}

if [[ "${SKIP_REMBG}" != "1" ]]; then
  echo ">>> prefetch rembg u2netp"
  run_in_env "${ENV_SIMFOUNDRY}" python - <<'PY'
import os
os.environ.setdefault("SIMFOUNDRY_REMBG_MODEL", "u2netp")
from rembg import new_session
session = new_session("u2netp")
print("rembg u2netp ready:", type(session).__name__)
PY
fi

if [[ "${SKIP_HUNYUAN}" != "1" ]]; then
  echo ">>> prefetch Hunyuan hy3dgen (shape + paint)"
  run_in_env "${ENV_HUNYUAN}" python - <<'PY'
from simfoundry.pipeline.hunyuan_weights import prefetch_hunyuan_weights, hunyuan_local_dir
info = prefetch_hunyuan_weights(include_paint=True)
print("hunyuan weights ready:", info["hunyuan_local_dir"])
print("local dir:", hunyuan_local_dir())
PY
fi

if [[ "${SKIP_DINO}" != "1" ]]; then
  echo ">>> prefetch facebook/dinov2-giant"
  run_in_env "${ENV_HUNYUAN}" python - <<'PY'
from simfoundry.pipeline.hunyuan_weights import prefetch_dinov2_giant
info = prefetch_dinov2_giant()
print("dinov2-giant ready:", info["dino_local_dir"])
PY
fi

echo "prefetch_runtime_weights.sh done"
