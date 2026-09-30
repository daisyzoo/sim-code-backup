#!/usr/bin/env bash

# Isolated persistent RTC experiment runner. It reuses the normal interactive
# script's configuration and validation, but keeps policy weights loaded while
# its own terminal menu changes runtime settings between tests.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PERSISTENT_DEBUG=true exec "${SCRIPT_DIR}/eval_pi05_expert_only_pick_up_6d_15hz_rtc_interactive.sh" "$@"
