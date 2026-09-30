# Data Editor 多阶段 Subtask 标注

`data_editor_CN.py` 支持在一个 Unitree episode 中标注多个 subtask。标注先写入原始 episode 的
`data.json`，之后由 Unitree→LeRobot 转换程序生成
`meta/episodes_detailed_task.jsonl`。

## 1. 配置数字键

可复制 `data_editor/subtask_config.example.yaml` 后修改：

```yaml
version: 1
subtasks:
  "1":
    action_text: "pick up the cup"
    language_memory: ""
    color: "#4CAF50"
  "2":
    action_text: "pour water"
    language_memory: "The cup has been picked up."
    color: "#2196F3"
```

仅支持数字键 `1`～`9`。`action_text` 必填；`language_memory` 和 `color` 可省略。

## 2. 标注操作

1. 打开数据集，并在界面中选择 YAML 文件。
2. 开启“Subtask 标注模式”。
3. 定位到 episode 的有效起点，按 `Q`。这一帧成为当前标注起点。
4. 定位到第一阶段的最后一帧，按对应数字键，例如 `1`。程序保存从起点到当前帧的阶段，并把下一帧作为新起点。
5. 定位到下一阶段的最后一帧，按 `2`，依次继续。
6. 定位到 episode 有效终点，按 `E`。`E` 只设置裁剪终点，不会自动补一个 subtask；如需标注尾段，应先在该帧按数字键，再按 `E`。

时间轴下方会用 YAML 中的颜色显示不同阶段。界面也支持撤销最后一段和清空当前 episode 的全部标注。

标注区间在文件中统一保存为左闭右开 `[start_frame, end_frame)`，但交互时数字键所在帧包含在刚刚创建的阶段中。

## 3. 保存和转换

每按一次数字键，程序都会原子更新当前 episode 的 `data.json`。裁剪或导出 episode 时，已有标注会自动映射到新的帧编号。

执行现有的 Unitree→LeRobot 转换流程后，转换器会按照最终 LeRobot episode 编号生成：

```text
<lerobot_dataset>/meta/episodes_detailed_task.jsonl
```

最终文件只保留训练所需的 `start_frame`、`end_frame`、`action_text` 和
`language_memory`；界面专用的数字键和颜色不会写入训练标注。
