# hallway2 文件与 Isaac Sim 6.1 导入说明

2026-10-14 更新：另已完成独立的 `hallway2_blend` 直接 BLEND → USDC 路线及 GPU/接触验收，
见 [BLEND 路线使用说明](hallway2_blend_usage.md)。本文下方描述的原 `hallway2` GLB 路线保持不变。

源目录：`World/Environment/hallway2/`。这些文件描述的是同一个场景。

| 文件 | 用途 |
|---|---|
| `hallway.blend` | Blender 原生编辑源，保留构件分组、材质、灯光和四台相机。修改房间/楼梯时优先编辑它。 |
| `hallway.glb` | glTF 2.0 二进制导出；包括几何、节点变换、材质、嵌入木纹和相机，未导出渲染灯光。本次转换实际输入。 |
| `build_model.py` | 在 Blender 中重建模型的脚本，包含尺寸、门位、楼梯与材质生成逻辑。运行会重建 Blender 场景，不是 Isaac Sim 启动脚本。 |
| `oak_grain.png` | 程序生成的木纹贴图，不是现场照片；GLB 已嵌入图像，单独文件也供源模型编辑使用。 |
| `view_north.png` | 面向走廊三扇门的 Blender 参考效果图。 |
| `view_stairs.png` | 面向另一端门与楼梯口的参考效果图。 |
| `view_stair_detail.png` | 楼梯、扶手和转折踏步细节参考图。 |
| `view_cutaway.png` | 隐去部分墙体/吊顶后的总览参考图；不能据此认为完整 GLB 缺少这些构件。 |
| `validation.json` | 素材作者的建模/GLB 回导检查记录，不是 Isaac Sim GPU 验收报告。 |
| `说明.txt` | 素材来源、范围、坐标、估计尺寸和 Blender 操作说明。 |

这个模型是根据照片/视频建立的可编辑近似模型，不是实测扫描。包含可见走廊、四樘门、
栏杆和局部下行楼梯，不包含门后房间；7 级直踏步和 3 级转折踏步也是近似表达。

## 本次已经执行的路径

```text
hallway.blend（保留编辑源）
         └─ 已有 hallway.glb
                 ↓ Isaac Sim 6.1 官方 omni.kit.asset_converter
        generated/hallway2/imported/visual.usdc + textures/
                 ↓ 坐标修正、静态物理、室内灯光、验收相机
        generated/hallway2/<build-id>/scene.usda
                 ↓ RTX 渲染 / PhysX 接触 / 巡览
        outputs/hallway2/acceptance_final_20261014/
```

1. 在独立 Isaac Sim 6.1 进程中运行转换器，保留节点、网格、UV、材质和相机；不合并整场景。
   结果保留 272 个网格、15 个材质和 4 台源相机，木纹以相对路径引用。
2. 本机转换器导出的 USD 标记 Z-up，但实际几何仍是 glTF 的 Y-up 坐标。
   已在环境父层施加 +90° X 旋转，恢复 Blender 源模型朝向；新版本转换器必须重新核验，
   不能无条件复制这项补偿。单位设为米，但模型尺寸仍是估计值。
3. 添加静态碰撞：墙、地板、门扇、楼梯等 58 个结构 Mesh 启用 triangle-mesh collision。
   没有用覆盖楼梯的平面或隐藏无限地板兜底。
4. GLB 未带照明，单独配置室内与楼梯补光；增加 entry、reverse、stairs 三台验收相机。
5. 保存 scene、geometry、physics、lighting、cameras 分层 USD 与哈希清单，执行真实 GPU 截图、
   视频及四处落球检查。渲染为 RTX GPU，接触验证使用 PhysX CPU。

## 复现命令

```bash
cd /home/user/Documents/zoo/sim/worldlab

# GLB 修改后才需要重新转换
.venv/bin/python scripts/convert_gltf.py \
  World/Environment/hallway2/hallway.glb \
  generated/hallway2/imported/visual.usdc

# 配置修改后重建
.venv-tools/bin/python scripts/build_scene.py --scene hallway2

# 打开
bash run_scene.sh --scene hallway2

# 新建一轮截图、视频、接触验收输出
bash run_scene.sh --scene hallway2 --headless --capture --physics-test --video-seconds 6
```

`.venv` 是 Isaac Sim 运行环境；`.venv-tools` 是 CPU 资产装配环境，不要混装 USD 包。
本次没有直接打开 `.blend` 或重新执行 `build_model.py`。需要修改源模型时，在独立 Blender
进程中编辑并导出 GLB/USD；不要把 `bpy` 安装进 Isaac Sim 环境。

门目前仍是静态构件。开门需要进一步分离门框与门扇，添加刚体、铰链、限位、质量与驱动；
构件被保留不等于已经有交互逻辑。

[运行验收](scene_acceptance_20261014.md) · [场景使用说明](scene_usage.md)
