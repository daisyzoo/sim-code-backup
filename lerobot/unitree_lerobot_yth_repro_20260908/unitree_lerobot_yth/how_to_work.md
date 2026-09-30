# How To Work

## 1. 目标

这份文档只记录 `unitree_lerobot` 仓内与模型训练、评测和真机测试直接相关的内容。

当前链路面向 `G1_23` 的“右手靠近抹布”任务，使用 `pi0.5 LoRA` 做训练与真机验证。

已确认：

- 训练数据来自 `G1_23` 真机采集链路
- 当前任务只关注受控关节子集 `arms5 + waist1`
- `pi0.5 LoRA` 已能在真机上做出“右手靠近抹布”的趋势动作

---

## 2. 项目与环境

项目目录：

- `/home/igs/Desktop/project/vla/unitree_lerobot`

环境划分：

- 训练：`unitree_lerobot`
- 评测：`vla_eval`

相关数据：

- LeRobot 数据集：`/home/igs/Desktop/project/vla/data/local/g1_23_right_hand_rag_reach_11d`
- 原始采集数据：`/home/igs/Desktop/project/vla/xr_teleoperate/teleop/utils/data/g1_23_right_hand_rag_reach`

说明：

- 数据采集、图像服务、终点示教等流程不再记录在本仓文档里
- 这些内容统一放在 `xr_teleoperate/how_to_work.md`

### 2.1 `pi0.5` 训练环境修复

当前项目的 `pi0.5` 训练依赖有一个容易踩坑的点：

- 不能只在 shell 里“看起来像”激活了 `unitree_lerobot`
- 也不能安装普通 PyPI 版 `transformers`

本机已验证可用的解释器与安装命令如下。

解释器：

- `/home/igs/miniconda3/envs/unitree_lerobot/bin/python`

安装命令：

```bash
/home/igs/miniconda3/envs/unitree_lerobot/bin/python -m pip install \
  peft==0.17.1 \
  "transformers @ git+https://github.com/huggingface/transformers.git@fix/lerobot_openpi"
```

验证命令：

```bash
/home/igs/miniconda3/envs/unitree_lerobot/bin/python - <<'PY'
import transformers, peft
print("transformers", transformers.__version__)
print("peft", peft.__version__)
from transformers.models.siglip import check
print("replace_installed =", check.check_whether_transformers_replace_is_installed_correctly())
PY
```

预期最后输出：

- `replace_installed = True`

如果不是 `True`，不要启动训练。

---

## 3. 训练

### 3.1 训练脚本

LoRA 训练脚本：

- [scripts/train_pi05_lora_g1_23_rag_reach.sh](/home/igs/Desktop/project/vla/unitree_lerobot/scripts/train_pi05_lora_g1_23_rag_reach.sh)
- [scripts/train_pi05_lora_g1_23_dual_hand_dock_multitask.sh](/home/igs/Desktop/project/vla/unitree_lerobot/scripts/train_pi05_lora_g1_23_dual_hand_dock_multitask.sh)

运行方式：

```bash
cd /home/igs/Desktop/project/vla/unitree_lerobot
bash scripts/train_pi05_lora_g1_23_rag_reach.sh
```

多任务版本：

```bash
cd /home/igs/Desktop/project/vla/unitree_lerobot
bash scripts/train_pi05_lora_g1_23_dual_hand_dock_multitask.sh
```

### 3.2 当前训练约定

- 输出默认写到：`/media/igs/EAGET/syh/vla/outputs`
- `train.log` 会落在每次运行目录下，和 `checkpoints/` 同级
- 当前训练使用：
  - `STATE -> QUANTILES`
  - `ACTION -> MIN_MAX`

### 3.3 训练前检查项

- 数据集路径是否存在
- 训练环境 `unitree_lerobot` 是否已激活
- 输出盘 `/media/igs/EAGET/syh/vla/outputs` 是否可写
- 训练脚本里的数据集、输出目录、模型参数是否仍是当前任务配置

---

## 4. 评测与测试

### 4.1 dry-run

脚本：

- [scripts/eval_pi05_lora_g1_23_rag_reach_dryrun.sh](/home/igs/Desktop/project/vla/unitree_lerobot/scripts/eval_pi05_lora_g1_23_rag_reach_dryrun.sh)

运行方式：

```bash
cd /home/igs/Desktop/project/vla/unitree_lerobot
bash scripts/eval_pi05_lora_g1_23_rag_reach_dryrun.sh
```

当前运行逻辑：

- 启动后先等待一次键盘输入 `s`
- 输入一次 `s` 后开始自动循环
- 每一轮开始一轮固定时长的 dry-run 推理
- 当前默认单轮时长：`4s`
- 到时后，本轮结束
- 脚本不退出，自动进入下一轮

### 4.2 真机发命令测试

脚本：

- [scripts/eval_pi05_lora_g1_23_rag_reach_real.sh](/home/igs/Desktop/project/vla/unitree_lerobot/scripts/eval_pi05_lora_g1_23_rag_reach_real.sh)
- [scripts/eval_pi05_lora_g1_23_rag_reach_real_mcp_controlled.sh](/home/igs/Desktop/project/vla/unitree_lerobot/scripts/eval_pi05_lora_g1_23_rag_reach_real_mcp_controlled.sh)

运行方式：

```bash
cd /home/igs/Desktop/project/vla/unitree_lerobot
bash scripts/eval_pi05_lora_g1_23_rag_reach_real.sh
```

MCP controlled 版本：

```bash
cd /home/igs/Desktop/project/vla/unitree_lerobot
bash scripts/eval_pi05_lora_g1_23_rag_reach_real_mcp_controlled.sh
```

当前运行逻辑：

- 默认按 `G1_23` 的 **非 debug 运控模式** 运行
- 启动后先完成一次初始化
- 初始化时：
  - 等待宇树运控上肢姿态稳定
  - 通过 `q29` handover 将上肢控制权切到 `rt/arm_sdk`
  - 先走一次**侧抬 waypoint**
  - 再平滑移动到数据集初始受控姿态
- 然后等待一次键盘输入 `s`（普通版）或等待 MCP `/vla/execute`（controlled 版）
- 每一轮 episode 结束后：
  - **直接回到数据集初始受控姿态**
  - 不回到大腿两侧
- 只有程序退出时才会：
  - 先走侧抬 waypoint
  - 再把 `q29` 从 `1 -> 0`
  - 再等待宇树运控把手臂带回大腿两侧

### 4.3 非 debug 运控模式约束

当前已验证，G1_23 升级固件后可以在 **非 debug 模式** 下做上肢真机评测，但前提明确：

- **不要进入 debug mode**
- app 里必须关闭 **`g1_arm_example`** 服务
- 下肢继续由宇树运控保持平衡
- 上肢通过 `rt/arm_sdk` 接管
- `q29` 作为 handover weight joint 使用

当前默认脚本参数：

- `MOTION=true`
- `HANDOVER_WAIT_SECONDS=0.8`
- `PRE_HANDOVER_WAIT_SECONDS=0.8`

如果启动 handover 偏快，可临时调大：

```bash
HANDOVER_WAIT_SECONDS=1.0 PRE_HANDOVER_WAIT_SECONDS=1.2 \
bash scripts/eval_pi05_lora_g1_23_rag_reach_real.sh
```

### 4.4 本次已解决的问题

#### 4.4.1 非 debug 下腰能动、手臂不动

排查结论：

- 旧固件阶段，`arm_sdk` 只能稳定控制腰 yaw，手臂不接管
- 升级固件后，关闭 app 里的 `g1_arm_example`，手臂与腰 yaw 均可通过 `rt/arm_sdk` 控制

#### 4.4.2 q29 handover 被控制逻辑覆盖

问题：

- `kNotUsedJoint0 = 29` 被“锁其它关节”的逻辑重新写回
- 导致 handover weight 实际没有拉起来

处理：

- 在 `xr_teleoperate` 和 `unitree_lerobot` 的相关控制器里，显式排除 `q29`
- 并把 handover 改成可控的 weight 渐变逻辑

#### 4.4.3 启动时先掉回大腿两侧，再去任务初始姿态

问题：

- 程序上一次退出时没有把控制权完整还回运控
- 下次启动时，运控先把上肢纠正回大腿两侧
- 然后外部 SDK 再把手臂带到任务初始姿态

处理：

- 启动前先等待运控姿态稳定
- handover 后先保持当前姿态
- 再显式移动到任务初始姿态
- 程序退出时再统一走“waypoint -> 还控制权 -> 回大腿两侧”

#### 4.4.4 启动直达关节全 0 会扫到桌子

问题：

- 从大腿两侧直接去“关节全 0 / 双臂前举 90 度”时
- 手臂可能扫到 75cm 桌面

处理：

- 在启动阶段增加了**侧抬 waypoint**
- 当前 waypoint 只改肩 roll，不在第一段主动改肘部
- 先把手臂从桌面附近抬开，再去任务初始姿态

当前侧抬 waypoint 约定：

- 左肩 roll：`1.30`
- 右肩 roll：`-1.30`

#### 4.4.5 episode 边界和程序退出逻辑分离

当前约定：

- episode 内循环结束：只回数据集初始姿态
- 程序退出：才回大腿两侧并归还控制权

这个区分已经同时同步到：

- 普通真机脚本链路
- MCP controlled 真机脚本链路

---

## 5. 推荐工作流

### 步骤 1：确认数据集

- 确认 LeRobot 数据集路径可用
- 确认当前训练脚本指向正确数据集

### 步骤 2：启动训练

```bash
cd /home/igs/Desktop/project/vla/unitree_lerobot
bash scripts/train_pi05_lora_g1_23_rag_reach.sh
```

### 步骤 3：检查训练输出

重点检查：

- 是否生成新的运行目录
- 是否生成 `train.log`
- 是否正常落盘 `checkpoints/`

### 步骤 4：先做 dry-run

```bash
cd /home/igs/Desktop/project/vla/unitree_lerobot
bash scripts/eval_pi05_lora_g1_23_rag_reach_dryrun.sh
```

### 步骤 5：再做真机测试

```bash
cd /home/igs/Desktop/project/vla/unitree_lerobot
bash scripts/eval_pi05_lora_g1_23_rag_reach_real.sh
```

---

## 6. 常用排查

### 6.1 训练没有输出

优先检查：

- 输出目录是否可写
- 环境是否激活正确
- 脚本里的数据集路径是否存在

### 6.2 dry-run 不启动

优先检查：

- 是否已按提示输入 `s`
- 评测环境 `vla_eval` 是否正确
- checkpoint 路径和模型配置是否对应当前实验

### 6.3 真机测试动作异常

优先检查：

- 是否处于 **非 debug 运控模式** 预期流程：
  - 未进入 debug mode
  - `g1_arm_example` 已关闭
  - `MOTION=true`
- 是否加载了预期 checkpoint
- 当前受控关节定义是否与训练配置一致
- 真机初始姿态和数据集初始姿态是否仍匹配

如果是 non-debug 下的桌面干涉问题，优先检查：

- 当前侧抬 waypoint 高度是否足够
- 桌面位置是否比之前测试时更靠近机器人
- handover 等待时间是否太短，导致启动段还没完全稳定

---

## 7. 边界说明

本仓文档只保留：

- 训练
- dry-run 评测
- 真机发命令测试

不再保留：

- 图像服务启动
- 相机配置
- 网格预览
- 终点示教
- 正式采集
- 原始 episode 目录检查

这些内容统一见：

- `/home/igs/Desktop/project/vla/xr_teleoperate/how_to_work.md`
