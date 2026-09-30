# Codex 交接：G1 VLA 工程、训练数据与 PI0.5 Padding Mask

> 本文用于在新的 Codex 会话中快速恢复上下文。当前仓库是只包含代码的开发副本；截至本文创建时，尚未修改 PI0.5 的 loss 或其他模型代码。

## 1. 当前工作区

- 工作目录：`/home/igs/Desktop/project/vla/unitree_lerobot_yth`
- Git 分支：`yth/dev`
- 创建本文前工作区状态：干净，与 `origin/yth/dev` 对齐
- 后续所有检查和改动都应在本目录、`yth/dev` 分支进行，不要操作原目录：
  - `/home/igs/Desktop/project/vla/unitree_lerobot`
- 本文已加入本仓库 `.gitignore`，仅作为本地 Codex 交接材料，不应提交。

## 2. 工程概况

这是一个基于 Hugging Face LeRobot 的 Unitree G1 VLA 工程，主要由三层组成：

1. `unitree_lerobot/lerobot/`
   - LeRobot 训练框架和 PI0.5 模型实现。
   - 本项目对 PI0.5 增加了 LoRA、离线 tokenizer、训练指标和推理计时等适配。
2. `unitree_lerobot/utils/`
   - Unitree 原始 JSON 数据到 LeRobot v3 数据集的转换。
   - 定义不同 G1 状态/动作维度。
3. `unitree_lerobot/eval_robot/`
   - 图像接入、DDS、G1 手臂控制、IK、真机评测和 MCP/HTTP 控制。

当前讨论重点是 G1 23DoF 的右手拿杯子/提包任务，较成熟的控制形式是 6D：

```text
[右肩 pitch, 右肩 roll, 右肩 yaw, 右肘, 右腕 roll, 腰 yaw]
```

当前 6D 模型不输出手指或夹爪动作。拿杯子/提包主要依赖右臂和腰的轨迹、预设手型以及场景几何；不能把它理解为模型同时学习了灵巧手抓握。

## 3. 训练数据如何组织

以原工程中的杯子+提包 6D 多任务数据为例：

- 358 条 episode
- 每条 50 帧
- 共 17,900 帧
- 20 Hz，相邻帧 0.05 秒
- 每条轨迹持续 2.5 秒
- 单头部 RGB 相机，原始分辨率 640×480
- 两个语言任务：拿杯子、提包

一条原始 Unitree episode 的概念结构是：

```text
episode
├── text.goal                 一条任务指令
└── data[0..49]
    ├── colors.color_0        当前 RGB 图像路径
    ├── states.right_arm.qpos 当前实测右臂关节角，5D
    ├── states.body.qpos[0]   当前实测腰 yaw，1D
    ├── actions.right_arm.qpos 示教/控制目标右臂关节角，5D
    └── actions.body.qpos[0]   示教/控制目标腰 yaw，1D
```

需要区分：

- `observation.state_t`：机器人在时刻 t 实际测到的关节位置。
- `action_t`：在时刻 t 下发或记录的目标关节位置。
- 二者通常接近，但受控制延迟、惯性和跟踪误差影响，不会完全相同。

原始 JSON 还可能含左臂、腰 roll/pitch、qvel、torque、深度、音频等字段；当前 6D 转换只取右臂 5D 和腰 yaw 1D。

转换到 LeRobot v3 后：

```text
observation.images.cam_high  RGB 视频帧
observation.state            [6]
action                       [6]
task                         字符串（通过 task_index 查表）
```

非视觉数据保存在 Parquet，RGB 图像集中编码为 MP4。

## 4. 一个 PI0.5 训练样本是什么

当前 PI0.5 配置：

```text
n_obs_steps = 1
chunk_size = 50
n_action_steps = 50
observation_delta_indices = None
action_delta_indices = [0, 1, ..., 49]
```

因此以某一帧 t 为锚点时：

```text
输入：
    image_t
    state_t
    task

监督目标：
    action_t, action_t+1, ..., action_t+49
```

batch 中的典型形状：

```text
图像       [B, 3, 224, 224]  # 进入模型前 resize/pad
state      [B, 6]
action     [B, 50, 6]
action_is_pad [B, 50]
```

模型不需要前 t 帧真值。第 20 帧被采样时，它把 `image_20 + state_20 + task` 当作一个独立的当前状态，预测从当前开始的未来动作。模型没有显式获得 `frame_index=20`，只能从当前图像和关节状态隐式判断任务进度。

PI0.5 中 state 不直接作为连续向量进入主干，而是先归一化、padding 到 32D、离散到 256 个 bin，并拼进语言 prompt：

```text
Task: ..., State: ...; Action:
```

模型通过 flow matching 一次生成 `[B, 50, 6]` 动作 chunk。

## 5. Episode 尾部 padding 的现状

每条 episode 只有 50 帧，但任何一帧都可能成为训练锚点。LeRobot 在查询越过 episode 末尾的未来动作时，会将索引 clamp 到最后一帧，并同时生成 `action_is_pad`。

例子：

```text
t = 0：
    50 个真实动作 action_0 ... action_49

t = 20：
    30 个真实动作 action_20 ... action_49
    20 个 padding，内容重复 action_49

t = 49：
    1 个真实动作 action_49
    49 个 padding，内容重复 action_49
```

控制语义上，重复最终位置目标近似表示“任务完成后保持最终关节姿态”。它不是电机失能，也不是模型拥有 `cup_grasped=true` 之类的成功信号。模型只是从终点图像和终点 state 学到继续输出相同位置目标。

当前 PI0.5 loss 在：

```text
unitree_lerobot/lerobot/src/lerobot/policies/pi05/modeling_pi05.py
PI05Policy.forward()
```

当前核心代码是：

```python
losses = self.model.forward(images, img_masks, tokens, masks, actions)

original_action_dim = self.config.output_features[ACTION].shape[0]
losses = losses[:, :, :original_action_dim]

loss = losses.mean()
```

`losses` 形状为 `[B, 50, action_dim]`，但这里没有使用 `batch["action_is_pad"]`，所以 padding 也参与 loss。

一条 50 帧 episode 若所有锚点均匀采样，会形成 50×50=2500 个动作位置，其中最终 `action_49` 因真实覆盖和 padding 合计会出现约 1275 次，超过一半。这会明显强化“终点保持”，也可能导致模型倾向过早停止或动作幅度不足。

即使 mask 掉额外 padding，后半段真实动作仍会被更多滑动窗口覆盖：`action_0` 被覆盖 1 次，`action_49` 作为真实动作被覆盖 50 次。这是另一个采样分布问题，不属于本次最小 mask 改动的范围。

## 6. 计划尝试的改动：mask action padding

用户希望先做一个直接忽略 padding loss 的实验。不要立即扩大范围；优先做可回退的 A/B 开关。

### 6.1 推荐配置项

文件：

```text
unitree_lerobot/lerobot/src/lerobot/policies/pi05/configuration_pi05.py
```

建议在 `PI05Config` 中增加：

```python
mask_action_padding: bool = False
```

保留 `False` 默认值可以兼容旧训练行为。实验训练时使用：

```bash
--policy.mask_action_padding=true
```

### 6.2 推荐 loss 实现位置

文件：

```text
unitree_lerobot/lerobot/src/lerobot/policies/pi05/modeling_pi05.py
```

位置：`PI05Policy.forward()` 中截断真实 action dimension 之后、`loss_dict` 之前。

建议逻辑：

```python
if self.config.mask_action_padding:
    valid_action_mask = (~batch["action_is_pad"]).unsqueeze(-1)  # [B, T, 1]
    masked_losses = losses * valid_action_mask

    valid_elements = valid_action_mask.sum() * losses.shape[-1]
    loss = masked_losses.sum() / valid_elements.clamp_min(1)
else:
    loss = losses.mean()
```

不要使用：

```python
(losses * valid_action_mask).mean()
```

因为它仍按全部 `B×T×D` 元素作分母，会让有效帧少的样本被人为降权。

### 6.3 指标也必须同步 mask

当前 `loss_dict` 中还有：

```python
"loss_per_dim": losses.mean(dim=[0, 1])
"loss_per_sample": losses.mean(dim=[1, 2])
```

若总 loss 使用 mask，但这两个指标不使用 mask，训练日志会继续统计 padding，容易误判。推荐同步计算：

```python
valid_steps_per_dim = valid_action_mask.sum(dim=(0, 1))
loss_per_dim = (
    masked_losses.sum(dim=(0, 1))
    / valid_steps_per_dim.clamp_min(1)
)

valid_elements_per_sample = (
    valid_action_mask.sum(dim=1).squeeze(-1) * losses.shape[-1]
)
loss_per_sample = (
    masked_losses.sum(dim=(1, 2))
    / valid_elements_per_sample.clamp_min(1)
)
```

在不开 mask 时保持当前指标算法。

### 6.4 防御性检查

mask 开启时应明确检查键存在，避免静默退回未 mask 行为：

```python
if "action_is_pad" not in batch:
    raise KeyError(...)
```

正常 LeRobot 离线数据加载链路已经会生成该键：

```text
unitree_lerobot/lerobot/src/lerobot/datasets/lerobot_dataset.py
LeRobotDataset._get_query_indices()
```

## 7. Mask 后的推理含义与风险

mask 只改变训练 loss，不改变推理输出长度。PI0.5 推理仍固定输出 50 步。

对 t=49 的终点观测，mask 后只有第一个 `action_49` 是有效监督，后 49 个输出位置在这种终点条件下没有直接监督。虽然这些位置会从其他样本中学到参数，但不能保证终点时继续保持，可能出现漂移或再次运动。

当前 MCP controlled 链路每个请求最多消费一个 chunk，queue 耗尽后结束请求，不在同一请求中自动续写，这提供了一层运行时保护。请求结束后可由控制器 `hold/freeze` 保持姿态。

若后续需要兼顾“不过度训练 padding”和“终点可靠保持”，可考虑：

1. mask 人工 padding，但在数据中加入少量真实终点保持帧；
2. 给 padding hold loss 较小权重，而不是完全置零；
3. 推理仅执行 chunk 前若干步并重新规划；
4. 增加任务完成/done 信号，由控制器在完成后 hold。

这些都不属于第一次最小 mask 实验，除非用户明确要求，不要顺手扩改。

## 8. 建议验证步骤

实现后至少做以下检查：

1. 静态/单元级张量检查
   - 构造 `[B,T,D]` losses 和 `[B,T] action_is_pad`。
   - 将 padding 部分 loss 设成极大值，确认 masked loss 完全不受影响。
   - 确认 `loss_per_dim`、`loss_per_sample` 与手算一致。
2. 数据 batch 检查
   - 读取真实 batch，打印一次 `action_is_pad.shape/dtype/device`。
   - 应为 bool、`[B,50]`，并与 losses 同设备。
3. 短训练 smoke test
   - 仅运行少量 step，确认 forward/backward、指标和 checkpoint 保存正常。
4. A/B 对比
   - 相同数据、随机种子、训练步数；只切换 `mask_action_padding`。
   - 对比总 loss、分维 loss、动作幅度、终点稳定性和是否过早停止。
5. 真机前先 dry-run/offline eval
   - 重点观察终点条件下 50 步预测是否漂移。

## 9. 工作约束

- 用户此前要求先理解工程，并明确要求只读时不得修改代码。
- 创建本文是用户明确授权的文件写入。
- 除本文和 `.gitignore` 外，目前不要修改其他文件。
- 实施 mask 前应再次确认用户授权，然后检查工作区是否仍干净，避免覆盖他人改动。
- 真机相关命令可能发送 DDS/`rt/arm_sdk` 控制，除非用户明确要求且完成安全确认，不要运行。

## 10. 新会话建议提示词

新会话可以直接说：

```text
请先完整阅读仓库根目录的 CODEX_HANDOFF_PI05_DATA_AND_PADDING.md，
然后检查当前分支和工作区。先不要改代码，向我确认你理解的 padding mask
改动范围、风险和验证计划。
```

