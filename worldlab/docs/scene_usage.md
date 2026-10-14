# Worldlab 新场景使用文档

运行环境：本项目 `.venv`，Isaac Sim **6.1.0.0**。以下命令从 worldlab 目录执行。

新增独立 BLEND 路线：`bash run_scene.sh --scene hallway2_blend`；三遍录制巡览：
`bash run_blend_tour.sh`。见 [BLEND 使用说明](hallway2_blend_usage.md) 和
[验收记录](hallway2_blend_acceptance_20261014.md)。原三场景及其默认录制列表不变。

## 打开场景

```bash
cd /home/user/Documents/zoo/sim/worldlab
bash run_scene.sh --scene hallway1_elegant
bash run_scene.sh --scene hallway1_modern
bash run_scene.sh --scene hallway2
```

每次执行一个命令即可，关闭当前窗口后再打开另一场景。
三个场景 ID 不依赖原始文件名中的空格；启动器会读取 `generated/<ID>/current.json`，
检查源文件、配置和已生成资源的哈希，然后打开对应构建版本。
厨房继续用 `bash run.sh`，没有迁移或覆盖旧厨房场景。

查看固定视角：

```bash
bash run_scene.sh --scene hallway1_elegant --camera reverse
bash run_scene.sh --scene hallway1_modern --camera stairs
bash run_scene.sh --scene hallway2 --camera entry
```

每个场景均有 entry、reverse、stairs 三个验收相机。
hallway2 还保留导入的四台源相机，可以在 Isaac Sim 的相机列表中选择。
在 Isaac Sim 的 File → Open 中也可以打开 `current.json` 指向的 `scene.usda`；
为了复现报告中的渲染设置，建议使用本项目启动器。

## 自动巡览和录屏

```bash
bash run_scene.sh --scene hallway1_elegant --demo-seconds 35 --demo-repeats 3 --demo-delay 8
```

加载后预留 8 秒录屏准备时间，巡览每轮 35 秒，共三轮；结束后窗口保持打开。
将 scene ID 替换为另外两个场景即可。路线存放在 `configs/scenes/<ID>.json` 的 tour 字段。
这是人眼高度的相机动画，没有角色碰撞控制器，不能视为机器人导航测试。

输出干净的离线视频（无编辑器 UI）：

```bash
bash run_scene.sh --scene hallway2 --headless --capture --video-seconds 6
```

生成 24 fps 的 `tour.mp4`、首中尾帧截图和 `report.json`。
`--video-seconds` 把完整巡览映射到指定视频时长；6 秒版本用于快速验收，
正式展示可改为 35。离线编码帧率不等于实测交互帧率，实际采集帧时记录在报告里。

## 碰撞诊断与复验

```bash
bash run_scene.sh --scene hallway1_elegant --mode collision
bash run_scene.sh --scene hallway1_modern --mode overlay
bash run_scene.sh --scene hallway2 --headless --capture --physics-test --video-seconds 6
```

高斯场景的 collision 模式显示原始 GLB 静态碰撞网格，overlay 显示与高斯的交叠。
两层表面几乎重合时会出现颗粒/闪烁，这是诊断视图，不应用作展示画面。
hallway2 在原始视觉 Mesh 上附加碰撞，诊断模式将启用碰撞的构件标成绿色；
其他装饰仍可见，不代表所有装饰都被设置为碰撞体。

`--physics-test` 添加临时落球并记录射线命中、接触次数、轨迹和最终支撑面；完成后删除探针。
RTX 渲染使用 GPU；当前接触测试明确使用 **PhysX CPU**，不是 GPU 动力学或机器人步行验收。
所有查看器临时操作写入 USD session layer，不覆盖已构建源层。

输出默认在 `outputs/<ID>/<时间>/`。可用 `--output /完整/路径` 指定新目录；
不要重用已有验收目录，以免覆盖历史截图或报告。

## 修改配置与重建

编辑 `configs/scenes/<ID>.json` 后，需要先构建再运行：

```bash
.venv-tools/bin/python scripts/build_scene.py --scene hallway1_elegant
.venv-tools/bin/python scripts/build_scene.py --scene hallway1_modern
.venv-tools/bin/python scripts/build_scene.py --scene hallway2
.venv-tools/bin/python -m pytest tests -q
```

构建时生成新的指纹目录及 `current.json`。外观、物理、灯光、相机独立分层。
高斯转换在 `.venv-tools` 执行；不要将 usd-core 安装到 `.venv`。
源 `World/` 文件保留不改写；所有转换产物都位于 `generated/`。

如果 hallway2 的 GLB 更改或首次在新机器构建，先运行官方转换器：

```bash
.venv/bin/python scripts/convert_gltf.py \
  World/Environment/hallway2/hallway.glb \
  generated/hallway2/imported/visual.usdc
.venv-tools/bin/python scripts/build_scene.py --scene hallway2
```

转换设置保留构件、材质和相机，使用 USD Preview Surface，纹理通过相对路径引用。
本机转换器虽写 Z-up 元数据，实际导入几何仍沿用 glTF Y-up；当前配置已补偿 +90° X 旋转。
换版本后务必重新检查实际几何，不要只信 upAxis 标签，也不要重复叠加旋转。

BLEND 保留为编辑源，本次使用其已有 GLB 导出，并未直接运行 Blender 或 build_model.py。
若从 BLEND 重新导出，使用独立 Blender 进程，保留完整场景、贴图和构件层次；再重新验收。

## 可用范围

- 三个场景：静态观看、固定视角/巡览录制、已采样区域的接触验证。
- hallway2：保留可编辑构件，但门扇尚无铰链、驱动和独立动态物理。
- SPZ/GLB 资产并不自动提供精确语义、可靠传感器深度或可操作物品。
- 尺寸为估计值；下行楼梯的主平台作为高度基准，没有用隐藏平板补洞。
- 高斯边缘/近距离可能有漂浮和模糊；两份 SPZ 的抗锯齿训练标记不由当前 reader 保留，
  验收基于实际呈现，不宣称与 Marble 原始渲染像素一致。

验收结果和具体证据见 [三场景验收文档](scene_acceptance_20261014.md)。

## 三场景录屏巡览（带场景标签）

```bash
bash run_recording_tour.sh
```

在同一 Isaac Sim 窗口内依次播放 Elegant、Modern、hallway2。默认每个场景巡览
3 遍、每遍 15 秒，共 9 遍约 135 秒；每个场景先预留 8 秒录屏准备，另外有加载时间。
左上角显示颜色区分的场景名称、场景序号、TAKE 轮次和倒计时。每条路线包含走动和
360° 环视，结束后停留在 hallway2。相机动画没有人物碰撞控制器。

```bash
# 只重录 hallway2；结束后退出程序
bash run_recording_tour.sh --scenes hallway2 --seconds 15 --repeats 3 --prepare 8 --exit-after
```

录屏请选择整个应用窗口或包含左上角标签的视口区域。标签是屏幕 UI，不写入场景模型，
不进入普通 Replicator RGB 视频；带标签的截图与实际每轮耗时保存到
`outputs/recording_tour/<运行时间>/`。脚本不自动录制桌面视频；录屏由用户的录制软件完成。
相机/图层只写 session layer，原始资产和已验收构建不变。
