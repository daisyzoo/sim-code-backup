#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/igs/Desktop/project/vla/unitree_lerobot"
VLA_ROOT="/media/igs/EAGET/syh/vla"

RUN_GROUP="${RUN_GROUP:-g1_23_right_hand_cup_pick_ablation_6d_20hz_$(date +%Y%m%d_%H%M%S)}"
OUTPUT_ROOT="${OUTPUT_ROOT:-${VLA_ROOT}/outputs}"
LOG_ROOT_BASE="${LOG_ROOT_BASE:-${VLA_ROOT}/experiment_logs}"
RUN_LOG_ROOT="${LOG_ROOT_BASE}/${RUN_GROUP}"

ACTION="${ACTION:-all}"              # prepare | train | all
EXPERIMENTS="${EXPERIMENTS:-all}"    # all | comma-separated experiment ids

PREPARE_BASELINE="${REPO_ROOT}/scripts/prepare_g1_23_right_hand_cup_pick_baseline_6d_20hz_dataset.sh"
PREPARE_BACKGROUND="${REPO_ROOT}/scripts/prepare_g1_23_right_hand_cup_pick_background_6d_20hz_dataset.sh"
PREPARE_MULTITASK="${REPO_ROOT}/scripts/prepare_g1_23_right_hand_cup_pick_and_lift_bag_multitask_6d_20hz_dataset.sh"

TRAIN_BASELINE="${REPO_ROOT}/scripts/train_pi05_lora_g1_23_right_hand_cup_pick_baseline_6d_20hz.sh"
TRAIN_BACKGROUND="${REPO_ROOT}/scripts/train_pi05_lora_g1_23_right_hand_cup_pick_background_6d_20hz.sh"
TRAIN_MULTITASK="${REPO_ROOT}/scripts/train_pi05_lora_g1_23_right_hand_cup_pick_and_lift_bag_multitask_6d_20hz.sh"
TRAIN_BASELINE_AUG="${REPO_ROOT}/scripts/train_pi05_lora_g1_23_right_hand_cup_pick_baseline_aug_6d_20hz.sh"
TRAIN_BASELINE_ZSCORE="${REPO_ROOT}/scripts/train_pi05_lora_g1_23_right_hand_cup_pick_baseline_action_zscore_6d_20hz.sh"

mkdir -p "${OUTPUT_ROOT}" "${RUN_LOG_ROOT}"

usage() {
  cat <<EOF
Usage:
  ACTION=all EXPERIMENTS=all ${0}

Environment variables:
  ACTION=prepare|train|all
  EXPERIMENTS=all or comma-separated list:
    exp01_baseline
    exp02_background
    exp03_multitask
    exp04_baseline_aug
    exp05_baseline_action_zscore
  RUN_GROUP=<group_name>
  OUTPUT_ROOT=<train_output_root>
  LOG_ROOT_BASE=<central_log_root>

Examples:
  ACTION=prepare EXPERIMENTS=exp01_baseline,exp02_background ${0}
  ACTION=train EXPERIMENTS=exp04_baseline_aug RUN_GROUP=my_run ${0}
EOF
}

normalize_experiments() {
  if [[ "${EXPERIMENTS}" == "all" ]]; then
    printf '%s\n' \
      exp01_baseline \
      exp02_background \
      exp03_multitask \
      exp04_baseline_aug \
      exp05_baseline_action_zscore
    return
  fi

  tr ',' '\n' <<<"${EXPERIMENTS}"
}

should_run_prepare() {
  [[ "${ACTION}" == "prepare" || "${ACTION}" == "all" ]]
}

should_run_train() {
  [[ "${ACTION}" == "train" || "${ACTION}" == "all" ]]
}

run_logged_step() {
  local exp_name="$1"
  local step_name="$2"
  shift 2

  local exp_log_dir="${RUN_LOG_ROOT}/${exp_name}"
  local log_file="${exp_log_dir}/${step_name}.log"
  mkdir -p "${exp_log_dir}"

  echo "[$(date '+%F %T')] start ${exp_name} ${step_name}" | tee -a "${log_file}"
  (
    set -euo pipefail
    "$@"
  ) 2>&1 | tee -a "${log_file}"
  echo "[$(date '+%F %T')] done ${exp_name} ${step_name}" | tee -a "${log_file}"
}

run_experiment() {
  local exp_id="$1"

  case "${exp_id}" in
    exp01_baseline)
      if should_run_prepare; then
        run_logged_step "${exp_id}" prepare "${PREPARE_BASELINE}"
      fi
      if should_run_train; then
        run_logged_step \
          "${exp_id}" \
          train \
          env \
          RUN_GROUP="${RUN_GROUP}" \
          OUTPUT_ROOT="${OUTPUT_ROOT}" \
          LOG_ROOT_BASE="${LOG_ROOT_BASE}" \
          JOB_NAME="g1_23_right_hand_cup_pick_6d20hz_${exp_id}" \
          "${TRAIN_BASELINE}"
      fi
      ;;
    exp02_background)
      if should_run_prepare; then
        run_logged_step "${exp_id}" prepare "${PREPARE_BACKGROUND}"
      fi
      if should_run_train; then
        run_logged_step \
          "${exp_id}" \
          train \
          env \
          RUN_GROUP="${RUN_GROUP}" \
          OUTPUT_ROOT="${OUTPUT_ROOT}" \
          LOG_ROOT_BASE="${LOG_ROOT_BASE}" \
          JOB_NAME="g1_23_right_hand_cup_pick_6d20hz_${exp_id}" \
          "${TRAIN_BACKGROUND}"
      fi
      ;;
    exp03_multitask)
      if should_run_prepare; then
        run_logged_step "${exp_id}" prepare "${PREPARE_MULTITASK}"
      fi
      if should_run_train; then
        run_logged_step \
          "${exp_id}" \
          train \
          env \
          RUN_GROUP="${RUN_GROUP}" \
          OUTPUT_ROOT="${OUTPUT_ROOT}" \
          LOG_ROOT_BASE="${LOG_ROOT_BASE}" \
          JOB_NAME="g1_23_right_hand_cup_pick_6d20hz_${exp_id}" \
          "${TRAIN_MULTITASK}"
      fi
      ;;
    exp04_baseline_aug)
      if should_run_prepare; then
        run_logged_step "${exp_id}" prepare "${PREPARE_BASELINE}"
      fi
      if should_run_train; then
        run_logged_step \
          "${exp_id}" \
          train \
          env \
          RUN_GROUP="${RUN_GROUP}" \
          OUTPUT_ROOT="${OUTPUT_ROOT}" \
          LOG_ROOT_BASE="${LOG_ROOT_BASE}" \
          JOB_NAME="g1_23_right_hand_cup_pick_6d20hz_${exp_id}" \
          "${TRAIN_BASELINE_AUG}"
      fi
      ;;
    exp05_baseline_action_zscore)
      if should_run_prepare; then
        run_logged_step "${exp_id}" prepare "${PREPARE_BASELINE}"
      fi
      if should_run_train; then
        run_logged_step \
          "${exp_id}" \
          train \
          env \
          RUN_GROUP="${RUN_GROUP}" \
          OUTPUT_ROOT="${OUTPUT_ROOT}" \
          LOG_ROOT_BASE="${LOG_ROOT_BASE}" \
          JOB_NAME="g1_23_right_hand_cup_pick_6d20hz_${exp_id}" \
          "${TRAIN_BASELINE_ZSCORE}"
      fi
      ;;
    -h|--help|help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown experiment id: ${exp_id}" >&2
      usage >&2
      exit 1
      ;;
  esac
}

main() {
  case "${ACTION}" in
    prepare|train|all) ;;
    *)
      echo "Unsupported ACTION: ${ACTION}" >&2
      usage >&2
      exit 1
      ;;
  esac

  mapfile -t selected_experiments < <(normalize_experiments)

  echo "run_group=${RUN_GROUP}"
  echo "action=${ACTION}"
  echo "output_root=${OUTPUT_ROOT}"
  echo "log_root=${RUN_LOG_ROOT}"
  printf 'experiments=%s\n' "${selected_experiments[*]}"

  for exp_id in "${selected_experiments[@]}"; do
    run_experiment "${exp_id}"
  done
}

main "$@"
