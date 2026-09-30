# PI0.5 LoRA 开发方案

本文档面向当前任务：

- 机器人：`Unitree G1 23DoF`
- 控制维度：`左臂 5 + 右臂 5 + 腰部 1 = 11`
- 观测：`单头部相机 + 11 维状态 + task 文本`
- 数据量：`100` 条 episode，`6000` 帧，`20 FPS`
- 数据集路径：`/home/igs/Desktop/project/vla/data/local/g1_23_right_hand_rag_reach_11d`
- 训练硬件：`RTX 3090 24GB`

---

## 1. 目标

目标不是做 `pi0.5 full finetune`，而是在当前仓库中补齐一条 `pi0.5 LoRA` 训练链路，使其满足：

1. 可以基于 `lerobot/pi05_base` 加载底座模型。
2. 冻结大部分 base weights，仅训练 LoRA adapter。
3. 在 `24GB` 显存上可训练。
4. 兼容当前本地 `LeRobot` 数据集格式。
5. 第一版先保证训练能跑通，不强求第一版就做 adapter-only 保存。

---

## 2. 当前现状

### 2.1 已完成

1. 原始 Unitree JSON 数据已转换为本地 LeRobot 数据集。
2. 已新增 `11` 维 G1 配置：
   - `Unitree_G1_23Dof_Arms5_Waist1`
3. 数据维度与频率已确认：
   - `state/action = 11`
   - `fps = 20`
   - `camera = observation.images.cam_high`

### 2.2 当前缺口

`pi0.5` 当前只支持：

- 从 `lerobot/pi05_base` 加载预训练权重
- 直接做 full finetune

当前代码中没有：

- `LoRA` 配置字段
- `peft` adapter 注入逻辑
- `pi0.5` 专用 adapter 保存/加载逻辑

因此现在要做的是：在 `pi0.5` 路径中补齐 LoRA。

---

## 3. 为什么选 PI0.5 LoRA

对当前任务，选择 `pi0.5 LoRA` 的原因是：

1. 当前数据结构和 `pi0.5` 输入形式天然匹配：
   - 图像
   - 文本
   - 状态向量
   - 动作向量
2. 数据只有 `100` 条，适合用小步微调验证任务可学性，不适合 full finetune 大模型。
3. `24GB 3090` 对 `pi0.5 full finetune` 风险高，但对 `LoRA` 更现实。
4. 当前任务是窄任务 imitation learning，不需要优先追求最重的通用模型路线。

---

## 4. 开发范围

第一版只做：

1. `pi0.5` LoRA 训练接入
2. 本地训练可跑通
3. 保存 checkpoint
4. 能恢复推理或继续训练

第一版暂不强求：

1. adapter-only 单独保存
2. merge LoRA 回 base model
3. 多卡优化
4. Hub 发布

---

## 5. 代码改造方案

### 5.1 配置层

修改文件：

- `unitree_lerobot/lerobot/src/lerobot/policies/pi05/configuration_pi05.py`

新增字段建议：

```python
lora_rank: int = 0
lora_alpha: int = 16
lora_dropout: float = 0.05
lora_target_language_model: bool = True
lora_target_action_expert: bool = True
```

说明：

- `lora_rank = 0` 表示关闭 LoRA，保持兼容现有 full finetune 路径。
- 第一版不建议给 `vision tower` 上 LoRA，优先只处理语言和 action expert。

### 5.2 模型注入层

修改文件：

- `unitree_lerobot/lerobot/src/lerobot/policies/pi05/modeling_pi05.py`

在 `PI05Policy` / `PI05Pytorch` 初始化路径里增加 LoRA 包装逻辑。

建议新增方法：

```python
def _apply_lora(self): ...
def _print_trainable_parameters(self): ...
```

建议注入位置：

1. `self.model = PI05Pytorch(config)` 之后
2. `gradient_checkpointing_enable()` 之前或之后都可以，但应保证 LoRA 注入完成后再统计参数

### 5.3 目标模块

优先给这两部分挂 LoRA：

1. `paligemma.language_model`
2. `gemma_expert`

推荐 target modules：

```python
[
    "self_attn.q_proj",
    "self_attn.k_proj",
    "self_attn.v_proj",
    "self_attn.o_proj",
    "mlp.gate_proj",
    "mlp.up_proj",
    "mlp.down_proj",
]
```

注意：

- `paligemma` 某些模块命名可能和 `gemma_expert` 略有差异，接入前需要打印 `named_modules()` 校对。
- 如果 `o_proj` 名称不一致，要按实际模块名调整。

### 5.4 依赖

需要使用 `peft`：

- `LoraConfig`
- `get_peft_model`

依赖检查点：

1. `peft` 已安装
2. 当前 `transformers` 为支持 openpi 的补丁版本
3. `paligemma` / `gemma` 在 `CONFIG_MAPPING` 中可用

### 5.4.1 当前仓库已验证可用的安装方式

当前仓库里，`pi0.5` 依赖不是普通 PyPI 版 `transformers`，而是 `lerobot` 自己声明的 OpenPI 兼容分支：

- `transformers @ git+https://github.com/huggingface/transformers.git@fix/lerobot_openpi`

如果只执行：

```bash
pip install transformers peft
```

大概率会出现以下问题之一：

1. `ModuleNotFoundError: No module named 'transformers'`
2. `ImportError: cannot import name 'check' from 'transformers.models.siglip'`
3. `check.check_whether_transformers_replace_is_installed_correctly() == False`

当前项目在本机上已验证通过的修复方式如下。

#### 1. 明确使用训练环境解释器

不要依赖当前 shell 是否激活了正确 conda 环境，直接使用：

```bash
/home/igs/miniconda3/envs/unitree_lerobot/bin/python
```

#### 2. 安装 `pi0.5` 训练依赖

```bash
/home/igs/miniconda3/envs/unitree_lerobot/bin/python -m pip install \
  peft==0.17.1 \
  "transformers @ git+https://github.com/huggingface/transformers.git@fix/lerobot_openpi"
```

说明：

- `peft==0.17.1` 为当前仓库已验证可用版本
- `transformers` 必须使用 `fix/lerobot_openpi` 分支
- 不要把这个依赖装到 `base` 环境

#### 3. 验证安装结果

```bash
/home/igs/miniconda3/envs/unitree_lerobot/bin/python - <<'PY'
import transformers, peft
print("transformers", transformers.__version__)
print("peft", peft.__version__)
from transformers.models.siglip import check
print("siglip.check import: OK")
print("replace_installed =", check.check_whether_transformers_replace_is_installed_correctly())
PY
```

预期结果：

- `transformers 4.53.3`
- `peft 0.17.1`
- `siglip.check import: OK`
- `replace_installed = True`

只要最后一行不是 `True`，当前环境就不满足 `pi0.5` 训练要求。

### 5.5 冻结策略

第一版建议策略：

- 冻结 base model 全部权重
- 只训练 LoRA adapter

实现上依赖 `get_peft_model()` 自动处理大部分冻结行为，但仍建议：

1. 显式打印 `trainable params / total params`
2. 确保非 LoRA 参数 `requires_grad=False`

### 5.6 保存与加载

第一版建议采取保守方案：

- 保持现有 `save_pretrained()` 流程
- 先允许整个包过 LoRA 的模型按当前逻辑保存

原因：

- 改动小
- 最快跑通
- 先解决训练，不先做产物瘦身

后续第二版再考虑：

1. adapter-only 保存
2. base model + adapter 分离加载
3. merge/unmerge 逻辑

---

## 6. 推荐实现顺序

### 阶段 A：最小可训练版

目标：在 `24GB` 上起训

步骤：

1. 在 `PI05Config` 增加 LoRA 参数
2. 在 `PI05Policy` 中加入 LoRA 注入逻辑
3. 打印 trainable 参数统计
4. 用小 batch 跑通训练

完成标准：

1. 训练能进入 first step
2. 显存不爆
3. `loss` 正常返回

### 阶段 B：稳定训练版

目标：能持续训练并保存 checkpoint

步骤：

1. 验证 checkpoint 保存
2. 验证 resume
3. 验证推理时可以加载训练结果

完成标准：

1. 可训练 `1000+` steps
2. 可中断恢复
3. 推理能输出动作

### 阶段 C：规范化版

目标：只保存 adapter

步骤：

1. 覆写 `PI05Policy._save_pretrained()`
2. 适配 `from_pretrained()` 先加载 base，再加载 LoRA
3. 验证 adapter-only 推理

这一步可以放到训练链路跑通之后。

---

## 7. 推荐训练超参数（第一版）

面向 `24GB 3090`，第一版建议尽量保守：

```text
policy.type = pi05
policy.pretrained_path = lerobot/pi05_base
policy.dtype = bfloat16
policy.gradient_checkpointing = true

policy.lora_rank = 16
policy.lora_alpha = 32
policy.lora_dropout = 0.05

batch_size = 1
steps = 10000
save_freq = 1000
log_freq = 20
num_workers = 2
eval_freq = 0
```

说明：

- `batch_size=1` 是为了优先保证显存安全。
- 第一版不要追求吞吐量，先追求稳定起训。
- 如果显存还有余量，再考虑 `batch_size=2`。

---

## 8. 训练脚本建议（LoRA 接入完成后）

建议新增脚本：

- `scripts/train_pi05_lora_g1_23_rag_reach.sh`

建议参数：

```bash
python src/lerobot/scripts/lerobot_train.py \
  --dataset.repo_id=local/g1_23_right_hand_rag_reach_11d \
  --dataset.root=/home/igs/Desktop/project/vla/data/local/g1_23_right_hand_rag_reach_11d \
  --policy.type=pi05 \
  --policy.pretrained_path=lerobot/pi05_base \
  --policy.push_to_hub=false \
  --policy.dtype=bfloat16 \
  --policy.gradient_checkpointing=true \
  --policy.lora_rank=16 \
  --policy.lora_alpha=32 \
  --policy.lora_dropout=0.05 \
  --batch_size=1 \
  --steps=10000 \
  --save_freq=1000 \
  --log_freq=20 \
  --eval_freq=0 \
  --num_workers=2
```

---

## 9. 验证清单

### 9.1 代码验证

1. `python -m py_compile ...` 通过
2. `peft` 导入正常
3. `transformers` 补丁版本可用

### 9.2 模型验证

1. 模型可从 `lerobot/pi05_base` 加载
2. LoRA 注入后 trainable params 明显下降
3. 非 LoRA 权重被冻结

### 9.3 训练验证

1. 单步 forward 正常
2. backward 正常
3. 显存峰值在 `24GB` 内
4. checkpoint 能保存

### 9.4 推理验证

1. 能加载训练产物
2. 能对本地数据做离线动作预测
3. 输出动作维度为 `11`

---

## 10. 风险与注意事项

### 10.1 依赖风险

`pi0.5` 依赖：

- 特定 `transformers` 补丁分支
- `paligemma` 访问权限
- `peft`

这些环节任意一个不稳，训练都会被依赖问题卡住。

### 10.2 显存风险

即便 LoRA 后，`pi0.5` 仍然不是轻模型。

要预期：

1. `batch_size=1`
2. `bfloat16`
3. `gradient_checkpointing=true`

这三项大概率都需要保留。

### 10.3 数据风险

只有 `100` 条数据，核心风险是过拟合，不是欠拟合。

因此第一版目标应该是：

- 验证任务可学
- 验证模型能复现“接近 rag”动作

而不是先追求泛化。

---

## 11. 结论

当前建议路线：

1. 先做 `pi0.5 LoRA` 最小接入
2. 先跑通本地训练
3. 再做保存/恢复规范化

优先级排序：

1. **训练能起**
2. **显存能压住**
3. **checkpoint 能存**
4. **再考虑 adapter-only 保存**

如果要继续推进，下一步实际开发顺序建议是：

1. 先改 `configuration_pi05.py`
2. 再改 `modeling_pi05.py` 做 LoRA 注入
3. 再加专用训练脚本
4. 最后做 checkpoint / inference 验证
