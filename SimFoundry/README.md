# SimFoundry

厨房操作台场景铸造与 Isaac Lab 对接。场景与 G1 机器人解耦：先用现成 tabletop 资产通链路，资源到位后再接完整 Real2Sim。

训练侧统一走 **HuggingFace LeRobot v2.1**（ACT / Pi0 / SmolVLA）。Isaac 只负责出仿真轨迹；真机 LeRobot 采集与仿真导出共用同一套 key。

**新采集 / 新训练 / 改专家前必读**：[PROJECT_CONSTRAINTS.md](PROJECT_CONSTRAINTS.md)（项目硬约束；对**新数据**优先级高于 `handoff.md` 中的旧休息角描述）。

| 文档 / 目录 | 内容 |
|---|---|
| [PROJECT_CONSTRAINTS.md](PROJECT_CONSTRAINTS.md) | **硬约束**：11 关节首帧零位、prompt、h10 评测等不可违反限定 |
| [DEMO.md](DEMO.md) | **演示说明**：预览图、验收清单、Kit 回放命令 |
| [pipeline_resources.md](pipeline_resources.md) | 资源评估、GPU 占用、已拍板事项、scene 契约 |
| [g1_23_task_library.md](g1_23_task_library.md) | **G1 23**：同一室内世界的七个分区 + 中文任务语言（含长时序） |
| `task_library/g1_23_tasks.json` | 上述目录的机器可读索引 |
| `scenes/` | 场景包（与机器人无关） |
| `simfoundry/adapter/` | Mesh/VLM 等可替换后端；A 期是 stub / 资产库 |
| `simfoundry/scene_bridge/` | `layout.json` → USDA / Isaac spawn cfg |
| `simfoundry/isaac_envs/` | G1 23 DoF + D435i（**须在 AppLauncher 之后 import**） |
| `simfoundry/data/` | npz 中间格式 + LeRobot v2.1 导出 |

## 不依赖 Isaac 的检查

```bash
cd /home/user/Documents/zoo/sim/SimFoundry
python tests/test_scene_package.py
python scripts/export_scene_usd.py
```

## 采一条推杯种子（Newton 无头，1 env）

```bash
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes
cd /home/user/Documents/zoo/sim/IsaacLab
./isaaclab.sh -p ../SimFoundry/scripts/collect_seed.py \
  --scene-id kitchen_counter_placeholder \
  --num_envs 1 --device cuda \
  --task-id push_cup_to_bowl --num-episodes 1 --steps 60
```

中间轨迹写到 `datasets/<scene_id>/`：`rgb` `[T,3,480,640]`、`q` `[T,23]`、`instruction`、`embodiment_id`（厨房/室内 `g1_edu_23_bimanual`，分拣台 `g1_edu_23_u1_rubber`）。`--scene-id` 可选：`kitchen_counter_placeholder` | `indoor_lab_g1_23` | `sorting_station_g1_23`。

## 连通室内演示（七分区同一世界）

```bash
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes
cd /home/user/Documents/zoo/sim/IsaacLab
./isaaclab.sh -p ../SimFoundry/scripts/demo_indoor_lab.py \
  --num_envs 1 --device cuda --viz kit
```

机器人在同一室内**走过去**完成挥手 / 推门 / 按按钮 / 推杯等；Kit 带 D435i 头显面板。录像默认写到 `demo/preview_indoor_lab/head_d435i.mp4` 与 `kit_viewport.mp4`。详情见 [`DEMO.md`](DEMO.md)。

## 独立分拣台（蓝色工作台，不改厨房/室内实验室）

浅蓝桌面按实拍尺寸：`1.50 × 0.60 × 0.025` m，腿高 `0.75`，`TABLE_SURFACE_Z = 0.75 + 0.025/2 = 0.7625`，台面顶 `0.775`。台上木浆纸盒 + 黑色快递袋，台右侧地面两摞周转箱。G1 23 U1 橡胶假手只能推/拨进箱。演示主画面是头显 D435i。

```bash
conda activate env_isaaclab
export OMNI_KIT_ACCEPT_EULA=yes
cd /home/user/Documents/zoo/sim/IsaacLab
./isaaclab.sh -p ../SimFoundry/scripts/demo_sorting_station.py \
  --num_envs 1 --device cuda --viz kit
```

场景包：`scenes/sorting_station_g1_23/`。Gym：`SimFoundry-SortingStation-G1-Stump`。

## 转成 LeRobot v2.1（喂 ACT / Pi0）

```bash
conda activate env_isaaclab
cd /home/user/Documents/zoo/sim/SimFoundry
python scripts/npz_to_lerobot.py \
  --npz-dir datasets/kitchen_counter_placeholder \
  --out datasets/kitchen_counter_placeholder_lerobot \
  --overwrite
```

导出字段：

| LeRobot key | 来源 |
|---|---|
| `observation.state` | 23 维关节 `q` |
| `action` | 23 维脚本/策略动作 |
| `observation.images.d435i` | MP4，480×640 RGB |
| `task` / `task_index` | 语言指令 |
| `meta/simfoundry.json` | D435i 内参、关节名、embodiment（LeRobot 可忽略） |

真机用 LeRobot 原生采集时，相机 key 请同样用 `observation.images.d435i`，关节顺序用 `G1_23DOF_JOINT_NAMES`。

## Kit 拿杯演示（默认 ≤10s）

```bash
cd /home/user/Documents/zoo/sim/IsaacLab
./isaaclab.sh -p ../SimFoundry/scripts/demo_kit.py \
  --num_envs 1 --device cuda --viz kit
```

桌面杯子/碗/瓶已换 YCB mesh；官方 G1+Inspire 从 `unitree_ros` 转换见 `scripts/convert_g1_urdf.py`。细节见 [DEMO.md](DEMO.md)。

Kit/Omniverse 相机目前会把非正方形像素和主点偏移近似掉（日志里会有 warning），npz / `simfoundry.json` 里仍保存真实 D435i 内参。
