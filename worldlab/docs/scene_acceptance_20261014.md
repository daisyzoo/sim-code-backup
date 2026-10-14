# 三个新增场景验收 · 2026-10-14

结论：Elegant、Modern、hallway2 均在本机 Isaac Sim **6.1.0.0** 完成真实 RTX GPU 渲染验收，
并通过静态场景接触测试。原始 SPZ、GLB、BLEND 文件哈希全部未变。

## 环境与范围

- GPU：NVIDIA RTX PRO 5000 Blackwell，驱动 580.105.08。
- 渲染：RTX 实时渲染（实际设置为 RealTimePathTracing），单 GPU，1280×720；每场景三台固定验收相机。
- 物理：**PhysX CPU**，dt=1/60，240 步落球轨迹；GPU 用于图像渲染。
- 视频：每场景 6 秒 / 24 fps / 144 帧；已重新解码核对帧数和尺寸，检查首中尾画面。
- CPU：9 项测试通过，包括层引用、单位、静态碰撞、闭合巡览、纹理可解析与楼梯朝向。
- 官方 Skills：读取 isaac-sim-rendering、physics-simulation；以真实截图/接触报告验证，
  没有将静态扫描当作运行通过。技能及运行源码哈希记录在汇总 JSON。

## 结果

| 场景 | 固定截图 | 录像 | 落球通过 | 实际接触数 | 证据 |
|---|---:|---|---:|---|---|
| hallway1_elegant | 3/3 | 144 帧 / 24 fps | 3/3 | 353 / 280 / 621 | [报告](../outputs/hallway1_elegant/acceptance_final_20261014/report.json) · [视频](../outputs/hallway1_elegant/acceptance_final_20261014/tour.mp4) |
| hallway1_modern | 3/3 | 144 帧 / 24 fps | 3/3 | 256 / 230 / 309 | [报告](../outputs/hallway1_modern/acceptance_final_20261014/report.json) · [视频](../outputs/hallway1_modern/acceptance_final_20261014/tour.mp4) |
| hallway2 | 3/3 | 144 帧 / 24 fps | 4/4 | 20 / 20 / 20 / 20 | [报告](../outputs/hallway2/acceptance_final_20261014/report.json) · [视频](../outputs/hallway2/acceptance_final_20261014/tour.mp4) |

[场景九视角总览](../outputs/acceptance_20261014/scenes_overview.jpg) ·
[视频首中尾检查](../outputs/acceptance_20261014/video_review.jpg) ·
[高斯/碰撞配准检查](../outputs/source_audit/hallway_alignment_review.jpg) ·
[机器可读验收汇总与哈希](../outputs/acceptance_20261014/summary.json) ·
[视频解码结果](../outputs/acceptance_20261014/video_decode_check.json) ·
[CPU 测试日志](../outputs/source_audit/cpu_tests_20261014.txt)

## 资产与坐标

- Elegant：1,920,000 个高斯，49,046 个碰撞三角形。
- Modern：2,276,736 个高斯，47,918 个碰撞三角形。
- 两个 SPZ 都是 v2 / SH degree 0，直接转 USD，没有中间 PLY 或点云降采样。
- SPZ 与同组 GLB 原坐标一致；采用共同 +90° X 旋转转为 Z-up。
  主平台高度偏移分别为 +0.004 m 和 +1.83 m；未以最低楼梯点为地面。
  采样点到表面的近邻距离比对支持该配准，截图叠加确认整体结构对齐；
  此检查不表示高斯和简化碰撞网格逐点重合。
- hallway2：官方 GLB 转换器保留 272 个网格、15 个材质、4 台源相机和嵌入木纹；
  另外增加三台验收相机，58 个结构 Mesh 启用静态碰撞。
  木纹纹理路径已解析校验；BLEND 保留作为源，本次没有重新执行 Blender 建模脚本。
- hallway2 检出导出 USD 的 Z-up 元数据与实际 Y-up 几何不一致，已用父层 +90° X 修正；
  第四级直踏步实测高度 -0.72 m，转折踏步探针实测 -1.44 m，与源模型相符。

## 接触通过条件

射线必须命中场景白名单中的实际碰撞网格；落球半径 0.06 m、质量 0.1 kg，
从命中表面上方 0.45 m 释放。要求轨迹有限、发生真实网格接触、明显下落，
最终球心到实际支撑面高度与半径相符，且初始表面高度落在该探针预期范围。
没有使用隐藏无限地板；三个场景总计 10 个探针通过。

采样范围：Elegant/Modern 各为主平台、走廊、下行楼梯；hallway2 为两处走廊地面、
直踏步和转折踏步。结果只覆盖这些位置，不代表整场景无孔洞或机器人能上下楼梯。

## 性能记录与诊断

- hallway1_elegant：启动及预热 9.71 秒；离线平均采集 0.067 秒/帧；验收末整卡显存快照 `NVIDIA RTX PRO 5000 Blackwell, 580.105.08, 7952 MiB, 48935 MiB`。
- hallway1_modern：启动及预热 10.41 秒；离线平均采集 0.101 秒/帧；验收末整卡显存快照 `NVIDIA RTX PRO 5000 Blackwell, 580.105.08, 8089 MiB, 48935 MiB`。
- hallway2：启动及预热 8.48 秒；离线平均采集 0.055 秒/帧；验收末整卡显存快照 `NVIDIA RTX PRO 5000 Blackwell, 580.105.08, 4754 MiB, 48935 MiB`。

显存是 nvidia-smi 的整卡快照，含桌面或其他进程，不是场景独占值或峰值。
24 fps 是视频编码速率，不是实时仿真性能承诺。早期 hallway2 验收曾有约 211 秒 Kit 启动延迟，随后正常完成；
其他运行约 7–10 秒启动，不能把该延迟归结为场景几何复杂度。
日志中的 inotify change watches 报错指文件监视配额，不是本次磁盘写入失败；
所有最终图片、视频和报告均已保存并校验。没有修改系统配额。

## 已解决问题与保留限制

- 初次 hallway2 坐标导致楼梯射线无命中；修正后四处探针均通过。
- 封闭网格走廊初次照明过暗；增加室内和楼梯补光后重新验收。
- 初次场景缺少 timeline 范围；已设置 0–36000，最终构建没有该配置缺失。
- 检出 Kit 加载场景会覆盖渲染参数；最终在预热后固定 tonemap op=6、filmIso=100、histogram=false，报告核对实际值。
- 预览失败记录保留在各场景 preview_* 与 outputs/imports 日志中；最终结果以本页链接为准。
- 所有门、栏杆、家具当前为静态环境；没有创建开门关节、抓取任务或机器人控制器。
- 尺寸及楼梯为生成/近似资产；高斯的抗锯齿训练标记未由当前 reader 完整传递，
  不宣称与 Marble 原渲染像素一致。普通网格与高斯的照明观感也不要求完全相同。

## 复现

按照 [使用文档](scene_usage.md)启动、重建和复验。生成层、原始资产和运行源码哈希
在每个 report.json 的 manifest 以及汇总中；修改配置后必须先构建再运行。
执行 `.venv-tools/bin/python scripts/write_scene_acceptance.py` 会检查当前资产/代码与验收报告是否一致，
不一致或运行失败时拒绝生成通过汇总。
