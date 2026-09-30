# Isaac Sim / Isaac Lab 安装记录

记录时间：2026-08-18  
机器：本机 Ubuntu 工作站

## 环境概要

| 项目 | 值 |
|---|---|
| 系统 | Ubuntu 22.04.5 LTS（内核 6.8.0-40-generic，glibc 2.35） |
| CPU | Intel Core i9-14900KF |
| GPU | NVIDIA RTX PRO 5000 Blackwell（约 48 GB） |
| 驱动 | 580.105.08（R580 生产分支） |
| Conda 环境 | `env_isaaclab`（Python 3.12.13） |
| Isaac Sim | 6.0.1.0（pip，`isaacsim[all,extscache]`） |
| Isaac Lab | `develop` 分支，commit `a384e2f`，包版本 16.2.3 |
| PyTorch | 2.11.0+cu128 / torchvision 0.26.0+cu128 |

源码路径：`/home/user/Documents/zoo/sim/IsaacLab`  
Python 路径：`/home/user/miniconda3/envs/env_isaaclab/bin/python`

## 为何选 Isaac Sim 6.0

本机 GPU 是 Blackwell（compute capability `sm_120`）。Isaac Sim 4.x / 5.x 的 Kit/RTX 插件不支持该架构，启动时容易在渲染初始化阶段崩溃。官方当前栈要求：

- Isaac Sim **6.0.x**
- Python **3.12**（不能用 3.11）
- Linux 驱动建议 **580.95.05+**（本机 580.105.08 满足）

原先半成品 conda 环境 `env_isaaclab` 是 Python 3.11，已删除后按 3.12 重建。

## 安装方式

按官方「pip 安装 Isaac Sim + 源码安装 Isaac Lab」路径完成：

1. `conda create -n env_isaaclab python=3.12`
2. `pip install "isaacsim[all,extscache]==6.0.1.0" --extra-index-url https://pypi.nvidia.com`
3. `git clone --branch develop https://github.com/isaac-sim/IsaacLab.git`
4. `./isaaclab.sh -i`（安装 core、mimic、teleop，以及 newton / RL / visualizer 依赖；会把 PyTorch 固定到官方要求的 cu128 构建）

Isaac Lab 安装器会顺带生成 VS Code 配置（`IsaacLab/.vscode/`）。

## 使用方法

```bash
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes

# 打开 Isaac Sim
isaacsim

# Isaac Lab 空场景（弹出 Kit 视口）
cd /home/user/Documents/zoo/sim/IsaacLab
./isaaclab.sh -p scripts/tutorials/00_sim/create_empty.py --viz kit --device cuda

# 训练示例
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py --task=Isaac-Ant-v0 --headless
```

首次启动 Kit 会编译着色器，可能要等几分钟。无界面训练可加 `--headless`。

## 已做验证

- `isaacsim` 能启动，Vulkan 识别到 RTX PRO 5000 Blackwell（约 48935 MB）
- Isaac Lab 空场景脚本完成 10 帧步进后正常退出
- Warp 识别设备：`cuda:0` / `NVIDIA RTX PRO 5000 Blackwell` / `sm_120`

## 已知现象（可忽略或按需处理）

- **未装 ROS 2**：Isaac Sim 启动时 ROS 2 Bridge 会失败，不影响普通仿真和 RL 训练。若要用 ROS 桥，需另行配置 Humble 与 `LD_LIBRARY_PATH`。
- **pip 版本 pin 冲突**：Isaac Sim kernel 把部分依赖钉得很死（如 `psutil`、`click`），Isaac Lab 额外组件会覆盖它们。官方文档认为安装成功即可忽略。
- **CPU powersave / IOMMU 警告**：Kit 日志会提示电源策略为 `powersave`、IOMMU 已开启。需要更高性能时可再调 CPU governor；IOMMU 一般可先不管。
- **首次 Kit 启动较慢**：空场景冒烟测试第一次大约 4–5 分钟才完成 `Simulation App Startup Complete`，之后会快很多。
- **Isaac Sim PhysX 无头训练**：`physics=isaacsim_physx` 且不带 `--viz kit` 时，Kit 会在 `omni.usd.config` 启动阶段立刻 segfault（exit 139）。加上 `--viz kit` 后训练正常。日常无界面训练优先用 `presets=newton_mjwarp`。

## 训练冒烟（2026-08-18）

在 `IsaacLab` 里用 rsl_rl 跑了短训（日志：`smoke_logs/`）：

| 任务 | 后端 | 结果 |
|---|---|---|
| `Isaac-Cartpole-Direct`（16 env，5 iter） | Newton `presets=newton_mjwarp` | 通过，训练约 2.9s |
| `Isaac-Ant-Direct`（32 env，5 iter） | Newton `presets=newton_mjwarp` | 通过，训练约 1.4s |
| `Isaac-Cartpole-Direct`（16 env，3 iter） | Isaac Sim PhysX + `--viz kit` | 通过，训练约 2.7s |
| 同上，无 `--viz kit` | Isaac Sim PhysX 无头 | 失败（exit 139） |

复现命令：

```bash
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes
cd /home/user/Documents/zoo/sim/IsaacLab

./isaaclab.sh train --rl_library rsl_rl --task Isaac-Cartpole-Direct \
  --num_envs 16 --max_iterations 5 --device cuda presets=newton_mjwarp

./isaaclab.sh train --rl_library rsl_rl --task Isaac-Ant-Direct \
  --num_envs 32 --max_iterations 5 --device cuda presets=newton_mjwarp

./isaaclab.sh train --rl_library rsl_rl --task Isaac-Cartpole-Direct \
  --num_envs 16 --max_iterations 3 --device cuda --viz kit physics=isaacsim_physx
```

checkpoint 在 `IsaacLab/logs/rsl_rl/`。

## SimFoundry / 数据工厂规划

厨房操作台 + G1 EDU 双臂（23 DoF）+ D435i，从零训 VLA/WAM（训练协议：**LeRobot v2.1**，对接 ACT/Pi0）。场景与机器人解耦；资源到位前用现成 tabletop 资产通链路。

演示文档：[`SimFoundry/DEMO.md`](SimFoundry/DEMO.md)（含 RGB 预览与 Kit 回放命令）

目录：[`SimFoundry/`](SimFoundry/)  
规划文档：[`SimFoundry/pipeline_resources.md`](SimFoundry/pipeline_resources.md)  
LeRobot 导出：`SimFoundry/scripts/npz_to_lerobot.py`

## 参考

- [Isaac Lab 安装说明（develop）](https://isaac-sim.github.io/IsaacLab/develop/source/setup/installation/index.html)
- [Isaac Sim pip 安装](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_python.html)
- [Isaac Sim 系统要求](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/requirements.html)
