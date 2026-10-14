# hallway2：直接 BLEND → Isaac Sim 6.1

日期：2026-10-14。新增独立场景 ID：`hallway2_blend`。
原 `hallway2` 继续使用 GLB 链路；Kitchen、两个 hallway1 和原 hallway2 的配置、生成资产与场景入口均保留。

## 使用与录制

在项目目录运行：

```bash
cd /home/user/Documents/zoo/sim/worldlab
bash run_blend_tour.sh
```

打开 Isaac Sim 6.1 桌面窗口，预热后倒计时 15 秒，再连续巡览 3 遍，每遍 15 秒。
左上角显示 `HALLWAY 2 / DIRECT BLEND`、`BLEND -> USDC / Isaac Sim 6.1`、TAKE 遍数和剩余时间。
每遍从入口出发，在走廊内前进、环视 360°、俯看楼梯并返回起点；结束后窗口保持打开。
这是相机巡览，不是带碰撞控制器的人物或机器人行走；没有新增开门关节。
每次运行产生新的时间戳输出目录，保存逐遍用时、完成状态和带界面标签的截图。
脚本不自动保存桌面录像，可用自己的录屏软件录制；验收另有 6 秒无界面巡览 MP4。

重播前关闭上一次巡览窗口，以免多窗口争用 GPU。需要更长准备时间可使用：

```bash
bash run_blend_tour.sh --prepare 30
```

只查看新场景：

```bash
bash run_scene.sh --scene hallway2_blend
```

原 GLB 场景仍使用 `bash run_scene.sh --scene hallway2`。
原三场景录制入口 `bash run_recording_tour.sh` 的默认播放列表没有改变。

## 实际转换链路

```text
World/Environment/hallway2/hallway.blend
  → 独立 Blender 5.2.0 LTS 进程
  → generated/hallway2_blend/imported/visual.usdc + textures/
  → geometry / physics / lighting / cameras 四个 USD 层
  → generated/hallway2_blend/280833cb4f24/scene.usda
  → Isaac Sim 6.1.0.0 / RTX 渲染 + PhysX 接触检查
```

没有 GLB 中间文件，也没有 USDZ 环节。Isaac Sim 打开的是组合后的 `scene.usda`，
它引用真正的二进制几何文件 `visual.usdc`。USDC 需要随附贴图；只复制 USDC 会丢失外部贴图依赖。
稳定入口可查 `generated/hallway2_blend/current.json`；构建号会随源或转换代码变化。

转换器为 `scripts/export_blend_usd.py`；Blender 位于 `.tools/blender/blender-5.2.0-linux-x64/blender`。
没有向 Isaac Sim 的 `.venv` 安装 bpy，也没有改动原始 `World/` 文件。
使用 `--factory-startup --disable-autoexec` 打开工程，未执行原素材目录里的 `build_model.py`。

首次转换命令如下。当前输出已经存在，转换器会拒绝覆盖；请勿为了重放演示重复导出。
后续修改源时应导出到新的目录，保留旧导入结果及验收证据，再发布新构建。

```bash
.tools/blender/blender-5.2.0-linux-x64/blender \
  --background --factory-startup --disable-autoexec --python-exit-code 1 \
  --python scripts/export_blend_usd.py -- \
  --source World/Environment/hallway2/hallway.blend \
  --output generated/hallway2_blend/imported
.venv-tools/bin/python scripts/build_scene.py --scene hallway2_blend
```

转换保留 272 个网格、15 个材质、4 台源相机和 7 盏源灯光。
Blender 修改器按渲染结果求值；六种实际使用的地板色调的 Image×Constant 节点在临时内存中转为六张 PNG，
与原木纹合计七张贴图，不更改源文件的材质图。该处理专用于本资产的乘色节点，不是通用节点烘焙器。
Blender USD 导出遗漏了正交剖视相机，适配器额外写回它的正交视野和世界变换。
源灯光保留，同时添加独立的 Isaac 室内补光层，实际画面不承诺与 Blender Cycles 逐像素一致。

直接 USD 为米制、Z-up，父变换为零旋转；不能套用原 GLB 导入链路的 +90° X 修正。
主平台保留在约 Z=-0.01 米，楼梯向负 Z 延伸。58 个墙、地面、门扇及楼梯等网格附加静态三角碰撞。
没有为了通过测试添加隐形地板，也没有将整间房间变成凸包。

## 为什么同时提供 BLEND 和 GLB

素材目录 `build_model.py` 第 271–272 行先保存 BLEND、再导出 GLB，说明它们来自同一建模结果。
这一流程体现了“可继续编辑的工程 + 易于分发的交换文件”的用途分工：

| 文件 | 本项目中实际具有的信息 | 适合用途 |
|---|---|---|
| `hallway.blend` | 272 网格、集合组织、修改器、完整材质节点、打包纹理、4 相机、7 灯光及 Blender 渲染设置 | 改门窗/楼梯、调整材质和照明、重新导出；本次直接转 USD |
| `hallway.glb` | 272 网格、15 材质、UV/嵌入纹理、节点和4相机；源脚本明确 `export_apply=True`、`export_lights=False` | 无需 Blender 即可预览、传递、进入支持 glTF 的引擎；原 hallway2 路线 |

能独立使用不代表信息完全相同。GLB 是交付快照，无法完整还原 Blender 的修改器栈、专用材质节点和渲染配置。
BLEND 信息更丰富，但读取和导出依赖 Blender，且需要处理 USD 不支持的节点、坐标和材质表达。
两者不要求同时加载；同时叠加会重复显示同一套几何。后续编辑以 BLEND 为源，需要 GLB 的使用方再重新导出，
避免出现两个不同步的版本。对于当前 Isaac 运行环境，选择经过验收的一条 USD 路线即可。

验收数据和限制见 [本次验收文档](hallway2_blend_acceptance_20261014.md)。
