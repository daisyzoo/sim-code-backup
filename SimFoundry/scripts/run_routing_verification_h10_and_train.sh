#!/usr/bin/env bash
# Resume routing verification from ② oracle h10 + ④ mailer-only train.
set -Eeuo pipefail

SIM_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${SIM_ROOT}/demo/diagnostic_routing_verification"
LOG="${OUT}/h10_and_train.log"
POLICY="/home/user/Documents/zoo/sim/lerobot/outputs/package_sorting_pi05_1gpu_20260922_140103/checkpoints/last/pretrained_model"
PI05_ENV="/home/user/Documents/zoo/sim/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/pi05_sim_sorting_vla_officialhand_inactivepark_300_r2_20260922.env"
MAILer_ENV="/home/user/Documents/zoo/sim/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/pi05_sim_sorting_mailer_only_pilot_20260923.env"
PYTHON="/home/user/Desktop/project/vla/env/.venv/bin/python"
TRAIN_SH="/home/user/Documents/zoo/sim/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/train_pi05_package_sorting_local.sh"

DEFAULT_PROMPT='Sort the package on the table by type. If there is no package on the table, keep both arms still and wait. If it is a black bag, press and hold the bag down with the left hand, then push it to the left sorting area. If it is a box, press and hold the box down with the right hand, then push it to the right sorting area.'
ORACLE_MAILER='Push the black bag to the left with the left hand.'
WRONG_BOX='Push the box to the right with the right hand.'

mkdir -p "${OUT}"
exec > >(tee -a "${LOG}") 2>&1
echo "=== resume h10+train $(date -Is) ==="

run_h10() {
  local tag="$1"; shift
  local rec="${OUT}/${tag}"
  if [[ -f "${rec}/summary.json" ]]; then
    echo "skip existing ${tag}"
    return 0
  fi
  PI05_POLICY_PATH="${POLICY}" PI05_LOCAL_CONFIG="${PI05_ENV}" \
  PI05_RECORD_DIR="${rec}" PI05_EVAL_SEED=0 \
  bash "${SIM_ROOT}/scripts/run_pi05_sorting_sim.sh" --horizon 10 --viz none --no-realtime "$@"
}

run_h10 "02_h10_default" --task "${DEFAULT_PROMPT}"
run_h10 "02_h10_oracle_mailer_prompt" --task "${DEFAULT_PROMPT}" --mailer-task "${ORACLE_MAILER}"
run_h10 "02_h10_wrong_box_prompt" --task "${DEFAULT_PROMPT}" --mailer-task "${WRONG_BOX}"

echo "--- ④ mailer-only train ---"
PI05_LOCAL_CONFIG="${MAILer_ENV}" bash "${TRAIN_SH}"

MAILer_RUN="$(ls -td /home/user/Documents/zoo/sim/lerobot/outputs/package_sorting_pi05_1gpu_* 2>/dev/null | head -1)"
MAILer_CKPT="${MAILer_RUN}/checkpoints/last/pretrained_model"
echo "mailer-only checkpoint: ${MAILer_CKPT}"

if [[ ! -f "${OUT}/04_h10_mailer_only_train/summary.json" ]]; then
  PI05_POLICY_PATH="${MAILer_CKPT}" PI05_LOCAL_CONFIG="${MAILer_ENV}" \
  PI05_RECORD_DIR="${OUT}/04_h10_mailer_only_train" PI05_EVAL_SEED=0 \
  bash "${SIM_ROOT}/scripts/run_pi05_sorting_sim.sh" --horizon 10 --viz none --no-realtime \
    --task "${DEFAULT_PROMPT}"
fi

"${PYTHON}" "${SIM_ROOT}/scripts/write_routing_verification_report.py" --out-dir "${OUT}"
echo "=== done $(date -Is) ==="
