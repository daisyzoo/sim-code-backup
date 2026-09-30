# SimFoundry 演示说明

日期：2026-08-20  
范围：A 期通链路（YCB 桌面资产 + G1 + D435i + 脚本拿杯 / 推杯 + LeRobot v2.1）  

---

## 1. 当前效果

| 产物 | 路径 |
|---|---|
| YCB 杯子/碗/瓶 | `assets/objects/025_mug.usd` 等 |
| 官方 G1+Inspire（unitree_ros） | `assets/robots/g1_29dof_inspire_ftp/` |
| Kit 拿杯演示 | `scripts/demo_kit.py`（默认 `pick_cup`，≤10s） |
| LeRobot v2.1 | `datasets/kitchen_counter_placeholder_lerobot/` |

### 1.1 Kit 拿杯（默认，约 9 秒）

节奏：短静止 → 丝滑伸手 → 握住抬起 → 短收尾。杯子用 YCB mug mesh；抓取阶段把杯子运动学贴到右腕（A 期可靠演示，非接触力闭环）。

```bash
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes
cd /home/user/Documents/zoo/sim/IsaacLab
./isaaclab.sh -p ../SimFoundry/scripts/demo_kit.py \
  --num_envs 1 --device cuda --viz kit
```

可选：

```bash
# 仍要旧的推杯
./isaaclab.sh -p ../SimFoundry/scripts/demo_kit.py \
  --num_envs 1 --device cuda --viz kit \
  --task-id push_cup_to_bowl --duration-s 20 --hold-start-s 3 --hold-end-s 3

# 存头相机截帧
./isaaclab.sh -p ../SimFoundry/scripts/demo_kit.py \
  --num_envs 1 --device cuda --viz kit --save-preview
```

### 1.3 连通室内完整巡游（走路 + 双路录像）

七个分区同一世界。G1 23 **走过去**切区（脚本步态，不传送），并做出可见的挥手 / 推门 / 按按钮 / 推杯 / 拨盒子 / 按开关。Kit 会同时打开 **D435i 头显 streaming 面板**。

默认把两路视频写到 `demo/preview_indoor_lab/`：

| 文件 | 内容 |
|---|---|
| `head_d435i.mp4` | 机器人头显（D435i） |
| `kit_viewport.mp4` | 与 Kit 3D 镜头同步的第三人称视角 |

```bash
cd /home/user/Documents/zoo/sim/IsaacLab
./isaaclab.sh -p ../SimFoundry/scripts/demo_indoor_lab.py \
  --num_envs 1 --device cuda --viz kit
```

节奏：全景 4s → 走到假人挥手 → 走廊标记 → 推门 → 按墙按钮 → 进门走到厨房推杯 → 实验桌拨盒子并按开关 → 全景 4s。全程大约 **90–120 秒**。

```bash
# 不写 mp4
./isaaclab.sh -p ../SimFoundry/scripts/demo_indoor_lab.py \
  --num_envs 1 --device cuda --viz kit --no-record

# 头相机截帧
./isaaclab.sh -p ../SimFoundry/scripts/demo_indoor_lab.py \
  --num_envs 1 --device cuda --viz kit --save-preview
```

### 1.4 独立分拣台（Real2Sim，对齐 `pic/*.mp4`）

**不改**厨房 / 室内实验室场景。新包 `scenes/sorting_station_g1_23/`，布局按真实采集场景调色与道具：

| 常数 | 值 |
|---|---|
| `TABLE_LENGTH` | 1.50 m（沿 Y，长边朝向机器人） |
| `TABLE_WIDTH` | 0.60 m（沿 X，进深） |
| `TABLE_HEIGHT` | 0.725 m（腿高） |
| `TABLE_THICKNESS` | 0.025 m |
| `TABLE_SURFACE_Z` | 0.7375 m（台面立方体中心） |
| `TABLE_TOP` | 0.75 m（地面到桌面顶面） |
| `FLOOR_Z` | 0.0 |

台上：粉浅蓝哑光桌（前缘磨损白条）、木浆纸盒+白面单、两件近黑快递袋+白面单。台侧地面：两摞黑色周转箱（各 4 层）、灰地毯地面、塑料膜背景板、PC 塔、金属支架。机器人用 **G1 23DoF U1 橡胶假手**（官方 `*_wrist_roll_rubber_hand.STL`，elbow→wrist=0.100 m）。23 DoF 无腰俯仰，stump 骨盆固定在 z≈0.64 才能让假手够到台面；推拨靠 PhysX/Newton 碰撞，不做脚本传送。演示主录像是 **D435i 头显**，Kit 机位贴近实拍右肩后第三人称。抓取任务标了 `requires_ee=dexhand`，训练时会被过滤。

```bash
cd /home/user/Documents/zoo/sim/IsaacLab
./isaaclab.sh -p ../SimFoundry/scripts/demo_sorting_station.py \
  --num_envs 1 --device cuda --viz kit --save-preview --no-realtime
```

默认录像：`demo/preview_sorting_station/head_d435i.mp4` 与 `kit_viewport.mp4`。

采分拣台种子轨迹（Newton 无头）：

```bash
cd /home/user/Documents/zoo/sim/IsaacLab
./isaaclab.sh -p ../SimFoundry/scripts/collect_seed.py \
  --scene-id sorting_station_g1_23 --task-id push_box_to_bin \
  --num-episodes 1 --steps 120 --device cuda --unitree

cd /home/user/Documents/zoo/sim/SimFoundry
# 与真机 pick_cup_soring_0824 同布局：episode_XXXX/{colors,data.json}
python scripts/npz_to_unitree_json.py \
  --npz-dir datasets/sorting_station_g1_23 \
  --out datasets/sorting_station_g1_23_unitree --fps 15 --overwrite

python scripts/npz_to_lerobot.py \
  --npz-dir datasets/sorting_station_g1_23 \
  --out datasets/sorting_station_g1_23_lerobot --overwrite
```

`--unitree` 会额外写出 Unitree EpisodeWriter 格式（`left_arm/right_arm/body.qpos` + `color_0`），
可直接喂给 `unitree_lerobot` 的 `Unitree_G1_23Dof_Arms5_Waist1` 转换链路。

### 1.5 0918 分拣数据与 PI0.5（2026-09-16）

> **V2重采提示（2026-09-16）：** 对旧300条的增强审计发现大量终止自动重置污染（109条需复核），且旧资产存在视觉/碰撞失配。旧数据现冻结为V0研究对照，不再作为推荐主训练集。V2已修复时序与终止写入，采用刚性内核+真实外壳包裹、稳定左右侧区成功标准；新入口为 `scripts/collect_vla_sorting_v2.sh`。主机GPU正常，但Isaac需在沙箱外获准执行；视觉/物理烟测尚未完成，不能直接扩采300条。详见 `handoff.md` 最顶部。

已完成 300 条无辅助物理数据：纸盒 120、黑袋 120、空桌等待 60。推荐闭环权重是先通过质量门的 32 条试点模型；300 条全量模型离线 loss 更低，但纸盒闭环稳定性略差，二者均保留。

| 产物 | 路径 / 结果 |
|---|---|
| 300 条 NPZ | `datasets/sorting_station_g1_23_vla_0918/` |
| 300 条 Unitree | `datasets/sorting_station_g1_23_unitree_vla_0918/` |
| LeRobot v3 | `../lerobot/lerobot_sim_sorting_vla_0918/`（47,758 帧） |
| 推荐 PI0.5 | `../lerobot/outputs/package_sorting_pi05_1gpu_20260915_160015/checkpoints/last/pretrained_model` |
| 全量 PI0.5 | `../lerobot/outputs/package_sorting_pi05_1gpu_20260916_092142/checkpoints/last/pretrained_model` |

推荐模型三次公平闭环 h10 的中位结果：纸盒 −10.6 cm、黑袋 +14.2 cm，空桌无误触。纸盒目标为 −Y，黑袋目标为 +Y，过门线均为 8 cm。

复现推荐模型评测：

```bash
export PI05_LOCAL_CONFIG=/home/user/Documents/zoo/sim/lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/scripts/pi05_sim_sorting_vla_0918.env
export PI05_POLICY_PATH=/home/user/Documents/zoo/sim/lerobot/outputs/package_sorting_pi05_1gpu_20260915_160015/checkpoints/last/pretrained_model
export PI05_RECORD_DIR=/home/user/Documents/zoo/sim/SimFoundry/demo/preview_pi05_sorting_vla_0918_recheck
bash /home/user/Documents/zoo/sim/SimFoundry/scripts/run_pi05_sorting_sim.sh \
  --horizon 10 --viz none --no-realtime
```

详尽数据审计、训练与三次重复评测结论见 [`handoff.md`](handoff.md) 顶部“0918 项目最终状态”。面向模型训练师的交付口径、混训建议和真机验证方案见 [`PI05_SORTING_DATA_TRAINER_GUIDE.md`](PI05_SORTING_DATA_TRAINER_GUIDE.md)。

---

Nucleus 上的 `g1_29dof_inspire_hand.usd` 是缺 payload 的 stub。本仓库已从
`third_party/unitree_ros/robots/g1_description/g1_29dof_rev_1_0_with_inspire_hand_FTP.urdf`
转成本地 layered USD（约 17MB，含 STL mesh）：

```bash
./isaaclab.sh -p ../SimFoundry/scripts/convert_g1_urdf.py --device cuda
```

产物：`assets/robots/g1_29dof_inspire_ftp/g1_29dof_inspire_ftp.usd`  
A 期采数 / 23 DoF 动作仍用 Nucleus `g1.usd`（关节名兼容）；Inspire 资产给后续 dexhand 抓取用。

---

## 2. 其它命令

```bash
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes
```

### 2.1 单测（无 Isaac）

```bash
cd /home/user/Documents/zoo/sim/SimFoundry
python tests/test_scene_package.py
```

### 2.2 无头采推杯 + LeRobot

```bash
cd /home/user/Documents/zoo/sim/IsaacLab
./isaaclab.sh -p ../SimFoundry/scripts/collect_seed.py \
  --num_envs 1 --device cuda \
  --task-id push_cup_to_bowl --num-episodes 1 --steps 60

cd /home/user/Documents/zoo/sim/SimFoundry
python scripts/npz_to_lerobot.py \
  --npz-dir datasets/kitchen_counter_placeholder \
  --out datasets/kitchen_counter_placeholder_lerobot \
  --overwrite
```

---

## 3. 观感说明

| 项目 | 现状 |
|---|---|
| 杯子/碗/瓶 | **YCB mesh**（非圆柱） |
| 盘子 | 仍是薄圆柱占位 |
| G1 采数本体 | Nucleus `g1.usd` 23 DoF |
| G1 官方 mesh | 已转换 Inspire FTP，待接 dexhand env |
| 站立 | `fix_root_link=True` |
| 拿杯 | 脚本 reach + 腕部 attach 抬起，≤10s |

---

## 4. 相关文档

- 总规划：[`pipeline_resources.md`](pipeline_resources.md)
- 目录入口：[`README.md`](README.md)
