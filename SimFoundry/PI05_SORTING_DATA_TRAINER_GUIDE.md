# PI0.5 分拣仿真数据：训练师使用与验证说明

更新时间：2026-09-16

> **V2重采更正（2026-09-16）：** 重新审计发现旧300条中有109条需复核，其中大量198帧轨迹包含回合终止后的自动重置姿态跳变（约0.84–0.93 rad）。结合既有穿模、黑袋几何失真和长无效尾帧问题，这批数据现只保留作V0对照/消融，不再建议直接作为主训练数据交付。下文记录的是发现问题前的历史验证结果，不能覆盖此更正。新版采集已修复因果时序和终止污染；主机GPU正常，但Isaac烟测与重采尚未执行。

## 1. 一句话结论

这批旧300条仿真数据可以交给模型训练师做**问题分析、过滤实验和V0消融**，但不再建议未经逐条过滤就加入正式训练；正式混训应等待V2重采数据。

已经证明的价值是：模型学会了纸盒向右（机器人坐标 `-Y`）、黑袋向左（`+Y`）以及空桌等待；尚未证明的是：300 条全量训练比先采的 32 条试点或真机数据能带来更高的闭环成功率。当前证据反而表明，**数据选择和采样方式比条数更重要**。

推荐交付资产：

- 首选训练格式：`/home/user/Documents/zoo/sim/lerobot/lerobot_sim_sorting_vla_0918`
- 原始物理轨迹：`/home/user/Documents/zoo/sim/SimFoundry/datasets/sorting_station_g1_23_vla_0918`
- Unitree 中间格式：`/home/user/Documents/zoo/sim/SimFoundry/datasets/sorting_station_g1_23_unitree_vla_0918`
- 32 条试点模型：`/home/user/Documents/zoo/sim/lerobot/outputs/package_sorting_pi05_1gpu_20260915_160015/checkpoints/last/pretrained_model`
- 全量 300 条模型：`/home/user/Documents/zoo/sim/lerobot/outputs/package_sorting_pi05_1gpu_20260916_092142/checkpoints/last/pretrained_model`

## 2. 数据是什么

数据来自 Isaac/Newton 中的 Unitree G1 23DoF 分拣场景，由 Cartesian-Jacobian 物理专家执行“按压并侧推”。没有通过直接改写包裹位姿来助推物体。

| 项目 | 内容 |
|---|---|
| Episode | 300 条，编号 0–299 连续 |
| 构成 | 纸盒 120、黑袋 120、空桌等待 60 |
| 总帧数 | 47,758 |
| 频率 | 15 Hz |
| 图像 | 单路 RGB，640×480 |
| 状态 | 11D：左臂 5 + 右臂 5 + 腰 yaw 1 |
| 动作 | 11D 绝对关节位置目标，顺序与状态一致 |
| 训练/验证 | 270/30 条；训练 43,035 帧，验证 4,723 帧 |
| 语言 | 全部使用同一条英文任务指令 |
| 腰部 | 仿真动作锁定为 0 |

统一指令为：

> Sort the package on the table by type. If there is no package on the table, keep both arms still and wait. If it is a black bag, press and hold the bag down with the left hand, then push it to the left sorting area. If it is a box, press and hold the box down with the right hand, then push it to the right sorting area.

训练时不要改动关节顺序、动作含义或左右方向。纸盒目标方向为 `-Y`，黑袋目标方向为 `+Y`。

## 3. 数据质量证据

全量审计结果：

- 300/300 条均为 `assist_frames=0`，`push_assist=false`。
- 腰部 action 全为 0；未发现穿桌。
- 纸盒最终侧向位移：最小 8.02 cm，中位 16.71 cm，最大 24.91 cm。
- 黑袋最终侧向位移：最小 8.56 cm，中位 13.40 cm，最大 35.32 cm。
- 主动关节最大单步变化小于 0.034 rad。
- action-state MAE 中位数：纸盒约 0.00448，黑袋约 0.00405，等待约 0.00353。
- 视觉启发式检查 239 条直接通过，61 条进入复核；其中 60 条是短等待轨迹，另 1 条已人工检查，未发现动作异常。

这里的“过门”不是经过物理门或进入真实料箱，而是一个评测阈值：从初始位置算起，纸盒 `Δy <= -8 cm`、黑袋 `Δy >= +8 cm`。它只衡量方向和最低位移，不等于完整的工业分拣成功。

## 4. 已有训练与闭环验证结论

所有闭环结果均使用相同协议：单包裹摆位、统一指令、receding horizon=10；每 10 步根据新图像重新推理。每个模型重复 3 次。

| 模型 | 离线验证 loss | 纸盒三次 Δy | 纸盒过 8 cm | 黑袋三次 Δy | 黑袋过 8 cm | 空桌误触 |
|---|---:|---|---:|---|---:|---:|
| 32 条试点 | 0.01034 / 420 帧 | -18.10、-10.56、-7.65 cm | 2/3 | +12.28、+14.20、+15.18 cm | 3/3 | 0/3 |
| 全量 300 条 | 0.00445 / 4,723 帧 | -4.77、-9.44、-6.91 cm | 1/3 | +8.98、+26.07、+8.71 cm | 3/3 | 0/3 |

可以据此得出：

1. 数据中存在有效学习信号。旧模型曾把纸盒推向错误的 `+Y` 方向约 19.6 cm；0918 数据训练后的两个模型均在 3/3 次中选择正确的 `-Y` 方向。
2. 黑袋和等待分支已经表现稳定：两个模型黑袋均 3/3 过 8 cm，等待均无误触。
3. 不能声称“300 条优于 32 条”。全量模型离线 loss 更低，但纸盒闭环位移更弱。这说明 loss 主要衡量示范分布拟合，并不直接等于闭环控制质量。
4. 目前没有足够样本量给出严格显著性结论。每个模型只有 3 次闭环重复，因此这些结果是工程证据，不是统计意义上的最终证明。

评测原始结果位于：

- 32 条试点：`SimFoundry/demo/preview_pi05_sorting_vla_0918_fair`、`..._pilot_fair_r2`、`..._pilot_fair_r3`
- 全量 300 条：`SimFoundry/demo/preview_pi05_sorting_vla_0918_300_fair`、`..._300_fair_r2`、`..._300_fair_r3`

## 5. 优点与局限

### 优点

- 左右手、物体类型和目标方向的语义明确，且统一 prompt 与真机数据一致。
- 11D 关节布局、15 Hz、图像分辨率与真机数据兼容，可直接进入现有 PI0.5 LeRobot 训练管线。
- 三个任务分支均有覆盖，等待数据能抑制空桌误动作。
- 动作平滑、物理接触产生位移、没有运动学助推，标签比早期仿真数据可靠。
- 数据可复现，适合做预训练、辅助采样、消融和失败模式研究。

### 局限

- 存在 sim-to-real 外观、接触摩擦、柔性黑袋和动力学差异。
- 场景、相机、初始摆位和专家风格较单一，300 条不是 300 种独立技能。
- 全量训练在纸盒分支弱于 32 条试点，表明低价值重复帧可能稀释关键的“已接触后向外扫”动作。这是待消融验证的解释，不是已经定位完成的唯一因果。
- 仿真腰 action 恒为 0；真机训练集腰 action 标准差约 0.0146 rad。维度兼容，但分布不完全一致。
- 8 cm “过门”只验证最低侧向位移，不验证落入真实料箱、节拍、碰撞安全或连续多件分拣。
- 当前尚未完成真机闭环 A/B 测试，因此不能把仿真闭环结果表述为真机提升证明。

## 6. 建议训练方式

不建议把 300 条仿真数据无权重地拼入真机数据后只看总 loss。建议按以下顺序做：

1. 保留真机验证集不参与任何训练、归一化统计或数据筛选。
2. 先建立 `real-only` 基线，再比较 `real + sim`，而不是只比较 `sim32` 和 `sim300`。
3. 将仿真作为辅助采样源。初始可试每个 batch 中仿真占 10%、25%、50%，这三个比例是待验证的实验点，不是已证明最优值。
4. 优先保留接触后外扫阶段和高位移轨迹；纸盒可先以最终 `|Δy| >= 12 cm` 建一个高置信子集，再与全量 300 条做消融。
5. 分支采样保持平衡，不能让较长的纸盒/黑袋轨迹按帧数完全淹没等待分支。
6. 各数据源使用明确的 episode 级采样权重；不要复制 parquet 行来制造权重，也不要按帧随机切分同一条轨迹。
7. 使用训练 episode 计算归一化统计，验证 episode 只用于评估，避免泄漏。
8. 保存并报告至少 3 个训练随机种子；闭环每个分支建议至少 20 次，再报告成功率和 Wilson 置信区间。

最低限度的消融矩阵：

| 实验 | 目的 |
|---|---|
| real-only | 真机基线 |
| sim32-only | 复现当前最佳仿真闭环信号；使用 episode 0–31 |
| sim300-only | 复现全量结果 |
| real + sim32 | 检查少量高置信仿真是否增益 |
| real + filtered-sim300 | 检查筛选和阶段采样是否增益 |
| real + sim300 | 检查盲目全量混训的上限/负迁移 |

模型选择不能只看验证 loss。至少同时报告：纸盒正确手和方向、黑袋正确手和方向、8 cm 达标率、空桌误动作率、碰撞/限位次数。

## 7. 能否用真机数据验证模型

可以。真机数据 `/home/user/Documents/zoo/sim/lerobot/lerobot_v3.0` 已经具备可用的 held-out 划分：

| 划分 | Episode | 帧数 | 分支构成 |
|---|---:|---:|---|
| train | 278 | 45,698 | 分拣 209、等待 69 |
| validation | 15 | 1,873 | 分拣 11、等待 4 |

真机数据与仿真数据使用相同的统一 prompt、15 Hz、单路 640×480 RGB、11D 状态/动作顺序和绝对关节位置动作。划分以原始 `trajectory_identity` 分组，训练和验证互斥。

2026-09-16 已实际运行数据审计，结果为：

- train/validation episode 和帧集合互斥；
- 47,571 帧完整覆盖，无遗漏；
- episode 边界处的 50 步动作窗口 padding 正确，没有串到下一条轨迹；
- 训练统计只来自 278 条训练轨迹；
- train、validation 和非连续 episode 的视频解码均通过。

因此可以做三层验证，但三者回答的问题不同：

### A. 真机 held-out 离线验证

在 15 条真机 validation 上计算 PI0.5 原生 stochastic flow loss，并按纸盒/黑袋/等待拆分手臂选择、动作方向和动作幅度。它能回答“模型能否在真实相机图像和真实关节状态上复现示范动作分布”，适合快速淘汰明显退化模型。

注意：不同模型如果使用不同归一化统计，原生 flow loss 不一定能直接横向解释；应固定数据、prompt、噪声种子和评估代码。离线动作与示范不一致也不必然表示失败，因为可能存在多个有效动作。

### B. 仿真闭环验证

继续用当前 horizon=10 协议检查接触后的反馈行为。它能暴露开环 loss 看不到的循环贴合、方向反转和动作 chunk 问题，但仍不能替代真机。

### C. 真机闭环 A/B 验证

这是判断“是否真正提升 PI0.5 效果”的最终证据。建议对 `real-only`、`real+sim32`、`real+filtered-sim300` 使用相同初始摆位和安全约束，分别测试纸盒、黑袋、空桌；记录成功率、物体最终位移、正确手、误触、碰撞和人工接管。

如果 `lerobot_v3.0` 的 validation 轨迹被加入后续训练，它就不再是验证集，必须按原始采集 session 另切一个从未训练过的 test 集。

## 8. 现有验证入口

数据划分和训练统计：

```text
/home/user/Documents/zoo/sim/lerobot/lerobot_v3.0/meta/train_validation_split.json
/home/user/Documents/zoo/sim/lerobot/lerobot_v3.0/meta/train_only_stats.json
```

现有训练过程中的 held-out 验证实现：

```text
/home/user/Documents/zoo/sim/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src/lerobot/utils/pi05_validation.py
```

数据完整性审计命令：

```bash
cd /home/user/Documents/zoo/sim
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' \
PYTHONPATH=lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src \
/home/user/Desktop/project/vla/env/.venv/bin/python \
lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/audit_pi05_package_sorting.py \
  --root lerobot/lerobot_v3.0 \
  --split lerobot/lerobot_v3.0/meta/train_validation_split.json
```

现有 `pi05_validation.py` 是训练期间验证器，不是任意 checkpoint 的独立评测 CLI。要公平比较上述模型，应增加一个固定真机 validation、固定噪声种子、同时输出总体与分支指标的 checkpoint 评测入口；在该入口跑完之前，不应声称已完成真机数据上的模型效果验证。

## 9. 对训练师的最终建议

可以用，而且值得用；最合理的目标不是“证明 300 比 32 大”，而是利用这批数据补充方向语义、等待行为和接触动作，同时用真机 held-out 与真机闭环阻止负迁移。

当前首选方案是：`real-only` 做基线，小规模仿真试点做小比例辅助，逐步加入过滤后的 300 条，并用相同的真机 validation 和闭环协议做 A/B。只有当真机闭环成功率提高且误触/碰撞不变差，才把它认定为仿真数据带来的模型提升。

32 条试点并不是人工精选的“最好 32 条”，而是本批数据最先采集的 episode 0–31。其训练 episode 为 `0–9, 11–21, 23–29, 31`，验证 episode 为 `10, 22, 30`；该划分可从试点 checkpoint 的 `train_config.json` 和 420 帧验证记录复核。后续若构建真正的高置信子集，应另存 episode 清单并重新计算仅含训练集的统计量。

## 10. 真机闭环 A/B 当前执行状态

截至 2026-09-16，不能声称已经完成 `real-only`、`real+sim32`、`real+filtered-sim300` 的真机闭环 A/B：

- `real-only` 模型已经存在：`lerobot/outputs/package_sorting_pi05_1gpu_20260909_122124/checkpoints/last/pretrained_model`，训练 28,562 步，真机 held-out loss 为 0.01699；这个 loss 不是闭环成功率。
- `real+sim32` 和 `real+filtered-sim300` 两个混训 checkpoint 尚未训练，当前输出目录中没有对应模型。
- 主机侧GPU正常（RTX PRO 5000 Blackwell，驱动580.105.08）；Codex默认受限沙箱不映射NVIDIA设备，GPU任务需经主机执行权限运行。这不是驱动故障。
- 当前没有运行中的 Unitree、DDS 或 RTC 控制进程，也没有可确认的真机连接。
- 现有真机脚本默认依赖另一台机器的 `/home/igs`、`/skydata`、`eno1` 和 `192.168.123.164`，本机缺少这些路径；直接运行既会失败，也不满足真机安全验收条件。

完成证明至少需要：恢复 GPU 并训练两个混合模型；冻结一个三模型均未使用的 session 级 test 集；现场连接 G1 与 D435i；由操作员确认急停、工作空间和回零；三模型采用相同摆位、prompt、horizon、平滑和限速，每个纸盒/黑袋/空桌分支至少 20 次；盲化顺序并记录成功率、正确手、最终位移、误触、碰撞和人工接管。上述条件未满足前，任何“真机 A/B 提升”数字都不应写入结论。
