# hallway2 双路线录制与 hallway1 GLB 内容

日期：2026-10-14。

## hallway2：同一窗口连续对比

```bash
cd /home/user/Documents/zoo/sim/worldlab
bash run_hallway2_comparison.sh
```

顺序：GLB 路线 3 遍 → BLEND 路线 3 遍，每遍 15 秒，巡览净时长约 90 秒。
每个场景预热后有 15 秒准备倒计时，切换自动完成。左上角分别显示：

- 橙色 `HALLWAY 2 / GLB IMPORT`，来源 `GLB -> USD / Isaac Sim 6.1`。
- 紫色 `HALLWAY 2 / DIRECT BLEND`，来源 `BLEND -> USDC / Isaac Sim 6.1`。
- 当前场景序号、TAKE 1/3–3/3 和剩余时间。

每遍沿同一闭合路线前进、环视 360°、俯看楼梯并返回入口。两条路线的相机、轨迹、
曝光及补光配置已经程序比对一致；原场景文件不变，运行时仅在 session layer 移动相机。
BLEND 路线还保留了源文件 7 盏灯和烘焙的地板色调，因此这是两条实际交付链路的效果对比，
不能将全部亮度差异归因于几何格式。没有将两套几何叠加在同一空间，也没有修改两套场景以强行匹配外观。

脚本供桌面录屏，不自动写出 90 秒桌面视频。每次输出新的目录，保存六张带标签截图与实际用时报告。
本次六遍均完成，净巡览实测 **90.10 秒**；六张标签截图已检查，回归测试 **11 passed**。
本次运行：`outputs/recording_tour/hallway2_comparison_20261014_154807/`。
最新一次运行路径见 `outputs/recording_tour/latest_hallway2_comparison.json`。
重播前关闭当前演示窗口；可加 `--prepare 30` 延长每场景准备时间。

## hallway1 GLB：实际内容，不只看文件名判断

直接解析原始 GLB 的 JSON / BIN 块，审计记录：
`outputs/source_audit/hallway1_glb_contents_20261014.json`。

| 项目 | Elegant Hallway | Modern Hallway |
|---|---:|---:|
| 文件 | `Elegant Hallway with Staircase_collider.glb` | `Modern Hallway with Staircase_collider.glb` |
| 网格 | 1 | 1 |
| 顶点 | 24,839 | 24,259 |
| 三角形 | 49,046 | 47,918 |
| 场景 / 节点 | 1 / 3 | 1 / 3 |
| 基础材质 | 1 | 1 |
| 不同顶点 RGBA 颜色数 | 17,927 | 16,757 |
| UV / 贴图 / 图片 | 无 | 无 |
| 相机 / 灯光 / 动画 / 骨骼 | 无 | 无 |

两份文件均具有：

- `POSITION`：顶点位置；索引按三角形组织，可描述地面、墙、楼梯等表面。
- `NORMAL`：顶点法线，用于表面光照。
- `COLOR_0`：归一化 RGBA 顶点颜色；颜色确实变化，透明度均为 255，不是全白占位。
- 一个基础 PBR 材质，记录 `metallicFactor=1`、`roughnessFactor=1`，没有纹理引用。
- 节点父子关系与变换矩阵；转换时需要应用它们，不能只读取未变换的顶点数组。
- 少量名称和 `processed=true` 元数据。没有物理扩展或门、家具等逐物体语义标注。

因此它们是**带颜色的三角网格，被本项目用作静态碰撞代理**。
`_collider` 是预期用途，文件本身并没有 Isaac 的 CollisionAPI、质量、摩擦、刚体或门铰链配置。
碰撞属性是 Worldlab 转换后，在 USD 的物理层中添加的。

本项目分工：

```text
SPZ → visual.usdc → 可见的高斯外观
GLB → collision.usdc → 默认不显示的静态三角碰撞
                        ↓
                 physics.usda 添加碰撞规则
```

`assets.convert_collider()` 还会将顶点颜色写为 USD `displayColor`；它不是完整 GLB 外观材质导入器。
当前 `--mode collision` 调试显示会覆上统一绿色材质，看到绿色不表示原 GLB 没有颜色。

GLB 可以独立作为有颜色的网格显示或用于几何查询，但它没有 SPZ 的高斯外观数据，
也没有高清纹理或细分的可操作物体。单独加载它不能自动获得 SPZ 的视觉细节，不能直接让门开合。
