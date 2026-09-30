#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
set -a
source "${PI05_LOCAL_CONFIG:-${REPO_ROOT}/scripts/pi05_package_sorting_local.env}"
set +a
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PI05_PROJECT_ROOT:?}"
PYTHON_BIN="${PI05_PYTHON:?}"
DATASET_ROOT="${DATASET_V30_ROOT:?}"
SPLIT_FILE="${SHARED_SPLIT_FILE:?}"
BASE_MODEL_ROOT="${PI05_BASE_MODEL_ROOT:?}"
TOKENIZER_ROOT="${PI05_TOKENIZER_ROOT:?}"
OUTPUT_BASE="${PI05_OUTPUT_ROOT:?}"

NUM_GPUS="${PI05_NUM_GPUS:-8}"
GPU_IDS="${GPU_IDS:-0,1,2,3,4,5,6,7}"
MASTER_PORT="${PI05_MASTER_PORT:-29501}"
DATASET_REPO_ID="${DATASET_REPO_ID:-local/package_sorting_unified}"

STEPS="${PI05_STEPS:-30000}"
BATCH_SIZE_PER_GPU="${PI05_BATCH_SIZE_PER_GPU:-1}"
SAVE_FREQ="${PI05_SAVE_FREQ:-5000}"
LOG_FREQ="${PI05_LOG_FREQ:-20}"
NUM_WORKERS_PER_PROCESS="${PI05_NUM_WORKERS_PER_PROCESS:-2}"
POLICY_DTYPE="${PI05_DTYPE:-float32}"
GRADIENT_CHECKPOINTING="${PI05_GRADIENT_CHECKPOINTING:-false}"
USE_AMP="${PI05_USE_AMP:-false}"

for path in "${PROJECT_ROOT}" "${DATASET_ROOT}" "${BASE_MODEL_ROOT}" "${TOKENIZER_ROOT}"; do
    [[ -d "${path}" ]] || { echo "Missing directory: ${path}" >&2; exit 1; }
done
[[ -x "${PYTHON_BIN}" ]] || { echo "Missing Python: ${PYTHON_BIN}" >&2; exit 1; }
[[ -f "${SPLIT_FILE}" ]] || { echo "Missing split: ${SPLIT_FILE}" >&2; exit 1; }
[[ -f "${BASE_MODEL_ROOT}/model.safetensors" && -f "${TOKENIZER_ROOT}/tokenizer.json" ]] || { echo "Missing local model/tokenizer files" >&2; exit 1; }
[[ "${NUM_GPUS}" =~ ^[1-9][0-9]*$ ]] || { echo "Invalid PI05_NUM_GPUS" >&2; exit 1; }
IFS=, read -ra gpu_list <<<"${GPU_IDS}"
[[ "${#gpu_list[@]}" == "${NUM_GPUS}" ]] || { echo "GPU_IDS count differs from PI05_NUM_GPUS" >&2; exit 1; }

if [[ -f "${PROJECT_ROOT}/src/lerobot/scripts/lerobot_train.py" ]]; then
    LEROBOT_ROOT="${PROJECT_ROOT}"
elif [[ -f "${PROJECT_ROOT}/unitree_lerobot/lerobot/src/lerobot/scripts/lerobot_train.py" ]]; then
    LEROBOT_ROOT="${PROJECT_ROOT}/unitree_lerobot/lerobot"
else
    echo "Cannot locate src/lerobot/scripts/lerobot_train.py under ${PROJECT_ROOT}" >&2
    exit 1
fi

TRAIN_EPISODES="$(${PYTHON_BIN} - "${SPLIT_FILE}" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    split = json.load(handle)
episodes = split.get("train")
if not isinstance(episodes, list) or not episodes:
    raise SystemExit("split JSON has no non-empty 'train' list")
print(json.dumps(episodes, separators=(",", ":")))
PY
)"

RUN_NAME="package_sorting_pi05_${NUM_GPUS}gpu_$(date +%Y%m%d_%H%M%S)"
RUN_OUTPUT="${OUTPUT_BASE}/${RUN_NAME}"
mkdir -p "${OUTPUT_BASE}"

export CUDA_VISIBLE_DEVICES="${GPU_IDS}"
export PYTHONPATH="${LEROBOT_ROOT}/src:${PYTHONPATH:-}"
export PYTHONUNBUFFERED=1
export DATASET_V30_ROOT="${DATASET_ROOT}" SHARED_SPLIT_FILE="${SPLIT_FILE}"
export HF_HOME="${HF_HOME_ROOT:?}/pi05"
export HF_DATASETS_CACHE="${HF_HOME}/datasets"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export LEROBOT_TOKENIZER_NAME_OVERRIDE="${TOKENIZER_ROOT}"
export LEROBOT_TOKENIZER_LOCAL_FILES_ONLY_OVERRIDE=true
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

mkdir -p "${HF_HOME}"
cd "${LEROBOT_ROOT}"

echo "PI0.5 project:        ${LEROBOT_ROOT}"
echo "PI0.5 Python:         ${PYTHON_BIN}"
echo "Dataset:              ${DATASET_ROOT}"
echo "Train episodes:       ${TRAIN_EPISODES}"
echo "GPUs/processes:       ${GPU_IDS} / ${NUM_GPUS}"
echo "Per-GPU/global batch: ${BATCH_SIZE_PER_GPU} / $((BATCH_SIZE_PER_GPU * NUM_GPUS))"
echo "Output:               ${RUN_OUTPUT}"

accelerate_args=()
if (( NUM_GPUS > 1 )); then accelerate_args+=(--multi_gpu); fi
exec "${PYTHON_BIN}" -m accelerate.commands.launch \
    "${accelerate_args[@]}" \
    --num_processes "${NUM_GPUS}" \
    --num_machines 1 \
    --mixed_precision "${PI05_MIXED_PRECISION:-no}" \
    --main_process_port "${MASTER_PORT}" \
    -m lerobot.scripts.lerobot_train \
    --dataset.repo_id="${DATASET_REPO_ID}" \
    --dataset.root="${DATASET_ROOT}" \
    --dataset.episodes="${TRAIN_EPISODES}" \
    --dataset.use_imagenet_stats=false \
    --policy.type=pi05 \
    --policy.train_expert_only="${PI05_TRAIN_EXPERT_ONLY:-true}" \
    --policy.mask_action_padding=true \
    --policy.use_frame_loss_weights="${PI05_USE_FRAME_LOSS_WEIGHTS:-false}" \
    --policy.pretrained_path="${BASE_MODEL_ROOT}" \
    --policy.push_to_hub=false \
    --policy.device=cuda \
    --policy.dtype="${POLICY_DTYPE}" \
    --policy.gradient_checkpointing="${GRADIENT_CHECKPOINTING}" \
    --policy.use_amp="${USE_AMP}" \
    --policy.optimizer_lr="${PI05_LR:-2.5e-5}" \
    --policy.scheduler_warmup_steps="${PI05_WARMUP_STEPS:-1000}" \
    --policy.scheduler_decay_steps="${STEPS}" \
    --policy.scheduler_decay_lr="${PI05_DECAY_LR:-2.5e-6}" \
    --policy.train_expert_with_language_lora="${PI05_TRAIN_EXPERT_WITH_LANGUAGE_LORA:-false}" \
    --policy.lora_rank="${PI05_LORA_RANK:-0}" \
    --policy.lora_alpha="${PI05_LORA_ALPHA:-16}" \
    --policy.lora_dropout="${PI05_LORA_DROPOUT:-0.05}" \
    --policy.lora_target_language_model="${PI05_LORA_TARGET_LANGUAGE_MODEL:-true}" \
    --policy.lora_target_action_expert="${PI05_LORA_TARGET_ACTION_EXPERT:-true}" \
    --policy.normalization_mapping='{"ACTION":"MIN_MAX","STATE":"QUANTILES","VISUAL":"IDENTITY"}' \
    --output_dir="${RUN_OUTPUT}" \
    --job_name="${RUN_NAME}" \
    --steps="${STEPS}" \
    --batch_size="${BATCH_SIZE_PER_GPU}" \
    --save_freq="${SAVE_FREQ}" \
    --log_freq="${LOG_FREQ}" \
    --eval_freq=-1 \
    --num_workers="${NUM_WORKERS_PER_PROCESS}" \
    --seed="${PI05_SEED:-42}" \
    --wandb.enable="${WANDB_ENABLE:-true}" \
    --wandb.project="${WANDB_PROJECT_PI05:-package-sorting-pi05}" \
    --wandb.mode="${WANDB_MODE:-offline}"
