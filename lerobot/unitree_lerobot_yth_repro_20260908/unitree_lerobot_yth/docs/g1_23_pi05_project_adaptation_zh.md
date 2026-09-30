# G1_23 `pi0.5 LoRA` 项目适配记录

本文档整理当前仓库里已经完成的适配、训练结果、真机评测链路改动，以及截至目前的已知问题。

适用对象：

- Unitree G1 `23 DoF`
- 左臂 `5 DoF`
- 右臂 `5 DoF`
- 腰部 `1 DoF`
- 无夹爪
- 单头部相机
- 任务：`right hand approach rag`


## 1. 原始数据定义

当前项目采用的训练状态/动作定义是：

- `state = left_arm.qpos(5) + right_arm.qpos(5) + body.qpos[0](1)`
- `action = left_arm.qpos(5) + right_arm.qpos(5) + body.qpos[0](1)`
- 总维度：`11`

图像定义：

- 单路头部相机
- 训练特征键：`observation.images.cam_high`

原始数据目录：

- `/home/igs/Desktop/project/vla/xr_teleoperate/teleop/utils/data/g1_23_right_hand_rag_reach`

转换后的 LeRobot 数据集目录：

- `/home/igs/Desktop/project/vla/data/local/g1_23_right_hand_rag_reach_11d`


## 2. 数据转换适配

### 2.1 新增 G1_23 11 维 RobotConfig

修改文件：

- [unitree_lerobot/utils/constants.py](/home/igs/Desktop/project/vla/unitree_lerobot/unitree_lerobot/utils/constants.py)

关键改动：

- 新增 `G1_23DOF_ARMS5_WAIST1_CONFIG`
- 新增 `ROBOT_CONFIGS["Unitree_G1_23Dof_Arms5_Waist1"]`
- 图像映射：
  - `color_0 -> cam_high`
- 状态/动作路径：
  - `left_arm.qpos`
  - `right_arm.qpos`
  - `body.qpos[0]`

### 2.2 扩展 JSON 路径解析

修改文件：

- [unitree_lerobot/utils/convert_unitree_json_to_lerobot.py](/home/igs/Desktop/project/vla/unitree_lerobot/unitree_lerobot/utils/convert_unitree_json_to_lerobot.py)

关键改动：

- 支持 `body.qpos[0]` 这类带数组索引的路径
- 转换时从原始 `data.json` 读取 `fps`


## 3. 数据校验

新增脚本：

- [scripts/validate_g1_23_lerobot_alignment.py](/home/igs/Desktop/project/vla/unitree_lerobot/scripts/validate_g1_23_lerobot_alignment.py)

用途：

- 对照原始 JSON 和转换后的 parquet
- 逐帧校验：
  - `observation.state`
  - `action`

默认对照路径：

- raw:
  `/home/igs/Desktop/project/vla/xr_teleoperate/teleop/utils/data/g1_23_right_hand_rag_reach`
- lerobot:
  `/home/igs/Desktop/project/vla/data/local/g1_23_right_hand_rag_reach_11d`

结论：

- 已验证 `100` 条 episode、`6000` 帧对齐正确


## 4. `pi0.5 LoRA` 训练适配

### 4.1 配置层改动

修改文件：

- [unitree_lerobot/lerobot/src/lerobot/policies/pi05/configuration_pi05.py](/home/igs/Desktop/project/vla/unitree_lerobot/unitree_lerobot/lerobot/src/lerobot/policies/pi05/configuration_pi05.py)

新增参数：

- `lora_rank`
- `lora_alpha`
- `lora_dropout`
- `lora_target_language_model`
- `lora_target_action_expert`
- `debug_numerics_once`

归一化配置改动：

- `STATE -> QUANTILES`
- `ACTION -> MIN_MAX`

说明：

- 原先 `ACTION -> QUANTILES` 会因为第 11 维分位统计异常导致动作归一化爆炸
- 改成 `MIN_MAX` 后，训练恢复正常

### 4.2 模型层改动

修改文件：

- [unitree_lerobot/lerobot/src/lerobot/policies/pi05/modeling_pi05.py](/home/igs/Desktop/project/vla/unitree_lerobot/unitree_lerobot/lerobot/src/lerobot/policies/pi05/modeling_pi05.py)

关键改动：

- 给 `paligemma.language_model` 注入 LoRA
- 给 `gemma_expert` 注入 LoRA
- base 参数先全部冻结，再只训练 LoRA
- 加入 tied embedding 校验
- 加入 trainable 参数统计
- 加入训练时数值 debug 日志
- 兼容从 base checkpoint 启动再挂 LoRA 的路径

训练后典型状态：

- trainable params 约 `26.5M`
- total params 约 `3.64B`

### 4.3 训练脚本

脚本：

- [scripts/train_pi05_lora_g1_23_rag_reach.sh](/home/igs/Desktop/project/vla/unitree_lerobot/scripts/train_pi05_lora_g1_23_rag_reach.sh)

关键配置：

- 数据集：
  - `local/g1_23_right_hand_rag_reach_11d`
- 默认 `batch_size=2`
- `lora_rank=16`
- `lora_alpha=32`
- `lora_dropout=0.05`
- 输出目录在：
  - `/media/igs/EAGET/syh/vla/outputs/...`
- 训练日志保存为：
  - `RUN_OUTPUT_DIR/train.log`
- 优先复用本地 `pi05_base` snapshot


## 5. 当前训练结果

已完成一轮 `pi0.5 LoRA` 训练，checkpoint 根目录：

- `/media/igs/EAGET/syh/vla/outputs/pi05_lora_g1_23_rag_reach_20260520_172745/checkpoints`

当前常用测试 checkpoint：

- `006000/pretrained_model`

训练趋势总结：

- 修复归一化后，loss 从约 `0.35` 下降到 `0.02 ~ 0.04`
- `bs=2` 时训练稳定
- 当前最成熟 checkpoint 是 `6000`


## 6. 真机评测链路改动

### 6.1 配置与图像接入

修改文件：

- [unitree_lerobot/eval_robot/utils/utils.py](/home/igs/Desktop/project/vla/unitree_lerobot/unitree_lerobot/eval_robot/utils/utils.py)
- [unitree_lerobot/eval_robot/make_robot.py](/home/igs/Desktop/project/vla/unitree_lerobot/unitree_lerobot/eval_robot/make_robot.py)

关键改动：

- `EvalRealConfig` 增加：
  - `image_host`
  - `network_interface`
  - `send_real_robot`
- `setup_image_client()` 使用 `ImageClient(host=args.image_host, request_bgr=True)`
- `process_images_and_observations()` 增加：
  - `observation.images.cam_high`

### 6.2 G1_23 11 维状态/动作适配

修改文件：

- [unitree_lerobot/eval_robot/eval_g1.py](/home/igs/Desktop/project/vla/unitree_lerobot/unitree_lerobot/eval_robot/eval_g1.py)
- [unitree_lerobot/eval_robot/make_robot.py](/home/igs/Desktop/project/vla/unitree_lerobot/unitree_lerobot/eval_robot/make_robot.py)
- [unitree_lerobot/eval_robot/robot_control/robot_arm.py](/home/igs/Desktop/project/vla/unitree_lerobot/unitree_lerobot/eval_robot/robot_control/robot_arm.py)

关键改动：

- `G1_23` 评测按 `10 arm + 1 waist` 处理
- 构造 `observation.state = 11` 维
- 模型输出 `action = 11` 维拆分为：
  - arm action `10`
  - waist yaw `1`

### 6.3 dry-run 与真机模式分离

关键改动：

- `--send_real_robot=false`
  - 只做观测与推理
  - 不发送真机命令
- `--send_real_robot=true`
  - 执行初始化
  - 再发真机控制命令

### 6.4 真机初始化流程

在 `G1_23_ArmController` 中新增：

- `move_all_joints_to_zero_and_lock_non_arm_waist()`

逻辑：

- 先尝试整机目标归零
- 非手臂/非腰部关节锁定在 `0`
- 手臂和腰部保留后续控制能力


## 7. DDS / 真机排查结论

### 7.1 已定位过的问题

#### 问题 1：Shell 环境变量污染

当前机器某些 shell 会带着这些变量：

- `CYCLONEDDS_URI`
- `RMW_IMPLEMENTATION`
- `ROS_DOMAIN_ID`

其中一份坏的 `CYCLONEDDS_URI` 会直接导致：

- `ChannelFactoryInitialize(...)` 失败
- 或 `cyclonedds.domain.Domain` 初始化失败

规避方式：

```bash
unset CYCLONEDDS_URI
unset RMW_IMPLEMENTATION
unset ROS_DOMAIN_ID
```

#### 问题 2：真机侧状态异常

在某次调试中，最小 DDS 初始化恢复后，仍读不到 `rt/lowstate`。  
关机重启真机后，`tv` 环境里的最小订阅测试恢复正常，说明真机侧也可能进入异常状态。

#### 问题 3：`eno1` 同时绑定多个网段 IP，导致 DDS/RPC 选错源地址

现象：

- `ping 192.168.123.161` / `ping 192.168.123.164` 正常
- multicast 路由已修正到 `eno1`
- 但 `g1_rpc_probe.py --network-interface eno1` 仍然全部报 `3102 send request error`
- `eval_g1.py` 初始化时持续打印：

```text
[G1_23_ArmController] Waiting to subscribe dds...
```

当时 `eno1` 同时有两个 IPv4 地址：

```text
192.168.0.99/24
192.168.123.99/24
```

Unitree DDS/RPC 虽然指定了 `networkInterface=eno1`，但在同一网卡多个 IP 的情况下可能选到非机器人网段的源地址，导致服务发现和请求失败。

临时修复方式是在电脑端执行：

```bash
sudo ip addr del 192.168.0.99/24 dev eno1
sudo ip route replace 224.0.0.0/4 dev eno1
```

修复后，在 `tv` 环境中执行：

```bash
PYTHONPATH=/home/igs/Desktop/project/vla/unitree_lerobot \
python unitree_lerobot/eval_robot/g1_rpc_probe.py --network-interface eno1
```

已确认恢复：

- `motion_switcher get_server_api_version code=0`
- `motion_switcher check_mode code=0 result={'form': '0', 'name': 'ai'}`
- `arm get_action_list code=0`
- `sport get_server_api_version code=0`
- `sport get_fsm_id code=0 data={"data":500}`
- `sport get_fsm_mode code=0 data={"data":0}`

说明这类 `3102` 不是模型或评估脚本问题，而是电脑端 `eno1` 的 IP/组播路由配置导致 DDS/RPC 无法正常发现服务。

如需恢复被删除的地址：

```bash
sudo ip addr add 192.168.0.99/24 dev eno1
```

### 7.2 当前确认无误的事实

在 `tv` 环境里：

- 清掉 DDS/ROS 环境变量后
- 使用 `networkInterface=eno1`
- 最小 `rt/lowstate` 订阅测试成功
- 已读到：
  - `mode_machine = 4`
- 如果 `g1_rpc_probe.py` 持续报 `3102`，需要确认 `eno1` 是否只保留机器人网段 IP，并确认 `224.0.0.0/4` multicast 路由走 `eno1`

### 7.3 当前仍存在的问题

在 `unitree_lerobot` 环境里：

- 同样清理环境变量
- 同样使用 `eno1`
- 同样的最小 `rt/lowstate` subscriber 测试
- 仍会在 `Topic` 初始化时报：

```text
[DDS_RETCODE_PRECONDITION_NOT_MET]
Occurred upon initialisation of a cyclonedds.topic.Topic
```

这说明：

- 问题不在 `eval_g1.py` 业务逻辑
- 问题在 `unitree_lerobot` 这个 conda 环境的 DDS 运行时栈

### 7.4 当前建议

不要继续在现有 `unitree_lerobot` 环境里硬修 DDS。  
更合理的路线是：

- 基于 `tv` 新建一个干净的 `vla_eval` 环境
- 保留 `tv` 的 DDS 可用性
- 只额外安装 `pi0.5` 推理所需依赖


## 8. 文档与脚本清单

### 新增文档

- [docs/pi05_lora_plan_zh.md](/home/igs/Desktop/project/vla/unitree_lerobot/docs/pi05_lora_plan_zh.md)
- [docs/g1_23_pi05_project_adaptation_zh.md](/home/igs/Desktop/project/vla/unitree_lerobot/docs/g1_23_pi05_project_adaptation_zh.md)

### 新增脚本

- [scripts/train_pi05_lora_g1_23_rag_reach.sh](/home/igs/Desktop/project/vla/unitree_lerobot/scripts/train_pi05_lora_g1_23_rag_reach.sh)
- [scripts/validate_g1_23_lerobot_alignment.py](/home/igs/Desktop/project/vla/unitree_lerobot/scripts/validate_g1_23_lerobot_alignment.py)


## 9. 下一步

下一步推荐动作：

1. 新建 `vla_eval` conda 环境
2. 以 `tv` 环境为参考安装 DDS 可用依赖
3. 补齐 `pi0.5` 推理依赖
4. 在 `vla_eval` 中重新跑：
   - 最小 `rt/lowstate` 订阅测试
   - `eval_g1.py --send_real_robot=false`
5. dry-run 通过后，再切到 `--send_real_robot=true`
