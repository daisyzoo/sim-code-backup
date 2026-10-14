#!/usr/bin/env bash
set -euo pipefail
WORLDLAB_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$WORLDLAB_ROOT/run_recording_tour.sh" --scenes hallway2_blend --seconds 15 --repeats 3 --prepare 15 "$@"
