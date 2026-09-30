# evaluate

开源 VLA 仿真评测对照，以及一份可复现的 **LIBERO 官方场景评测 demo**。

## 文档

- [LIBERO / RoboCasa / LIBERO-Plus 对照](LIBERO_RoboCasa_LIBERO-Plus对照.md)

三者不是同一套评测的三个版本：LIBERO 测桌面知识迁移，RoboCasa 测厨房日常与长程组合，LIBERO-Plus 在原版 LIBERO 上加压。

## LIBERO 评测 demo

代码来自官方仓库 [Lifelong-Robot-Learning/LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO)（clone 在 `LIBERO/`）。场景用仓库自带的 BDDL、init states 和 3D 资产，协议对齐 README 的 Task 一节：取出套件任务 → 固定 `init_state` → `OffScreenRenderEnv.step`。

这是环境与协议冒烟，**不是**训练好的 VLA 排行榜。策略是全零 dummy action，成功率预期为 0。证明的是：公开场景能加载、官方初态能设进去、成功判定和图像观测能跑通。

### 本地两处最小改动

其余评测逻辑按 README Task 一节调用官方接口：

1. `libero/libero/envs/env_wrapper.py` 的 `reset()` 原先 `finally: continue`，循环不会返回；改为只在 `RandomizationError` 时重试。
2. `libero/libero/benchmark/__init__.py` 在存在 `.npy` 时不再强制 `import torch`。官方 `.pruned_init` 已转成同目录 `.npy`（每任务 50 条固定初态）。

### 环境

```bash
conda activate libero_eval   # Python 3.10，本机已建
export LIBERO_CONFIG_PATH=/home/user/Documents/zoo/sim/evaluate/libero_runtime
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl

pip install -r /home/user/Documents/zoo/sim/evaluate/requirements-libero-demo.txt
pip install -e /home/user/Documents/zoo/sim/evaluate/LIBERO
```

未安装官方 README 里的 `torch==1.11.0+cu113`（CUDA 11.3 轮子无法在本机 Blackwell 上跑）。本 demo 用 numpy 加载官方初态，不依赖 PyTorch。

### 运行

```bash
conda activate libero_eval
export LIBERO_CONFIG_PATH=/home/user/Documents/zoo/sim/evaluate/libero_runtime
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl

python /home/user/Documents/zoo/sim/evaluate/scripts/libero_eval_demo.py \
  --suite libero_spatial --task-id 0 --n-episodes 2 --max-steps 20
```

输出在 `outputs/libero_eval_demo/`（本机已跑通一次，约 47 秒）。

四套件场景效果拼图在 `outputs/libero_scene_gallery/`（厨房台 / 客厅桌 / 长程混场）。

- `report.json`：四套件任务目录、dummy 评测数字
- `libero_spatial_init_contact_sheet.jpg`：Spatial 10 个任务的官方初态拼图
- `catalog/`：每个任务一张初始帧
- `rollout/`：零动作 rollout 抽帧和 mp4
- `README.md`：本次运行摘要

完整 400-episode 协议（Spatial/Object/Goal/Long × 10 ep）需要训练好的策略，不在本 demo 范围。演示数据可用官方脚本按套件下载：

```bash
python /home/user/Documents/zoo/sim/evaluate/LIBERO/benchmark_scripts/download_libero_datasets.py \
  --datasets libero_spatial --use-huggingface
```
