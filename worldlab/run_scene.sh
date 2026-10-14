#!/usr/bin/env bash
set -euo pipefail
WORLDLAB_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1 OMNI_KIT_ACCEPT_EULA=YES
exec "$WORLDLAB_ROOT/.venv/bin/python" "$WORLDLAB_ROOT/scripts/view_scene.py" "$@"
