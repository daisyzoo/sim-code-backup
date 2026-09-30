# 待排查：MCP 版本推理速度偏慢

## 1. `inference_end_margin_s` 缺失

**来源**：`eval_g1.py` 第 274-285 行

```python
inference_end_margin_s = max(1.0 / cfg.frequency, 0.2)

if episode_start_time is not None:
    elapsed_s = time.perf_counter() - episode_start_time
    remaining_s = cfg.episode_duration_s - elapsed_s
    if remaining_s <= inference_end_margin_s:
        logger_mp.info("Episode %d stopping before inference at %s: remaining_s=%.3f <= margin_s=%.3f", ...)
        break
```

**作用**：在 episode 结束前的 `margin_s`（通常 0.2s）内，跳过本轮 `predict_action` 推理，直接进入 return 阶段。

**影响**：
- `eval_g1_mcp.py` 没有这段逻辑，episode 最后一轮仍会做完整推理（process_images + policy + execute），导致实际运行时长略超 `episode_duration_s`
- 如果 policy 推理本身较慢（如 >0.1s/step），最后一轮的动作可能来不及执行就结束了
- 对 2.5s episode + 20Hz：每步 0.05s，多跑一步约 +2% 误差

**当前状态**：`eval_g1_mcp.py` 第 277-288 行只检查 `episode_duration_s` 超时，没有 margin 提前保护

---

## 2. Per-episode `reset()` 调用

**来源**：`eval_g1_mcp.py` 第 191-194 行

```python
# Reset state for this episode
if policy is not None and preprocessor is not None and postprocessor is not None:
    policy.reset()
    preprocessor.reset()
    postprocessor.reset()
```

**实际情况**：
- `policy.reset()` (pi05)：只清空 `deque` 队列，无模型权重/状态重置，轻量
- `preprocessor.reset()` / `postprocessor.reset()`：基类实现是空操作 `return None`

**结论**：实测这三个 reset 几乎没有开销，不是导致变慢的原因。

**但保留此处记录**：如果后续 policy 改用有 hidden state 的模型（如 RNN/LSTM），每轮 reset 可能会累积额外 GPU 开销。

---

## 排查建议

1. **先验证 step 数**：对比两边日志，MCP 版本是否多出 1-2 steps
2. **加 `inference_end_margin_s` 保护**，看 step 数是否从 51 降到 50
3. 如果 step 数一样多但 episode 耗时长，检查 `return to init pose` 阶段是否有额外等待