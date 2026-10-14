# Worldlab · Marble Kitchen / Isaac Sim 6.1

将 Marble 的高斯 PLY 与碰撞 GLB 组合成可重复构建的 Isaac Sim 厨房场景。
源码、配置、环境及产物均位于本目录。运行时固定 Isaac Sim **6.1.0.0**，
素材转换在独立 CPU 环境执行，无需 Isaac Lab。

## 本机验收结果 · 2026-10-13

已在 RTX PRO 5000 Blackwell / 驱动 580.105.08 上运行 **Isaac Sim 6.1.0.0**。
旧 `env_isaaclab` 保持 6.0.1.0。`pip check` 无冲突，CPU 资产测试 4/4 通过。

- [厨房真实渲染](outputs/final/kitchen_visual.png)、[宽视角](outputs/final/wide_visual.png)、
  [窗边台面](outputs/final/counter_visual.png)：1280×720，完整 200 万高斯。
- [6 秒视频](outputs/final/kitchen_tour.mp4)：24 fps / 144 帧，已检查首、中、尾帧。
- [验收报告](outputs/final/report.json)：三处落球测试均通过；实际网格接触数为
  386 / 302 / 352，球滚动后与最终位置的真实地面射线结果相符。
- [碰撞视图](outputs/collision/kitchen_collision.png)及 GUI 启动通过；
  [叠加视图](outputs/overlay/kitchen_overlay.png)用于定位网格与高斯的交叠和几何差异。
- 本次预热后整卡显存约 4.4 GiB；首次着色器编译约 4 分钟，缓存后完整视频验收约 35 秒。
  每帧离线采集约 0.143 秒，不能将视频编码的 24 fps 当成交互渲染测速。

最终代码、资产和报告的哈希记录在 `outputs/acceptance_summary.json`。
开发期间 `acceptance_6_1*` 等目录保留失败原因，交付结果以 `outputs/final/` 为准。

## 输入与输出

原始素材保留在 `World/Environment/Kitchen/`：

- `GaussianSplats/rustic_kitchen_with_natural_light_2m.ply`：2,000,000 个高斯。
- `CollisionMesh/rustic_kitchen_with_natural_light_collider.glb`：114,183 个三角形。

构建输出在 `generated/Kitchen/`：

- `visual.usdc`：完整高斯外观，未降采样。
- `collision.usdc`：保留 GLB 节点变换的三角网格。
- `kitchen.usda`：组合场景、静态碰撞、灯光和三台相机。
- `asset_audit.json`、`manifest.json`：输入统计、SHA256、转换器版本和配置。

## 安装与启动

需要 Linux、Python 3.12、可用的 NVIDIA RTX GPU/驱动。安装包含数 GB 扩展包，
必须预留下载、解包、最终环境和着色器缓存的空间。安装脚本不会更新旧 env_isaaclab。
精确依赖快照为 `requirements-sim.lock.txt` 与 `requirements-tools.lock.txt`；
两套环境分别使用，运行环境不要安装独立的 `usd-core`。
本次复用了本地同版本 CUDA 文件以减少下载，并逐文件对照发行包 RECORD 校验；
发现四个包存在旧 CUDA 12/13 共享路径覆盖后，已改用官方包重新安装。
运行 `.venv/bin/python scripts/check_runtime_integrity.py` 可复查 NVIDIA/Triton 文件完整性。

```bash
cd /home/user/Documents/zoo/sim/worldlab
# 新机器安装：WORLDLAB_PYTHON 指向 Python 3.12
WORLDLAB_PYTHON=/path/to/python3.12 bash scripts/setup.sh

# 已安装环境：打开交互窗口
bash run.sh

# 切换到宽视角；使用 Isaac Sim 视口自身的鼠标/键盘浏览
bash run.sh --camera wide

# 检查碰撞模型或视觉/碰撞叠加
bash run.sh --mode collision
bash run.sh --mode overlay

# 无窗口输出三视角截图、6秒漫游录像和碰撞落球测试
bash run.sh --headless --capture --video-seconds 6 --physics-test
```

输出默认为 `outputs/run_<时间>/`，可用 `--output` 指定新目录。
`report.json` 记录运行状态、实际版本、配置、图像统计和物理探针结果。
`kitchen_tour.mp4` 是受控相机小幅移动，不代表机器人导航。
GUI 运行时只在 USD session layer 改相机和可见性，不覆盖已生成场景。

## 重建和诊断

```bash
.venv-tools/bin/python scripts/build_kitchen.py
.venv-tools/bin/python -m pytest tests -q
.venv-tools/bin/python scripts/inspect_source.py
```

修改 `configs/kitchen.json` 后重新构建即可。输入哈希不变时复用大资产，
只重新组装场景；修改转换实现时加 `--force`。
`inspect_source.py` 生成带明确标签的 CPU 稀疏点投影，只检查朝向，不能作为 RTX 验收图。

## 坐标、物理和表示边界

此素材的 PLY 和 GLB 原始坐标相互匹配；二者共用父变换，避免分别手调。
初始诊断确认原始坐标 Y 向下，统一绕 X 旋转 -90° 转为 Z-up，并将地面移到零高度附近。
目前 scale=1 是按室内几何估计，未获得真实测量尺寸，不宣称精确数字孪生。

PLY 只有 SH DC 颜色，没有高阶 SH；1,381 个正无穷 opacity 是原始 logit，
经官方转换器 sigmoid 变为 1。转换后检查不透明度为有限的 [0,1]。
原始 PLY 不改写。负无穷或过小的 opacity 在内存中限制为 -700，以避免转换器指数溢出。

厨房采用静态三角网格碰撞；不为整个房间创建凸包，不添加遮掩网格缺陷的无限地板。
碰撞模型默认不可见但保持 collisionEnabled。窗口、薄片、孔洞及生成式场景几何
不保证符合真实建筑，落球测试只验证列出的采样区域。
球会在生成的斜面上滚动，因此验收记录接触事件、轨迹和最终支撑面，不要求停留在初始 XY。

普通高斯保留 6.1 默认的 `skipTonemapping=true`；强制套用 SPG 的色调配置会导致偏色或过曝。
调试碰撞模式使用临时中性材质和室内补光。每台采集相机有独立渲染目标，避免相机切换时的白帧。
启动日志可能提示 inotify watches 用尽：这是文件监视额度，和磁盘容量不同；本次实际渲染与物理
均通过，未修改主机的系统参数。

高斯中的门、餐具和家具仍是静态视觉内容。抓取/开门需要独立可操作网格和关节。
本项目验收 RGB 呈现与基础碰撞，不预设深度、语义分割或 LiDAR 与真实场景一致。

## 参考

- [NVIDIA Marble 厨房教程](https://developer.nvidia.com/blog/simulate-robotic-environments-faster-with-nvidia-isaac-sim-and-world-labs-marble/)
- [GSplat Converter](https://docs.omniverse.nvidia.com/extensions/latest/ext_gsplat-converter/manual.html)
- [Particle Field 渲染](https://docs.omniverse.nvidia.com/materials-and-rendering/latest/particle-fields.html)
- [Isaac Sim NuRec 渲染设置](https://docs.isaacsim.omniverse.nvidia.com/latest/assets/nurec_utils.html)

用户提供的 CSDN 链接在本次调研工具中不可访问，未将其作为已核实实现来源。

## 发行版 Agent Skills

本机 6.1.0.0 安装包自带 42 个 `SKILL.md`，目录为
`.venv/lib/python3.12/site-packages/isaacsim/skills/`；清单保存在
`outputs/environment_inventory.json`。它们是工程流程和辅助脚本，不是仿真引擎扩展。
本次参考 `isaac-sim-rendering`、`isaac-sim-validator`，静态检查记录见
`outputs/skill_static_validation.txt`。其脚本按固定变量名扫描，对 `app.close()`
和可选 `--headless` 给出两个误报，已检查实际代码。

使用时先明确运行环境、资产路径和验收标准，再按任务选择技能：资产组合用
`usd-pipeline` / `isaac-sim-assets`，渲染用 `isaac-sim-rendering`，排错用
`isaac-sim-troubleshooting`。不要一次载入所有技能；通用仓库/机器人规则需要
结合当前高斯静态场景判断，最终以真实截图和物理结果为准。

## SIM 空间清理记录

2026-10-13 首轮清理以北京时间 2026-09-29 00:00 为保守截止点，删除105,884个
过期数据载荷文件，逻辑体积11.97 GiB。保留冻结对照基线、last checkpoint、
近期腰部实验、源码和审计摘要。逐文件清单见 `outputs/maintenance/cleanup_deleted.jsonl`。
旧数据保留元数据不代表仍可训练/回放；受影响目录带 `PAYLOADS_REMOVED_20261013.json`。
安装完成后另清理约 8.6 GiB 下载缓存；新运行环境约 27 GiB，最终磁盘剩余约 41 GiB。
11 个 last/基线/明确 keep 的 checkpoint 全部保留，已核对路径和大小。

## 人眼视角自动巡览

```bash
bash run.sh --demo-seconds 35 --demo-repeats 3 --demo-delay 8
```

启动后预留 8 秒准备录屏，连续播放三轮，每轮 35 秒，总计约 105 秒；
结束后窗口保持打开。路线包含进入、看向窗边台面、观察右侧、回望和转回起点，
视点高度 1.55 米，闭合路线定义在 `src/worldlab/tour.py`。
这是确定性的相机动画，没有角色控制器或相机碰撞约束，不代表机器人自主导航。
`--tour-preview` 可输出九张路线关键视角截图；`report.json` 记录各轮实际耗时和完成状态。
录屏时先将 Isaac Sim 视口调整至合适大小，再执行上述命令。

厨房现有餐具、柜门等属于不可独立操作的高斯视觉；GLB 提供整体静态碰撞。
可添加独立刚体与场景碰撞；抓取原有杯子或打开柜门需要单独资产、碰撞体和关节，
并处理原高斯中对应物体的静态残影。


## 多场景扩展设计 · 2026-10-14

已有厨房之外，新增 hallway1 的 Elegant/Modern 两组 SPZ + GLB，以及 hallway2 的
BLEND/GLB 同场景来源。参见 [技术路线与项目架构](docs/multi_scene_design.md)、
[四场景目录](configs/scene_catalog.json)与 [CPU 资产审计](outputs/source_audit/hallways.json)。
本轮实施已完成三个新场景构建、通用新场景 CLI、GPU 渲染和静态接触验收；
详细通过证据见下方三场景验收文档。

```bash
.venv-tools/bin/python scripts/audit_hallways.py
# 官方 Skills 辅助脚本需要环境合同时，在当前 shell 设置：
source scripts/skills_env.sh
```

官方 Skills 的按需读取入口已写入 AGENTS.md；不向全局安装目录复制或修改官方技能。


## 三个新增场景 · 实施入口

新增场景通过独立的 `run_scene.sh` 打开：

```bash
bash run_scene.sh --scene hallway1_elegant
bash run_scene.sh --scene hallway1_modern
bash run_scene.sh --scene hallway2
```

详见 [使用文档](docs/scene_usage.md)与 [验收文档](docs/scene_acceptance_20261014.md)。
原有厨房 `run.sh` 继续可用。此前多场景设计章节是实施前记录；当前实现及验收以这两份文档为准。
