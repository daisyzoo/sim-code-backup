# nvidia 重建交接（2026-09-12）

给下一个 agent / 人用。一律用中文回复用户。工作区：`/home/user/Documents/zoo/sim`。

**这不是 VLA/PI0.5 采集交接。** 采集与开环评测见 `SimFoundry/handoff.md`。本文件覆盖：官方/自拍视频重建，把包裹接到本地 Isaac 分拣台，以及 2026-09-11 起的帽/瓶/巾素材库。

相关会话：[包裹重建接入分拣](3e48101a-be4b-4115-9acb-882b64404d38)

计划备忘：`nvidia/pick_demo_library_plan.md`。

---

## 1. 当前任务（做到哪了）

**主线：自拍视频 5、6 建成素材，只追加进 `nvidia/SimFoundry/Data/pick_demo/library/`。不覆盖现有 9 个包裹。真机对齐仍走本地 Isaac Lab + Unitree G1，不要把 G1 搬进 nvidia OG。不跑 `4.mp4`。**

| 物体 | 工作目录 | 1b–8 | 剪假桌 + 凸包 | s9–s14 |
|---|---|---|---|---|
| 安全帽、水瓶 | `Data/pick_demo_5` | 完成 keep `{0=帽, 1=瓶}` | **完成**（15:42） | **s10–14 完成**（15:47）。s9 无 articulate 环境，跳过 |
| 三巾 | `Data/pick_demo_6` | 完成，人工 keep `{0,1,2}` | 未剪（主视觉已是扁盒） | 未跑 |
| 料箱 KLT | 不重建 | — | — | — |

帽/瓶：从 `_backup_pre_known_extents` 剪掉 Hunyuan 焊上的假桌，剩下帽壳+帽檐 / 瓶身，再锁尺寸、凸包碰撞。脚本 `tools/trim_fake_table.py`。library 已更新 `visual_scaled.glb` + `collision_hull.glb`。OG 预览：`Data/pick_demo_5/s14_og/reconstructed_scene.png`（近机位；无桌无 Franka）。交互窗口：`/tmp/simfoundry_install_logs/view_pick_demo_5_og.sh`，`DISPLAY=:1`。**没有**并进旧 `pick_demo/s14_og`。

三巾：主视觉仍是扁盒+s5 抠图。`pick_demo_6/s8_pose` 未原地缩放。

旧 `Data/pick_demo` 的 9 个包裹 + `s14_og` **完好，不要 rerun `scene_name=pick_demo`**。

本地分拣接入见第 4.2 节；帽/瓶/巾还没进 Isaac，除非用户明确说接入。G1 策略闭环仍在本地树。

---

## 2. 两棵树（不要混用）

| 路径 | 是什么 | 规则 |
|---|---|---|
| `/home/user/Documents/zoo/sim/nvidia/SimFoundry` | 官方 NVlabs SimFoundry + OmniGibson | **重建只在这里。** 已完成的 9 个包裹不要改，除非用户要求。帽/瓶/巾用独立场景名 `pick_demo_5` / `pick_demo_6`。 |
| `/home/user/Documents/zoo/sim/SimFoundry` | 本地 Isaac Lab + Unitree G1 分拣台 | 分拣接入/视觉只改这里。**当前帽/瓶/巾任务不要动这棵树。** |

硬约束：

- 不要动系统 CUDA，也不要动 `env_isaaclab` / `streamvln`。
- NVIDIA 重建只用 `simfoundry` / `hunyuan` / `any6d` / `da3`。
- 不要回显密钥；YAML 默认保持千问（`qwen3-vl-plus` / `qwen-image-edit`）。
- GPU：`NVIDIA RTX PRO 5000 Blackwell`（约 48GB）。`DISPLAY` 一般为 `:1`。
- 长任务用 `setsid` 写 `/tmp/*.log`，不要只挂在 Cursor shell 上。
- Isaac 窗口常被 Cursor 挡住，需 Alt+Tab（仅本地树）。
- **绝对不要** `scene_name=pick_demo` 再跑管线。
- 不要把 `pick_demo_5/6` 的 s14 并进旧 `pick_demo/s14_og`。
- 不跑 smoke-random、不跑 `--bg-splat`。`pick_demo_5` 的 s10–14 已跑完；本机没有 articulate conda，s9 会警告后跳过。
- 外观/碰撞分离：剪掉假桌后的 Hunyuan 当 visual；碰撞用凸包（`s11_sim.collision_method=convex`）。巾冻在拍摄那一折，不当布仿真。
- 真机必须跟 Unitree G1 对齐：采集/训练/评测只在本地 Isaac Lab。nvidia OG 只出资产和静物预览，不要加 Franka 冒充闭环。

conda 启动注意：`conda activate` 前必须 `export NVCC_PREPEND_FLAGS="${NVCC_PREPEND_FLAGS:-}"` 且 `set +u`，否则 `~cuda-nvcc_activate.sh` 在 `set -u` 下立刻退出。现成启动脚本：

- `/tmp/simfoundry_install_logs/run_pick_demo_5.sh`（1b–5）
- `/tmp/simfoundry_install_logs/run_pick_demo_5_s5.sh`（只重跑 stage 5）
- `/tmp/simfoundry_install_logs/run_pick_demo_5_678.sh`
- `/tmp/simfoundry_install_logs/run_pick_demo_6.sh`（1b–5）
- `/tmp/simfoundry_install_logs/run_pick_demo_6_678.sh`
- `/tmp/simfoundry_install_logs/run_pick_demo_5_s914.sh`（s9–14；s9 跳过）

密钥从 `nvidia/SimFoundry/api_keys.txt` 加载，日志里只打印 SET/EMPTY。

---

## 3. 已经完成的内容

### 3.1 视频与场景划分

`Data/pick_demo/origin_video/`：

| 文件 | 内容 | 用法 |
|---|---|---|
| `1.mp4` / `1_h264.mp4` | 圆桌/蓝桌上的纸箱黑袋 | 现有 9 包裹，**已完成，勿 rerun** |
| `2.mp4` `3.mp4` | 同类包裹近景 | 未当主重建 |
| `4.mp4` | 全桌：水瓶、安全帽、黑色料箱、两蓝巾、一橙巾 | **不重建**；料箱用现成 KLT |
| `5.mp4` / `5_h264.mp4` | 近景帽+瓶 | 场景 `pick_demo_5` |
| `6.mp4` / `6_h264.mp4` | 近景三巾 | 场景 `pick_demo_6` |

HEVC 必须先转 h264（和当初 `1.mp4` 一样），否则抽帧会挂。

锁尺寸（`Data/pick_demo/library/extents.json`）：

| 物体 | cm | 来源 |
|---|---|---|
| 料箱 | 30 × 20 × 15 | 用户实测 |
| 水瓶 | 直径 6.5 × 高 22 | 常见 550 ml 估计 |
| 安全帽 | 28 × 22 × 16 | 常见安全帽估计 |
| 蓝巾叠好 | 22 × 20 × 3.5 | 相对 0.60 m 桌宽估 |
| 蓝巾揉皱 | 24 × 22 × 8 | 同上 |
| 橙巾叠好 | 28 × 24 × 4.5 | 同上 |

除料箱外都可改；改完再烘焙。

### 3.2 `pick_demo_5` 帽 + 瓶

- 1b–4：`img_idx=2`（`frame_0057`），与地面点云对齐。
- 第一次 stage 5：千问认出帽和瓶，但 `box_2d` 被当成 Gemini `yxyx`，框对调；帽被 `boundary_proportion=0.02` 当成贴边丢掉。keep 只剩瓶。备份在 `pick_demo_5/s5_scene_run1/`。
- 代码：`s5_scene.bbox_order`（yaml 默认 `null` = 旧 Gemini 行为）。本任务 Hydra：`s5_scene.bbox_order=xyxy` + `s5_scene.boundary_proportion=null`。
- 第二次 stage 5：框正确。keep `{0=米色安全帽, 1=透明水瓶}`。抠图干净。
- 6 上采样干净；7 Hunyuan + 8 位姿完成。
- Hunyuan：**形状大致对**（帽有穹顶+帽檐，瓶是瓶子），但都粘了假桌面，贴图发脏。碰撞不要用整网。
- 已 `apply_known_extents.py`：帽 `28,22,16` → OBB 16/22/28 cm；瓶 `6.5,6.5,22`。瓶的原始 OBB 含假桌（约 14×29×29 cm），轴映射会歪，所以必须先剪桌再缩放。
- 2026-09-12 已剪假桌：`trim_fake_table.py` 读 `_backup_pre_known_extents`，按支撑面高度切开。帽 AABB 14.2×6.3×19.8 → 10.6×6.1×17.8 cm；瓶 28.9×13.7×28.9 → 4.8×13.2×4.8 cm。然后重新锁尺寸。
- 碰撞：`s8_pose/collision_hull/iter_{0,1}.glb`；s11 `collision_method=convex`。不要把 hull 写进 `canonical_mesh/iter_*_collision_hull.glb`，stage 10 会把文件名解析坏。
- 已拷 `library/hard_hat/`、`library/water_bottle/`（`visual_scaled.glb`、`collision_hull.glb`、`trim_after.png`）。
- s10–14：`pick_demo_5/s14_og/reconstructed_scene.png`。无桌无机器人。帽/瓶落在地板上；瓶立着，帽是穹顶+帽檐（Hunyuan 贴图仍偏棕）。s9 因无 `articulate-anything-*` 环境跳过。日志 `/tmp/pick_demo_5_s914.log`。

### 3.3 `pick_demo_6` 三巾

- 1b–5 完成（约 5 分钟）。自动帧 `img_idx=14`：左叠蓝、中皱蓝、右叠橙，左边露出半截水瓶。
- 自动 keep `{0,1,2,3,4}`。人工改成 `{0,1,2}`，丢掉 `iter_3` 纸标、`iter_4` 半截瓶（瓶已在 pick_demo_5）。
- `object_filter.json`：`source=human_keep_towels_only`，`approved=true`。
- 6–8 完成（18:35–18:42，墙钟约 7 分钟）。keep 只有三巾。
- Hunyuan 预览 `s8_pose/front_views/`：叠蓝/皱蓝能认但底下有圆盘假桌；橙巾一侧像毛巾、一侧像粘土条+砖板。
- 2026-09-12 已拷 `library/towel_blue_folded/`、`towel_blue_crumpled/`、`towel_peach_folded/`。只在 library 副本上按锁尺寸做 OBB 缩放。`pick_demo_6/s8` 未改。碰撞全部写 AABB。
- 橙巾：用户拍板后写入 `photo_flatbox.glb`（28×24×4.5 cm，顶面 s5 抠图，侧面布色填充）。主视觉 `asset.json visual.primary=photo_flatbox.glb`。Hunyuan 文件仍留在同目录。
- 蓝巾：同样脚本已跑。叠蓝 22×20×3.5 cm，皱蓝 24×22×8 cm。主视觉都是 `photo_flatbox.glb`。
- 帽/瓶：已剪假桌 + 凸包 + `pick_demo_5` s10–14。贴图仍脏（帽偏棕）。

### 3.4 nvidia 树：旧 9 个包裹（只读）

场景根：`nvidia/SimFoundry/Data/pick_demo/`

Hunyuan 网格作废；**正确尺寸凸包长方体 + 原视频机位投影贴图**。

- 脚本：`nvidia/SimFoundry/scripts/pipeline/A_reconstruction/tools/build_photo_textured_assets.py`
- 尺寸：`object_extents.json`（纸箱全 13×8×2.5 cm；大袋 iter_1 15×15×3 cm；其余见该文件）
- keep `{0,1,2,4,5,6,7,8,9}`（iter_3 drop）
- s14_og：`include_table: false`，9 物体，无圆桌
- 漏检黑袋用 `add_remaining_bags.py` 补，不加桌子

### 3.5 本地分拣接入（只改 `SimFoundry/`，当前任务不要动）

实体名必须保持 **`parcel_box` / `mailer`**。reset 从 4 张箱图 / 5 张袋图各抽 1。真图已含面单，`PHOTO_LABELS_BAKED=True`。

视觉已对照采集帧修好（D435i 灰度 ~127 / 浅蓝 ~59%，对照采集 ~130 / 61%）。策略：**文件贴图只给 parcel**；bind 只绑 Mesh；不要绑 Cube/geometry/root；地板不要 wrap 地毯图。袋子顶面 PNG + 原 `mailer_normal.png` 平铺 `(2.5, 2.0)`。

关键文件：`SimFoundry/simfoundry/scene_bridge/{textures,isaac_cfg,parcel_photos}.py`、`import_pick_demo_parcels.py`、`assets/textures/sorting_station/parcels/`。

录像：`SimFoundry/demo/preview_sorting_station/head_d435i.mp4`、`kit_viewport.mp4`。`reset_overview.png` **是 D435i**，不是 Kit 全景。

---

## 4. 卡住的问题

### 当前素材库（要接着做）

1. **三巾扁盒都已烘焙。** 等用户看 `photo_flatbox_top.png`。帽/瓶已剪假桌并走完 `pick_demo_5` s14。
2. **对 `pick_demo_6` 的 s8 不要原地 `apply_known_extents`。**
3. **除料箱外尺寸都是估计。** 帽/瓶/巾还没进 Isaac。

### 本地分拣（旧线，本任务不要主动修）

6. 黑袋几何仍是长方体；用户是否接受还没拍板。
7. MeshCuboid 包裹曾掉到 z≈0.01/0.075（桌面 0.775）。
8. 主 `mailer` 物理尺寸固定 15×15×3 cm，抽到小袋图碰撞盒不变。

---

## 5. 下一步计划

只动 nvidia 树，除非用户明确说把帽/瓶/巾接入本地 G1 分拣台。

1. 用户看 `pick_demo_5/s14_og/reconstructed_scene.png` 和 `s8_pose/table_trim_preview/`。
2. 三巾等用户看过 `photo_flatbox_top.png` 再改尺寸。不要对 `pick_demo_6` 原地 `apply_known_extents`。
3. **不要**把 `pick_demo_5/s14_og` 并进旧包裹场景。不要 smoke-random / `--bg-splat`。
4. 真机 G1 对齐继续在本地 Isaac Lab。VLA 加采去读 `SimFoundry/handoff.md`。

---

## 6. 踩过的坑

### 千问 `box_2d` 不是 Gemini `yxyx`

`5_decompose_scene.py` 只要看到 `box_2d` 就走 `convert_gemini_box2d_to_xyxy`（ymin,xmin,ymax,xmax / 1000）。千问实际吐 **xyxy / 1000**。帽的框被画到瓶子上，瓶子贴上沿 → 帽被「near image boundary」删掉。

修复：Hydra `s5_scene.bbox_order=xyxy`。yaml 默认 `null`，**不要改默认**，否则旧 Gemini 场景会反转。实现：`real2sim_cfg.yaml` 的 `bbox_order`；`5_decompose_scene.py` 在 override 时走 `canonicalize_vlm_bbox_xyxy`。

### 贴边过滤太狠

`boundary_proportion=0.02`：mask 任一像素进 2% 边就丢。瓶盖、半截物体必中。本任务 stage 5 用 `s5_scene.boundary_proportion=null`。换帧会和 s3 点云错位（stage 5 会 warning），帽+瓶坚持 `img_idx=2`。

### 不要 `scene_name=pick_demo`

会覆盖 9 个包裹。5/6 必须独立目录。

### `set -u` + 空的 `NVCC_PREPEND_FLAGS`

第一次 `setsid` 秒退。activate 前：`export NVCC_PREPEND_FLAGS="${NVCC_PREPEND_FLAGS:-}"` 然后 `set +u; conda activate simfoundry; set -u`。

### Cursor abort 长任务

重建用 `setsid` + `/tmp/pick_demo_5.log`、`/tmp/pick_demo_5_s5.log`、`/tmp/pick_demo_5_678.log`、`/tmp/pick_demo_6.log`、`/tmp/pick_demo_6_678.log`。

### Hunyuan 会粘桌面

帽檐下假砖、瓶后假桌、巾下圆盘/砖板。visual 与 collision 必须分开。含假桌的 OBB 再 `apply_known_extents` 会把真物体压扁（瓶已经这样过一次）。正确顺序：从 `_backup_pre_known_extents` **先剪桌**再锁尺寸。凸包文件不要放进 `canonical_mesh/` 根目录（`iter_0_collision_hull.glb` 会让 stage 10 把 idx 解析成 `0_collision_hull`）。

### keep-list 必须人工看

自动会把桌子/手/标签/半截瓶算进去。`pick_demo_6` 丢掉 iter_3 纸标、iter_4 半截瓶。stage 6 读 `s5_scene/object_filter.json` 的 `keep_indices`。

### 两块蓝巾曾被 SAM 标 duplicate

第一次检测日志里 crumpled/folded 被标 `duplicate mask`，但最终仍分成 iter_0 / iter_1，抠图是分开的。不要只看那一行日志。

### Isaac Cuboid 无 Mesh / 给所有 Cube 绑照片

本地分拣旧坑：`CuboidCfg` 是 Cube 无 Mesh，贴图绑不上 → 深灰砖。给所有 Cube 绑照片 → 桌子吃到 `table_top.jpg`，D435i 灰度从 ~130 掉到 ~38。正确：只给 parcel 绑 Mesh。JPEG 会吃近黑折痕；袋子用 PNG。`reset_overview.png` 是头显不是 Kit 全景。详见原第 7 节，接入时再读。

### 不要当 UV 的图

`photo_textured_preview/iter_*_top.png` 是带白底的 3D 预览。包裹 UV 用 `iter_*_atlas.png` 第一张打包脸。

---

## 7. 关键路径

| 用途 | 路径 |
|---|---|
| 本交接 | `nvidia/handoff.md` |
| 5/6 执行计划 | `nvidia/pick_demo_library_plan.md` |
| 素材库 | `nvidia/SimFoundry/Data/pick_demo/library/` |
| 锁尺寸 | `library/extents.json` |
| 帽/瓶资产 | `library/hard_hat/`、`library/water_bottle/` |
| 三巾资产 | `library/towel_blue_folded/`、`towel_blue_crumpled/`、`towel_peach_folded/` |
| 料箱说明 | `library/klt.json` |
| 帽+瓶工作目录 | `nvidia/SimFoundry/Data/pick_demo_5/` |
| 三巾工作目录 | `nvidia/SimFoundry/Data/pick_demo_6/` |
| 旧 9 包裹（只读） | `nvidia/SimFoundry/Data/pick_demo/` |
| 旧包裹尺寸 | `Data/pick_demo/object_extents.json` |
| 自拍视频 | `Data/pick_demo/origin_video/` |
| bbox 顺序开关 | `nvidia/SimFoundry/scripts/cfg/real2sim_cfg.yaml` → `s5_scene.bbox_order` |
| stage 5 | `.../stages/5_decompose_scene.py` |
| 锁尺寸工具 | `.../tools/apply_known_extents.py` |
| 剪假桌 + 凸包 | `.../tools/trim_fake_table.py` |
| 帽/瓶 OG 预览 | `Data/pick_demo_5/s14_og/reconstructed_scene.png` |
| 包裹投影贴图（只用于旧 9 包裹） | `.../tools/build_photo_textured_assets.py` |
| 巾扁盒+抠图（新，勿与上一行混用） | `.../tools/build_photo_textured_flatbox.py` |
| 密钥 | `nvidia/SimFoundry/api_keys.txt`（勿回显） |
| 采集交接 | `SimFoundry/handoff.md` |

官方水果 demo（更早、已完成）：`nvidia/SimFoundry/Data/fruits_demo/`。
