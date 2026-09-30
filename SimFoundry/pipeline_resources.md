# SimFoundry × Isaac Lab：资源、解耦与落地拍板

日期：2026-08-19  
机器：本机 Ubuntu 工作站（当前唯一承载节点）  
目标：厨房操作台场景 → 可交互仿真 → 服务 Unitree G1 EDU **双臂** 从零训练 VLA / WAM

原则：

1. **场景与机器人解耦**。第一期锁 23 DoF，后续加腕/手不重做场景重建。
2. **先通 pipeline，再建全链路模型**。资源到位前用现成桌面资产占位，SimFoundry 各模型以接口预留。

本目录是 SimFoundry 相关文档与代码的根：`/home/user/Documents/zoo/sim/SimFoundry/`。

---

## 0. 已拍板的四件事

| # | 议题 | 决定 |
|---|---|---|
| 1 | 机器人 | Unitree G1 EDU **双臂**，23 DoF。头部相机为 Intel RealSense **D435i**（见 §2） |
| 2 | 训练目标 | **从零**训 **VLA 或 WAM**（同一套轨迹数据，训练头可切换） |
| 3 | 第一场景 | **厨房操作台**（tabletop，单平面） |
| 4 | 起步方式 | **先跑 tabletop 示例**：用现成资产把 Isaac 出数据链路跑通，SimFoundry 接口留好，全链路重建等资源/Blackwell 探针通过后再接 |

### 0.1 资源受限下的工作方式

本机只有一张 48GB Blackwell。Hunyuan / TRELLIS / VOID / SAM3 视频等尚未在本机验证，且与 Isaac 的 PyTorch/Kit 不能混装。

因此分两期，**接口不变、实现可替换**：

| 期 | 场景从哪来 | 做什么 |
|---|---|---|
| **A. 通链路** | 现成资产（Isaac Lab 厨房/桌面、YCB、Nucleus 道具）写成与 SimFoundry 相同的 scene 包 | G1 双臂 + D435i 观测 → 种子演示 → MimicGen → 从零 VLA/WAM |
| **B. 全链路** | 真厨房视频走 SimFoundry Extraction → Generation → cousins | 只替换 scene 包来源，**不改** env / 数据集格式 / 训练脚本 |

占位资产必须走 `SimFoundry/scenes/<id>/` 契约（§5），禁止在 env 里写死 prim 路径。这样 B 期换 twin 是换目录，不是改训练代码。

---

## 1. 本机资源基线

| 项目 | 值 |
|---|---|
| CPU | Intel Core i9-14900KF（32 线程） |
| 内存 | 125 GB |
| GPU | NVIDIA RTX PRO 5000 Blackwell，约 **48 GB** |
| 驱动 | 580.105.08 |
| 磁盘 | 约 1.9 TB，可用约 1.5 TB |
| 已有环境 | `env_isaaclab`（Python 3.12，Isaac Sim 6.0.1，Isaac Lab 16.2.3，约 33 GB） |

约束：**单卡**。重建、背景 3DGS、Isaac 出数据必须分时。理想流畅态：每阶段独占 GPU、做完卸载；权重分 conda，不和 Isaac 混装。

---

## 2. 真机相机（embodiment，不属于场景包）

D435i 标定写进 **G1 传感器配置**，不写进 SimFoundry twin。换桌子不改内参；换相机才改这里。

| 项 | 值 |
|---|---|
| 型号 | Intel RealSense D435i |
| 序列号 | 233622077487 |
| 当前固件 | 5.16.0.1 |
| 官方建议固件 | 5.17.0.10（建议择机升级，避免与 SDK 行为不一致） |
| 彩色分辨率 | 640 × 480 |
| fx | 605.5006 |
| fy | 605.4136 |
| cx | 326.1470 |
| cy | 249.5715 |
| 实测 FOV | 55.71° × 43.24° |

Isaac 侧 RGB 相机应尽量对齐：640×480、上述内参、FOV。深度流若用于 WAM/点云，再单独记 D435i 深度内参（本次未提供，出深度数据前补测）。

仿真相机外参（头到光学中心的 SE3）第一期可用 Unitree / Isaac 默认 G1 头部安装；有真机外参标定后只改 embodiment yaml。

---

## 3. 场景与机器人解耦（加 DoF 不重做场景）

**23 DoF 不会绑死后续加腕、加灵巧手。** 场景包只描述世界，不描述关节数。

```
                    scene_id（与机器人无关）
  现成资产 或 视频──► SceneAdapter ──► twin / cousins / tasks
                                          │
                                          ▼
                                   scene_bridge → USD
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
               G1 23 DoF 双臂        G1 29 DoF              G1 + 手
               （第一期）            （加腕）               （加手）
                    │
                    ▼
              同一套轨迹格式 → 从零 VLA 或 WAM
```

| 层 | 内容 | 换机器人 / 加 DoF |
|---|---|---|
| **Scene** | 网格、碰撞、位姿、物理、柜门 URDF、背景、task predicate | **不重做** |
| **Bridge** | scene 包 → Isaac USD | 一般不改 |
| **Embodiment** | G1 USD、双臂、D435i、IK、遥操作 | 只改这一层 |
| **Skill** | 23 DoF：走近、伸手、推；有手后：抓放 | 打开已标记任务，资产复用 |

Isaac Lab 现成抓取多用 `G1_29DOF` + Inspire/Dex3。第一期用 `G1_CFG` / `g1.usd`（23 DoF 双臂）自写 env，以 `ArticulationCfg` 注入，不要把场景绑死在带手 cfg 上。

G1 23 DoF 本身就是双臂（无灵巧手）。第一期技能：走近操作台、双臂伸到目标、前臂/手掌推拨/清桌。抓取类 cousin 打标 `requires_ee: dexhand`，加手后再启用。

---

## 4. 目标 Pipeline

```
[A 期] 现成厨房桌面资产 ──┐
                          ├─► SceneAdapter ──► SimFoundry/scenes/<id>/
[B 期] 厨房视频 + SimFoundry ─┘         │
                                       ▼
                                scene_bridge → USD
                                       ▼
                         env_isaaclab：G1 双臂 + D435i 640×480
                                       ▼
                         种子演示 → MimicGen → 轨迹数据集
                                       ▼
                              从零训 VLA 或 WAM
```

A 期 SceneAdapter 的输入是 Nucleus/YCB 等；B 期换成 SimFoundry 导出。输出目录结构必须一致。

分时：重建（B 期）→ 可选背景 → Isaac 出数据。同时只活一个重 GPU 进程。

---

## 5. Scene 包契约（占位资产也必须遵守）

```
SimFoundry/scenes/<scene_id>/
  twin/
    objects/*.glb
    collision/*
    articulations/*.urdf      # 柜门/抽屉，不是机器人
    layout.json               # 位姿、尺度、质量、摩擦、语义名
    background/
  cousins/
    object/
    scene/
    task/<task_id>.json       # predicate + requires_ee
  meta.json                   # 单位、重力、来源（placeholder | simfoundry）；不要写 robot_dof
```

`layout.json`：桌面 z-up，物体在桌面坐标系。G1 站立高度、D435i 内外参在 embodiment 配置。

`task` 字段建议：

```json
{
  "task_id": "push_cup_to_bowl",
  "predicates": [{"type": "Near", "a": "cup", "b": "bowl"}],
  "requires_ee": "stump",
  "arms": "bimanual"
}
```

`requires_ee`: `stump` | `gripper` | `dexhand`  
第一期只跑 `stump` + `bimanual`。

A 期示例 `scene_id` 建议：`kitchen_counter_placeholder`。B 期真重建：`kitchen_counter_<date>`。

---

## 6. 模型依赖与 GPU 占用

峰值按 **独占本机 48GB、做完卸载**。禁止与 Isaac 并发。

A 期不加载下表中的重建模型，但 **SceneAdapter / MeshBackend / VlmBackend 接口先写好**，B 期只换实现。

### 6.1 必须 API（与是否本机 GPU 无关）

| 组件 | 角色 | 本机 GPU | A 期 | B 期 |
|---|---|---|---|---|
| Gemini-Pro-3 | 识物、物理参数、task cousin | 0 | stub：人手写 3 个 task json | API |
| Gemini 图像编辑 | object cousin 外观 | 0 | stub：跳过或换 YCB 实例 | API |
| Gemini 关节 | 抽屉/柜门 URDF | 0 | stub：厨房台面先不用活动柜 | API |

### 6.2 本机可串行跑（B 期）

| 阶段 | 模型 | 峰值显存 | 48GB | 接口名（预留） |
|---|---|---|---|---|
| 深度 / 相机 | DepthAnything3 Base/Large | 4–12 GB | 满足 | `DepthBackend` |
| 单图分割 | SAM3 | 8–16 GB | 满足 | `SegBackend` |
| 短视频分割 | SAM2/SAM3，1–2 min @1080p | 15–30 GB | 勉强 | 同上；视频必须短 |
| 图→网格 形状 | Hunyuan3D 2.1 Shape | ~10 GB | 满足 | `MeshBackend` |
| 图→网格 纹理 | Hunyuan3D 2.1 Paint | ~21 GB | 满足 | 同上；峰值约 21–29 GB |
| 备选图→网格 | TRELLIS.2-4B | ≥24 GB | 满足 | `MeshBackend` 另一实现 |
| 6D 位姿 | FoundationPose | 6–10 GB | 满足 | `PoseBackend` |
| 部件分割 | P3-SAM 等 | 4–10 GB | 满足 | `PartSegBackend` |
| 碰撞 / 稳定 | CoACD + PyBullet | CPU | 满足 | `PhysicsStabilize` |
| 背景 splat | splatfacto | 8–16 GB | 满足 | `BackgroundBackend` |

### 6.3 临界 / Plan B

| 组件 | 峰值 / 耗时 | 本机 | 策略 |
|---|---|---|---|
| SAM3 长视频 / 4K / 多轨 | 40–80 GB | 不够 | 采集 30–90s 1080p；超标外置 |
| VOID 两遍 inpaint | 12–24 GB，~90 min/场景 | 显存够，占满唯一的卡 | A/B 第一期用 mesh 背景 |
| Hunyuan 自定义 CUDA | 显存够 | Blackwell `sm_120` 可能编不过 | P0 探针；失败则 `MeshBackend` 走远程或只吃现成 glb |
| TRELLIS.2 | ≥24 GB | 工具链偏 CUDA 12.4 / A100 | 独立 conda；失败同上 |
| Isaac 多 env 多路 RTX | 易 >48 GB | 不够 | 少 env；无头 Newton |

### 6.4 Isaac 出数据（A/B 共用，与重建分时）

| 模式 | 显存 | 说明 |
|---|---|---|
| G1 双臂，无头 Newton，D435i 规格 1 路 RGB | 8–20 GB | **主路径** |
| 加 Kit 视口 | 12–24 GB | 调试用 |
| 大规模并行 + 多相机 RTX | >48 GB 风险 | 本机不做 |

出数据优先 `presets=newton_mjwarp`。本机 PhysX 无头曾 segfault。

观测对齐从零 VLA/WAM：

- RGB：640×480，§2 内参
- 双臂关节：23 DoF 全量（或上肢子集，在 dataset 字段里写死，方便以后加 DoF 只扩维）
- 可选深度：待补 D435i 深度内参后再开

---

## 7. 软件环境

| 环境 | 用途 | 不要装 |
|---|---|---|
| `env_isaaclab`（已有） | Isaac、G1 env、MimicGen、出数据 | Hunyuan、TRELLIS、SAM3、NerfStudio |
| `env_simfoundry`（B 期再建） | 感知与重建 | Isaac Kit |
| 训练环境（可与 Lab 分可合） | 从零 VLA / WAM | 视框架而定；WAM 若在 `FastWAM` 则保持独立 |

A 期只需 `env_isaaclab` + scene 包手工/脚本填充。磁盘：A 期现成资产很小；B 期 3D 权重预留 50–80 GB，场景缓存预留 200–400 GB。

---

## 8. 本目录结构（A 期就要有，B 期填实现）

```
zoo/sim/SimFoundry/
  README.md                    # 本目录入口
  pipeline_resources.md        # 本文：资源评估与拍板
  scenes/                      # 场景包（与机器人无关）
  scene_bridge/                # scene 包 → Isaac USD
  adapter/                     # B 期接入；A 期全是 stub
    backends/
      mesh.py                  # MeshBackend: image → glb
      depth.py
      seg.py
      pose.py
      vlm.py                   # VlmBackend: 识物 / 任务提案
      background.py
    pipeline.py                # Extraction → Generation → cousins
  isaac_envs/                  # 注入 robot cfg + D435i（embodiment）
```

`MeshBackend.generate(image) -> MeshAsset`：A 期实现 `FromLibraryBackend`（按语义名取 YCB/Nucleus）；B 期实现 `HunyuanBackend` / `TrellisBackend` / `RemoteMeshBackend`。

`VlmBackend.propose_tasks(scene) -> list[TaskSpec]`：A 期返回写死的厨房三任务；B 期调 Gemini。

---

## 9. 第一期厨房 tabletop 示例（现成资产）

场景语义（占位，可换成 Nucleus 实际资产名）：

- 桌面 / 操作台
- 杯、碗、盘子、瓶子（YCB 或 Isaac 道具）
- 可选固定柜体（无活动关节）

任务（`requires_ee: stump`）。完整场景库与 **中文规范指令** 见 [`g1_23_task_library.md`](g1_23_task_library.md)。

| task_id | 行为 | 成功 |
|---|---|---|
| `approach_counter` | 走到台前站定 | 骨盆距桌沿小于阈值，站立稳定 |
| `reach_cup` | 一臂伸向杯子 | EE 距杯口小于阈值 |
| `push_cup_to_bowl` | 推杯靠近碗 | 杯–碗水平距离小于阈值 |

抓取任务（`place_cup_in_bowl` 等）只生成 json，`requires_ee: dexhand`，23 DoF 过滤掉。G1 23 合法动词只有走/伸/推/拨/扫/按/挥/指，不用「拿、抓、放进」。

Tabletop 示例跑通标准：

1. 能加载 `kitchen_counter_placeholder` 并注入 G1 23 DoF 双臂
2. D435i 规格相机出 640×480 RGB
3. 至少一条 `push_cup_to_bowl` 种子轨迹能 reset/replay
4. MimicGen 或脚本扩出 N 条（N 先 10 即可）
5. 轨迹字段可被 VLA 与 WAM 两套 dataloader 读取（图像 + 双臂关节 + 语言指令）

---

## 10. 训练侧（从零 VLA / WAM）

数据是唯一对接点。场景来自占位还是 SimFoundry，训练脚本不关心。

建议每条样本：

- `rgb`: [T, 3, 480, 640]
- `intrinsics`: fx, fy, cx, cy
- `q`: [T, 23] 或带名字的关节 dict（加 DoF 时扩列，旧数据 pad）
- `action`: 与 `q` 同空间的增量或目标
- `instruction`: 语言
- `scene_id` / `task_id` / `embodiment_id`: `g1_edu_23_bimanual`

VLA 与 WAM 共用上述格式；差别只在网络。WAM 若走现有 FastWAM，对齐图像尺寸与动作维即可。

从零训：A 期数据量会很小，先验证 **格式和闭环 rollout**，不追求成功率。B 期 cousins 上来后再拉规模。

---

## 11. 任务拆解

### P0 拍板已完成 + 风险探针

- [x] 双臂 G1 23 DoF、D435i 内参、从零 VLA/WAM、厨房台面、先 tabletop 占位
- [ ] 固件 5.16.0.1 → 建议评估升到 5.17.0.10
- [ ] 补 D435i **深度**内参（若 WAM 要用深度）
- [ ] 头到相机 SE3（可用默认，有标定再替换）
- [ ] B 期前：本机 Blackwell 探针 Hunyuan 或 TRELLIS 出一张杯子 mesh

### P1 通链路（现成资产，本机即可）

- [x] 定死 `SimFoundry/scenes/` 目录与 `layout.json` schema
- [x] `FromLibraryBackend` 把厨房桌面现成资产写成 `kitchen_counter_placeholder`
- [x] `scene_bridge` → USDA / Isaac spawn cfg
- [x] G1 23 DoF 双臂 env + D435i 640×480 相机
- [x] 三个 stump 任务 + 过滤 `requires_ee`
- [x] 一条推杯种子 → 扩数据 → 能喂 VLA/WAM dataloader（`scripts/collect_seed.py` + `scripts/npz_to_lerobot.py` → LeRobot v2.1）
- [x] 训练协议对齐 HuggingFace LeRobot（ACT / Pi0）；Isaac 与真机采集并行，汇合在数据集

### P2 SimFoundry 接口填实（资源/探针通过后）

- [ ] 独立 `env_simfoundry`
- [ ] Gemini API
- [ ] `MeshBackend` / `DepthBackend` / `SegBackend` / `PoseBackend` 真实现
- [ ] 厨房真机视频 → 新 `scene_id`，env 与训练脚本零改
- [ ] VOID 背景后置

### P3 加自由度

- [ ] 换 29 DoF / 灵巧手 cfg
- [ ] 打开 `requires_ee: dexhand` 任务
- [ ] 重录带手种子；twin 复用

---

## 12. 流畅跑起来的检查清单

- [ ] A 期不依赖 Hunyuan/SAM/Gemini 也能出一条厨房轨迹
- [ ] scene 包无 `robot_dof`；G1 与 D435i 只在 embodiment
- [ ] 占位资产与未来 twin 同一目录结构
- [ ] `MeshBackend` / `VlmBackend` 可替换
- [ ] 重建与 Isaac **分时独占 GPU**
- [ ] 出数据用 Newton 无头
- [ ] 轨迹含 640×480 RGB 与 23 维双臂关节，VLA/WAM 都能读
- [ ] 抓取任务有 `requires_ee`，第一期不跑

降级：mesh 远程生成；背景第二次空桌拍摄；cousin 人手写任务；只出状态轨迹。

---

## 13. 参考

- SimFoundry：https://research.nvidia.com/labs/gear/simfoundry/
- 论文：arXiv:2606.28276
- 本机 Isaac 安装：[`../README.md`](../README.md)
- Isaac Lab G1 23 DoF：`G1_CFG` → `g1.usd`
- Isaac Lab G1 29 DoF / 手：`G1_29DOF_CFG`、`G1_INSPIRE_FTP_CFG`（P3 再用）
