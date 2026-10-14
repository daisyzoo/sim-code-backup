#!/usr/bin/env bash
# Source this file; does not install skills or modify any simulator environment.
WORLDLAB_PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export ISAAC_SIM_DIR="$WORLDLAB_PROJECT_ROOT/.venv/lib/python3.12/site-packages/isaacsim"
export ISAAC_LAB_DIR="$(dirname -- "$WORLDLAB_PROJECT_ROOT")/IsaacLab"
export WORKSPACE_DIR="$WORLDLAB_PROJECT_ROOT/outputs/skills"
