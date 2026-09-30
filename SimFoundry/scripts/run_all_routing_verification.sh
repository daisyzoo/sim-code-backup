#!/usr/bin/env bash
# Overnight routing verification: tests ①③⑤ offline, ② oracle h10, ④ mailer-only train+h10.
set -Eeuo pipefail

SIM_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${SIM_ROOT}/demo/diagnostic_routing_verification"
LOG="${OUT}/run_all.log"
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
echo "=== routing verification start $(date -Is) ==="

if [[ ! -f "${OUT}/01_open_loop.json" ]]; then
  echo "--- ① open-loop ---"
  "${PYTHON}" "${SIM_ROOT}/scripts/run_routing_diagnostics.py" \
    --policy-path "${POLICY}" --out-dir "${OUT}" --skip-val-loss --skip-classifier
fi
if [[ ! -f "${OUT}/03_per_task_val_loss.json" ]]; then
  echo "--- ③ per-task val loss ---"
  "${PYTHON}" "${SIM_ROOT}/scripts/run_routing_diagnostics.py" \
    --policy-path "${POLICY}" --out-dir "${OUT}" --skip-open-loop --skip-classifier
fi
if [[ ! -f "${OUT}/05_frame0_classifier.json" ]]; then
  echo "--- ⑤ frame0 classifier ---"
  "${PYTHON}" "${SIM_ROOT}/scripts/run_routing_diagnostics.py" \
    --policy-path "${POLICY}" --out-dir "${OUT}" --skip-open-loop --skip-val-loss
fi

echo "--- ② oracle h10: default (reference) ---"
PI05_POLICY_PATH="${POLICY}" PI05_LOCAL_CONFIG="${PI05_ENV}" \
PI05_RECORD_DIR="${OUT}/02_h10_default" PI05_EVAL_SEED=0 \
bash "${SIM_ROOT}/scripts/run_pi05_sorting_sim.sh" --horizon 10 --viz none --no-realtime \
  --task "${DEFAULT_PROMPT}" || echo "WARN: default h10 failed"

echo "--- ② oracle h10: oracle mailer prompt ---"
PI05_POLICY_PATH="${POLICY}" PI05_LOCAL_CONFIG="${PI05_ENV}" \
PI05_RECORD_DIR="${OUT}/02_h10_oracle_mailer_prompt" PI05_EVAL_SEED=0 \
bash "${SIM_ROOT}/scripts/run_pi05_sorting_sim.sh" --horizon 10 --viz none --no-realtime \
  --task "${DEFAULT_PROMPT}" --mailer-task "${ORACLE_MAILER}" || echo "WARN: oracle h10 failed"

echo "--- ② oracle h10: wrong box prompt on mailer scene ---"
PI05_POLICY_PATH="${POLICY}" PI05_LOCAL_CONFIG="${PI05_ENV}" \
PI05_RECORD_DIR="${OUT}/02_h10_wrong_box_prompt" PI05_EVAL_SEED=0 \
bash "${SIM_ROOT}/scripts/run_pi05_sorting_sim.sh" --horizon 10 --viz none --no-realtime \
  --task "${DEFAULT_PROMPT}" --mailer-task "${WRONG_BOX}" || echo "WARN: wrong-box h10 failed"

echo "--- ④ prepare mailer-only meta ---"
"${PYTHON}" "${SIM_ROOT}/scripts/prepare_mailer_only_train_meta.py"

echo "--- ④ mailer-only train ---"
PI05_LOCAL_CONFIG="${MAILer_ENV}" bash "${TRAIN_SH}"

MAILer_RUN="$(ls -td /home/user/Documents/zoo/sim/lerobot/outputs/package_sorting_pi05_1gpu_* 2>/dev/null | head -1)"
MAILer_CKPT="${MAILer_RUN}/checkpoints/last/pretrained_model"
echo "mailer-only checkpoint: ${MAILer_CKPT}"

echo "--- ④ mailer-only h10 seed0 ---"
PI05_POLICY_PATH="${MAILer_CKPT}" PI05_LOCAL_CONFIG="${MAILer_ENV}" \
PI05_RECORD_DIR="${OUT}/04_h10_mailer_only_train" PI05_EVAL_SEED=0 \
bash "${SIM_ROOT}/scripts/run_pi05_sorting_sim.sh" --horizon 10 --viz none --no-realtime \
  --task "${DEFAULT_PROMPT}" || echo "WARN: mailer-only h10 failed"

echo "--- final report ---"
"${PYTHON}" "${SIM_ROOT}/scripts/write_routing_verification_report.py" --out-dir "${OUT}"
echo "=== routing verification done $(date -Is) ==="
