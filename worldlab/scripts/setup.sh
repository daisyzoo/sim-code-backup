#!/usr/bin/env bash
set -euo pipefail
WORLDLAB_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
WORLDLAB_PYTHON="${WORLDLAB_PYTHON:-python3.12}"
"$WORLDLAB_PYTHON" -c 'import sys; assert sys.version_info[:2] == (3, 12), "Python 3.12 required"'
"$WORLDLAB_PYTHON" -m venv "$WORLDLAB_ROOT/.venv-tools"
"$WORLDLAB_ROOT/.venv-tools/bin/python" -m pip install --no-cache-dir -r "$WORLDLAB_ROOT/requirements-tools.txt"
"$WORLDLAB_PYTHON" -m venv "$WORLDLAB_ROOT/.venv"
"$WORLDLAB_ROOT/.venv/bin/python" -m pip install --no-cache-dir -r "$WORLDLAB_ROOT/requirements-sim.txt"
"$WORLDLAB_ROOT/.venv-tools/bin/python" "$WORLDLAB_ROOT/scripts/build_kitchen.py"
