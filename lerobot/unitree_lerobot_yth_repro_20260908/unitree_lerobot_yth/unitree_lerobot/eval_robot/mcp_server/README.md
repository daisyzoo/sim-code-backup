# VLA MCP Server 使用指南

## 架构

```
┌────────────────────────────────────────────────────────┐
│                  eval_pi05_..._mcp.sh                  │
│            (启动脚本，传递所有参数)                        │
└──────────────────────────┬─────────────────────────────┘
                           │ python -m
                           ▼
┌────────────────────────────────────────────────────────┐
│              vla_mcp_server.py  (入口)                  │
│   - 参数解析 (draccus.parse EvalRealConfig)            │
│   - 启动 HTTP server                                    │
└──────────────────────────┬─────────────────────────────┘
                           │ threading.Thread
                           ▼
┌────────────────────────────────────────────────────────┐
│              vla_server.py  (FastAPI)                   │
│   /vla/execute  POST  SSE 流式响应 (提交任务)             │
│   /vla/stop     POST  紧急停止                          │
│   /vla/status   GET   查询状态                          │
│   /vla/health   GET   存活探针                          │
│                                                        │
│   后台线程运行 eval_g1_mcp.py 推理循环                   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│              eval_g1_mcp.py                            │
│   eval_policy_controlled() 任务驱动推理循环              │
│   状态机: IDLE→PREPARING→RUNNING→RETURNING→IDLE         │
└────────────────────────────────────────────────────────┘
```

## 快速启动

```bash
# 方式1: 使用默认参数（推荐先跑通）
./scripts/eval_pi05_lora_g1_23_rag_reach_real_mcp.sh

# 方式2: 自定义环境变量
POLICY_PATH=/path/to/checkpoint MCP_PORT=9000 ./scripts/eval_pi05_lora_g1_23_rag_reach_real_mcp.sh

# 方式3: 直接运行 Python
python -m unitree_lerobot.eval_robot.vla_mcp_server \
  --port=8765 \
  --policy.path="/media/igs/EAGET/syh/vla/outputs/pi05_lora_g1_23_rag_reach_20260520_210832/checkpoints/010000/pretrained_model" \
  --repo_id="local/g1_23_right_hand_rag_reach_11d" \
  --root="/home/igs/Desktop/project/vla/data/local/g1_23_right_hand_rag_reach_11d" \
  --arm=G1_23 \
  --image_host="192.168.123.164" \
  --send_real_robot=true
```

## HTTP API

服务启动后监听 `http://0.0.0.0:8765`（可通过 `--port` 修改）。

### 1. 提交任务 (`/vla/execute`)

```bash
curl -X POST http://localhost:8765/vla/execute \
  -H "Content-Type: application/json" \
  -d '{"task_text": "reach forward", "duration_s": 4.0}' \
  -N
```

返回 SSE 流：
```
data: {"type": "ack", "task_id": "..."}

data: {"type": "progress", "state": "running", "step": 1}

data: {"type": "progress", "state": "running", "step": 2}

...

data: {"type": "done", "result": {"task_id": "...", "steps": 80, "completed": true}}

data: [DONE]
```

### 2. 紧急停止 (`/vla/stop`)

```bash
curl -X POST http://localhost:8765/vla/stop
```

### 3. 查询状态 (`/vla/status`)

```bash
curl http://localhost:8765/vla/status
```

返回：
```json
{
  "state": "idle",
  "task_id": null,
  "step": 0,
  "task_text": null,
  "last_result": {
    "task_id": "...",
    "steps": 80,
    "completed": true
  }
}
```

### 4. 存活探针 (`/vla/health`)

```bash
curl http://localhost:8765/vla/health
```

## 主要参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--policy.path` | 模型 checkpoint 路径 | `.../010000/pretrained_model` |
| `--repo_id` | 数据集 ID | `local/g1_23_right_hand_rag_reach_11d` |
| `--root` | 数据集根目录 | `.../data/local/g1_23_right_hand_rag_reach_11d` |
| `--arm` | 机器人型号 | `G1_23` |
| `--image_host` | 相机服务 IP | `192.168.123.164` |
| `--episode_duration_s` | 每次任务执行时长(秒) | `4` |
| `--return_to_zero_duration_s` | 返回零点时长(秒) | `3` |
| `--frequency` | 控制频率(Hz) | `20` |
| `--send_real_robot` | 是否控制真实机器人 | `true` |
| `--port` | HTTP 服务端口 | `8765` |

完整参数列表参考 `EvalRealConfig` 类定义 (`utils/utils.py`)。

## MCP 模式 (可选)

除了 HTTP API，还支持通过 MCP (Model Context Protocol) 协议调用：

```bash
# 先启动 HTTP server（后台运行）
python -m unitree_lerobot.eval_robot.vla_mcp_server --port=8765 &

# 然后启动 MCP stdio 客户端（需要额外配置 Claude Code MCP）
# 或直接使用 vla_mcp_server.py 中的 create_vla_mcp() 函数
```

## 日志输出

日志默认输出到 stdout，包含：
- 机器人初始化状态
- 每个 episode 的开始/结束
- 每步推理耗时 (`observation_s`, `policy_s`, `execute_s`)
- 每 5 秒一次心跳日志

```bash
# 运行时查看日志
tail -f /dev/null  # 日志直接打印到 stdout
```