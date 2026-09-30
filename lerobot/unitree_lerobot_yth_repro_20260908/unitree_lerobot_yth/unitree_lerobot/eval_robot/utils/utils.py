import numpy as np
import torch
import time
from typing import Any
from contextlib import nullcontext
from copy import copy
import logging
from dataclasses import dataclass, field
from lerobot.configs import parser
from lerobot.configs.policies import PreTrainedConfig
from lerobot.policies.pretrained import PreTrainedPolicy
from lerobot.processor import PolicyAction, PolicyProcessorPipeline


import logging_mp

logger_mp = logging_mp.getLogger(__name__)
logger_mp.setLevel(logging_mp.INFO)


def _sync_if_needed(device: torch.device) -> None:
    if device.type == "cuda" and torch.cuda.is_available():
        torch.cuda.synchronize(device)


def extract_observation(step: dict):
    observation = {}

    for key, value in step.items():
        if key.startswith("observation.images."):
            if isinstance(value, np.ndarray) and value.ndim == 3 and value.shape[-1] in [1, 3]:
                value = np.transpose(value, (2, 0, 1))
            observation[key] = value

        elif key == "observation.state":
            observation[key] = value

    return observation


def predict_action(
    observation: dict[str, np.ndarray],
    policy: PreTrainedPolicy,
    device: torch.device,
    preprocessor: PolicyProcessorPipeline[dict[str, Any], dict[str, Any]],
    postprocessor: PolicyProcessorPipeline[PolicyAction, PolicyAction],
    use_amp: bool,
    task: str | None = None,
    use_dataset: bool | None = False,
    robot_type: str | None = None,
):
    observation = copy(observation)
    profile: dict[str, float] = {}
    with (
        torch.inference_mode(),
        torch.autocast(device_type=device.type) if device.type == "cuda" and use_amp else nullcontext(),
    ):
        _sync_if_needed(device)
        input_start = time.perf_counter()
        # Convert to pytorch format: channel first and float32 in [0,1] with batch dimension
        for name in observation:
            if not use_dataset:
                # Skip non-tensor observations (like task strings)
                if not hasattr(observation[name], "unsqueeze"):
                    continue
                if "images" in name:
                    observation[name] = observation[name].type(torch.float32) / 255
                    observation[name] = observation[name].permute(2, 0, 1).contiguous()

            observation[name] = observation[name].unsqueeze(0).to(device)
        _sync_if_needed(device)
        profile["input_tensor_s"] = time.perf_counter() - input_start

        observation["task"] = task if task else ""
        observation["robot_type"] = robot_type if robot_type else ""

        _sync_if_needed(device)
        preprocess_start = time.perf_counter()
        observation = preprocessor(observation)
        _sync_if_needed(device)
        profile["preprocess_s"] = time.perf_counter() - preprocess_start

        # Compute the next action with the policy
        # based on the current observation
        _sync_if_needed(device)
        select_start = time.perf_counter()
        action = policy.select_action(observation)
        _sync_if_needed(device)
        profile["select_action_s"] = time.perf_counter() - select_start

        _sync_if_needed(device)
        postprocess_start = time.perf_counter()
        action = postprocessor(action)
        _sync_if_needed(device)
        profile["postprocess_s"] = time.perf_counter() - postprocess_start

        # Remove batch dimension
        action = action.squeeze(0)

        # Move to cpu, if not already the case
        _sync_if_needed(device)
        to_cpu_start = time.perf_counter()
        action = action.to("cpu")
        _sync_if_needed(device)
        profile["to_cpu_s"] = time.perf_counter() - to_cpu_start
        policy._last_predict_action_profile = profile

    return action


def reset_policy(policy: PreTrainedPolicy):
    policy.reset()


def cleanup_resources(image_info: Any):
    """Safely release image client resources for both old and new interfaces."""
    logger_mp.info("Cleaning up image resources.")
    if image_info is None:
        return

    if isinstance(image_info, tuple):
        image_client = image_info[0]
        if hasattr(image_client, "close"):
            image_client.close()
        return

    if isinstance(image_info, dict) and "shm_resources" in image_info:
        for shm in image_info["shm_resources"]:
            if shm:
                shm.close()
                shm.unlink()
        return

    if hasattr(image_info, "close"):
        image_info.close()


def to_list(x):
    if torch is not None and isinstance(x, torch.Tensor):
        return x.detach().cpu().ravel().tolist()
    if isinstance(x, np.ndarray):
        return x.ravel().tolist()
    if isinstance(x, (list, tuple)):
        return list(x)
    return [x]


def to_scalar(x):
    if torch is not None and isinstance(x, torch.Tensor):
        return float(x.detach().cpu().ravel()[0].item())
    if isinstance(x, np.ndarray):
        return float(x.ravel()[0])
    if isinstance(x, (list, tuple)):
        return float(x[0])
    return float(x)


@dataclass
class EvalRealConfig:
    repo_id: str
    policy: PreTrainedConfig | None = None

    root: str = ""
    episodes: int = 0
    frequency: float = 30.0
    episode_duration_s: float = 6.0
    return_to_zero_duration_s: float = 2.0
    handover_wait_seconds: float = 0.8
    pre_handover_wait_seconds: float = 0.8

    # Basic control parameters
    arm: str = "G1_29"  # G1_29, G1_23
    ee: str = ""  # empty string means no end-effector; otherwise dex3, dex1, inspire1, brainco
    image_host: str = "192.168.123.164"
    image_backend: str = "zmq"
    network_interface: str = ""
    ros2_head_topic: str = "/camera/color/image_raw"
    ros2_node_name: str = "unitree_eval_image_client"
    ros2_qos: str = "sensor_data"
    ros2_image_height: int = 480
    ros2_image_width: int = 640

    # Mode flags
    motion: bool = False
    headless: bool = False
    visualization: bool = False
    send_real_robot: bool = False
    arm_controller_process: bool = False
    use_dataset: bool = False
    task_override: str = ""
    interactive_task_selection: bool = False
    interactive_single_task: bool = False
    # Used by the persistent debug runner, which owns the start/stop menu.
    persistent_runner_managed: bool = False
    task_s_text: str = ""
    task_r_text: str = ""
    tokenizer_name_override: str = ""
    idle_publish_mode: str = "hold"  # hold or freeze
    arm_tau_mode: str = "gravity"  # gravity or zero
    constant_target_duration_s: float = 0.0
    # Optional final command smoothing/rate limiting. Disabled by default so
    # existing evaluation scripts retain their current behavior.
    action_smoothing_enabled: bool = False
    action_smoothing_arm_cutoff_hz: float = 1.5
    action_smoothing_waist_cutoff_hz: float = 1.0
    action_smoothing_chunk_blend_frames: int = 5
    action_velocity_limits: str = "0.90,0.50,0.80,1.20,1.50,0.18"
    action_acceleration_limits: str = "4.00,2.50,3.50,5.00,8.00,0.80"
    post_action_shoulder_roll_nudge_rad: float = 0.0
    post_action_nudge_duration_s: float = 0.3
    post_action_nudge_hold_s: float = 0.0
    left_arm_ready_pose_deg: str = ""
    right_ee_pose_from_fk: bool = False

    rename_map: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if self.image_backend not in {"zmq", "ros2"}:
            raise ValueError(f"Unsupported image_backend={self.image_backend!r}; expected 'zmq' or 'ros2'.")
        if self.ros2_qos not in {"sensor_data", "default", "reliable"}:
            raise ValueError(
                f"Unsupported ros2_qos={self.ros2_qos!r}; expected 'sensor_data', 'default', or 'reliable'."
            )
        if self.idle_publish_mode not in {"hold", "freeze"}:
            raise ValueError(
                f"Unsupported idle_publish_mode={self.idle_publish_mode!r}; expected 'hold' or 'freeze'."
            )
        if self.arm_tau_mode not in {"gravity", "zero"}:
            raise ValueError(f"Unsupported arm_tau_mode={self.arm_tau_mode!r}; expected 'gravity' or 'zero'.")
        if self.constant_target_duration_s < 0.0:
            raise ValueError("constant_target_duration_s must be >= 0.")
        if self.action_smoothing_arm_cutoff_hz <= 0.0:
            raise ValueError("action_smoothing_arm_cutoff_hz must be > 0.")
        if self.action_smoothing_waist_cutoff_hz <= 0.0:
            raise ValueError("action_smoothing_waist_cutoff_hz must be > 0.")
        if self.action_smoothing_chunk_blend_frames < 0:
            raise ValueError("action_smoothing_chunk_blend_frames must be >= 0.")
        if self.interactive_task_selection and (not self.task_s_text.strip() or not self.task_r_text.strip()):
            raise ValueError(
                "interactive_task_selection requires non-empty task_s_text and task_r_text."
            )
        if self.interactive_task_selection and self.interactive_single_task:
            raise ValueError(
                "interactive_task_selection and interactive_single_task cannot both be enabled."
            )
        if self.post_action_nudge_duration_s < 0.0:
            raise ValueError("post_action_nudge_duration_s must be >= 0.")
        if self.post_action_nudge_hold_s < 0.0:
            raise ValueError("post_action_nudge_hold_s must be >= 0.")

        # HACK: We parse again the cli args here to get the pretrained path if there was one.
        policy_path = parser.get_path_arg("policy")
        if policy_path:
            cli_overrides = parser.get_cli_overrides("policy")
            self.policy = PreTrainedConfig.from_pretrained(policy_path, cli_overrides=cli_overrides)
            self.policy.pretrained_path = policy_path
        else:
            logging.warning(
                "No pretrained path was provided, evaluated policy will be built from scratch (random weights)."
            )

    @classmethod
    def __get_path_fields__(cls) -> list[str]:
        """This enables the parser to load config from the policy using `--policy.path=local/dir`"""
        return ["policy"]
