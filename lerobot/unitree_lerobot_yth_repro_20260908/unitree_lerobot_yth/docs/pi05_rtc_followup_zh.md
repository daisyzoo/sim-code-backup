# PI0.5 RTC 后续完善与优化记录

更新时间：2026-08-03

## 1. 文档目的

本文记录当前 PI0.5 真机推理与 Real-Time Chunking（RTC）讨论中已经发现、但尚未全部解决的问题，作为后续开发和验证清单，避免在继续训练、迁移环境或修改推理流程时遗漏。

当前 RTC 代码采用独立入口，不修改原有非 RTC 推理脚本：

- `scripts/eval_pi05_lora_g1_23_right_hand_cup_pick_and_lift_bag_multitask_6d_20hz_rtc_interactive.sh`
- `unitree_lerobot/eval_robot/eval_g1_rtc.py`
- `unitree_lerobot/eval_robot/pi05_rtc_runtime.py`

## 2. 当前已确认的运行条件

当前模型和控制配置：

- 控制频率：20 Hz。
- Action chunk：50 帧，对应 2.5 秒有效动作。
- 去噪步数：默认 10 步。
- 本机完整推理一次约 2.5 秒，即推理期间对应约 50 个控制周期。
- 当前任务：拿杯子与提包双任务，动作维度为右臂 5 维加腰部 1 维。

在 20 Hz 下，2.5 秒推理延迟等于整个 50 帧 action chunk。仅调整 `RTC_QUEUE_THRESHOLD` 无法实现无停顿的连续 RTC，因为下一块动作生成时，上一块动作可能已经全部执行完。

## 3. 算力不足时的 RTC 验证方式

当前采用“有限执行，然后保持等待”的方式验证 RTC：

```bash
RTC_QUEUE_THRESHOLD=30
RTC_EXECUTION_HORIZON=10
RTC_MAX_ACTIONS_DURING_INFERENCE=10
RTC_LATENCY_WINDOW=100
```

预期时序：

```text
A0～A19：正常执行
A20：开始推理 B
A20～A29：继续执行 10 帧
推理尚未结束：保持 A29 的目标姿态
B 推理结束：丢弃 B0～B9，从 B10 开始执行
```

参数职责：

- `RTC_LATENCY_WINDOW` 保存近期推理耗时，用来估计墙钟时间对应的延迟帧数。
- `RTC_MAX_ACTIONS_DURING_INFERENCE` 限制推理期间机器人实际执行的旧动作帧数。
- RTC 实际使用的引导延迟为“耗时估计帧数”和“执行上限”中的较小值。
- `RTC_MAX_ACTIONS_DURING_INFERENCE` 不应大于 `RTC_EXECUTION_HORIZON`，否则实际执行的部分轨迹可能超出 RTC 的约束覆盖范围。

此方案可以验证新旧 action chunk 的衔接能力，但不能代表无停顿实时控制性能。预计每次重推理期间会出现约 2 秒的保持。

## 4. RTC 仍需完善的工程问题

### 4.1 真机保持行为验证

需要确认主推理线程阻塞等待时，底层机械臂发布线程是否持续发布最后一个目标，而不是停止发布或触发控制权异常。验证内容包括：

- 保持期间关节目标是否稳定。
- 是否出现明显下垂、抖动或控制权切换。
- 保持结束后从旧动作切换到 RTC 新动作是否平滑。
- 推理异常和超时后是否能安全回到初始姿态。

### 4.2 避免 episode 末尾的无效推理

当前动作队列降到阈值时会触发后台推理。若队列中的动作已经足够完成本次 episode，则不应再生成下一块动作。

后续应把“episode 剩余动作帧数”提供给 RTC 适配器：

```text
若当前队列长度 >= episode 剩余动作数：不再启动新推理
```

### 4.3 区分有效动作时间和墙钟时间

加入保持等待后，`EPISODE_DURATION_S=2.5` 表示 50 帧有效动作，不再等于真实经过的 2.5 秒。需要在日志中分别记录：

- 有效动作帧数与有效动作时间。
- 首次模型推理时间。
- RTC 后台推理时间。
- 等待保持时间。
- episode 总墙钟时间。

超时策略也应根据这种差异重新检查，避免任务还在正常等待推理时被墙钟超时提前终止。

### 4.4 RTC 运行指标

建议持续记录：

- `latency_s`：实际推理耗时。
- `latency_delay`：根据耗时估计的控制帧数。
- `guided_delay`：经过执行上限裁剪后用于 RTC 的延迟帧数。
- `consumed`：推理期间实际执行的动作数。
- `hold_s`：保持最后目标的时间。
- action chunk 交界处的最大关节跳变量。
- RTC 开启和关闭时的任务成功率与轨迹平滑度。

### 4.5 完整模型离线验证

目前已完成 RTC 数值、队列、线程和等待机制测试，但尚未加载完整模型权重执行 RTC guided denoising。真机前应先用数据集样本完成：

1. 生成第一段无 RTC action chunk。
2. 取其中的剩余前缀作为上一段动作。
3. 生成第二段 RTC action chunk。
4. 检查显存、dtype、autograd、动作形状及数值范围。
5. 对比 RTC 开关前后的 action chunk 交界变化。

## 5. 任务何时结束：当前尚未解决的核心问题

RTC 只负责动作块衔接，不负责判断任务成功。当前 PI0.5 推理输出只有 action chunk，没有以下输出：

```text
done
success
success_probability
```

当前 LeRobot PI0.5 移植版也没有论文完整版中的高层文本子任务推理。因此，程序现在只能依赖固定动作帧数或固定最大时限结束任务，无法自动判断“杯子已经在手里”或“包已经提起”。

仅使用动作变小、关节停止变化等条件不可靠，因为任务失败、机械臂卡住或模型失去目标时也可能出现小动作。

## 6. 推荐的终止判断开发路线

### 阶段一：人工终止，优先用于 RTC 验证（已实现基础版）

当前 RTC 入口已经增加运行过程中的单键监听和墙钟时间上限：

```text
q：停止当前任务，按正常流程回初始姿态，然后返回任务选择
MAX_EPISODE_WALL_TIME_S：从第一帧动作发出后开始计算的最长墙钟时间
```

首次模型加载和第一块动作生成不计入该墙钟时间。任务选择界面的 `q` 仍用于退出整个程序。后续仍可按需要增加单独的 `x=成功结束` 与 `q=紧急退出` 语义；当前基础版先统一使用运行中的 `q` 结束当前任务。

### 阶段二：独立 Success Detector

推荐先在动作模型外部训练成功检测器：

```text
当前图像 + 当前机器人状态 + 任务文本
                    ↓
             success probability
```

建议终止条件不是单帧超过阈值，而是：

```text
success_probability >= threshold
并且连续保持 0.5～1.0 秒
```

杯子任务可关注杯子是否离开桌面、是否与右手保持接近；提包任务可关注包或提手是否达到目标高度。若有深度、物体位姿、力传感器或手部接触信号，应与视觉判断融合。

独立检测器的优点：

- 不改变已经训练好的 π0.5 动作权重。
- 可以单独采集和修正失败样本。
- 可以独立设定保守阈值。
- 检测器失效时仍可退回人工终止和最大时限。

### 阶段三：在 PI0.5 中增加 Success Head

若后续数据量充足，可以在 VLM prefix hidden state 后增加二分类 head：

```text
VLM prefix hidden state
        ├── Action Expert → action chunk
        └── Success Head  → success probability
```

成功判断应接在表示当前图像、任务和机器人状态的 VLM prefix 上，而不是直接接在 flow-matching action 输出上。

训练时需要增加成功标签和二分类损失：

```text
total_loss = action_loss + lambda_success * success_BCE_loss
```

现有 checkpoint 不包含 success head 权重，新 head 不能直接使用，必须重新训练或微调。

### 阶段四：显式 Terminate Action

另一条路线是参考 RT-1，把 `terminate episode` 作为策略动作空间中的一个独立输出。该方案同样需要：

- 对演示数据提供明确终止标签。
- 训练模型学习终止动作。
- 设置连续判定、防抖和最大步数兜底。
- 防止策略在失败或不确定时过早终止。

## 7. Success Detector 数据要求

不能简单地把所有 episode 最后一帧都视为成功，必须区分：

- 真正成功完成的结尾。
- 失败、超时或人工中止的结尾。
- 物体短暂满足条件但随后掉落的状态。
- 成功后稳定保持一段时间的状态。

推荐包含：

- 成功前的负样本。
- 成功并稳定保持的正样本。
- 抓取失败、拿空、物体滑落、遮挡等困难负样本。
- 不同杯子、包、背景、光照和相机角度。

只有成功演示、没有失败样本时，检测器可能只学会“episode 接近结尾”，而没有真正学会任务是否完成。

## 8. 安全终止状态机

无论采用人工判断、规则、独立分类器还是模型 success head，都应通过统一状态机控制：

```text
RUNNING
  ├── success 连续满足 → HOLD → RETURN_TO_INITIAL
  ├── 人工 x          → HOLD → RETURN_TO_INITIAL
  ├── 最大时限         → HOLD → RETURN_TO_INITIAL
  ├── 推理异常         → HOLD → SAFE_SHUTDOWN
  └── 人工 q / 急停    → SAFE_SHUTDOWN
```

成功检测结果不应直接绕过关节限位、速度限制、碰撞保护和超时保护。

## 9. 推荐实施优先级

- [ ] 用完整 checkpoint 和离线数据执行一次 RTC guided denoising。
- [ ] dry-run 验证 2.5 秒推理、执行 10 帧、保持等待、从新块第 10 帧继续的完整时序。
- [ ] 真机低风险姿态验证底层最后目标保持行为。
- [x] 增加运行中的 `q` 结束当前任务和最大墙钟时间上限（基础版）。
- [ ] 进一步区分 `x` 成功结束与 `q` 紧急退出，并记录不同终止原因。
- [ ] 避免 episode 末尾无效预推理。
- [ ] 调整墙钟超时与有效动作时间统计。
- [ ] 采集杯子与提包成功/失败检测数据。
- [ ] 先训练独立 Success Detector。
- [ ] 评估是否需要把 Success Head 或 terminate action 合入 PI0.5。

## 10. 相关工作

- RT-1：在动作空间中增加 terminate episode 离散模式。
  <https://robotics-transformer1.github.io/>
- Vision-Language Models as Success Detectors（SuccessVQA）：把成功判断建模为视觉问答。
  <https://arxiv.org/abs/2303.07280>
- VICE：从目标事件样本学习视觉奖励/事件判别。
  <https://arxiv.org/abs/1805.11686>
- VIP：从视频学习视觉价值和目标距离。
  <https://arxiv.org/abs/2210.00030>
- LIV：使用语言或图像目标产生视觉价值。
  <https://arxiv.org/abs/2306.00958>
- π0.5：高层文本子任务与低层 action chunk 的层次化推理。
  <https://www.physicalintelligence.company/download/pi05.pdf>
- AHA：机器人操作失败检测与推理。
  <https://arxiv.org/abs/2410.00371>
