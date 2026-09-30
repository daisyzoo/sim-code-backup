# 工程提交变更日志

本文档按 Git 实际提交日期倒序记录 `yth/dev` 分支的重要版本节点，便于快速了解每次提交解决了什么问题、影响了哪些功能，以及当时完成了哪些验证。

## 维护规则

以后创建功能提交时，在本文档顶部追加一个日期节点，至少包含：

- Git 实际提交日期、提交号和提交主题；
- 本次提交的目标；
- 用户可感知的功能变化；
- 关键配置、脚本和源码文件；
- 已执行的测试，以及尚未验证的部分；
- 未纳入提交的模型、数据、缓存或构建产物。

如果提交主题中使用了功能日期，但实际 Git 提交日期不同，应同时记录两者。

---

## 2026-09-01：支持 Episode 多阶段 Subtask 标注与 LeRobot 转换

- Commit：本条记录随对应功能提交创建，提交号以 `git log` 为准。
- 主题：`feat: 支持多阶段 Subtask 标注与转换`

### 主要目标

让 Unitree 原始数据在裁剪 episode 的同时，能够通过 YAML 配置和数字快捷键标注多个连续 subtask，并在后续 Unitree→LeRobot 转换时自动生成 InternVLA-A1.5 使用的详细任务监督文件。

### 功能变化

1. Data Editor Subtask 标注

   - 支持从界面选择 YAML，为数字键 `1`～`9` 配置 `action_text`、`language_memory` 和时间轴颜色。
   - 开启标注模式后，按 `Q` 设置标注起点，按数字键保存“起点到当前帧”的阶段，并自动把下一帧设为新起点；按 `E` 仍只设置 episode 裁剪终点。
   - 时间轴增加彩色 Subtask 轨道和数字标签，并支持撤销最后一段、清空当前 episode 标注。
   - 标注以左闭右开区间写入原始 `data.json`，采用同目录临时文件原子替换，避免写入中断损坏数据。
   - 导出或原地裁剪 episode 时，已有阶段会随保留帧自动拆分、重编号和映射。

2. LeRobot 标注转换

   - Unitree→LeRobot 转换完成后，根据最终 episode 排序生成 `meta/episodes_detailed_task.jsonl`。
   - 输出保留训练所需的 `start_frame`、`end_frame`、`action_text` 和 `language_memory`，去除编辑器专用的数字键和颜色字段。
   - 转换前检查区间边界、空文本、帧数越界和区间重叠；未标注 episode 使用空 `action_config`。

3. 配置、依赖和文档

   - 增加可直接复制修改的 Subtask YAML 示例。
   - 增加中文操作说明，记录 `Q → 数字键 → E` 的交互方式及转换后的文件位置。
   - 项目依赖增加 `PyYAML>=6.0`。

### 关键文件

- `data_editor/data_editor_CN.py`
- `data_editor/subtask_config.example.yaml`
- `data_editor/SUBTASK_ANNOTATION_CN.md`
- `unitree_lerobot/utils/convert_unitree_json_to_lerobot.py`
- `data_editor/test_data_editor_export.py`
- `unitree_lerobot/utils/tests/test_convert_subtask_annotations.py`

### 验证情况

- 相关 Python 文件通过 `py_compile`。
- Git 差异通过 `git diff --check`。
- 15 项自动化测试通过，覆盖 YAML 解析、快捷键区间、重叠拒绝、裁剪/导出重映射和最终 JSONL episode 编号。
- Data Editor 界面完成无头渲染检查，尚未使用一套真实采集数据完整人工标注并训练 InternVLA-A1.5。

### 未纳入提交

- `.idea/`、`outputs/`、模型与环境打包目录、第三方构建目录以及 notebook 生成内容。

---

## 2026-09-01：完善双臂分拣、完整 RTC Jacobian 与离线归因分析

- Commit：本条记录随对应功能提交创建，提交号以 `git log` 为准。
- 主题：`feat: 完善双臂分拣 RTC 与离线归因分析`

### 主要目标

将 15 Hz 拿杯子数据流程扩展为多目录合并转换，为 11 维双臂分拣任务补齐安全的真机推理入口，并把 PI0.5 RTC 从 identity-Jacobian 近似扩展为可配置的真实 autograd Jacobian/VJP 引导。同时增加离线工具，用训练数据与真机快照检查模型是否利用图像，或依赖左右臂状态捷径。

### 功能变化

1. 完整 RTC Jacobian/VJP

   - `PI05RTCConfig` 增加 `use_autograd_jacobian`，默认启用。
   - 完整模式在调用 denoiser 前让当前动作 latent 参与 autograd，通过 `x_t -> v_t -> x1_t` 计算 VJP；只计算输入梯度，不更新模型参数。
   - 关闭该配置时保留原 identity-Jacobian 近似，便于消融、性能对比和兼容旧行为。
   - 交互式、MCP Controlled 和 Persistent Debug 入口均可配置并记录该开关。

2. 15 Hz 多目录数据合并

   - 数据准备脚本支持通过冒号分隔的 `SOURCE_ROOTS` 输入多个原始目录。
   - 多个目录统一校验为 15 Hz，汇总 episode 数量并生成一个 preparation spec，最后转换成一个连续的 LeRobot 数据集。
   - 保留原 `SOURCE_ROOT` 单目录调用方式。
   - 15 Hz 拿杯子交互推理默认数据集更新为合并后的 0804/0805/0813/0817 版本。

3. 11 维双臂分拣真机推理

   - 新增 15 Hz 双臂分拣交互推理脚本，动作顺序固定为 `left_arm[0:5] + right_arm[5:10] + waist[10]`。
   - 启动前检查数据集 state/action 均为 11 维、关节名顺序正确且频率为 15 Hz，防止错误维度直接下发真机。
   - 支持 RTC、完整 Jacobian、独立控制进程、动作平滑、速度/加速度限制、运行期间按 `q` 停止。
   - Persistent Debug 支持机器人到达预备位置后再次按 `s` 确认，避免到位后立即开始模型推理。

4. PI0.5 数据与模型归因分析

   - 增加训练集初始状态分支可预测性分析，检查左右任务是否能仅凭初始关节状态分类。
   - 增加固定扩散噪声的图像模糊、局部遮挡、状态原型替换和逐关节反事实测试。
   - 增加精确训练样本回放验证，用 ground-truth 动作确认左右维度和模型分支是否一致。

5. FastWAM 训练与真机快照分析

   - 增加 FastWAM 训练日志解析、训练/验证曲线和 checkpoint 指标汇总工具。
   - 复用两张已保存的盒子/黑袋真机快照，执行固定噪声的图像 × 机器人状态反事实推理。
   - 结果表明模型在正常起始状态附近能够利用图像区分左右任务；黑袋后期快照中的大幅右臂状态会触发较强右臂动作，但该动作仍可能是收回右臂，现有指标不能直接把它判定为错误抓取分支。

### 关键文件

- `unitree_lerobot/eval_robot/pi05_rtc_runtime.py`
- `unitree_lerobot/eval_robot/eval_g1_rtc.py`
- `unitree_lerobot/eval_robot/persistent_rtc_debug.py`
- `unitree_lerobot/eval_robot/tests/test_pi05_rtc_runtime.py`
- `scripts/prepare_g1_23_xr_pick_cup_6d_15hz_dataset.sh`
- `scripts/eval_pi05_expert_only_sorting_11d_15hz_rtc_interactive.sh`
- `scripts/eval_pi05_expert_only_sorting_11d_15hz_persistent_debug.sh`
- `scripts/analyze_sorting_state_shortcut.py`
- `scripts/analyze_pi05_sorting_snapshot_attribution.py`
- `scripts/validate_pi05_sorting_training_samples.py`
- `scripts/analyze_fastwam_sorting_live_snapshots.py`
- `scripts/report_fastwam_sorting_analysis.py`

### 验证情况

- 5 个相关 Shell 脚本通过 `bash -n`。
- 8 个相关 Python 文件通过 `py_compile`。
- PI0.5 RTC 14 项测试通过，包括完整 Jacobian/VJP、旧近似模式、动作队列、推理期间等待、超时、按键停止和快照保存。
- FastWAM `step_020000.pt` 在 GPU 上完成两张真机快照、5 种状态条件及 3 个随机种子的离线推理；模型热启动后单次动作推理约 0.78 秒。
- 本提交不包含新的双臂分拣真机动作验证。

### 未纳入提交

- `outputs/` 下约 732 MB 的真机日志、图像快照、分析图和 JSON 结果。
- LingBot/离线 CUDA 环境打包目录、第三方构建目录和 IDE 配置。
- 模型权重、训练数据、缓存及历史 notebook 生成报告。

---

## 2026-08-14：增加真机动作平滑与关节限速

- Commit：`c4632b0fa7cff5e3c64666dd6506b14d5fac4011`
- 主题：`feat: 增加真机动作平滑与关节限速`
- 规模：6 个文件，新增 383 行，删除 7 行。

### 功能变化

- 增加动作块边界混合与可选低通平滑，降低连续推理换块时的目标跳变。
- 增加逐关节速度和加速度限制，并将限制后的目标作为下一帧状态继续积分。
- 交互脚本和 Persistent Debug 支持调整平滑截止频率、混合帧数及安全限制。
- 新增动作平滑和关节限速单元测试。

---

## 2026-08-14：完善 PI0.5 RTC 真机调试与受控执行

- Commit：`a78d4344c15d0b551a05b83808aa866fddc2ead4`
- 主题：`feat: 完善 PI0.5 RTC 真机调试与受控执行`
- 规模：21 个文件，新增 1613 行，删除 66 行。

### 功能变化

- 增加模型常驻的 RTC 调试菜单，可运行、显示和修改配置而无需重复加载模型。
- 增加 RTC MCP Controlled 服务及启动脚本，支持远程开始、停止和查询执行状态。
- 增加基于训练终点关节分布的自动终止检测，并保留墙钟超时和人工停止。
- 增加逐帧 RTC 执行日志、推理图像快照和图像客户端时间信息。
- 完善异步动作块的真实消费帧对齐、等待策略、最大运行时间和外部停止逻辑。

---

## 2026-08-11：完善 PI0.5 数据、RTC 推理与独立控制进程

- Commit：`efb5f7b345b726d426b1896c23b13192e9649b18`
- 主题：`feat: 20260811 完善 PI0.5 数据、RTC 推理与独立控制进程`
- 规模：20 个文件，新增 3880 行，删除 90 行。

### 主要目标

完善 15 Hz 拿杯子数据和 Expert-only 训练流程，为 PI0.5 增加可选 RTC 连续推理能力，并将 G1-23 高频控制从 CUDA 推理进程中隔离。

### 功能变化

1. PI0.5 Expert-only 训练

   - `train_expert_only=true` 时冻结 PaliGemma/VLM 主体。
   - 只训练 Action Expert、动作输入输出投影和时间编码模块。
   - 增加 15 Hz 拿杯子训练脚本和 G1-23 XR 数据准备脚本。
   - 数据集配置增加 `tolerance_s`，并传递给普通和流式 LeRobot 数据集，用于控制视频帧与数据行的时间戳匹配容差。

2. RTC 连续推理

   - 新增异步动作块推理、动作队列替换、延迟估计和 Prefix 引导。
   - 支持 `execution_horizon`、`queue_threshold`、`max_actions_during_inference`、`latency_window`、推理超时和 Prefix 权重调度。
   - 算力不足时可执行有限数量的旧动作，然后保持最后目标等待新动作块。
   - 支持保存每次推理使用的图像和机器人状态快照。
   - 当前实现是与所参考 LeRobot 实现对齐的简化 RTC，不是论文中的完整 Jacobian/VJP 引导版本。

3. 真机交互和终止逻辑

   - 新增单任务交互模式：菜单按 `s` 开始，运行期间按 `q` 停止当前任务，随后返回菜单。
   - 支持连续运行到人工停止，不再强制使用固定动作帧数结束任务。
   - 保留最长墙钟时间作为可选安全终止条件。
   - Episode 结束时重置 RTC 队列，并完善回初始姿态和运动控制权交还流程。

4. G1-23 独立控制进程

   - DDS 初始化、低状态订阅和 250 Hz 关节命令发布移入 `spawn` 子进程。
   - 主推理进程和控制进程通过共享内存交换动作目标、关节位置、速度和腰部状态。
   - 初始化、运动控制权交接、回零等低频阻塞操作通过同步进程间调用执行。
   - `ARM_CONTROLLER_PROCESS=true` 使用独立进程，设置为 `false` 可回退旧的同进程线程实现。

5. 性能与动作连续性诊断

   - 增加模型输入、预处理、Prefix、去噪、后处理和 CPU 传输分段耗时。
   - 增加 `INFERENCE_RESOURCE_DIAG`、`CHUNK_REFILL_DIAG` 和 `JITTER_DIAG`。
   - 记录控制循环实际频率、平均/最大耗时、4 ms 超时次数、动作块边界跳变和关节跟踪误差。
   - Dry-run 可以直接读取本地数据集图像和状态，不依赖实时相机或真实控制器。

6. 数据编辑器

   - 支持输入起止帧精确选择区间。
   - 增加逐帧、快速跳帧和设置区间边界的键盘快捷键。
   - 支持将所选区间导出为新的 Episode，并同步重建 JSON 索引及复制彩色、深度和音频文件。
   - 增加 G1-23 右手掌 EE 位姿投影，以及当前帧前后 3 秒的手掌轨迹显示。

7. 文档和脚本

   - 新增 15 Hz 拿杯子 RTC 真机脚本。
   - 新增 20 Hz 拿杯子/提包双任务 RTC 真机脚本。
   - 新增 RTC 后续优化文档，记录自动成功判断、任务终止和论文完整 RTC 等待办方向。

### 关键文件

- `unitree_lerobot/eval_robot/pi05_rtc_runtime.py`
- `unitree_lerobot/eval_robot/eval_g1_rtc.py`
- `unitree_lerobot/eval_robot/eval_g1.py`
- `unitree_lerobot/eval_robot/robot_control/g1_23_process_controller.py`
- `unitree_lerobot/eval_robot/robot_control/robot_arm.py`
- `unitree_lerobot/lerobot/src/lerobot/policies/pi05/modeling_pi05.py`
- `data_editor/data_editor_CN.py`
- `scripts/eval_pi05_expert_only_pick_up_6d_15hz_rtc_interactive.sh`
- `scripts/train_pi05_expert_only_pick_up_6d_15hz_0804_0805.sh`
- `docs/pi05_rtc_followup_zh.md`

### 验证情况

- 数据编辑器：7 项测试通过。
- RTC：12 项测试通过。
- G1-23 独立控制进程：Dummy 子进程共享目标、共享状态和退出测试通过。
- 相关 Python 文件编译检查通过。
- 4 个新增 Shell 脚本通过 `bash -n` 检查。
- 独立控制进程在该提交前未进行真实 DDS/真机验证。

### 未纳入提交

模型推理快照、环境打包目录、第三方构建目录、notebook 报告和其他生成产物未纳入 Git。

---

## 2026-08-03：实现拿杯子/提包双任务训练和交互推理

- Commit：`8fed01d2ad381ae0da9bc3915d698006d4f35ea4`
- Tag：`20260730-dual-task-training-inference`
- 主题：`feat: 20260730 实现双任务训练和推理`
- 功能命名日期：2026-07-30。
- Git 实际提交日期：2026-08-03。
- 规模：5 个文件，新增 201 行，删除 28 行。

### 功能变化

- 新增拿杯子/提包双任务交互推理脚本。
- 菜单按 `s` 选择拿杯子，按 `r` 选择提包，按 `q` 退出。
- 每个 Episode 根据所选任务动态切换语言指令，结束后回到任务菜单。
- 增加 `interactive_task_selection`、`task_s_text`、`task_r_text` 和 `tokenizer_name_override` 配置。
- 支持用本地 Tokenizer 覆盖 checkpoint 中保存的旧路径，适配模型迁移后的目录变化。
- 修复 PI0.5 推理中 Attention Mask、Prefix Embedding 和 Suffix Embedding 的 dtype 对齐问题，解决 `invalid dtype for bias - should match query's dtype`。
- 在 `PI05Config` 中保留 `train_expert_only` 字段，使 Expert-only 训练生成的 checkpoint 可以被当前推理代码解析；该节点尚未实现实际冻结逻辑。
- 异常日志由只打印错误字符串改为输出完整 traceback。

### 关键文件

- `scripts/eval_pi05_lora_g1_23_right_hand_cup_pick_and_lift_bag_multitask_6d_20hz_interactive.sh`
- `unitree_lerobot/eval_robot/eval_g1.py`
- `unitree_lerobot/eval_robot/utils/utils.py`
- `unitree_lerobot/lerobot/src/lerobot/policies/pi05/configuration_pi05.py`
- `unitree_lerobot/lerobot/src/lerobot/policies/pi05/modeling_pi05.py`

### 验证说明

本节点的历史提交没有单独保存自动化测试命令；功能随后通过双任务真机启动、任务选择和 dtype 报错修复过程继续验证。

---

## 2026-07-17：训练损失忽略 Action Padding

- Commit：`996c367c842411ea7e298d020818fb573918d982`
- 主题：`feat(pi05): mask padded actions in training loss`
- 规模：6 个文件，新增 343 行，删除 3 行。

### 功能变化

- 在 `PI05Config` 中增加 `mask_action_padding`，默认关闭，保持历史训练行为不变。
- 开启后要求 batch 中存在 `action_is_pad`。
- 训练损失、每维损失和每样本损失只统计真实动作帧，不再让补齐帧影响梯度和指标。
- 对有效动作数使用最小值保护，避免全 Padding 样本产生除零。
- 新增对应的训练、普通推理和 MCP Controlled 推理脚本。
- `.gitignore` 增加训练输出目录规则。

### 关键文件

- `unitree_lerobot/lerobot/src/lerobot/policies/pi05/configuration_pi05.py`
- `unitree_lerobot/lerobot/src/lerobot/policies/pi05/modeling_pi05.py`
- `scripts/train_pi05_lora_g1_23_right_hand_cup_pick_all_baseline_aug_6d_20hz_50k_mask_action_padding.sh`
- `scripts/eval_pi05_lora_g1_23_right_hand_cup_pick_all_baseline_aug_6d_20hz_50k_mask_action_padding.sh`
- `scripts/eval_pi05_lora_g1_23_right_hand_cup_pick_all_baseline_aug_6d_20hz_50k_mask_action_padding_mcp_controlled.sh`

### 验证说明

本节点的历史提交没有在 Git 中保存独立的自动化测试记录。

---

## 2026-07-15：建立可发布的代码基线

- Commit：`30d801ecc74f0d84c27581611913e1bd387b7974`
- 主题：`chore: publish code-only snapshot`
- 规模：775 个文件，新增 154785 行。

### 主要内容

- 建立当前仓库的首个代码基线和项目目录结构。
- 纳入 LeRobot 源码、测试和基础配置。
- 纳入 Unitree G1/G1-23 真机、仿真、图像服务、机器人控制和 MCP 相关实现。
- 纳入 G1、机械手等 URDF、网格和配置资源。
- 纳入数据转换、数据编辑、数据集准备、训练、评估和诊断脚本。
- 纳入 PI0.5 模型适配、LoRA 方案、G1-23 工程适配和模型结构等说明文档。
- 通过 `.gitignore`、`.gitattributes` 和 pre-commit 配置，形成只发布代码与必要资源的仓库快照。

### 说明

这是一次体量较大的初始化快照，主要作用是建立后续提交可以比较和回退的基准，而不是单一功能变更。
