"""G1 PI0.5 evaluation entry point with optional Real-Time Chunking."""

import logging
import time
from contextlib import nullcontext
from copy import copy
from dataclasses import asdict, dataclass
from pprint import pformat
from typing import Any

import torch

from lerobot.configs import parser
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies.factory import make_policy, make_pre_post_processors
from lerobot.processor.rename_processor import rename_stats
from lerobot.utils.utils import get_safe_torch_device, init_logging
from unitree_lerobot.eval_robot import eval_g1 as base_eval
from unitree_lerobot.eval_robot.pi05_rtc_runtime import PI05RTCConfig, PI05RTCPolicyAdapter
from unitree_lerobot.eval_robot.utils.utils import EvalRealConfig


@dataclass
class EvalRealRTCConfig(EvalRealConfig):
    max_episode_wall_time_s: float = 15.0
    run_until_q: bool = False
    # Persistent debug only: after ``run`` moves the robot to the dataset
    # initial pose, wait for an explicit ``s`` before starting inference.
    persistent_confirm_after_ready: bool = False
    rtc_enabled: bool = True
    rtc_guidance_enabled: bool = True
    rtc_use_autograd_jacobian: bool = True
    rtc_execution_horizon: int = 10
    rtc_max_guidance_weight: float = 10.0
    rtc_prefix_attention_schedule: str = "exp"
    rtc_queue_threshold: int = 30
    rtc_max_actions_during_inference: int = 10
    rtc_inference_timeout_s: float = 120.0
    rtc_latency_window: int = 100
    rtc_snapshot_dir: str = ""
    rtc_execution_log_path: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.run_until_q and not self.interactive_single_task:
            raise ValueError("run_until_q requires interactive_single_task=true.")
        # Centralize validation in the runtime config so CLI and direct usage
        # receive exactly the same checks.
        self.make_rtc_config()

    def make_rtc_config(self) -> PI05RTCConfig:
        return PI05RTCConfig(
            enabled=self.rtc_enabled,
            guidance_enabled=self.rtc_guidance_enabled,
            use_autograd_jacobian=self.rtc_use_autograd_jacobian,
            execution_horizon=self.rtc_execution_horizon,
            max_guidance_weight=self.rtc_max_guidance_weight,
            prefix_attention_schedule=self.rtc_prefix_attention_schedule,
            queue_threshold=self.rtc_queue_threshold,
            max_actions_during_inference=self.rtc_max_actions_during_inference,
            inference_timeout_s=self.rtc_inference_timeout_s,
            latency_window=self.rtc_latency_window,
        )


def predict_action_rtc(
    observation: dict[str, Any],
    policy: PI05RTCPolicyAdapter,
    device: torch.device,
    preprocessor,
    postprocessor,
    use_amp: bool,
    task: str | None = None,
    use_dataset: bool | None = False,
    robot_type: str | None = None,
):
    """Preprocess the newest observation and consume one async RTC action."""
    del postprocessor  # The worker postprocesses complete chunks before queueing them.
    observation = copy(observation)
    snapshot_observation = {
        name: value.detach().cpu().clone()
        for name, value in observation.items()
        if isinstance(value, torch.Tensor)
        and (name.startswith("observation.images.") or name == "observation.state")
    }
    snapshot_observation["observed_wall_time_ns"] = time.time_ns()
    snapshot_observation["observed_monotonic_ns"] = time.monotonic_ns()
    profile: dict[str, float] = {}
    with torch.no_grad(), (
        torch.autocast(device_type=device.type)
        if device.type == "cuda" and use_amp
        else nullcontext()
    ):
        start = time.perf_counter()
        for name in observation:
            if not use_dataset:
                if not hasattr(observation[name], "unsqueeze"):
                    continue
                if "images" in name:
                    observation[name] = observation[name].to(torch.float32) / 255
                    observation[name] = observation[name].permute(2, 0, 1).contiguous()
            observation[name] = observation[name].unsqueeze(0).to(device)
        profile["input_tensor_s"] = time.perf_counter() - start

        observation["task"] = task if task else ""
        observation["robot_type"] = robot_type if robot_type else ""
        start = time.perf_counter()
        observation = preprocessor(observation)
        profile["preprocess_s"] = time.perf_counter() - start

        start = time.perf_counter()
        action = policy.select_action(
            observation,
            snapshot_observation=snapshot_observation,
        )
        profile["select_action_s"] = time.perf_counter() - start
        policy._last_predict_action_profile = profile
        # The RTC adapter returns None for a normal episode stop (runtime q or
        # wall-time limit). Preserve that sentinel so eval_policy can leave the
        # loop cleanly instead of trying tensor operations on it.
        if action is None:
            return None
        return action.squeeze(0).to("cpu")


@parser.wrap()
def eval_main(cfg: EvalRealRTCConfig) -> None:
    logging.info(pformat(asdict(cfg)))
    device = get_safe_torch_device(cfg.policy.device, log=True)
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True

    dataset = LeRobotDataset(
        repo_id=cfg.repo_id,
        root=cfg.root if cfg.root else None,
        episodes=[cfg.episodes],
    )
    policy = make_policy(cfg=cfg.policy, ds_meta=dataset.meta)
    policy.eval()
    if hasattr(policy, "model") and hasattr(policy.model, "gradient_checkpointing_disable"):
        policy.model.gradient_checkpointing_disable()
        logging.info("Disabled gradient checkpointing for evaluation.")

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

    if not cfg.rtc_enabled:
        logging.info("RTC is disabled; using the unchanged synchronous PI0.5 evaluation path.")
        with torch.no_grad(), (
            torch.autocast(device_type=device.type) if cfg.policy.use_amp else nullcontext()
        ):
            base_eval.eval_policy(cfg, dataset, policy, preprocessor, postprocessor)
        return

    adapter = PI05RTCPolicyAdapter(
        policy,
        postprocessor,
        cfg.make_rtc_config(),
        cfg.frequency,
        max_episode_wall_time_s=0.0 if cfg.run_until_q else cfg.max_episode_wall_time_s,
        snapshot_dir=cfg.rtc_snapshot_dir,
    )
    original_predict_action = base_eval.predict_action
    base_eval.predict_action = predict_action_rtc
    logging.info(
        "RTC enabled: guidance_enabled=%s autograd_jacobian=%s execution_horizon=%d max_guidance_weight=%.3f schedule=%s "
        "queue_threshold=%d max_actions_during_inference=%d",
        cfg.rtc_guidance_enabled,
        cfg.rtc_use_autograd_jacobian,
        cfg.rtc_execution_horizon,
        cfg.rtc_max_guidance_weight,
        cfg.rtc_prefix_attention_schedule,
        cfg.rtc_queue_threshold,
        cfg.rtc_max_actions_during_inference,
    )
    if cfg.rtc_snapshot_dir:
        logging.info("RTC inference snapshots enabled: %s", cfg.rtc_snapshot_dir)
    try:
        with torch.no_grad(), (
            torch.autocast(device_type=device.type) if cfg.policy.use_amp else nullcontext()
        ):
            base_eval.eval_policy(cfg, dataset, adapter, preprocessor, postprocessor)
    finally:
        base_eval.predict_action = original_predict_action
        adapter.close()


if __name__ == "__main__":
    init_logging()
    eval_main()
