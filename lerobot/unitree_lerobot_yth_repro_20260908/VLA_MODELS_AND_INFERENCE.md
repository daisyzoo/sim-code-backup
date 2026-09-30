# VLA 场景、模型与推理命令记录

最后更新：2026-09-07

这份文档只记录目前仍有实际使用价值、且路径已经确认存在的版本，不穷举更早期的 20 Hz、LoRA 等实验 checkpoint。

## 1. 拿杯子

### 当前推荐模型：PI0.5 Expert Only，6 维，15 Hz，FP32

- 训练数据批次：0804-0805、0813、0817
- 模型路径：

```text
/media/igs/EAGET/syh/vla/outputs/iwork_train_pi05_expert_only_pick_cup_6d_15hz_0804_0805_0813_0817_fp32/pretrained_model
```

- 当前两个推理脚本默认都指向这个模型，无需手工填写 `POLICY_PATH`。
- 工程目录：

```text
/home/igs/Desktop/project/vla/unitree_lerobot_yth
```

#### 普通交互模式

```bash
cd /home/igs/Desktop/project/vla/unitree_lerobot_yth
bash scripts/eval_pi05_expert_only_pick_up_6d_15hz_rtc_interactive.sh
```

#### 持久 RTC 调试模式

模型只加载一次，可以在交互菜单中执行 `show`、切换 mode 和反复运行。

```bash
cd /home/igs/Desktop/project/vla/unitree_lerobot_yth
bash scripts/eval_pi05_expert_only_pick_up_6d_15hz_persistent_debug.sh
```

#### 临时切换到其他拿杯子模型

```bash
cd /home/igs/Desktop/project/vla/unitree_lerobot_yth
POLICY_PATH=/目标模型目录/pretrained_model \
bash scripts/eval_pi05_expert_only_pick_up_6d_15hz_rtc_interactive.sh
```

持久调试脚本同样支持：

```bash
POLICY_PATH=/目标模型目录/pretrained_model \
bash scripts/eval_pi05_expert_only_pick_up_6d_15hz_persistent_debug.sh
```

### 其他已保留的主要拿杯子模型

| 版本 | 模型路径 | 备注 |
| --- | --- | --- |
| PI0.5 Expert Only，0804-0805，FP32 | `/media/igs/EAGET/syh/vla/outputs/iwork_train_pi05_expert_only_pick_cup_6d_15hz_0804_0805_fp32/pretrained_model` | 早期两日数据版本 |
| PI0.5 Expert Only，0804-0805，BF16 | `/media/igs/EAGET/syh/vla/outputs/iwork_train_pi05_expert_only_pick_cup_6d_15hz_0804_0805_bp16/pretrained_model` | BF16 对照版本 |
| PI0.5 Expert Only，clean data | `/media/igs/EAGET/syh/vla/outputs/iwork_train_pi05_expert_only_pick_cup_6d_15hz_clean_data/pretrained_model` | 清洗数据版本 |
| PI0.5 Expert Only，2026-08-06 run | `/media/igs/EAGET/syh/vla/outputs/pi05_expert_only_pick_up_6d_15hz_0804_0805_20260806_151401/checkpoints/last/pretrained_model` | `last` 当前指向 `090000` |

以上模型可通过设置 `POLICY_PATH` 使用同一套 6 维、15 Hz 推理脚本。

## 2. 分拣快递

任务定义：黑色包装袋由左手压住并推向左侧；盒子由右手压住并推向右侧。动作维度为 11 维：左臂 5 + 右臂 5 + 腰部 1，频率为 15 Hz。

### 2026-09-07 实测：本次三模型单任务分拣训练

**用户本次结论：PI0.5 效果比 InternVLA 差；FastWAM 待测试。** 这是本批权重的定性真机反馈，尚未统计成功率；不能将待测试的 FastWAM 纳入效果排名，也不与下文历史版本混为一谈。

三个模型均来自 `run_20260905_095628` 串行训练队列，最终 checkpoint 为第 28,562 步；动作顺序为左臂 5 + 右臂 5 + 腰部 1，15 Hz。

| 模型 | 训练启动时间（run 名） | 本次反馈 |
| --- | --- | --- |
| PI0.5 | 2026-09-05 09:56:28 | 已测试，效果比本批 InternVLA 差 |
| InternVLA | 2026-09-06 01:01:17 | 已测试，修复关节映射后，效果优于本批 PI0.5 |
| FastWAM | 2026-09-05 18:24:45 | 待测试，暂无真机效果结论 |

本批模型权重：

```text
PI0.5:
/skydata/yth/inference/weights/package_sorting_queue_20260905_095628/package_sorting_pi05_8gpu_20260905_095628/checkpoints/028562/pretrained_model

InternVLA:
/skydata/yth/inference/weights/package_sorting_queue_20260905_095628/package_sorting_internvla_8gpu_20260906_010117/checkpoints/028562/pretrained_model

FastWAM:
/skydata/yth/inference/weights/package_sorting_queue_20260905_095628/package_sorting_fastwam_8gpu_20260905_182445/checkpoints/weights/step_028562.pt
```

推理入口位于 `/skydata/yth/inference/`，模型路径和环境由 `paths.json` 管理；本次单任务使用 `tasks.json` 中的 `sorting`，不是多任务模型的 `multi_sorting`。

```bash
cd /skydata/yth/inference
# 分别启动，一次只测试一个模型：
CUDA_VISIBLE_DEVICES=0 bash run.sh pi05 --task sorting --run
CUDA_VISIBLE_DEVICES=0 bash run.sh internvla --task sorting --run
```

FastWAM 待补齐资源并验证后，再使用同目录的 `bash run.sh fastwam --task sorting --run`；不能将入口存在视为已通过加载或真机测试。

本批单任务训练／推理 prompt：

```text
Sort the package on the table by type. If there is no package on the table, keep both arms still and wait. If it is a black bag, press and hold the bag down with the left hand, then push it to the left sorting area. If it is a box, press and hold the box down with the right hand, then push it to the right sorting area.
```

推理入口保留 RTC、滤波、平滑、速度和加速度限制；当前 RTC 默认为 `horizon=10 / queue=10 / max-actions-during-inference=10`，每次实际测试设置以运行日志为准。默认禁止真机发送，确认后才开启。

已修复问题：InternVLA 历史后端假设右臂在前，导致本批左臂在前的数据在输入／输出时被错误交换，出现两手翻转。新入口已修复普通及 RTC 路径映射，并通过离线检查；用户随后确认“这次可以了”。修复前的异常不作为本批模型训练效果结论。

### 历史推荐（2026-09-02）：FastWAM，非 IDM，0824+0828，step 20000

- 当前结论：在已经完成的离线图像/状态反事实分析中，这一版对物体图像的响应最好，因此当前优先测试它。
- “非 IDM”指训练模型结构，不等于推理时必须开启或关闭 RTC。
- Run 目录：

```text
/skydata/syh/FastWAM/runs/pick_cup_sorting_first_frame_0824_0828_1cam224x288_1e-4/2026-08-31_17-41-07
```

- 模型权重：

```text
/skydata/syh/FastWAM/runs/pick_cup_sorting_first_frame_0824_0828_1cam224x288_1e-4/2026-08-31_17-41-07/checkpoints/weights/step_020000.pt
```

- 训练配置：

```text
/skydata/syh/FastWAM/runs/pick_cup_sorting_first_frame_0824_0828_1cam224x288_1e-4/2026-08-31_17-41-07/config.yaml
```

- 归一化统计：

```text
/skydata/syh/FastWAM/runs/pick_cup_sorting_first_frame_0824_0828_1cam224x288_1e-4/2026-08-31_17-41-07/dataset_stats.json
```

#### 持久调试/真机推理入口

下面的启动命令默认 `SEND_REAL_ROBOT=false`，加载完成后不会立刻向真机发送动作：

```bash
cd /skydata/syh/FastWAM
PICK_CUP_SORTING_RUN_DIR=/skydata/syh/FastWAM/runs/pick_cup_sorting_first_frame_0824_0828_1cam224x288_1e-4/2026-08-31_17-41-07 \
CHECKPOINT=/skydata/syh/FastWAM/runs/pick_cup_sorting_first_frame_0824_0828_1cam224x288_1e-4/2026-08-31_17-41-07/checkpoints/weights/step_020000.pt \
TRAIN_CONFIG=/skydata/syh/FastWAM/runs/pick_cup_sorting_first_frame_0824_0828_1cam224x288_1e-4/2026-08-31_17-41-07/config.yaml \
DATASET_STATS=/skydata/syh/FastWAM/runs/pick_cup_sorting_first_frame_0824_0828_1cam224x288_1e-4/2026-08-31_17-41-07/dataset_stats.json \
bash scripts/debug_fastwam_g1_23_11d_rtc.sh
```

进入 `fastwam-rtc>` 菜单后，首次真机验证建议：

```text
show
mode async_no_guidance
set send_real_robot true
run
```

需要验证 RTC guidance 时再切换：

```text
mode rtc_guided
show
run
```

每次 `run` 前仍有初始位姿和首个动作 chunk 的人工确认。执行中按 `q` 停止当前 run，但模型进程不会退出。

### FastWAM 早期分拣模型：非 IDM，仅 0824，step 10000

- 模型权重：

```text
/skydata/syh/FastWAM/runs/pick_cup_sorting_first_frame_1cam224x288_1e-4/2026-08-27_17-10-45/checkpoints/weights/step_010000.pt
```

- 这一版正是 11 维 FastWAM 调试脚本的历史默认值，用作对照：

```bash
cd /skydata/syh/FastWAM
bash scripts/debug_fastwam_g1_23_11d_rtc.sh
```

### PI0.5 分拣模型：0824+0828 合并训练，step 20000

- 模型路径：

```text
/skydata/model/sorting_11d_merged_20260828_103515/checkpoints/020000/pretrained_model
```

- 普通交互模式：

```bash
cd /home/igs/Desktop/project/vla/unitree_lerobot_yth
POLICY_PATH=/skydata/model/sorting_11d_merged_20260828_103515/checkpoints/020000/pretrained_model \
bash scripts/eval_pi05_expert_only_sorting_11d_15hz_rtc_interactive.sh
```

- 持久 RTC 调试模式：

```bash
cd /home/igs/Desktop/project/vla/unitree_lerobot_yth
POLICY_PATH=/skydata/model/sorting_11d_merged_20260828_103515/checkpoints/020000/pretrained_model \
bash scripts/eval_pi05_expert_only_sorting_11d_15hz_persistent_debug.sh
```

- 已知现象：训练样本/强动作窗口复现正确，但在真实快照的图像与机器人状态冲突时，仍明显依赖 state，左右手决策不够稳健。

### PI0.5 分拣模型：早期 sorting_0828 版本

- 模型路径：

```text
/skydata/model/sorting_0828/pretrained_model
```

- 当前 PI0.5 分拣脚本的默认路径仍是这一版；直接运行即可加载它：

```bash
cd /home/igs/Desktop/project/vla/unitree_lerobot_yth
bash scripts/eval_pi05_expert_only_sorting_11d_15hz_rtc_interactive.sh
```

- 为避免以后误用，测试新版 PI0.5 时应显式设置 `POLICY_PATH`，不要依赖这个历史默认值。

## 3. PI0.5 多任务模型：抱箱子、分拣、倒水、拿杯

### 模型与训练方式

- 实测记录日期：2026-09-07；结论来自用户本次真机测试反馈。
- 训练只开启 action expert（Expert Only），VLM 冻结，不使用 LoRA。
- FP32，11 维：左臂 5 + 右臂 5 + 腰部 1；执行频率 15 Hz；action chunk 为 50 步。
- 本次测试 checkpoint：第 10,000 步。训练 run 名为 `multitask_11d_20260902_014815`，来自包内 `train_config.json`；本地目录中的 `20260906` 不作为训练启动日期。
- 权重目录：

```text
/skydata/yth/inference/weights/multi_task_20260906/extracted/010000/pretrained_model
```

- 同目录保留 `config.json`、`train_config.json`、前后处理器配置及归一化参数；推理使用该 checkpoint 自带的统计，不使用单任务分拣模型的统计。
- 入口配置：`/skydata/yth/inference/paths.json` 的 `pi05_multitask`；任务配置：`/skydata/yth/inference/tasks.json`。原 `pi05` 单任务入口保持独立。

### 推理运行脚本与任务切换

```bash
cd /skydata/yth/inference
CUDA_VISIBLE_DEVICES=0 bash run.sh pi05_multitask --task multi_box --run
```

`CUDA_VISIBLE_DEVICES=0` 选择第一张卡，第二张改为 `1`。模型常驻，在停止状态通过菜单切换任务，不必重新加载权重。

| 任务 | 菜单命令 | 训练提示词（原文） | 本次实测效果 |
| --- | --- | --- | --- |
| 抱箱子／搬箱子 | `task multi_box` | `pick_up_and_move_the_box` | 效果不错 |
| 分拣 | `task multi_sorting` | `Sort packages: place black bags on the left and boxes on the right.` | 效果一般 |
| 倒水 | `task multi_water` | `pour_the_water_out_of_the_cup` | 效果一般 |
| 拿杯 | `task multi_cup` | `pick_up_the_cup_with_the_right_hand` | 效果一般 |

提示词更新（2026-09-07）：上表保留此前测试使用的提示词及其反馈，不追溯改写测试条件。
随后用户根据云端 unified 数据，要求本地多任务入口改用自然语言版本：
`multi_box` → `Pick up and move the box.`；
`multi_water` → `Pour the water out of the cup.`；
`multi_cup` → `Pick up the cup with the right hand.`；分拣提示词不变。
新提示词下的效果待复测；该变更不代表已核实旧 PI0.5 checkpoint 训练时也使用这些自然语言文本。

菜单中 `tasks` 查看任务、`show` 核对配置、`run` 开始本轮；执行中按 `q` 停止并返回菜单，`quit` 退出模型。初次启动默认禁止真机发送；确认准备位姿与动作安全后，才使用 `set send_real_robot true` 开启发送。

RTC 默认 `horizon=10`、`queue=10`、`max-actions-during-inference=10`；保留滤波、chunk 衔接平滑及速度／加速度限制。guidance 可在菜单切换，默认关闭；这里记录的是入口默认值，不将其视为所有实测轮次的最终设置。

### 本次结论与测试限制

**本次用户结论：抱箱子效果不错，其余三个任务（分拣、倒水、拿杯）效果都一般。** 这是定性实测反馈，尚无量化成功率，不据此直接替换此前的单任务推荐模型。

倒水测试时发现初始姿态不符合任务要求：双手抬起，而预期右手在下面。已查明当前菜单仅切换 prompt，准备姿态仍来自分拣数据第 0 个 episode，而非对应多任务轨迹。此问题在本次记录时尚未修复；倒水结果包含初始位姿不匹配的影响，不能全部归因于训练效果。后续应为每个任务配置并核对独立的初始位姿，再复测。

## 3.1 多任务真机测试更新：InternVLA no_WAN 与 PI05 VLM LoRA（2026-09-08）

以下为用户本次真机测试反馈，区别于上一节 PI05 Expert Only 第10,000步的旧实验。

### InternVLA 多任务 no_WAN · 第31,875步

- 训练运行：`queue_20260907_113309/no_wan`；203,994帧、679 episodes，全局batch64、约10轮，无验证集。
- 训练配置为视觉/语言LoRA rank16 + action expert微调，关闭WAN视频loss；仍有VQA/FAST训练目标，并非只有action loss。
- 权重：`/skydata/yth/inference/weights/internvla_multitask_20260907_113309_no_wan/no_wan/checkpoints/031875/pretrained_model`。
- 使用同目录的 `inference_stats.json`，来自该checkpoint自身统计，不复用单分拣统计。
- 配置键：`internvla_multitask_no_wan_20260907`。

```bash
cd /skydata/yth/inference
CUDA_VISIBLE_DEVICES=0 bash run.sh internvla_multitask_no_wan_20260907 --task multi_box --run
```

**本次反馈：无法完成抱箱子任务；倒水还可以；分拣和拿杯效果一般。**
未提供各任务试验次数或量化成功率。训练loss下降不等于真机任务成功；
WAN smoke首次前向精度断言失败，未产生可比较的WAN训练结果，本条仅指no_WAN。

### PI05 多任务 VLM LoRA + action expert · 第20,000步

- 训练运行：`multitask_11d_vlm_lora_expert_full_20260907_085603`。
- 完整FP32 checkpoint；语言模型LoRA rank16/alpha16，action expert不使用LoRA、全参微调；与旧Expert Only模型区分。
- 11维状态/动作、15Hz、chunk50；checkpoint配置启用action padding mask。
- 权重：`/skydata/yth/inference/weights/pi05_multitask_vlm_lora_20260907_085603/020000/pretrained_model`。
- 使用checkpoint自带的前后处理器和归一化文件；原ZIP及云端原JSON配置保留。
- 配置键：`pi05_multitask_lora_20260907`。

```bash
cd /skydata/yth/inference
CUDA_VISIBLE_DEVICES=0 bash run.sh pi05_multitask_lora_20260907 --task multi_box --run
```

**本次反馈：效果非常好，四个任务都能完成，用户报告成功率95%以上。**
成功率按用户反馈记录；尚未提供每个任务的成功/尝试次数及统计口径，
不将其展开为“四个任务各自都达到95%以上”，也不作为独立复核后的评测数据。

### 两个模型的任务参数与效果对照

上述命令中的 `--task` 可替换为下表任务键；常驻菜单停止状态下用 `task <任务键>` 切换。

| 任务 | 任务键 | 当前提示词（原文） | InternVLA no_WAN | PI05 VLM LoRA + Expert |
| --- | --- | --- | --- | --- |
| 抱箱子／搬箱子 | `multi_box` | `Pick up and move the box.` | 无法完成 | 能完成，效果非常好 |
| 分拣 | `multi_sorting` | `Sort packages: place black bags on the left and boxes on the right.` | 一般 | 能完成，效果非常好 |
| 倒水 | `multi_water` | `Pour the water out of the cup.` | 还可以 | 能完成，效果非常好 |
| 拿杯 | `multi_cup` | `Pick up the cup with the right hand.` | 一般 | 能完成，效果非常好 |

配置文件为 `/skydata/yth/inference/paths.json`，任务文件为 `/skydata/yth/inference/tasks.json`。
基于本次用户反馈，四任务后续验证优先使用本节PI05 VLM LoRA版本。
本次具体RTC调参、初始姿态和逐次评测记录未提供，不推定所有实验条件完全一致，
也不将差异仅归因于模型架构。终端不会自动采用网页保存的初始姿态；
切换任务后仍需现场核对准备姿态与物体场景，避免误用分拣初始姿态。

## 4. 快速选择

| 场景 | 当前优先模型 | 推理入口 |
| --- | --- | --- |
| 四任务：抱箱、分拣、倒水、拿杯 | PI05 VLM LoRA + Expert，20260907_085603，step20000（2026-09-08用户反馈） | `bash /skydata/yth/inference/run.sh pi05_multitask_lora_20260907 --task multi_box --run` |
| 拿杯子 | PI0.5 Expert Only，0804-0805+0813+0817，FP32 | `scripts/eval_pi05_expert_only_pick_up_6d_15hz_rtc_interactive.sh` |
| 分拣快递 | FastWAM 非 IDM，0824+0828，step 20000 | `scripts/debug_fastwam_g1_23_11d_rtc.sh`，启动时覆盖 run、checkpoint 和 stats 路径 |

## 5. 更新约定

后续每训练一个值得保留的新模型，至少补充以下信息：

1. 场景和动作维度/频率。
2. 模型类型、训练数据范围和训练日期。
3. 完整 checkpoint 路径。
4. 对应的配置和归一化统计路径。
5. 可直接复制执行的推理命令。
6. 真机或离线验证结论，以及是否替代当前推荐版本。

### 更新日志

- 2026-09-08：记录InternVLA多任务no_WAN step31875与PI05多任务VLM LoRA + Expert step20000的推理命令和真机反馈；前者抱箱失败、倒水尚可、其余一般，后者四任务均能完成、用户报告成功率95%以上（未提供逐任务统计）。
- 2026-09-07：补充三模型单任务分拣第 28,562 步权重与推理入口；用户反馈 PI0.5 效果比 InternVLA 差，FastWAM 待测试；注明 InternVLA 左右臂映射修复与历史 FastWAM 版本的区别。
- 2026-09-07：补充 PI0.5 Expert Only 四任务模型第 10,000 步权重、常驻推理入口、四个原样 prompt 和用户真机反馈：抱箱子效果不错，其余三项一般；记录倒水初始位姿误用分拣配置的已知限制。
- 2026-09-02：建立文档；整理拿杯子 PI0.5 版本，以及分拣 PI0.5/FastWAM 版本；将 FastWAM 非 IDM 0824+0828 step 20000 标为当前推荐。
