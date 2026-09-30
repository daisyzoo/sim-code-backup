"""Continuous PI0.5 RTC evaluation driven by the controlled MCP server.

The RTC sampler and asynchronous action queue live in ``pi05_rtc_runtime``.
This module only connects that runtime to MCP task lifecycle and the existing
real-robot preparation/return choreography.
"""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass

import torch

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies.factory import make_policy, make_pre_post_processors
from lerobot.processor.rename_processor import rename_stats
from lerobot.utils.utils import get_safe_torch_device
from unitree_lerobot.eval_robot.eval_g1_mcp_controlled import eval_policy_controlled_loop
from unitree_lerobot.eval_robot.eval_g1_rtc import EvalRealRTCConfig, predict_action_rtc
from unitree_lerobot.eval_robot.mcp_server.vla_controller import VLAController
from unitree_lerobot.eval_robot.pi05_rtc_runtime import PI05RTCPolicyAdapter
from unitree_lerobot.eval_robot.terminal_joint_detector import TerminalJointPoseDetector

import logging_mp

logger_mp = logging_mp.getLogger(__name__)
logger_mp.setLevel(logging_mp.INFO)


@dataclass
class EvalRealRTCMCPConfig(EvalRealRTCConfig):
    """RTC MCP configuration.

    ``episode_duration_s`` is the default requested action duration.
    ``max_episode_wall_time_s`` is the server-side hard action-duration limit.
    Both are measured from the first action, so preparation and initial
    inference do not consume the action budget.
    """

    episode_duration_s: float = 40.0
    max_episode_wall_time_s: float = 60.0
    run_until_q: bool = False
    interactive_single_task: bool = False
    terminal_joint_detector_enabled: bool = True
    terminal_joint_detector_config: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.rtc_enabled:
            raise ValueError("The RTC MCP entry requires rtc_enabled=true.")
        if self.episode_duration_s <= 0.0:
            raise ValueError("episode_duration_s must be greater than zero.")
        if self.max_episode_wall_time_s <= 0.0:
            raise ValueError("max_episode_wall_time_s must be greater than zero for MCP safety.")
        if self.terminal_joint_detector_enabled and not self.terminal_joint_detector_config:
            raise ValueError(
                "terminal_joint_detector_config is required when terminal_joint_detector_enabled=true."
            )


def run_rtc_eval_with_controller(cfg: EvalRealRTCMCPConfig, controller: VLAController) -> None:
    """Load PI0.5 once, then serve repeated continuous RTC MCP requests."""
    device = get_safe_torch_device(cfg.policy.device, log=True)
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True

    logger_mp.info("Making PI0.5 policy for continuous RTC MCP evaluation.")
    dataset = LeRobotDataset(
        repo_id=cfg.repo_id,
        root=cfg.root if cfg.root else None,
        episodes=[cfg.episodes],
    )
    policy = make_policy(cfg=cfg.policy, ds_meta=dataset.meta)
    policy.eval()
    if hasattr(policy, "model") and hasattr(policy.model, "gradient_checkpointing_disable"):
        policy.model.gradient_checkpointing_disable()
        logger_mp.info("Disabled gradient checkpointing for evaluation.")

    preprocessor_overrides = {
        "device_processor": {"device": cfg.policy.device},
        "rename_observations_processor": {"rename_map": cfg.rename_map},
    }
    if cfg.tokenizer_name_override:
        preprocessor_overrides["tokenizer_processor"] = {
            "tokenizer_name": cfg.tokenizer_name_override,
            "local_files_only": True,
        }

    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=cfg.policy,
        pretrained_path=cfg.policy.pretrained_path,
        dataset_stats=rename_stats(dataset.meta.stats, cfg.rename_map),
        preprocessor_overrides=preprocessor_overrides,
    )

    terminal_detector = (
        TerminalJointPoseDetector(cfg.terminal_joint_detector_config, cfg.frequency)
        if cfg.terminal_joint_detector_enabled
        else None
    )
    adapter = PI05RTCPolicyAdapter(
        policy,
        postprocessor,
        cfg.make_rtc_config(),
        cfg.frequency,
        max_episode_wall_time_s=cfg.episode_duration_s,
        snapshot_dir=cfg.rtc_snapshot_dir,
        external_stop_requested=lambda: controller.should_stop()
        or (terminal_detector is not None and terminal_detector.succeeded),
        enable_terminal_control=False,
    )
    logger_mp.info(
        "RTC MCP enabled: default_action_duration_s=%.1f hard_max_action_duration_s=%.1f "
        "inference_timeout_s=%.1f queue_threshold=%d execution_horizon=%d",
        cfg.episode_duration_s,
        cfg.max_episode_wall_time_s,
        cfg.rtc_inference_timeout_s,
        cfg.rtc_queue_threshold,
        cfg.rtc_execution_horizon,
    )

    try:
        with torch.no_grad(), (
            torch.autocast(device_type=device.type) if cfg.policy.use_amp else nullcontext()
        ):
            eval_policy_controlled_loop(
                cfg,
                dataset,
                controller,
                adapter,
                preprocessor,
                postprocessor,
                predict_action_fn=predict_action_rtc,
                single_chunk_per_request=False,
                max_action_duration_s=cfg.max_episode_wall_time_s,
                terminal_joint_detector=terminal_detector,
            )
    finally:
        adapter.close()
