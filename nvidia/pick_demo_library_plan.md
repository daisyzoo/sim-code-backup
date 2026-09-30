# 执行计划：帽+瓶+三巾入库（2026-09-11）

只往 `nvidia/SimFoundry/Data/pick_demo` **加文件**。不 rerun、不覆盖现有 9 个包裹。不进本地 Isaac。

## 目标

| 来源 | 物体 | 碰撞 | 外观 |
|---|---|---|---|
| `5.mp4` → 场景 `pick_demo_5` | 安全帽、水瓶 | 帽：凸包或球冠+帽檐；瓶：**圆柱** | Hunyuan 网格缩放到锁尺寸；烂则简单体+视频投影 |
| `6.mp4` → 场景 `pick_demo_6` | 三块毛巾（冻在拍摄那一折） | 扁 AABB / 凸包 | 同上 |
| 现成 KLT | 料箱 | 外框 **30×20×15 cm** | Nucleus/已有 KLT，不跑 `4.mp4` |

成品拷到 `Data/pick_demo/library/`。`pick_demo_5` / `pick_demo_6` 是重建工作目录。

## 尺寸（无更多实测，先锁一版）

| 物体 | cm | 来源 |
|---|---|---|
| 料箱 | 30 × 20 × 15 | 用户实测 |
| 水瓶 | 直径 6.5 × 高 22 | 常见 550 ml，可改 |
| 安全帽 | 28 × 22 × 16 | 常见安全帽，可改 |
| 蓝巾叠好 | 22 × 20 × 3.5 | 相对 0.60 m 桌宽估 |
| 蓝巾揉皱 | 24 × 22 × 8 | 同上 |
| 橙巾叠好 | 28 × 24 × 4.5 | 同上 |

## 步骤

1. `5.mp4` / `6.mp4` 转 h264（HEVC 和当初 `1.mp4` 一样）。
2. **先跑 `pick_demo_5` 的 1b→5**（抽帧、DA3、地面、分解）。停下看检测：只要帽和瓶，桌子/手/背景丢掉。
3. 过 keep-list 后跑 6→8（上采样、Hunyuan、位姿）。`--no-stream`，`s7_mesh.low_vram=true`。
4. 按上表锁尺寸；visual / collision 分离；投影贴图兜底。拷进 `library/`。
5. 同样流程跑 `pick_demo_6`（三巾）。
6. 料箱只写 `library/klt.json`（缩放 0.30×0.20×0.15），不重建。

不跑 stage 9 关节。不跑 smoke-random。不跑 `--bg-splat`。

## 风险

- **检测**：两块蓝巾、透明瓶、近黑物体易漏/合并。stage 5 后必须人工看一眼。
- **Hunyuan**：瓶和巾大概率废网格。不阻塞，降级到投影贴图。
- **尺度**：除料箱外都是估计，碰撞会偏。有实测随时改 `library/extents.json` 再烘焙。
- **覆盖**：绝对不用 `scene_name=pick_demo`。
- **GPU / 时长**：一张卡串行；5 的 1–5 大约几十分钟，7 看物体数。Cursor 可能 abort，用 `setsid` 写 `/tmp/pick_demo_5.log`。
- **千问 API**：stage 3/5 依赖 DashScope；失败就停，不改 YAML 模型名除非账号挂。
- **坐标**：`pick_demo_5/6` 的 s14 若生成，不要并进旧 `pick_demo/s14_og`。
