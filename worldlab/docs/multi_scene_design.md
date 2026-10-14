# Worldlab 多场景、多格式设计

日期：2026-10-14。本文保留实施前的技术路线和目标结构。

**实施更新：三个新增场景现已构建并完成 GPU 渲染与静态接触验收。**
见 [验收文档](scene_acceptance_20261014.md) 和 [使用文档](scene_usage.md)。
本次实际使用 `scenes.py`、`scene_physics.py`、`scene_tour.py` 与独立 `view_scene.py`，
没有迁移厨房旧查看器，也没有实现 Blender 重导出和动态开门；下方待实现描述为原始设计快照。
本次交付：原始资产审计脚本与报告、四场景目录、Skills 使用入口及本设计。
现有厨房运行链路保留；通用构建器、查看器与新场景 GPU 验收为后续实施项。

## 1. 已核实资产与 Skills

| 场景 ID | 输入 | 用途 | 当前状态 |
|---|---|---|---|
| kitchen | PLY + collider GLB | 高斯外观 + 静态碰撞 | 已有 6.1 渲染、落球、三轮巡览报告 |
| hallway1_elegant | Elegant Hallway with Staircase.spz + 对应 collider.glb | 高斯外观 + 静态碰撞 | CPU 审计；未做 GPU 验收 |
| hallway1_modern | Modern Hallway with Staircase.spz + 对应 collider.glb | 高斯外观 + 静态碰撞 | CPU 审计；未做 GPU 验收 |
| hallway2 | hallway.blend + hallway.glb + oak_grain.png | 同一场景的编辑源和便携导出 | GLB CPU 审计；BLEND 未在 Blender 打开 |

SPZ 均为 v2、SH degree 0；Elegant 1,920,000 个点，Modern 2,276,736 个点。
本机 usd-convert-gsplat 0.1.15 提供 read_spz，可与 PLY 共用 GaussianSplatData → USD writer。
两份 SPZ flags=1，需检查抗锯齿训练标记与渲染结果：当前 reader 没有将该标记传入返回数据，不能宣称像素无损。
GLB 的网格统计、包围盒、节点名和源文件 SHA256 见 outputs/source_audit/hallways.json。

hallway2 GLB 有 280 个节点、272 个网格、15 个材质、1 个图像、4 台相机；
使用 KHR_materials_emissive_strength。源说明将尺寸和楼梯标为近似，不能当作实测环境。
本机 PATH 未发现 blender，直接读 .blend 的路线需先确定独立 Blender 可执行文件及版本。

此前 README 记录参考了 isaac-sim-rendering / isaac-sim-validator，
outputs/skill_static_validation.txt 有官方 validator 的 Level 2 执行证据：0 errors / 2 warnings。
警告源于扫描器要求固定的 simulation_app 变量和固定 headless 模式；不能替代 GPU 验收。
本次读取 usd-composition-architecture，采用外观/物理分层的原则。
还核对了 isaac-sim-assets：其实际职责是资产根路径/网络访问，不能把它描述为 SPZ 或 Blender 转换器。
Skills 是按需读取的工作流程，不是运行时插件；安装目录存在不等于每次任务都会自动调用。

## 2. hallway1 路线：SPZ + GLB

1. 建立两个独立 scene ID，显式配对 visual 和 collision，禁止依赖目录中“第一个文件”。
2. 在 .venv-tools 中 read_spz → validate_splats → write_gaussian_splat_usd，输出 visual.usdc。
   不经普通点云/网格导入器，不必生成庞大的临时 PLY；保留尺度、旋转、opacity 与 SH。
   先检查版本；未来 v4 或带未知坐标扩展的文件应明确拒绝并走经验证的解码器，不冒充 v2。
3. 对 *_collider.glb 保留并烘焙 glTF 节点变换，转换为 collision.usdc；静态 triangle mesh。
   不为整栋房间加 convex hull；楼梯不能用平板替代，孔洞不能用无限地板掩盖。
4. 显式记录 visual_to_scene、collision_to_scene 两个格式归一化变换；验证两者在同一局部坐标后，
   用公共 /World/Environment 父变换设置场景位置、米制比例与 Z-up。
   SPZ 默认 RUB，而厨房 PLY 的实测朝向不同；USD upAxis 元数据本身不旋转引用几何。
   不照搬 kitchen 的 rotateX=-90、translateZ=1.1；重力、地面、楼梯方向用叠加图和几何核验。
   有下行台阶时以主平台为高度基准，不能把整个模型最低点抬到零当作走廊地面。
5. 配置每个场景自己的室内相机、入口位姿、35 秒闭合巡览、楼梯区域和探针位置。
6. 分开验收外观和碰撞：固定视角 + 视觉/碰撞叠加 + 多段巡览检查穿墙；
   地面/平台/踏步射线与落球接触；记录楼梯缺面、异常坡度及模型外区域。
   相机路线不等于角色控制器，更不等于双足机器人可以上下楼。

## 3. hallway2 路线：GLB 优先，BLEND 保留编辑源

首选直接转换已导出的 hallway.glb：

GLB → Isaac Sim 6.1 中的 omni.kit.asset_converter → 分层 USD → 物理配置 → GPU 验收。

转换时保留节点层次、UV、法线、材质绑定、贴图与相机；不开启合并全场景网格的选项。
将嵌入木纹导出到 Textures/，使用可重定位相对路径；核验发光强度扩展、木纹、金属、粗糙度。
与厨房不同，普通网格需要适当照明。源 GLB 明确没有导出灯光，应在 lighting.usda 中补室内灯，
发光材质不自动等同于足够的场景照明；不要默认继承厨房的高斯曝光方案。
转换器需在 SimulationApp 启动后加载；成功返回还要检查引用、材质和真实截图。

不使用 assets.load_mesh().to_mesh() 生成 visual：这条已有函数适合碰撞数据，会破坏需要保留的构件组织。
墙、地板、台阶采用静态三角网格或经验证的简单形状；装饰小件默认不生成大量精细碰撞。
物理层可对同一 Mesh 增加 CollisionAPI，无需再渲染一套重叠表面。

需要修改模型/从源重新导出时：

Blender 独立进程打开 hallway.blend → 固定导出选项 → USDC + Textures → 同一场景装配流程。
不要向 Isaac Sim Python 环境安装 bpy。必要时将程序材质烘焙为可携带纹理，检查修改器、
法线、可见性和相机。Blender 场景为 Z-up；导出后的 USD 和 GLB 不能无条件重复旋转。
源脚本会清空/重建 Blender 场景并写文件，审计时不执行；构建时输出重定向到 generated/，不覆盖 World/。

交互第二阶段：D1–D4 分拆 static frame 与 moving leaf；门扇饰面/把手随 leaf 运动，
门框、门套、门槛留在静态层。以真实铰链位置建立 RevoluteJoint，配置轴、角限位、质量/惯性、
碰撞近似、阻尼及可选驱动；在此之前只能说“结构可编辑”，不能说“已经能开门”。
动态门扇使用简单凸形/凸分解碰撞，不套用全场景静态 triangle-mesh 策略。

## 4. 统一项目结构（目标）

```text
World/Environment/                  原始输入，只读约定
configs/scene_catalog.json          已建立：scene ID、来源角色、路线和状态
configs/scenes/<id>.json            待实现：坐标/相机/物理/验收的完整运行配置
configs/tours/<id>.json             待实现：场景专属巡览轨迹
src/worldlab/
  registry.py                      待实现：配置校验、路径和 scene ID 解析
  importers/{gsplat,gltf,blender}.py 待实现：按表示形式转换
  compose.py                       待实现：组合 USD 与稳定 prim 路径
  physics.py                       待实现：静态/动态物理装配
  validate.py                      待实现：分级验收和报告
  viewer.py                        待实现：通用查看器
scripts/audit_hallways.py           已建立：当前新增素材 CPU 审计
scripts/{build_scene,view_scene}.py 待实现：薄 CLI，不复制每个场景脚本
scripts/{build_kitchen,view_kitchen}.py 现有入口，迁移期继续可用
scripts/skills_env.sh               已建立：仅在 source 后设置本项目技能环境
generated/<id>/<build-id>/         下方结构；build-id 由源/配置/转换器指纹生成
  scene.usda                       单一入口，metersPerUnit=1 / Z-up
  geometry/{visual,collision}.usdc  大型数组；网格视觉保留层次与材质绑定
  materials.usda + Textures/        网格材质与相对纹理资源
  physics.usda                     碰撞、刚体、关节和物理参数
  lighting.usda                    普通网格与高斯分别配置
  cameras.usda                     固定验收视角与巡览起点
  semantics.usda                   可选且经标注验证，不能从格式导入凭空生成
  manifest.json                    来源哈希、配置、工具版本、生成文件哈希
outputs/<id>/<run-id>/              截图、录屏、日志、实测验收
```

公共场景 prim：/World/Environment、/World/PhysicsScene、/World/Cameras。
独立交互物体位于 /World/Objects；物理层指向明确 prim，而不是写死 /World/Kitchen/Collision/Mesh。
先抽取现有硬编码，保留 kitchen 兼容包装；不能仅新增 --scene 参数便宣称支持多场景。
视觉 payload 可以独立控制加载；仅隐藏 visibility 不等于卸载，也不能仅凭 visual_material=None
宣称已经跳过外观内存。默认一次打开一个场景；验证后再考虑并排、多实例或按需加载。

配置至少包含：schema_version、id、representation、sources（角色+格式+哈希）、
每个输入的归一化变换、scene_to_world、scale_status、lighting_profile、collision_policy、
固定相机、tour、机器人起点、区域边界、physics_probes、验收阈值与允许的降级。
尚未核实的变换必须为 null / pending_alignment，构建器拒绝自动套用厨房参数。

manifest 与运行报告分离：configured → source_audited → built → render_passed → physics_passed → interaction_passed。
interaction 允许 not_requested；不要用一个模糊的 runtime_validated 布尔值覆盖不同验收层级。
源变更、转换器变更、配置变更均使相应缓存失效；临时构建完成且检查通过后原子发布，
失败保留诊断但不覆盖最近一次通过版本。记录峰值 RAM/VRAM、预热时间、真实帧时和输出体积。

## 5. 实施顺序和完成标准

1. 本次完成设计、源审计、目录与 Skills 指引。
2. 通用化配置/装配/相机/物理目标路径；用 kitchen 回归保证三视角、落球与 35s×3 巡览仍通过。
3. 接入 SPZ importer，依次完成 elegant、modern 的配准和验收；不同时开两份高斯场景猜性能。
4. GLB 保材质导入 hallway2，检查 272 网格构件与源相机/材质映射，补灯光并做楼梯验收。
5. 有编辑需求时加入 Blender 导出适配器；交互需求再选择一扇门做完整开合试验，再推广至其余门。

CPU 检查：配置/源配对/坏文件、有限数值、四元数、单位、节点变换、依赖路径与缓存失效。
GPU 检查：每场景固定视角、叠加图、巡览首中尾、材质/贴图、接触事件与最终支撑面。
发布报告必须分别写“未测试/通过/失败”；旧截图与新资产哈希不一致时不得复用作为通过证据。
当前新场景尚无 GPU 验收，因此不输出虚构的可运行 build_scene 命令或可通行保证。

## 6. 参考依据

- [官方 Agent Skills](https://docs.isaacsim.omniverse.nvidia.com/latest/development_tools/agent_skills.html)
- [GSplat Converter：SPZ v2/v3 与 PLY](https://docs.omniverse.nvidia.com/extensions/latest/ext_gsplat-converter/manual.html)
- [Niantic SPZ：格式与坐标约定](https://github.com/nianticlabs/spz)
- [Omniverse Asset Converter：GLB、材质、相机](https://docs.omniverse.nvidia.com/extensions/latest/ext_asset-converter.html)
- [Blender 4.4 USD 导出与限制](https://docs.blender.org/manual/en/4.4/files/import_export/usd.html)

在线文档可能滚动更新；具体行为以本机版本、转换结果与真实 6.1 验收为准。
