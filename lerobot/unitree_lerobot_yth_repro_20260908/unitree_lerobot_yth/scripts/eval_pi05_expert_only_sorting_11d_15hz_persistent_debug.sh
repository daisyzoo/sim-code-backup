#!/usr/bin/env bash

# Keep the sorting policy loaded while switching RTC debug modes interactively.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PERSISTENT_DEBUG=true exec "${SCRIPT_DIR}/eval_pi05_expert_only_sorting_11d_15hz_rtc_interactive.sh" "$@"
