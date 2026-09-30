# 开发者复现资料包

## 内容与范围

- `unitree_lerobot_yth/`：指定项目的代码、配置、安装脚本、依赖清单、许可证、文档及文档插图；保留项目内 vendored LeRobot 和第三方源码。
- `VLA_MODELS_AND_INFERENCE.md`：原始模型与推理记录，逐字复制。本机路径和历史测试结果均保留原文。
- demo：`unitree_lerobot_yth/data/raw/g1_23_xr_pick_cup_6d_15hz_json/right_hand_cup_pick/episode_0000/`。
  从原 271 帧轨迹中保留前 30 帧（15 Hz，约 2 秒），包含状态、动作和 30 张引用图片，共 1.49 MiB。
  图片已复制为普通文件，无外部软链接。此片段用于格式检查/转换演示，不是完整成功轨迹，也不是 LeRobot v3 数据集，不可用于复现训练效果。

## 开始使用

1. 解压后先阅读本文件、项目 `docs/README_zh.md`、`docs/g1_23_pi05_project_adaptation_zh.md`、`how_to_work.md` 和模型记录。
2. 项目 `pyproject.toml` 要求 Python >=3.10,<3.11。按项目 README 创建独立环境并安装 pinocchio、ffmpeg 等依赖；在项目根目录执行：

   ```bash
   python -m pip install -e ./unitree_lerobot/lerobot
   python -m pip install -e .
   ```

   DDS 通信还需要 README 中的 `unitree_sdk2_python`。其他模型分支的依赖以各自安装说明为准，不要混装为单一环境。本包不含 wheel 或离线环境，安装需要自行准备依赖源。
3. 本包已有项目内源码，无需照搬原 README 的 clone/submodule 步骤；Git 历史已排除。
4. 模型权重、tokenizer、checkpoint 配置/归一化统计和完整训练数据需要另行获取并匹配。原记录中的本地权重路径不是下载地址。
5. 推理脚本仍保持原代码。按所用脚本修改/覆盖 `CONDA_SH`、`CONDA_ENV_NAME`、`POLICY_PATH`、`TOKENIZER_PATH`、`DATASET_ROOT`、`DATASET_REPO_ID`、`LOCAL_HF_HOME`、`LOCAL_HF_HUB_CACHE`、`LOCAL_HF_DATASETS_CACHE`、`IMAGE_HOST`、`NETWORK_INTERFACE` 等路径与设备参数；不是每个脚本都支持全部变量。
6. 部分旧真机脚本的 `SEND_REAL_ROBOT` 默认为 true；首次准备环境和离线检查时明确设置 `SEND_REAL_ROBOT=false`，不要直接照抄真机启动命令。该拿杯 demo 不能充当 11 维分拣/多任务模型的准备姿态数据。

## 尚需外部提供的内容

- 原始文档中的 `/skydata/yth/inference/`（包括 `run.sh`、`paths.json`、`tasks.json` 和后端代码）不在用户指定项目内，因此未打包。最新多任务入口不能仅凭此包直接运行。
- `/skydata/syh/FastWAM` 以及原文中的其他外部工程、环境和模型资产未打包。
- 按“只含代码和文档”要求排除 `.STL` 等机器人几何网格；保留 URDF/XML 文本定义。需要 Meshcat/仿真或引用这些网格的初始化流程时，须从原项目补齐相应 `eval_robot/assets/**/meshes` 资源。
- 已排除测试二进制 fixture，相关依赖这些 fixture 的第三方测试需另行获取测试资源。

## 打包规则与校验

排除完整 data（仅回添上述 demo）、checkpoints、outputs、Git 历史、缓存、IDE 配置、环境、构建元数据、压缩备份、wheel、模型/张量/数据二进制、日志、生成的分析报告及本地 `.env`。保留源码中 `models`/`datasets` 等目录内的代码。Notebook 清空执行输出；内部文档软链接复制为普通文件，失效/外部链接排除。原项目未修改。

`EXCLUDED.tsv` 记录被排除文件或目录（目录按整棵子树排除）；`CHANGES.txt` 记录副本处理；`MANIFEST.sha256` 记录内容校验值。在解压后的本目录运行：

```bash
sha256sum -c MANIFEST.sha256
```

本包完成文件内容和压缩完整性校验，未安装环境、训练模型或执行真机推理；不保证历史脚本跨机器直接运行。
