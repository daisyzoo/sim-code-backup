# PI0.5本机分拣训练入口

已将云端r2的数据过滤、动作窗口索引和padding检查同步回原工程。
新增训练统计和参数审计位于lerobot.utils.pi05_training，验证位于lerobot.utils.pi05_validation；不依赖/skydata/yth/cloud_training的Python模块，不使用猴子补丁。

入口：scripts/train_pi05_package_sorting_local.sh；配置：scripts/pi05_package_sorting_local.env。
默认沿用云端八卡策略：每卡2、全局16、28562步，冻结VLM，动作专家/动作及时间投影全参训练，LoRA关闭，mask_action_padding=true，BF16+梯度检查点。每5000步及末步验证，保存周期5000。
状态/动作统计从train_only_stats.json读入，按实际数据维度校验；不是所有任务都强制11D。

旧训练脚本不修改。统计替换和审计仅在环境变量明确启用时生效，专家范围断言另由PI05_REQUIRE_EXPERT_ONLY启用；普通LoRA任务不被强制改为专家训练。
如在同一shell中手动source过新.env，启动旧任务前须清除PI05_TRAIN_STATS_FILE、PI05_SHARED_SPLIT_FILE、PI05_VAL_FREQ、PI05_PARAMETER_AUDIT、PI05_REQUIRE_EXPERT_ONLY，或换新终端。正常用bash运行新脚本不会污染父shell。

仅在GPU空闲时启动，脚本不会自动选择空闲卡，也不启动其他两个模型：

```bash
bash scripts/train_pi05_package_sorting_local.sh
# 仅有两卡时可以指定，但全局batch和等效epoch随之改变：
GPU_IDS=0,1 PI05_NUM_GPUS=2 bash scripts/train_pi05_package_sorting_local.sh
```

本机路径集中在.env，可通过同名环境变量覆盖。数据默认/skydata/data/vla_processed/package_sorting/lerobot_v3.0；模型和tokenizer复用原本本机资源；输出/skydata/yth/train/pi05_local。tokenizer默认仍在移动盘，未挂载会明确报错，不联网下载。

CPU回归（不占GPU；缓存放/tmp）：

```bash
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' PYTHONPATH=unitree_lerobot/lerobot/src /home/igs/miniconda3/envs/unitree_lerobot/bin/python -m unittest discover -s unitree_lerobot/lerobot/tests -p 'test_pi05_*local.py'
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' HF_HOME=/tmp/pi05_local_sync_hf HF_DATASETS_CACHE=/tmp/pi05_local_sync_hf/datasets /home/igs/miniconda3/envs/unitree_lerobot/bin/python scripts/audit_pi05_package_sorting.py --root /skydata/data/vla_processed/package_sorting/lerobot_v3.0 --split /skydata/data/vla_processed/package_sorting/shared_train_validation_split.json
```

验证loss为原生flow loss的逐帧平均，排除动作padding的直接loss，不等同于机器人任务成功率；此移植没有执行真实模型GPU训练或部署验收。对其他数据集的旧任务只做了通用兼容性单元测试，未遍历所有历史训练任务。
