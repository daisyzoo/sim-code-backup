# G1 23 DoF 任务场景库与任务语言

日期：2026-08-20  
本体：`embodiment_id = g1_edu_23_bimanual`（腿 12 + 腰 yaw 1 + 双臂各 5，橡胶 stump，无灵巧手）  
用途：规定 **23 适合跑的场景 / 任务 / 中文指令**，供 scene 包、LeRobot `task` 字段、真机采集共用。  
原则：场景包仍不写 `robot_dof`；本文件是 **embodiment 侧的任务目录**，不是 twin 几何。

配套契约：[`pipeline_resources.md`](pipeline_resources.md) §5、`simfoundry/schema.py` 的 `TaskSpec`。

---

## 0. 能力边界（写任务前先过）

23 能做的末端动作只有：**够、推、拨、扫、压、钩、示意**。  
不能做：**抓、放、倒、拧、插、开抽屉/柜门（需手）**。

| 可以依赖 | 不要依赖 |
|---|---|
| 双腿行走、原地转、站稳 | 腕 pitch / yaw 把掌面对准物体 |
| 腰 yaw（左右转躯干） | 腰 pitch / roll（俯身探台、侧倾探柜） |
| 肩 3 + 肘 + 腕 roll | Dex3 / Inspire / 夹爪 |
| D435i 头视 + Mid360（真机） | 精细力控捏取 |
| 台面高度约 **0.72–0.82 m**、物体在身前 **0.20–0.45 m** | 高柜、水槽深处、桌下、身后 |

身高约 1.32 m、臂展约 0.45 m：操作台必须 **贴身、偏低、物体靠前沿**。深桌面中后排够不到。

**A 期（当前仿真）**：骨盆固定，locomotion 类任务只出 json、不采集。  
**解锁行走后**：同一套 `task_id` 可开跑，不改指令。

`requires_ee`：本库任务全部为 `stump`。抓取类继续用 `dexhand` 打标并过滤，不进 23 训练集。

---

## 1. 中文任务语言规范

LeRobot 的 `task` / `task_index` 用 **简体中文祈使句**。短任务一条一个主动词；长时序用「然后 / 再」把 2–4 个合法动词串起来。

### 1.1 句式

```
[可选：用哪只手] + 动词 + 物体 + 空间关系
```

| 规则 | 要 | 不要 |
|---|---|---|
| 动词 | 走、停、转到、伸、推、拨、扫、按、挥、指 | 拿、抓、夹、放进、倒、拧、打开抽屉 |
| 长度 | 8–24 字，口语 | 说明书长句、英文混写 |
| 物体 | 场景里有的语义名（杯子、碗、瓶子） | 「那个东西」「物品 A」 |
| 空间 | 向前、向左、到台前、靠近碗 | 未标定的毫米坐标 |
| 手臂 | 默认不写（双臂站立）；单臂任务写「右臂 / 左臂」 | 同时写两套互斥动作 |

真机与仿真必须用 **同一句**，不要仿真英文、真机中文。

**短任务**一条一个动词。**长时序**用合法动词串起来，用「然后 / 再」连接，一般 2–4 步，例如：「走到门前把门推开，再走到操作台前，把杯子推向碗。」每一步仍须是 §1.2 里的动词。

### 1.2 动词表（23 合法）

| 动词 | 含义 | 典型成功判据 |
|---|---|---|
| 走到 | 移动到目标附近并面向它 | 骨盆水平距离 < 阈值，站稳 |
| 停在 / 站定 | 已到达后保持静止 | 线速度、角速度近 0 |
| 转到 | 原地 yaw，面向目标 | 朝向误差 < 阈值 |
| 伸向 | stump 靠近物体，不要求接触 | EE–物体距离 < 阈值 |
| 推 | 接触后沿桌面平移 | 物体位移或与目标 Near |
| 拨 | 短时侧向冲击，改变物体位置 | 物体越过分界 |
| 扫 | 沿桌沿把物体赶到一侧 | 指定区域清空或物体入区 |
| 按 | stump 压下按钮/开关 | 按钮行程或接触保持 |
| 挥手 | 上肢示意，可不接触 | 肩/肘轨迹进入挥手区间 |
| 指向 | 前臂对准目标 | 前臂射线与目标夹角小 |

禁止作为 23 主动词：拿起、抓取、放下、放入、倒入、拧开、拣起、握住。

### 1.3 同义改写（数据增强）

每条 `task_id` 有一条 **规范句**（写入 json 的 `instruction`），另给 2–4 条 **改写**，采集/导出时可轮换，`task_id` 不变。

改写只换说法，不换成功条件：

- 「走到操作台前站定」↔「走到台边停下」↔「去操作台前面站好」
- 「把杯子推向碗」↔「把杯子拨到碗旁边」↔「把红杯子推近碗」

物体外观 cousin（换杯子网格）时，规范句仍用语义名「杯子」，不要写成「025_mug」。

### 1.4 json 字段

```json
{
  "task_id": "push_cup_to_bowl",
  "instruction": "把杯子推向碗。",
  "instruction_variants": [
    "把杯子拨到碗旁边。",
    "把桌上的杯子推近碗。"
  ],
  "predicates": [{"type": "Near", "a": "cup", "b": "bowl", "threshold": 0.12}],
  "requires_ee": "stump",
  "arms": "right",
  "needs_locomotion": false
}
```

- `instruction`：规范中文，LeRobot `task` 主句。
- `instruction_variants`：可选；schema 可先放 extras，A 期导出仍用规范句。
- `needs_locomotion`：true 的任务在固定骨盆阶段跳过。
- `arms`：`right` / `left` / `bimanual`（站立姿态或双手配合，不是抓取）。
- `zone_id`：本任务发生的分区（同一世界内）。
- `horizon`：`atomic`（单技能）或 `long`（跨分区时序）。

---

## 2. 一个世界、七个分区

**目标空间是同一套室内，不是七个互不连通的小世界。** 走廊连着门，门里是厨房台和实验桌，墙上有按钮，空地里可以对人挥手。长时序（走到 → 推门 → 去台前 → 推杯）必须共享坐标系，否则只能「传送切关」，学不到导航与操作的衔接。

先前写成独立 `scenes/<id>/`，只是 A 期骨盆还锁着、走不到隔壁时的 **采数切片**，不是终局拓扑。切片可以继续用（只加载台面附近、reset 更快），但权威布局是一个 twin：

权威布局包：[`scenes/indoor_lab_g1_23/`](scenes/indoor_lab_g1_23/)（大厅 → 走廊 → 门 → 厨房/实验桌）。Kit 演示：`scripts/demo_indoor_lab.py`（脚本步态走过去切区，不传送）。现有 `kitchen_counter_placeholder` 仍是厨房分区的桌面切片。

```
          [hri / open_floor]
                  │
            走廊 corridor
                  │
           轻门 swing_door
                  │
     ┌────────────┼────────────┐
     │            │            │
 wall_button   kitchen      lab_low_bench
```

连通约束（写进 `layout.json` 的区原点，单位 m，可微调）：

| 分区 zone_id | 中文 | 建议相对位置 | 操作面 |
|---|---|---|---|
| `open_floor` | 室内空地 | 入口大厅，≥ 3×3 m 净空 | 无；可放地面标记 |
| `hri_open_space` | 对人示意 | 与空地重叠或一侧，人在 1.5–2.5 m 外 | 无接触 |
| `corridor` | 走廊 | 连接大厅与门，宽 1.2–1.8 m、长 2–6 m | 无桌面物 |
| `swing_door` | 轻门 | 走廊尽头，推向厨房侧 | 门板可推 |
| `wall_button` | 墙面按钮 | 门旁墙，高 0.90–1.10 m | 大按钮 |
| `kitchen_counter_stump` | 厨房操作台 | 门内一侧；台高 ~0.78 m、深 0.60 m，物体靠前沿 | 杯/碗/瓶 |
| `lab_low_bench` | 实验矮桌 | 同一房间邻墙；台高 ~0.75 m、深 ≤ 0.50 m | 盒/瓶/开关 |

厨房与实验桌可以同室两面墙，不必做成两套公寓。`kitchen_counter_placeholder` 并入厨房分区语义。

### 2.1 分区表

| zone_id | 中文名 | 短任务 A 期 | 长时序 | 主技能 |
|---|---|---|---|---|
| `open_floor` | 室内空地 | 原地走、转、挥手 | 起点 | 走、转、停、挥手 |
| `corridor` | 走廊 | 否（需行走） | 过道 | 走到点、面向门 |
| `lab_low_bench` | 实验矮桌 | 是（出生在桌前） | 第二操作面 | 伸、推、扫、按开关 |
| `kitchen_counter_stump` | 厨房操作台 | 是（出生在台前） | 主操作面 | 伸、推、拨 |
| `wall_button` | 墙面按钮 | 是（贴墙站） | 进门前后 | 伸、按 |
| `swing_door` | 轻门 | 贴门时可推 | 房间边界 | 走到、推门 |
| `hri_open_space` | 对人示意 | 人与机器人都固定 | 收束 | 挥、指、转到 |

### 2.2 短任务 vs 长时序

| | 短任务（atomic） | 长时序（long） |
|---|---|---|
| 空间 | 可只激活一个分区做 reset | **必须整包加载**，机器人用腿换区 |
| 指令 | 一个动词 | 2–4 个合法动词串联 |
| A 期（骨盆固定） | 可采 | **不能采**（走不到） |
| 成功 | 单 predicate | 逐步 predicate 全满足，允许中间站稳 |

长时序的瓶颈是 **站立/行走策略**，不是「能不能把网格放进同一个 USD」。网格应尽早按一张图铺；没走路之前只在厨房/桌前切片出生。

### 2.3 各分区布局要点

**`open_floor`**  
无桌。原点为机器人；可放 1–2 个地面路标（锥桶、地贴）。适合全身动作与短距行走。

**`corridor`**  
两侧墙，前方门口或地标。目标点距离 2–6 m。不要放需要操作的桌面物体。

**`lab_low_bench`**  
桌沿距骨盆投影约 0.75–0.85 m（与当前厨房台一致量级）。桌深 ≤ 0.50 m。物体：杯/瓶/块，质量 0.05–0.25 kg，摩擦系数 0.4–0.6，全部放在 **靠机器人一侧的半张桌**。

**`kitchen_counter_stump`**  
沿用现布局：台面中心约 (1.10, 0, 0.78)，深 0.60 m。杯子、碗放在靠近机器人的半区。盘子、瓶子可作障碍或扫除对象。柜门若存在必须 **锁死**（23 打不开）。

**`wall_button`**  
一面墙，大按钮或面板，高度对齐胸部（约 0.95 m）。机器人鼻尖距墙约 0.40–0.55 m。周围不要放桌面抓取物。

**`swing_door`**  
轻质铰链门，推向开。成功 = 门角位移超过阈值。不要用门锁、门把手旋转。

**`hri_open_space`**  
前方站立人物或假人。任务不接触人体，只做朝向与上肢示意。

---

## 3. 任务目录

编号：`{skill}__{scene}` 不够时用功能名（已有 `push_cup_to_bowl` 保持稳定，不改 id）。

状态：`A` = 固定骨盆可采；`L` = 需要行走；`H` = 可固定骨盆做上肢。

### 3.1 移动与站定

| task_id | 场景 | 状态 | 规范指令 | 改写 | predicate 要点 |
|---|---|---|---|---|---|
| `approach_counter` | kitchen / lab | L | 走到操作台前站定。 | 走到台边停下。 / 去操作台前面站好。 | pelvis Near counter，站稳 |
| `walk_to_marker` | open_floor | L | 走到地上的标记处停下。 | 走到地标前面站定。 | pelvis Near marker |
| `walk_down_corridor` | corridor | L | 沿走廊走到尽头停下。 | 顺着走廊走到前面的门口。 | pelvis Near goal |
| `turn_to_face_door` | corridor / door | L/H | 转到面向门口。 | 转身正对那扇门。 | yaw 对准 door |
| `stand_still` | 任意 | H | 站在原地不要动。 | 保持站立，不要迈步。 | 速度近 0，时长 ≥ 2 s |

### 3.2 伸手（无接触或轻接触）

| task_id | 场景 | 状态 | 规范指令 | 改写 | predicate 要点 |
|---|---|---|---|---|---|
| `reach_cup` | kitchen / lab | A | 把右臂伸向杯子。 | 右手够到杯子旁边。 / 伸手靠近桌上的杯子。 | right_ee Near cup ~0.12 m |
| `reach_bottle` | kitchen / lab | A | 把右臂伸向瓶子。 | 右手够到瓶子。 | right_ee Near bottle |
| `reach_bowl` | kitchen / lab | A | 把左臂伸向碗。 | 左手靠近碗。 | left_ee Near bowl |
| `reach_button` | wall_button | A | 把手伸向墙上的按钮。 | 举起手臂对准按钮。 | ee Near button |
| `both_arms_forward` | open_floor / lab | H | 双臂向前平伸。 | 两只手一起往前伸。 | 双 EE 在躯干前方工作空间内 |

### 3.3 推 / 拨 / 扫（23 桌面主技能）

| task_id | 场景 | 状态 | 规范指令 | 改写 | predicate 要点 |
|---|---|---|---|---|---|
| `push_cup_to_bowl` | kitchen | A | 把杯子推向碗。 | 把杯子拨到碗旁边。 / 把桌上的杯子推近碗。 | cup Near bowl ~0.12 m |
| `push_cup_forward` | lab / kitchen | A | 把杯子沿桌面往前推。 | 把杯子往桌内推一点。 | cup 沿 +x 位移 > 阈值 |
| `nudge_bottle_left` | kitchen / lab | A | 把瓶子向左拨开。 | 把瓶子拨到左边。 | bottle 的 y 越过阈值 |
| `sweep_bottle_aside` | kitchen / lab | A | 把瓶子扫到桌子一侧。 | 把瓶子拨到桌边清出走道。 | bottle 进入 side 区域 |
| `clear_front_zone` | lab | A | 把身前桌面上的瓶子拨走。 | 把挡在前面的瓶子推开。 | 前沿区域无 bottle |
| `push_box_along_table` | lab | A | 把小盒子沿桌子推到另一头。 | 把盒子从左侧推到右侧。 | box Near table_end |

物体须轻、底面可滑。杯子侧倒不算成功，除非另立 `tip_cup`（默认不做）。

### 3.4 按压

| task_id | 场景 | 状态 | 规范指令 | 改写 | predicate 要点 |
|---|---|---|---|---|---|
| `press_wall_button` | wall_button | A | 按下墙上的按钮。 | 用手按一下那个按钮。 | 按钮行程或接触力×时间 |
| `press_table_switch` | lab | A | 按下桌上的开关。 | 按一下台面上的开关。 | switch 状态翻转 |

按钮要大、行程明显（≥ 1 cm），避免细键。23 没有指尖。

### 3.5 推门（行走解锁后）

| task_id | 场景 | 状态 | 规范指令 | 改写 | predicate 要点 |
|---|---|---|---|---|---|
| `approach_and_push_door` | swing_door | L | 走到门前，把门推开。 | 去门口把门推开。 | 先 Near door，再门角 > 阈值 |
| `push_door_open` | swing_door | A（若已贴门） | 把门推开。 | 用力把门推开。 | 门开合角 |

用 stump 推门板，指令不要写「拧把手」「拉门」。

### 3.6 示意 / HRI（不接触）

| task_id | 场景 | 状态 | 规范指令 | 改写 | predicate 要点 |
|---|---|---|---|---|---|
| `wave_hello` | open_floor / hri | H | 对着前面挥手。 | 举起右手挥一挥。 | 右臂挥手区间 |
| `point_at_person` | hri | H | 用右臂指向前面的人。 | 伸手指向那个人。 | 前臂朝向 person |
| `point_at_cup` | kitchen / lab | A | 用右臂指向杯子。 | 伸手指向桌上的杯子。 | 朝向 cup（可比 reach 更远、不要求 Near） |
| `turn_and_wave` | hri | L/H | 转到面向人，然后挥手。 | 转身对着人挥手。 | yaw + 挥手 |

适合无桌采集、动作模仿、语言–动作对齐；不要当操作成功率指标。

### 3.7 长时序（同一世界内跨分区）

下列任务 `horizon=long`，`needs_locomotion=true`。技能仍全是 stump，只是把原子任务按空间顺序接起来。

| task_id | 路径 | 规范指令 |
|---|---|---|
| `enter_and_push_cup` | 空地 → 走廊 → 门 → 厨房 | 走到门前把门推开，再走到操作台前，把杯子推向碗。 |
| `press_then_enter` | 按钮 → 门 → 厨房 | 按下门旁的按钮，然后推开门走到台前。 |
| `enter_and_wave` | 空地 → 门 → 对人 | 推开门，走到人前面挥手。 |
| `kitchen_then_lab` | 厨房 → 实验桌 | 把杯子推向碗，再走到实验桌前把瓶子拨开。 |
| `greet_then_work` | HRI → 走廊 → 厨房 | 对着人挥手，然后走到操作台前把右臂伸向杯子。 |

改写只压缩或换连接词，不增 capturable 新技能：「去把门推开，到台子那儿把杯子推到碗边。」

成功：记录子目标序列（与上表路径一致），最后一步满足对应原子 predicate。中途摔倒或卡在门口算失败。

不要把「拿起杯子再放到实验桌上」写成 23 长时序——缺手，拼再长也无效。

---

## 4. 明确不做（23 过滤）

下列可保留 json 以便以后换 29+手，但 **`requires_ee` 不得为 stump**，23 采集脚本必须跳过。

| 错误指令（不要用于 23） | 原因 | 以后机型 |
|---|---|---|
| 拿起杯子。 / 把杯子抓起来。 | 无手、无腕 pitch | 29+夹爪或灵巧手 |
| 把杯子放到碗里。 | 抓放 | 同上 |
| 把瓶子从桌上拿走。 | 抓取 | 同上 |
| 打开抽屉。 / 拉开柜门。 | 需侧握+拉 | 29+手 |
| 把水倒进碗里。 | 抓 + 腕倾倒 | 29+手 |
| 拧开瓶盖。 | 精细腕+指 | 29+手 |

现有 `place_cup_in_bowl`（`dexhand`）保持过滤。  
`pick_cup.json` 若仍是 `requires_ee: stump`，与本库冲突：**23 不得采集「拿起」**；应改为 `dexhand` 或从 23 目录删除。

---

## 5. 与现有厨房占位包的对照

`scenes/kitchen_counter_placeholder/` 建议任务集：

| 现 task_id | 本库处理 | 规范中文 |
|---|---|---|
| `approach_counter` | 保留，标 `needs_locomotion` | 走到操作台前站定。 |
| `reach_cup` | A 期可采 | 把右臂伸向杯子。 |
| `push_cup_to_bowl` | A 期主任务 | 把杯子推向碗。 |
| `pick_cup` | 不采 | — |
| `place_cup_in_bowl` | 已是 dexhand，过滤 | — |

建议补进同一 scene 包（仍 `stump`）：

- `reach_bottle`：把右臂伸向瓶子。
- `nudge_bottle_left`：把瓶子向左拨开。
- `point_at_cup`：用右臂指向杯子。

A 期固定骨盆时 **不要** 把「走到台前」写成好像已经完成；机器人已在台前则直接采 reach/push。

---

## 6. 分期落地

权威场景包始终是 **`indoor_lab_g1_23` 一张图**。A 期可以只把机器人 reset 到厨房分区（等价于现在的占位包），不必拆成七个 USD。

| 期 | 空间 | 任务 | 仿真条件 |
|---|---|---|---|
| **A 通链路** | 整包或仅厨房切片 | `reach_cup`、`push_cup_to_bowl` 等 atomic | 固定骨盆、出生在台前 |
| **A′ 分区切片** | 同一 USD，reset 到桌 / 按钮 / 人前方 | 推、拨、挥、按（贴墙） | 仍固定骨盆 |
| **B 行走** | 整包连通 | `approach_*`、`walk_*`、推门 | 解开骨盆，要站立策略 |
| **B′ 长时序** | 整包连通 | §3.7 | 子目标序列 + 中文多句指令 |
| **P3 非本库** | 同一室内 twin | 抓放 | 换 29+手，不拆房间 |

训练协议不变：`observation.images.d435i` + 23 维 `observation.state` + 中文 `task`。

---

## 7. 采集与验收

1. 只采 `requires_ee == stump` 且（A 期）`needs_locomotion != true`。
2. `instruction` 必须是 §1 合法动词；抽检禁止出现「拿/抓/放进」。
3. 成功以 predicate 为准，不以「关节在动」为准；推杯要看到杯子位移。
4. 每条 `task_id` 至少 1 条规范句；改写进入同一 `task_id`，不要为每句同义新建 id。
5. 物体质量、桌高、桌深违反 §2 的，不算 23 可用分区，即使指令合法。
6. 长时序必须在 `indoor_lab_g1_23` 整包上采，禁止「推门结束 → 加载另一个 scene → 出现在厨房」。

---

## 8. 机器可读索引

完整条目见 [`task_library/g1_23_tasks.json`](task_library/g1_23_tasks.json)。字段与 `TaskSpec` 对齐，并多了 `instruction_variants`、`needs_locomotion`、`zone_id` / `zone_ids`、`horizon`、`phase`。长时序在 `long_horizon_tasks`。
