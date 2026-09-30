#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
ORCHESTRATOR="${REPO_ROOT}/scripts/run_g1_23_right_hand_cup_pick_ablation_6d_20hz.sh"

RUN_GROUP="${RUN_GROUP:-g1_23_right_hand_cup_pick_ablation_6d_20hz_float32_20k_seq_$(date +%Y%m%d_%H%M%S)}"
EXPERIMENTS="${EXPERIMENTS:-all}"
OUTPUT_ROOT="${OUTPUT_ROOT:-/media/igs/EAGET/syh/vla/outputs}"
LOG_ROOT_BASE="${LOG_ROOT_BASE:-/media/igs/EAGET/syh/vla/experiment_logs}"

exec env \
  ACTION="all" \
  RUN_GROUP="${RUN_GROUP}" \
  EXPERIMENTS="${EXPERIMENTS}" \
  OUTPUT_ROOT="${OUTPUT_ROOT}" \
  LOG_ROOT_BASE="${LOG_ROOT_BASE}" \
  "${ORCHESTRATOR}"
