# SimFoundry 项目硬约束

本文档定义分拣台 / G1 23 DoF VLA 流水线中**不可违反**的限定。新采集、新转换、新训练、新闭环评测、改场景或改专家时必须先读本文档；与本文档冲突的旧习惯（例如用视觉标定休息角当第一帧）不得继续用于新数据。

历史已冻结数据集（如 `officialhand_inactivepark_300_r2`、V3 pilot、0918 等）仅作对照，**不要求 retroactive 修改**；但从下一批新数据起必须遵守。

---

## 1. 上半身 11 关节的初始位姿为零位

**每条 episode 的第一帧**，下列 11 个关节的 `observation.state`（以及与之对齐的绝对关节角 / Unitree JSON 中的 `states.*.qpos`）**必须全部为 0 rad**：

| 序号 | 关节名（Unitree / LeRobot 11D 顺序） | 说明 |
|------|--------------------------------------|------|
| 1–5 | `kLeftShoulderPitch` … `kLeftWristRoll` | 左臂 5 DoF |
| 6–10 | `kRightShoulderPitch` … `kRightWristRoll` | 右臂 5 DoF |
| 11 | `waist_yaw_joint`（`body.qpos[0]`） | 腰 yaw；仿真中 waist roll/pitch 恒为 0 且不进入 11D |

在 23 DoF 全关节向量中，对应 `G1_U1_23DOF_JOINT_NAMES` 的索引 **12–22**（`waist_yaw_joint` + 双臂）。

**零位的含义**：URDF / Isaac 关节角为 0，不是 `U1_REAL_REST_*` 那套视觉休息角，也不是 `demo/real_ref_frames/1_t0.5.jpg` 标定出来的悬停角。

**允许非零的部分**（不进入 11D 训练，但可在 npz 23D 里存在）：

- 双腿 12 关节：可为固定站立姿态，用于稳定骨盆；**不得**把腿的 settle 写进 11D 的 state/action。
- 机器人基座：固定 `SORTING_ROBOT_POS` / `SORTING_ROBOT_ROT_XYZW`（见 `simfoundry/calibration/sorting_station.py`）。

**动作约定**（与零位初始态配套）：

- 若导出 **绝对** 关节角（与真机 `pick_cup_soring_0824` 一致）：第 0 帧 `action` 的上述 11 维也为 0。
- 若导出 **相对 default 的 offset**：`u1_sorting_default_qpos()` 中上述 11 维必须为 0，第 0 帧 offset 为 0。

**验收**（新数据写盘前必做）：

```python
# Unitree episode_*/data.json 第 0 帧
assert all(abs(x) < 1e-4 for x in frame0["states"]["left_arm"]["qpos"])
assert all(abs(x) < 1e-4 for x in frame0["states"]["right_arm"]["qpos"])
assert abs(frame0["states"]["body"]["qpos"][0]) < 1e-4
# 300 条之间：上述 11 维首帧必须一致（全 0）
```

**禁止**：用 `U1_REAL_REST_LEFT_ARM` / `U1_REAL_REST_RIGHT_ARM`（肩 pitch −0.66、肘 1.00 等）作为新数据的 episode 起始 state；禁止「首帧已是悬停休息角、action 从 0 偏移」混用。

相关代码索引（新采集前核验实际初始状态，不以旧休息角注释代替验收）：

- `simfoundry/robots/g1_assets.py` — `U1_REAL_REST_*`、`u1_sorting_default_qpos()`
- `simfoundry/robots/g1_assets.py` — `g1_u1_rubber_cfg().init_state.joint_pos`

---

## 2. 训练与评测只用 11 维上半身 + 腰 yaw

- LeRobot / Pi0.5 的 `observation.state` 与 `action` 为 **11 维**：左臂 5 + 右臂 5 + `waist_yaw_joint`。
- 仿真 npz 可保留 23 维 `q`，但转 LeRobot 时只导出上述 11 维；腰 roll/pitch 不参与训练。
- **2026-09-29 用户更新：首帧保持 §1 的零位；之后双臂允许运动，腰部允许转动。** 当前接口中“腰部转动”指 `waist_yaw_joint`，不新增腰 pitch/roll 自由度。
- 双臂可协调接近、避障与撤离；指定左手推袋、右手推盒的任务语义不变。允许另一臂运动，不代表允许其推动目标或扰动非目标。
- 新协议命名为 `waist_yaw_enabled_v1`：允许腰 yaw 在模型关节限位内运动，仍须满足原上半身相邻动作变化 ≤0.08 rad 的质量门。工作角度/速度范围须经可达性、碰撞和控制验证后冻结，不能直接把模型极限当作日常工作范围。
- 历史 `waist_locked_v1` 数据和评测保持原样。新协议明确替换“腰 action 全程锁 0”这一项；h10、无助推、零位初始态及其他原质量门保留。结果必须注明协议，不能与旧分数冒充同协议比较。
- 等待任务仍要求稳定，不能因允许腰部运动而出现无指令旋转；须保留原双掌稳定门，并在新协议中增加腰部漂移记录与预先冻结的验收阈值。
- 数据采集和导出首动作仍遵守 §1；模型闭环首个预测动作不强制为零（当前 `require_zero_action=False`），但初始 state 必须为零。不得通过插入未声明的零动作更改评测时序。
- **落实状态（2026-09-30）：**生产采集器已接入显式新鲜 pilot 合同，首个随机前后与左右交换组均已完成、各四推仅两条通过，整组拒绝训练；尚无合格完整新训练组或新模型。当前正在原失败前后几何上复测顶部接触路由候选。普通等待与完整前后/左右专家组分别通过，1.0rad 仅作为这些精确绑定设置的新鲜 pilot 工作界，不是一般部署认证。双臂与腰允许运动，首零位、无助推、原质量门和实际画面复核仍必需；逐帧完整可见不是新增硬门。目标裁切/画外风险仍需真实模型验证，见实施计划B→C与[交接](handoff.md)。


---

## 3. 语言 prompt 全链路一致

历史统一指令实验继续使用 `VLA_SORTING_UNIFIED_PROMPT`。

2026-09-24 用户批准双物体配对指令实验：新实验使用 `simfoundry/data/prompts.py` 的 `PAIRED_SORTING_PROMPTS`，盒/袋/等待分别使用固定英文短句。同一任务的采集、Unitree JSON、LeRobot `task`、PI0.5 闭环评测必须逐字一致，不得被转换器覆盖。通用指令 A 组仅为明确标识的消融副本，不修改源数据。配对布局必须整体划分 train/val/test，禁止拆开一对造成泄漏。

---

## 4. 闭环成败只认 horizon=10

正式通过标准：`scripts/demo_pi05_sorting.py --horizon 10`（`--viz none --no-realtime`）。纸盒进右侧区、黑袋进左侧区、空桌双臂静止。`h=50` 仅作诊断，**不能**作为扩采或宣称成功的依据。

---

## 5. 物理采集不得使用 kinematic 助推

- `assist_frames` 必须为 **0**（`--push-assist` 关）。
- 质量门以 PhysX 接触推得侧向位移为准；不得用 `maybe_assist_push` 类运动学改包裹位姿过门。

---

## 6. 数据与 checkpoint 安全

- 新数据写入**新目录**；不得 `--wipe` 已冻结对照集（0911/0912/0914/0915/0918 等）。
- 不得删除仍被 `checkpoints/last` symlink 指向的编号 checkpoint 目录。
- Isaac 采集与 Pi0.5 训练**不得同进程**占 GPU；长采集用 `setsid`/`nohup`。

---

## 7. 文档与交接

- 暂停或阶段切换时更新 `handoff.md`，并注明与本文档的关系（新数据是否已满足 §1）。
- 本文档优先级：对**新采集/新训练**高于 `handoff.md` 中关于 `U1_REAL_REST` 休息角的旧描述。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-09-23 | 初版：明确 §1 上半身 11 关节首帧零位为硬约束 |
| 2026-09-29 | 用户允许首帧之后双臂运动、腰部转动；取消新协议腰 yaw 全程锁零，保留初始零位及其余质量门，历史协议冻结 |
