# hallway2_blend 验收记录

日期：2026-10-14。独立场景，未替换原 `hallway2`。

## 环境与可追溯性

- Blender **5.2.0 LTS**，官方压缩包 SHA256：`96f6c181a30f4950607839dc84d42a354b250d8a0231b098b59b7bc69c351c48`。
  安装包来自清华 Blender 镜像，对照 [Blender 官方校验文件](https://download.blender.org/release/Blender5.2/blender-5.2.0.sha256) 验证。
- Isaac Sim **6.1.0.0**；NVIDIA RTX PRO 5000 Blackwell，48 GB；驱动 **580.105.08**。
- 构建：`generated/hallway2_blend/280833cb4f24/scene.usda`。
- 转换清单：`generated/hallway2_blend/imported/conversion.json`，记录原 BLEND、导出代码、每个输出文件的 SHA256、参数及对象清单。
- 运行报告：`outputs/hallway2_blend/acceptance_20261014/report.json`，记录源码、配置、场景及依赖哈希。
- 原文件保护：`outputs/hallway2_blend/preservation_before.json` 与 `preservation.json`。
  118 个原始素材、旧配置及已有生成文件在目录扩展前逐项哈希一致。
  `catalog_extension.json` 记录仅向场景目录追加新条目；原四个目录条目没有改变。

## 检查与结果

| 检查 | 结果 |
|---|---|
| 原始 BLEND 不变、无 GLB 中间步骤 | 通过 |
| 272 网格 / 15 材质 / 4 源相机 / 7 源灯光 | 通过 |
| 原木纹 + 6 张地板色调贴图，相对路径可解析 | 通过 |
| 米制 Z-up、楼梯向下、主平台高度 | 通过 |
| 静态三角网格碰撞 | 58 个，无整场景凸包或替代地板 |
| CPU 回归测试 | 11 passed，包含原三个新场景和本次 BLEND 场景 |
| RTX GPU RGB 三视角 | 通过；1280×720 |
| 6 秒验收巡览视频 | 144 帧 / 24 fps，首中尾曝光检查通过 |
| PhysX CPU 接触 | 4/4 探针通过；240 步，每个探针记录到 20 次网格接触 |

三视角平均 RGB：入口 **174.79**、回望 **137.13**、楼梯 **147.73**。
入口、门、木地板、墙面、扶手和楼梯图片已经实际查看；没有黑帧、缺贴图紫色或整体倾倒。
图像：`entry_visual.png`、`reverse_visual.png`、`stairs_visual.png`；视频：`tour.mp4`，均在上述验收目录。

| 探针 | 实测支撑面 Z / 米 | 结果 |
|---|---:|---|
| landing | -0.0100 | 通过 |
| corridor | -0.0100 | 通过 |
| stair4 | -0.7200 | 通过 |
| winder | -1.4400 | 通过 |

GPU 用于 RTX 图像渲染；本次接触测试明确运行于 **PhysX CPU**，不称为 GPU 物理验收。
检查后整卡显存使用约 4813 MiB，该读数包含桌面等进程，不是独立测得的本场景峰值。

实际命令：

```bash
.venv-tools/bin/python -m pytest tests -q
bash run_scene.sh --scene hallway2_blend --headless --capture \
  --physics-test --video-seconds 6 \
  --output outputs/hallway2_blend/acceptance_20261014
bash run_recording_tour.sh --scenes hallway2_blend --seconds 15 \
  --repeats 3 --prepare 15 --output outputs/hallway2_blend/recording_20261014
```

自动演示证据在 `outputs/hallway2_blend/recording_20261014/report.json`，
附三张带 DIRECT BLEND / TAKE 标签的桌面截图。三遍均完成，分别为 **15.017 / 15.016 / 15.015 秒**，
总时长 **45.049 秒**；每遍环视 360°。汇总及证据哈希见 `outputs/hallway2_blend/summary.json`。

## 官方 Skills 的实际应用

读取了 Isaac Sim 6.1.0.0 安装内的以下技能文档，应用其分层、渲染实测和物理后端显式选择原则：

- `.venv/lib/python3.12/site-packages/isaacsim/skills/usd-composition-architecture/SKILL.md`
- `.venv/lib/python3.12/site-packages/isaacsim/skills/isaac-sim-rendering/SKILL.md`
- `.venv/lib/python3.12/site-packages/isaacsim/skills/physics-simulation/SKILL.md`

本次运行的是项目脚本，不是直接执行这些技能的示例 helper。色调映射与灯强使用本机实测配置，
没有照抄技能中的室外或仓库数值。最终凭据为实际 RTX 截图和 PhysX 接触报告。

## 使用范围

这是可渲染、具有静态碰撞的近似建筑场景。尺寸来自素材的近似建模，未进行现场测量。
未配置门铰链、动态操作、导航网格或机器人控制器；相机巡览不能当作机器人通行验收。
Blender 材质和 USD Preview Surface、Cycles 和 RTX 之间仍有渲染差异；六种地板乘色已显式处理，
不是对任意 Blender 节点图作通用保真承诺。
