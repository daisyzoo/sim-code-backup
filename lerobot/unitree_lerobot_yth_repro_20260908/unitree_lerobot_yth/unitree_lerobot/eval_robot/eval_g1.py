"""'
Refer to:   lerobot/lerobot/scripts/eval.py
            lerobot/lerobot/scripts/econtrol_robot.py
            lerobot/robot_devices/control_utils.py
"""

import os
import select
import sys
import termios
import time
import tty
import torch
import logging

import numpy as np
import pinocchio as pin
from pprint import pformat
from dataclasses import asdict
from pathlib import Path
from torch import nn
from contextlib import nullcontext
from typing import Any
from lerobot.policies.factory import make_policy, make_pre_post_processors
from lerobot.utils.utils import (
    get_safe_torch_device,
    init_logging,
)
from lerobot.configs import parser
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies.pretrained import PreTrainedPolicy
from multiprocessing.sharedctypes import SynchronizedArray
from lerobot.processor.rename_processor import rename_stats
from lerobot.processor import (
    PolicyAction,
    PolicyProcessorPipeline,
)
from unitree_lerobot.eval_robot.make_robot import (
    setup_image_client,
    setup_robot_interface,
    process_images_and_observations,
)
from unitree_lerobot.eval_robot.utils.utils import (
    cleanup_resources,
    extract_observation,
    predict_action,
    to_list,
    to_scalar,
    EvalRealConfig,
)
from unitree_lerobot.eval_robot.utils.rerun_visualizer import RerunLogger, visualization_data
from unitree_lerobot.eval_robot.rtc_execution_log import RTCExecutionLogger
from unitree_lerobot.eval_robot.action_smoothing import (
    ActionSmoothingConfig,
    JointActionSmoother,
)

import logging_mp

logger_mp = logging_mp.getLogger(__name__)
logger_mp.setLevel(logging_mp.INFO)

G1_23_URDF_PATH = Path(__file__).resolve().parents[0] / "assets/g1/g1_body23.urdf"
G1_23_RIGHT_ARM_Q_SLICE = slice(18, 23)


def _format_wall_time(ts: float | None = None) -> str:
    if ts is None:
        ts = time.time()
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


def _enable_runtime_q() -> tuple[int, list[Any]] | None:
    """Enable nonblocking ``q`` handling for the synchronous continuous mode."""
    if not sys.stdin.isatty():
        logger_mp.warning("No TTY available; use Ctrl+C to stop the continuous synchronous run.")
        return None
    try:
        fd = sys.stdin.fileno()
        settings = termios.tcgetattr(fd)
        tty.setcbreak(fd)
        return fd, settings
    except (OSError, termios.error):
        logger_mp.warning("Could not enable runtime q handling; use Ctrl+C to stop the run.")
        return None


def _runtime_q_requested(runtime_q: tuple[int, list[Any]] | None) -> bool:
    if runtime_q is None:
        return False
    try:
        readable, _, _ = select.select([runtime_q[0]], [], [], 0.0)
        return bool(readable) and os.read(runtime_q[0], 1).decode(errors="ignore").lower() == "q"
    except OSError:
        return False


def _restore_runtime_q(runtime_q: tuple[int, list[Any]] | None) -> None:
    if runtime_q is None:
        return
    try:
        termios.tcsetattr(runtime_q[0], termios.TCSADRAIN, runtime_q[1])
    except (OSError, termios.error):
        logger_mp.warning("Failed to restore terminal settings after continuous synchronous run.")


def _parse_joint_pose_degrees(pose_text: str, expected_len: int) -> np.ndarray | None:
    pose_text = pose_text.strip()
    if not pose_text:
        return None
    values = [item.strip() for item in pose_text.split(",") if item.strip()]
    if len(values) != expected_len:
        raise ValueError(
            f"left_arm_ready_pose_deg expects {expected_len} comma-separated values, got {len(values)}: {pose_text!r}"
        )
    return np.deg2rad(np.asarray([float(item) for item in values], dtype=np.float32))


def _build_robot_state(current_arm_q, arm_ctrl, arm_dof: int, waist_dof: int, left_ee_state, right_ee_state):
    parts = [np.asarray(current_arm_q[:arm_dof], dtype=np.float32)]
    if waist_dof > 0 and hasattr(arm_ctrl, "get_current_waist_yaw_q"):
        parts.append(np.asarray([arm_ctrl.get_current_waist_yaw_q()], dtype=np.float32))
    if left_ee_state.size > 0:
        parts.append(np.asarray(left_ee_state, dtype=np.float32))
    if right_ee_state.size > 0:
        parts.append(np.asarray(right_ee_state, dtype=np.float32))
    return np.concatenate(parts, axis=0)


class G1_23RightEeFk:
    def __init__(self) -> None:
        self.model = pin.buildModelFromUrdf(str(G1_23_URDF_PATH))
        self.model.addFrame(
            pin.Frame(
                "R_ee",
                self.model.getJointId("right_wrist_roll_joint"),
                pin.SE3(np.eye(3), np.array([0.20, 0.0, 0.0])),
                pin.FrameType.OP_FRAME,
            )
        )
        self.data = self.model.createData()
        self.frame_id = self.model.getFrameId("R_ee")

    def compute(self, right_arm_q: np.ndarray) -> np.ndarray:
        if right_arm_q.shape[0] != 5:
            raise ValueError(f"Expected right arm q length 5 for G1_23 RightArm5 FK, got {right_arm_q.shape[0]}")
        q = np.zeros(self.model.nq)
        q[G1_23_RIGHT_ARM_Q_SLICE] = np.asarray(right_arm_q, dtype=np.float64)
        pin.forwardKinematics(self.model, self.data, q)
        pin.updateFramePlacements(self.model, self.data)
        transform = self.data.oMf[self.frame_id]
        quat_xyzw = pin.Quaternion(transform.rotation).coeffs()
        return np.concatenate([transform.translation, quat_xyzw]).astype(np.float32)


def _split_robot_action(action_np, arm_dof: int, waist_dof: int, ee_dof: int):
    offset = 0
    arm_action = action_np[offset : offset + arm_dof]
    offset += arm_dof

    waist_action = None
    if waist_dof > 0:
        waist_action = float(action_np[offset])
        offset += waist_dof

    left_ee_action = right_ee_action = np.array([])
    if ee_dof > 0:
        left_ee_action = action_np[offset : offset + ee_dof]
        offset += ee_dof
        right_ee_action = action_np[offset : offset + ee_dof]

    return arm_action, waist_action, left_ee_action, right_ee_action


def _new_jitter_stats() -> dict[str, float]:
    return {
        "count": 0,
        "cmd_delta_sum": 0.0,
        "cmd_delta_max": 0.0,
        "q_delta_sum": 0.0,
        "q_delta_max": 0.0,
        "track_err_max": 0.0,
        "actual_dq_max": 0.0,
        "chunk_refills": 0,
        "chunk_cmd_delta_max": 0.0,
        "slow_policy": 0,
    }


def _update_jitter_stats(
    stats: dict[str, float],
    *,
    cmd_delta_max: float | None,
    q_delta_max: float | None,
    track_err_max: float,
    actual_dq_max: float | None,
    chunk_refill: bool,
    slow_policy: bool,
) -> None:
    stats["count"] += 1
    if cmd_delta_max is not None:
        stats["cmd_delta_sum"] += cmd_delta_max
        stats["cmd_delta_max"] = max(stats["cmd_delta_max"], cmd_delta_max)
        if chunk_refill:
            stats["chunk_cmd_delta_max"] = max(stats["chunk_cmd_delta_max"], cmd_delta_max)
    if q_delta_max is not None:
        stats["q_delta_sum"] += q_delta_max
        stats["q_delta_max"] = max(stats["q_delta_max"], q_delta_max)
    stats["track_err_max"] = max(stats["track_err_max"], track_err_max)
    if actual_dq_max is not None:
        stats["actual_dq_max"] = max(stats["actual_dq_max"], actual_dq_max)
    if chunk_refill:
        stats["chunk_refills"] += 1
    if slow_policy:
        stats["slow_policy"] += 1


def _log_jitter_stats(stats: dict[str, float], episode_idx: int, step_idx: int, prefix: str) -> None:
    count = max(1, int(stats["count"]))
    logger_mp.info(
        "%s episode=%d step=%d samples=%d cmd_delta_avg=%.5f cmd_delta_max=%.5f "
        "q_delta_avg=%.5f q_delta_max=%.5f track_err_max=%.5f actual_dq_max=%.5f "
        "chunk_refills=%d chunk_cmd_delta_max=%.5f slow_policy=%d",
        prefix,
        episode_idx,
        step_idx,
        count,
        stats["cmd_delta_sum"] / count,
        stats["cmd_delta_max"],
        stats["q_delta_sum"] / count,
        stats["q_delta_max"],
        stats["track_err_max"],
        stats["actual_dq_max"],
        int(stats["chunk_refills"]),
        stats["chunk_cmd_delta_max"],
        int(stats["slow_policy"]),
    )


def _compute_arm_tau(arm_ik, arm_q: np.ndarray, arm_tau_mode: str) -> np.ndarray:
    if arm_tau_mode == "zero":
        return np.zeros_like(np.asarray(arm_q), dtype=np.float32)
    if arm_tau_mode == "gravity":
        return arm_ik.solve_tau(arm_q)
    raise ValueError(f"Unsupported arm_tau_mode={arm_tau_mode!r}")


def _run_constant_target_diagnostic(
    *,
    cfg: EvalRealConfig,
    arm_ctrl,
    arm_ik,
    arm_dof: int,
    waist_dof: int,
    episode_idx: int,
) -> None:
    target_arm_q = np.asarray(arm_ctrl.get_current_dual_arm_q()[:arm_dof], dtype=np.float32).copy()
    target_waist_q = float(arm_ctrl.get_current_waist_yaw_q()) if waist_dof > 0 else None
    target_steps = max(1, int(round(cfg.constant_target_duration_s * cfg.frequency)))
    stats = _new_jitter_stats()
    prev_arm_q = None
    start_time = time.perf_counter()

    logger_mp.info(
        "CONSTANT_TARGET_DIAG_START episode=%d duration_s=%.3f steps=%d tau_mode=%s target_norm=%.5f waist=%s",
        episode_idx,
        cfg.constant_target_duration_s,
        target_steps,
        cfg.arm_tau_mode,
        float(np.linalg.norm(target_arm_q)),
        "None" if target_waist_q is None else f"{target_waist_q:.5f}",
    )

    for step_idx in range(1, target_steps + 1):
        loop_start = time.perf_counter()
        current_arm_q = np.asarray(arm_ctrl.get_current_dual_arm_q()[:arm_dof], dtype=np.float32)
        q_delta_max = None if prev_arm_q is None else float(np.max(np.abs(current_arm_q - prev_arm_q)))
        track_err_max = float(np.max(np.abs(target_arm_q - current_arm_q)))
        actual_dq_max = None
        if hasattr(arm_ctrl, "get_current_dual_arm_dq"):
            actual_dq_max = float(np.max(np.abs(np.asarray(arm_ctrl.get_current_dual_arm_dq())[:arm_dof])))

        tau = _compute_arm_tau(arm_ik, target_arm_q, cfg.arm_tau_mode)
        arm_ctrl.ctrl_dual_arm(target_arm_q, tau, target_waist_q)
        _update_jitter_stats(
            stats,
            cmd_delta_max=0.0,
            q_delta_max=q_delta_max,
            track_err_max=track_err_max,
            actual_dq_max=actual_dq_max,
            chunk_refill=False,
            slow_policy=False,
        )
        prev_arm_q = current_arm_q.copy()
        time.sleep(max(0, (1.0 / cfg.frequency) - (time.perf_counter() - loop_start)))

    _log_jitter_stats(stats, episode_idx, target_steps, "CONSTANT_TARGET_DIAG_FINAL")
    logger_mp.info(
        "CONSTANT_TARGET_DIAG_DONE episode=%d elapsed_s=%.3f tau_mode=%s",
        episode_idx,
        time.perf_counter() - start_time,
        cfg.arm_tau_mode,
    )


def _move_controlled_joints_smoothly(
    arm_ctrl,
    arm_ik,
    arm_target,
    waist_target,
    frequency: float,
    duration_s: float,
):
    stage_start_perf = time.perf_counter()
    stage_start_wall = time.time()
    current_arm_q = np.asarray(arm_ctrl.get_current_dual_arm_q(), dtype=np.float32)
    current_waist_q = float(arm_ctrl.get_current_waist_yaw_q()) if waist_target is not None else None

    arm_target = np.asarray(arm_target, dtype=np.float32)
    steps = max(1, int(round(duration_s * frequency)))
    logger_mp.info(
        "Smooth move start at %s: duration_s=%.2f steps=%d waist_target=%s",
        _format_wall_time(stage_start_wall),
        duration_s,
        steps,
        "None" if waist_target is None else f"{waist_target:.4f}",
    )
    for i in range(1, steps + 1):
        alpha = i / steps
        arm_q = current_arm_q + alpha * (arm_target - current_arm_q)
        if waist_target is not None and current_waist_q is not None:
            waist_q = current_waist_q + alpha * (float(waist_target) - current_waist_q)
        else:
            waist_q = None
        tau = arm_ik.solve_tau(arm_q)
        arm_ctrl.ctrl_dual_arm(arm_q, tau, waist_q)
        time.sleep(max(0.0, 1.0 / frequency))
    logger_mp.info(
        "Smooth move complete at %s: elapsed_s=%.3f",
        _format_wall_time(),
        time.perf_counter() - stage_start_perf,
    )


def _build_side_waypoint_q(current_q: np.ndarray) -> np.ndarray:
    side_waypoint_q = np.asarray(current_q, dtype=np.float32).copy()
    if side_waypoint_q.shape[0] >= 10:
        side_waypoint_q[1] = 1.30
        side_waypoint_q[6] = -1.30
    elif side_waypoint_q.shape[0] >= 5:
        side_waypoint_q[1] = -1.30
    return side_waypoint_q


def _build_prepare_side_raise_waypoint_q(current_q: np.ndarray, target_q: np.ndarray) -> np.ndarray:
    """Raise arms from thigh-side to near side-raise without bending elbows."""
    side_raise_q = np.asarray(current_q, dtype=np.float32).copy()
    if side_raise_q.shape[0] >= 10:
        side_raise_q[0] = 0.0
        side_raise_q[1] = 1.30
        side_raise_q[3] = current_q[3]
        side_raise_q[5] = 0.0
        side_raise_q[6] = -1.30
        side_raise_q[8] = current_q[8]
    elif side_raise_q.shape[0] >= 5:
        side_raise_q[0] = 0.0
        side_raise_q[1] = -1.30
        side_raise_q[3] = current_q[3]
    return side_raise_q


def _build_prepare_diagonal_front_raise_waypoint_q(current_q: np.ndarray, target_q: np.ndarray) -> np.ndarray:
    """Move from side-raise to a 45-degree diagonal-front raise while keeping elbows straight."""
    diagonal_front_raise_q = np.asarray(current_q, dtype=np.float32).copy()
    if diagonal_front_raise_q.shape[0] >= 10:
        diagonal_front_raise_q[0] = -0.78
        diagonal_front_raise_q[1] = 0.92
        diagonal_front_raise_q[2] = 0.0
        diagonal_front_raise_q[3] = current_q[3]
        diagonal_front_raise_q[5] = -0.78
        diagonal_front_raise_q[6] = -0.92
        diagonal_front_raise_q[7] = 0.0
        diagonal_front_raise_q[8] = current_q[8]
    elif diagonal_front_raise_q.shape[0] >= 5:
        diagonal_front_raise_q[0] = -0.78
        diagonal_front_raise_q[1] = -0.92
        diagonal_front_raise_q[2] = 0.0
        diagonal_front_raise_q[3] = current_q[3]
        diagonal_front_raise_q[4] = current_q[4]
    return diagonal_front_raise_q


def _move_controlled_joints_via_prepare_waypoints(
    arm_ctrl,
    arm_ik,
    arm_target,
    waist_target,
    frequency: float,
    duration_s: float,
):
    current_arm_q = np.asarray(arm_ctrl.get_current_dual_arm_q(), dtype=np.float32)
    current_waist_q = float(arm_ctrl.get_current_waist_yaw_q()) if waist_target is not None else None
    arm_target = np.asarray(arm_target, dtype=np.float32)
    side_raise_q = _build_prepare_side_raise_waypoint_q(current_arm_q, arm_target)
    diagonal_front_raise_q = _build_prepare_diagonal_front_raise_waypoint_q(current_arm_q, arm_target)

    stage1_s = max(1.0, duration_s * 0.40)
    stage2_s = max(0.8, duration_s * 0.35)
    stage3_s = max(0.8, duration_s * 0.25)

    logger_mp.info(
        "Prepare waypoint move start at %s: thigh-side -> side-raise -> diagonal-front-raise -> target, stage_s=(%.2f, %.2f, %.2f)",
        _format_wall_time(),
        stage1_s,
        stage2_s,
        stage3_s,
    )
    _move_controlled_joints_smoothly(
        arm_ctrl,
        arm_ik,
        side_raise_q,
        current_waist_q,
        frequency,
        stage1_s,
    )
    time.sleep(0.2)
    _move_controlled_joints_smoothly(
        arm_ctrl,
        arm_ik,
        diagonal_front_raise_q,
        waist_target,
        frequency,
        stage2_s,
    )
    time.sleep(0.2)
    _move_controlled_joints_smoothly(
        arm_ctrl,
        arm_ik,
        arm_target,
        waist_target,
        frequency,
        stage3_s,
    )


def _move_controlled_joints_via_side_waypoint(
    arm_ctrl,
    arm_ik,
    arm_target,
    waist_target,
    frequency: float,
    duration_s: float,
):
    current_arm_q = np.asarray(arm_ctrl.get_current_dual_arm_q(), dtype=np.float32)
    current_waist_q = float(arm_ctrl.get_current_waist_yaw_q()) if waist_target is not None else None
    side_waypoint_q = _build_side_waypoint_q(current_arm_q)
    first_stage_s = max(1.5, duration_s * 0.55)
    second_stage_s = max(1.2, duration_s * 0.45)
    logger_mp.info(
        "Waypoint move start at %s: side-raise then target, first_stage_s=%.2f second_stage_s=%.2f",
        _format_wall_time(),
        first_stage_s,
        second_stage_s,
    )
    _move_controlled_joints_smoothly(
        arm_ctrl,
        arm_ik,
        side_waypoint_q,
        current_waist_q,
        frequency,
        first_stage_s,
    )
    time.sleep(0.3)
    _move_controlled_joints_smoothly(
        arm_ctrl,
        arm_ik,
        arm_target,
        waist_target,
        frequency,
        second_stage_s,
    )


def eval_policy(
    cfg: EvalRealConfig,
    dataset: LeRobotDataset,
    policy: PreTrainedPolicy | None = None,
    preprocessor: PolicyProcessorPipeline[dict[str, Any], dict[str, Any]] | None = None,
    postprocessor: PolicyProcessorPipeline[PolicyAction, PolicyAction] | None = None,
):
    assert isinstance(policy, nn.Module), "Policy must be a PyTorch nn module."

    logger_mp.info(f"Arguments: {cfg}")

    if cfg.visualization:
        model_image_keys = tuple(getattr(getattr(policy, "config", None), "image_features", ()))
        rerun_logger = RerunLogger(
            image_keys=model_image_keys or None,
            log_state=False,
            log_action=True,
        )
        logger_mp.info(
            "Rerun visualization enabled: images=%s action=policy_action state=false",
            model_image_keys or "all observation image keys",
        )

    # Reset policy and processor if they are provided
    if policy is not None and preprocessor is not None and postprocessor is not None:
        policy.reset()
        preprocessor.reset()
        postprocessor.reset()

    image_info = None
    robot_interface = None
    runtime_q = None
    try:
        # --- Setup Phase ---
        if cfg.use_dataset:
            image_client, camera_config = None, None
            logger_mp.info("Dataset observation mode enabled; live image client is not started.")
        else:
            image_client, camera_config = setup_image_client(cfg)
            image_info = (image_client, camera_config)
        robot_interface = setup_robot_interface(cfg)

        # Unpack interfaces for convenience
        arm_ctrl, arm_ik, ee_shared_mem, arm_dof, waist_dof, ee_dof = (
            robot_interface[key] for key in ["arm_ctrl", "arm_ik", "ee_shared_mem", "arm_dof", "waist_dof", "ee_dof"]
        )
        rtc_execution_logger = RTCExecutionLogger(
            str(getattr(cfg, "rtc_execution_log_path", ""))
        )
        if rtc_execution_logger.enabled:
            logger_mp.info("RTC executed-action JSONL logging enabled: %s", rtc_execution_logger.path)
        action_smoothing_config = ActionSmoothingConfig(
            enabled=cfg.action_smoothing_enabled,
            frequency=cfg.frequency,
            arm_dof=arm_dof,
            waist_dof=waist_dof,
            arm_cutoff_hz=cfg.action_smoothing_arm_cutoff_hz,
            waist_cutoff_hz=cfg.action_smoothing_waist_cutoff_hz,
            chunk_blend_frames=cfg.action_smoothing_chunk_blend_frames,
            velocity_limits=cfg.action_velocity_limits,
            acceleration_limits=cfg.action_acceleration_limits,
        )
        action_smoothing_config.validate()
        logger_mp.info(
            "Action smoothing enabled=%s arm_cutoff_hz=%.2f waist_cutoff_hz=%.2f "
            "chunk_blend_frames=%d velocity_limits=%s acceleration_limits=%s",
            action_smoothing_config.enabled,
            action_smoothing_config.arm_cutoff_hz,
            action_smoothing_config.waist_cutoff_hz,
            action_smoothing_config.chunk_blend_frames,
            cfg.action_velocity_limits,
            cfg.action_acceleration_limits,
        )
        right_ee_fk = G1_23RightEeFk() if cfg.right_ee_pose_from_fk else None
        if right_ee_fk is not None:
            logger_mp.info(
                "right_ee_pose_from_fk enabled: appending G1-23 R_ee FK pose to observation.state; "
                "predicted eepose action dimensions are not sent to the robot."
            )
        if hasattr(arm_ctrl, "set_idle_publish_mode"):
            arm_ctrl.set_idle_publish_mode(cfg.idle_publish_mode)
        if hasattr(arm_ctrl, "set_episode_active"):
            arm_ctrl.set_episode_active(False)

        # Get initial pose from the first step of the dataset
        from_idx = dataset.meta.episodes["dataset_from_index"][0]
        to_idx = dataset.meta.episodes["dataset_to_index"][0]
        step = dataset[from_idx]
        init_state = step["observation.state"].cpu().numpy()
        init_arm_pose = init_state[:arm_dof]
        init_waist_yaw = float(init_state[arm_dof]) if waist_dof > 0 else None
        left_arm_ready_pose = _parse_joint_pose_degrees(cfg.left_arm_ready_pose_deg, expected_len=5)
        task_text = cfg.task_override if cfg.task_override else step["task"]
        dataset_episode_steps = int(to_idx - from_idx)
        run_until_q = bool(getattr(cfg, "run_until_q", False))
        if run_until_q:
            target_episode_steps = None
            target_episode_duration_s = None
            episode_timeout_s = 0.0
            logger_mp.info(
                "Loaded dataset episode with dataset_steps=%d; continuous mode has no action-count or wall-time limit.",
                dataset_episode_steps,
            )
        else:
            target_episode_steps = max(1, int(round(cfg.episode_duration_s * cfg.frequency)))
            target_episode_duration_s = target_episode_steps / cfg.frequency
            configured_wall_timeout_s = float(getattr(cfg, "max_episode_wall_time_s", 0.0))
            if configured_wall_timeout_s > 0.0:
                episode_timeout_s = configured_wall_timeout_s
            else:
                timeout_slack_s = max(5.0, target_episode_duration_s)
                episode_timeout_s = target_episode_duration_s + timeout_slack_s
            logger_mp.info(
                "Loaded dataset episode with dataset_steps=%d target_episode_steps=%d target_duration_s=%.3f configured_duration_s=%.3f timeout_s=%.3f",
                dataset_episode_steps,
                target_episode_steps,
                target_episode_duration_s,
                cfg.episode_duration_s,
                episode_timeout_s,
            )

        if cfg.send_real_robot:
            if cfg.motion:
                logger_mp.info(
                    "Motion mode startup: ensure app service 'g1_arm_example' is closed, wait for motion-controller pose, then hand over to arm_sdk."
                )
                settled = arm_ctrl.wait_for_motion_controller_pose(
                    stable_seconds=cfg.pre_handover_wait_seconds,
                    timeout_s=max(cfg.pre_handover_wait_seconds + 4.0, 5.0),
                )
                if not settled:
                    logger_mp.warning(
                        "Motion-controlled upper-body pose did not fully settle before handover; continuing with latest pose."
                    )
                arm_ctrl.start_motion_handover(ramp_duration_s=cfg.handover_wait_seconds)
                handover_ready = True
                if hasattr(arm_ctrl, "wait_for_motion_weight"):
                    handover_ready = arm_ctrl.wait_for_motion_weight(
                        1.0,
                        timeout_s=max(cfg.handover_wait_seconds + 2.0, 3.0),
                    )
                if not handover_ready:
                    logger_mp.warning(
                        "Motion handover weight did not reach arm_sdk ownership within timeout; continuing after conservative wait."
                    )
                    time.sleep(max(cfg.handover_wait_seconds, 1.0))
                if hasattr(arm_ctrl, "set_left_lock_q"):
                    current_full_arm_q = np.asarray(robot_interface["arm_ctrl"]._base.get_current_dual_arm_q(), dtype=np.float32)
                    arm_ctrl.set_left_lock_q(current_full_arm_q[:5])
                    logger_mp.info(
                        "Refreshed left-arm lock after motion handover at %s: q=%s",
                        _format_wall_time(),
                        np.array2string(current_full_arm_q[:5], precision=4, suppress_small=True),
                    )
                logger_mp.info(
                    "Motion mode startup: arm_sdk ownership acquired, moving through side-raise waypoint to dataset initial pose at %s.",
                    _format_wall_time(),
                )
                if hasattr(arm_ctrl, "set_episode_active"):
                    arm_ctrl.set_episode_active(True)
                _move_controlled_joints_via_side_waypoint(
                    arm_ctrl,
                    arm_ik,
                    init_arm_pose,
                    init_waist_yaw,
                    cfg.frequency,
                    cfg.return_to_zero_duration_s,
                )
                if hasattr(arm_ctrl, "set_episode_active"):
                    arm_ctrl.set_episode_active(False)
            elif hasattr(robot_interface["arm_ctrl"], "move_all_joints_to_zero_and_lock_non_arm_waist"):
                init_zero_stage_start = time.perf_counter()
                logger_mp.info(
                    "Initializing robot at %s: return whole body to zero and lock non-arm / non-waist joints...",
                    _format_wall_time(),
                )
                robot_interface["arm_ctrl"].move_all_joints_to_zero_and_lock_non_arm_waist(
                    duration_s=cfg.return_to_zero_duration_s
                )
                logger_mp.info(
                    "Robot initialization zero-lock complete at %s: elapsed_s=%.3f",
                    _format_wall_time(),
                    time.perf_counter() - init_zero_stage_start,
                )

        interactive_mode = cfg.interactive_task_selection or cfg.interactive_single_task
        if not interactive_mode and not cfg.persistent_runner_managed:
            if cfg.send_real_robot:
                user_input = input(
                    f"Enter 's' to start automatic {cfg.episode_duration_s:.1f}s real-robot evaluation cycles: "
                )
            else:
                user_input = input(
                    f"Enter 's' to start automatic {cfg.episode_duration_s:.1f}s dry-run evaluation cycles: "
                )
            print(f"user_input: {user_input}")
            if user_input.lower() != "s":
                logger_mp.info("Startup command is not 's'; exit without starting evaluation.")
                return

        episode_idx = 0
        while True:
            if cfg.interactive_single_task:
                run_mode = "real robot" if cfg.send_real_robot else "dry run"
                duration_label = "until q" if run_until_q else f"{cfg.episode_duration_s:.1f}s"
                user_input = input(
                    f"\nSelect the next {run_mode} run "
                    f"({duration_label}): [s] start, [q] quit: "
                ).strip().lower()
                if user_input == "s":
                    task_name = "single_task"
                elif user_input in {"q", "quit", "exit"}:
                    logger_mp.info("Single-task selection received %r; exiting evaluation.", user_input)
                    break
                else:
                    logger_mp.warning("Unknown command %r; expected s or q.", user_input)
                    continue
                logger_mp.info(
                    "Interactive single task selected: command=%s task=%s text=%r",
                    user_input,
                    task_name,
                    task_text,
                )
            elif cfg.interactive_task_selection:
                run_mode = "real robot" if cfg.send_real_robot else "dry run"
                user_input = input(
                    f"\nSelect the next {run_mode} task "
                    f"({cfg.episode_duration_s:.1f}s): [s] cup pick, [r] lift bag, [q] quit: "
                ).strip().lower()
                if user_input == "s":
                    task_text = cfg.task_s_text
                    task_name = "cup_pick"
                elif user_input == "r":
                    task_text = cfg.task_r_text
                    task_name = "lift_bag"
                elif user_input in {"q", "quit", "exit"}:
                    logger_mp.info("Interactive task selection received %r; exiting evaluation.", user_input)
                    break
                else:
                    logger_mp.warning("Unknown task command %r; expected s, r, or q.", user_input)
                    continue
                logger_mp.info(
                    "Interactive task selected: command=%s task=%s text=%r",
                    user_input,
                    task_name,
                    task_text,
                )

            if policy is not None and preprocessor is not None and postprocessor is not None:
                policy.reset()
                preprocessor.reset()
                postprocessor.reset()

            full_state = None
            step_idx = 0
            episode_boundary_start = time.perf_counter()
            episode_boundary_start_wall = _format_wall_time()

            if cfg.send_real_robot and episode_idx == 0 and not cfg.motion:
                move_to_init_start = time.perf_counter()
                logger_mp.info(
                    "Episode %d boundary start at %s: moving controlled joints to dataset initial pose...",
                    episode_idx,
                    episode_boundary_start_wall,
                )
                _move_controlled_joints_smoothly(
                    robot_interface["arm_ctrl"],
                    robot_interface["arm_ik"],
                    init_arm_pose,
                    init_waist_yaw,
                    cfg.frequency,
                    cfg.return_to_zero_duration_s,
                )
                logger_mp.info(
                    "Episode %d initial-pose move complete at %s: elapsed_s=%.3f boundary_elapsed_s=%.3f",
                    episode_idx,
                    _format_wall_time(),
                    time.perf_counter() - move_to_init_start,
                    time.perf_counter() - episode_boundary_start,
                )
            elif cfg.send_real_robot:
                logger_mp.info(
                    "Episode %d boundary start at %s: skip initial-pose move because previous episode already ended at dataset initial pose.",
                    episode_idx,
                    episode_boundary_start_wall,
                )

            if cfg.constant_target_duration_s > 0.0:
                _run_constant_target_diagnostic(
                    cfg=cfg,
                    arm_ctrl=arm_ctrl,
                    arm_ik=arm_ik,
                    arm_dof=arm_dof,
                    waist_dof=waist_dof,
                    episode_idx=episode_idx,
                )
                break

            loop_mode = "real-robot" if cfg.send_real_robot else "dry-run"
            if run_until_q:
                logger_mp.info(
                    "Starting continuous %s evaluation loop at %.1f Hz; press q to stop the current run.",
                    loop_mode,
                    cfg.frequency,
                )
                runtime_q = _enable_runtime_q()
            else:
                logger_mp.info(
                    "Starting %s evaluation loop at %.1f Hz with target_steps=%d target_duration_s=%.3f timeout_s=%.3f.",
                    loop_mode,
                    cfg.frequency,
                    target_episode_steps,
                    target_episode_duration_s,
                    episode_timeout_s,
                )
            last_heartbeat_time = time.perf_counter()
            last_jitter_log_time = time.perf_counter()
            episode_start_time = None
            image_missing_start_time = None
            prev_arm_action = None
            prev_current_arm_q = None
            action_smoother = JointActionSmoother(action_smoothing_config)
            jitter_stats = _new_jitter_stats()
            if hasattr(arm_ctrl, "set_episode_active"):
                arm_ctrl.set_episode_active(True)

            while True:
                if run_until_q and _runtime_q_requested(runtime_q):
                    logger_mp.info("Runtime q received; stopping the current evaluation run.")
                    break
                if target_episode_steps is not None and step_idx >= target_episode_steps:
                    elapsed_after_first_action = (
                        0.0 if episode_start_time is None else time.perf_counter() - episode_start_time
                    )
                    logger_mp.info(
                        "Episode %d finished after sending %d/%d actions in %.3fs.",
                        episode_idx,
                        step_idx,
                        target_episode_steps,
                        elapsed_after_first_action,
                    )
                    break
                if (
                    not run_until_q
                    and episode_start_time is not None
                    and (time.perf_counter() - episode_start_time) >= episode_timeout_s
                ):
                    logger_mp.warning(
                        "Episode %d timed out after %.3fs before completing all target steps (%d/%d).",
                        episode_idx,
                        time.perf_counter() - episode_start_time,
                        step_idx,
                        target_episode_steps,
                    )
                    break

                loop_start_time = time.perf_counter()
                observation_start_time = time.perf_counter()
                if cfg.use_dataset:
                    dataset_step_idx = from_idx + min(step_idx, dataset_episode_steps - 1)
                    dataset_step = dataset[dataset_step_idx]
                    observation = extract_observation(dataset_step)
                    dataset_state = dataset_step["observation.state"]
                    if isinstance(dataset_state, torch.Tensor):
                        dataset_state = dataset_state.detach().cpu().numpy()
                    current_arm_q = np.asarray(dataset_state, dtype=np.float32)[:arm_dof]
                else:
                    observation, current_arm_q = process_images_and_observations(
                        image_client, camera_config, arm_ctrl
                    )
                observation_elapsed = time.perf_counter() - observation_start_time
                if current_arm_q is None:
                    logger_mp.warning("Current arm state is unavailable; skip this cycle.")
                    time.sleep(max(0, (1.0 / cfg.frequency) - (time.perf_counter() - loop_start_time)))
                    continue
                has_image_observation = any(
                    key.startswith("observation.images.") and value is not None
                    for key, value in observation.items()
                )
                if not has_image_observation:
                    now = time.perf_counter()
                    if image_missing_start_time is None:
                        image_missing_start_time = now
                    missing_elapsed = now - image_missing_start_time
                    image_wait_timeout_s = max(5.0, episode_timeout_s)
                    if missing_elapsed >= image_wait_timeout_s:
                        raise RuntimeError(
                            "No valid image observation received for "
                            f"{missing_elapsed:.3f}s. Check image_server, IMAGE_HOST, and cam_config_client.yaml."
                        )
                    if missing_elapsed == 0.0 or int(missing_elapsed * cfg.frequency) % max(1, int(cfg.frequency)) == 0:
                        logger_mp.warning(
                            "No valid image observation; waiting for camera frame before policy inference "
                            "(elapsed=%.3fs timeout=%.3fs).",
                            missing_elapsed,
                            image_wait_timeout_s,
                        )
                    time.sleep(max(0, (1.0 / cfg.frequency) - (time.perf_counter() - loop_start_time)))
                    continue
                image_missing_start_time = None

                left_ee_state = right_ee_state = np.array([])
                if cfg.ee:
                    with ee_shared_mem["lock"]:
                        full_state = np.array(ee_shared_mem["state"][:])
                        left_ee_state = full_state[:ee_dof]
                        right_ee_state = full_state[ee_dof:]
                elif right_ee_fk is not None:
                    right_ee_state = right_ee_fk.compute(np.asarray(current_arm_q[:arm_dof], dtype=np.float32))
                if not cfg.use_dataset:
                    state_tensor = torch.from_numpy(
                        _build_robot_state(current_arm_q, arm_ctrl, arm_dof, waist_dof, left_ee_state, right_ee_state)
                    ).float()
                    observation["observation.state"] = state_tensor

                queue_len_before = None
                if hasattr(policy, "_action_queue"):
                    queue_len_before = len(policy._action_queue)
                control_diag_supported = hasattr(arm_ctrl, "get_control_loop_diagnostics")
                if control_diag_supported:
                    arm_ctrl.get_control_loop_diagnostics(reset=True)
                policy_process_cpu_start = time.process_time()
                policy_start_time = time.perf_counter()
                action = predict_action(
                    observation,
                    policy,
                    get_safe_torch_device(policy.config.device),
                    preprocessor,
                    postprocessor,
                    policy.config.use_amp,
                    task_text,
                    use_dataset=cfg.use_dataset,
                    robot_type=None,
                )
                policy_elapsed = time.perf_counter() - policy_start_time
                policy_process_cpu_s = time.process_time() - policy_process_cpu_start
                control_diag = arm_ctrl.get_control_loop_diagnostics() if control_diag_supported else None
                if action is None:
                    stop_reason = getattr(policy, "episode_stop_reason", "policy requested stop")
                    logger_mp.info(
                        "Episode %d stopped before the next action: %s",
                        episode_idx,
                        stop_reason,
                    )
                    break
                queue_len_after = None
                if hasattr(policy, "_action_queue"):
                    queue_len_after = len(policy._action_queue)
                action_np = action.cpu().numpy()

                execute_start_time = time.perf_counter()
                raw_arm_action, raw_waist_action, left_ee_action, right_ee_action = _split_robot_action(
                    action_np, arm_dof, waist_dof, ee_dof
                )
                current_arm_q_np = np.asarray(current_arm_q[:arm_dof], dtype=np.float32)
                chunk_refill = queue_len_before == 0 if queue_len_before is not None else policy_elapsed > 1.0
                rtc_metadata = (
                    policy.get_last_action_metadata()
                    if hasattr(policy, "get_last_action_metadata")
                    else None
                )
                raw_control_action = np.concatenate(
                    (
                        np.asarray(raw_arm_action, dtype=np.float32).reshape(-1),
                        np.asarray([raw_waist_action], dtype=np.float32)
                        if waist_dof > 0
                        else np.empty(0, dtype=np.float32),
                    )
                )
                measured_control_state = np.concatenate(
                    (
                        current_arm_q_np,
                        np.asarray([arm_ctrl.get_current_waist_yaw_q()], dtype=np.float32)
                        if waist_dof > 0
                        else np.empty(0, dtype=np.float32),
                    )
                )
                smoothed_control_action, action_smoothing_diag = action_smoother.process(
                    raw_control_action,
                    measured_q=measured_control_state,
                    metadata=rtc_metadata,
                    chunk_refill=chunk_refill,
                )
                arm_action = smoothed_control_action[:arm_dof]
                waist_action = (
                    float(smoothed_control_action[arm_dof]) if waist_dof > 0 else None
                )
                cmd_delta_max = None
                if prev_arm_action is not None:
                    cmd_delta_max = float(np.max(np.abs(np.asarray(arm_action) - prev_arm_action)))
                q_delta_max = None
                if prev_current_arm_q is not None:
                    q_delta_max = float(np.max(np.abs(current_arm_q_np - prev_current_arm_q)))
                track_err_max = float(np.max(np.abs(np.asarray(arm_action) - current_arm_q_np)))
                actual_dq_max = None
                if hasattr(arm_ctrl, "get_current_dual_arm_dq"):
                    actual_dq_max = float(np.max(np.abs(np.asarray(arm_ctrl.get_current_dual_arm_dq())[:arm_dof])))
                slow_policy = policy_elapsed > 1.0
                if slow_policy or chunk_refill:
                    logger_mp.info(
                        "INFERENCE_RESOURCE_DIAG policy_wall_s=%.3f process_cpu_s=%.3f cpu_to_wall=%.2f "
                        "ctrl_window_s=%s ctrl_hz=%s ctrl_work_avg_ms=%s ctrl_work_max_ms=%s "
                        "ctrl_overruns=%s ctrl_iterations=%s ctrl_published=%s",
                        policy_elapsed,
                        policy_process_cpu_s,
                        policy_process_cpu_s / policy_elapsed if policy_elapsed > 0.0 else 0.0,
                        "None" if control_diag is None else f"{control_diag['window_s']:.3f}",
                        "None" if control_diag is None else f"{control_diag['actual_hz']:.1f}",
                        "None" if control_diag is None else f"{control_diag['work_avg_ms']:.3f}",
                        "None" if control_diag is None else f"{control_diag['work_max_ms']:.3f}",
                        "None" if control_diag is None else str(control_diag["overruns"]),
                        "None" if control_diag is None else str(control_diag["iterations"]),
                        "None" if control_diag is None else str(control_diag["published"]),
                    )
                _update_jitter_stats(
                    jitter_stats,
                    cmd_delta_max=cmd_delta_max,
                    q_delta_max=q_delta_max,
                    track_err_max=track_err_max,
                    actual_dq_max=actual_dq_max,
                    chunk_refill=chunk_refill,
                    slow_policy=slow_policy,
                )
                if chunk_refill:
                    predict_profile = getattr(policy, "_last_predict_action_profile", {})
                    chunk_profile = getattr(policy, "_last_chunk_profile", {})
                    logger_mp.info(
                        "CHUNK_REFILL_DIAG episode=%d step=%d queue_before=%s queue_after=%s policy_s=%.3f "
                        "cmd_delta_max=%s q_delta_max=%s track_err_max=%.5f actual_dq_max=%s action_norm=%.4f "
                        "input_tensor_s=%s preprocess_s=%s select_action_s=%s postprocess_s=%s to_cpu_s=%s "
                        "chunk_total_s=%s prefix_s=%s denoise_total_s=%s denoise_avg_s=%s denoise_steps=%s",
                        episode_idx,
                        step_idx + 1,
                        "None" if queue_len_before is None else str(queue_len_before),
                        "None" if queue_len_after is None else str(queue_len_after),
                        policy_elapsed,
                        "None" if cmd_delta_max is None else f"{cmd_delta_max:.5f}",
                        "None" if q_delta_max is None else f"{q_delta_max:.5f}",
                        track_err_max,
                        "None" if actual_dq_max is None else f"{actual_dq_max:.5f}",
                        float(np.linalg.norm(action_np)),
                        "None"
                        if "input_tensor_s" not in predict_profile
                        else f"{predict_profile['input_tensor_s']:.3f}",
                        "None" if "preprocess_s" not in predict_profile else f"{predict_profile['preprocess_s']:.3f}",
                        "None"
                        if "select_action_s" not in predict_profile
                        else f"{predict_profile['select_action_s']:.3f}",
                        "None"
                        if "postprocess_s" not in predict_profile
                        else f"{predict_profile['postprocess_s']:.3f}",
                        "None" if "to_cpu_s" not in predict_profile else f"{predict_profile['to_cpu_s']:.3f}",
                        "None" if "total_s" not in chunk_profile else f"{chunk_profile['total_s']:.3f}",
                        "None" if "prefix_s" not in chunk_profile else f"{chunk_profile['prefix_s']:.3f}",
                        "None"
                        if "denoise_total_s" not in chunk_profile
                        else f"{chunk_profile['denoise_total_s']:.3f}",
                        "None"
                        if "denoise_avg_s" not in chunk_profile
                        else f"{chunk_profile['denoise_avg_s']:.3f}",
                        "None"
                        if "denoise_steps" not in chunk_profile
                        else str(chunk_profile["denoise_steps"]),
                )
                if cfg.send_real_robot:
                    tau = _compute_arm_tau(arm_ik, arm_action, cfg.arm_tau_mode)
                    arm_ctrl.ctrl_dual_arm(arm_action, tau, waist_action)
                    if episode_start_time is None:
                        episode_start_time = time.perf_counter()
                        if run_until_q:
                            logger_mp.info(
                                "Episode %d first action sent at %s; boundary_elapsed_s=%.3f; running until q.",
                                episode_idx,
                                _format_wall_time(),
                                time.perf_counter() - episode_boundary_start,
                            )
                        else:
                            logger_mp.info(
                                "Episode %d first action sent at %s; boundary_elapsed_s=%.3f; timing %.2fs from first command.",
                                episode_idx,
                                _format_wall_time(),
                                time.perf_counter() - episode_boundary_start,
                                cfg.episode_duration_s,
                            )

                    if cfg.ee:
                        if isinstance(ee_shared_mem["left"], SynchronizedArray):
                            ee_shared_mem["left"][:] = to_list(left_ee_action)
                            ee_shared_mem["right"][:] = to_list(right_ee_action)
                        elif hasattr(ee_shared_mem["left"], "value") and hasattr(ee_shared_mem["right"], "value"):
                            ee_shared_mem["left"].value = to_scalar(left_ee_action)
                            ee_shared_mem["right"].value = to_scalar(right_ee_action)
                elif episode_start_time is None:
                    episode_start_time = time.perf_counter()
                    if run_until_q:
                        logger_mp.info(
                            "Episode %d first action ready at %s; boundary_elapsed_s=%.3f; running until q.",
                            episode_idx,
                            _format_wall_time(),
                            time.perf_counter() - episode_boundary_start,
                        )
                    else:
                        logger_mp.info(
                            "Episode %d first action ready at %s; boundary_elapsed_s=%.3f; timing %.2fs from first action.",
                            episode_idx,
                            _format_wall_time(),
                            time.perf_counter() - episode_boundary_start,
                            cfg.episode_duration_s,
                        )
                execute_elapsed = time.perf_counter() - execute_start_time

                # This is deliberately after ctrl_dual_arm: every JSONL row is a
                # target actually handed to the robot controller, not merely a
                # candidate emitted by the RTC inference worker.
                rtc_execution_logger.write(
                    {
                        "episode_index": episode_idx,
                        "control_step_index": step_idx,
                        "sent_to_real_robot": bool(cfg.send_real_robot),
                        "policy_action": np.asarray(action_np).reshape(-1).tolist(),
                        "raw_arm_q_target": np.asarray(raw_arm_action).reshape(-1).tolist(),
                        "raw_waist_q_target": raw_waist_action,
                        "arm_q_target": np.asarray(arm_action).reshape(-1).tolist(),
                        "waist_q_target": waist_action,
                        "left_ee_target": np.asarray(left_ee_action).reshape(-1).tolist(),
                        "right_ee_target": np.asarray(right_ee_action).reshape(-1).tolist(),
                        "arm_tau_command": (
                            np.asarray(tau).reshape(-1).tolist() if cfg.send_real_robot else None
                        ),
                        "observed_arm_q": current_arm_q_np.tolist(),
                        "policy_elapsed_s": policy_elapsed,
                        "execute_elapsed_s": execute_elapsed,
                        "queue_len_before": queue_len_before,
                        "queue_len_after": queue_len_after,
                        "rtc_source": rtc_metadata,
                        "action_smoothing": action_smoothing_diag,
                    }
                )

                if cfg.visualization:
                    visualization_data(step_idx, observation, state_tensor.numpy(), action_np, rerun_logger)
                step_idx += 1
                loop_elapsed = time.perf_counter() - loop_start_time
                if step_idx <= 3:
                    logger_mp.info(
                        "Eval loop step=%d observation_s=%.3f policy_s=%.3f execute_s=%.3f total_s=%.3f",
                        step_idx,
                        observation_elapsed,
                        policy_elapsed,
                        execute_elapsed,
                        loop_elapsed,
                    )
                    logger_mp.info(
                        "Eval action step=%d arm=%s waist=%s left_ee=%s right_ee=%s",
                        step_idx,
                        np.array2string(np.asarray(arm_action), precision=4, suppress_small=True),
                        "None" if waist_action is None else f"{waist_action:.4f}",
                        np.array2string(np.asarray(left_ee_action), precision=4, suppress_small=True),
                        np.array2string(np.asarray(right_ee_action), precision=4, suppress_small=True),
                    )
                elif policy_elapsed > 1.0:
                    logger_mp.warning(
                        "SLOW_POLICY episode=%d step=%d observation_s=%.3f policy_s=%.3f execute_s=%.3f total_s=%.3f action_norm=%.4f action_mean=%.4f waist=%s",
                        episode_idx,
                        step_idx,
                        observation_elapsed,
                        policy_elapsed,
                        execute_elapsed,
                        loop_elapsed,
                        float(np.linalg.norm(action_np)),
                        float(np.mean(action_np)),
                        "None" if waist_action is None else f"{waist_action:.4f}",
                    )
                elif time.perf_counter() - last_heartbeat_time >= 5.0:
                    logger_mp.info(
                        "Eval loop heartbeat step=%d last_total_s=%.3f last_policy_s=%.3f action_norm=%.4f action_mean=%.4f waist=%s",
                        step_idx,
                        loop_elapsed,
                        policy_elapsed,
                        float(np.linalg.norm(action_np)),
                        float(np.mean(action_np)),
                        "None" if waist_action is None else f"{waist_action:.4f}",
                    )
                    last_heartbeat_time = time.perf_counter()
                if time.perf_counter() - last_jitter_log_time >= 5.0:
                    _log_jitter_stats(jitter_stats, episode_idx, step_idx, "JITTER_DIAG")
                    jitter_stats = _new_jitter_stats()
                    last_jitter_log_time = time.perf_counter()
                prev_arm_action = np.asarray(arm_action, dtype=np.float32).copy()
                prev_current_arm_q = current_arm_q_np.copy()
                time.sleep(max(0, (1.0 / cfg.frequency) - (time.perf_counter() - loop_start_time)))

            _restore_runtime_q(runtime_q)
            runtime_q = None
            if hasattr(policy, "on_episode_end"):
                policy.on_episode_end()
            if jitter_stats["count"] > 0:
                _log_jitter_stats(jitter_stats, episode_idx, step_idx, "JITTER_DIAG_FINAL")
            if hasattr(arm_ctrl, "set_episode_active"):
                arm_ctrl.set_episode_active(False)

            if cfg.send_real_robot:
                return_init_start = time.perf_counter()
                if cfg.motion:
                    logger_mp.info(
                        "Episode %d end at %s: moving directly back to dataset initial pose for the next episode...",
                        episode_idx,
                        _format_wall_time(),
                    )
                    if hasattr(arm_ctrl, "set_episode_active"):
                        arm_ctrl.set_episode_active(True)
                    _move_controlled_joints_smoothly(
                        robot_interface["arm_ctrl"],
                        robot_interface["arm_ik"],
                        init_arm_pose,
                        init_waist_yaw,
                        cfg.frequency,
                        cfg.return_to_zero_duration_s,
                    )
                    if hasattr(arm_ctrl, "set_episode_active"):
                        arm_ctrl.set_episode_active(False)
                    logger_mp.info(
                        "Episode %d dataset-initial return complete at %s: elapsed_s=%.3f",
                        episode_idx,
                        _format_wall_time(),
                        time.perf_counter() - return_init_start,
                    )
                elif hasattr(robot_interface["arm_ctrl"], "move_all_joints_to_pose_and_lock_non_arm_waist"):
                    logger_mp.info(
                        "Episode %d end at %s: moving directly to dataset initial pose and locking non-arm / non-waist joints...",
                        episode_idx,
                        _format_wall_time(),
                    )
                    robot_interface["arm_ctrl"].move_all_joints_to_pose_and_lock_non_arm_waist(
                        init_arm_pose,
                        init_waist_yaw if init_waist_yaw is not None else 0.0,
                        duration_s=cfg.return_to_zero_duration_s,
                    )
                    logger_mp.info(
                        "Episode %d initial-pose relock complete at %s: elapsed_s=%.3f",
                        episode_idx,
                        _format_wall_time(),
                        time.perf_counter() - return_init_start,
                    )
                else:
                    _move_controlled_joints_smoothly(
                        robot_interface["arm_ctrl"],
                        robot_interface["arm_ik"],
                        init_arm_pose,
                        init_waist_yaw,
                        cfg.frequency,
                        cfg.return_to_zero_duration_s,
                    )
                    logger_mp.info(
                        "Episode %d initial-pose move complete at %s: elapsed_s=%.3f",
                        episode_idx,
                        _format_wall_time(),
                        time.perf_counter() - return_init_start,
                    )
            if interactive_mode:
                logger_mp.info(
                    "Episode %d complete at %s. Waiting for the next task command.",
                    episode_idx,
                    _format_wall_time(),
                )
            else:
                logger_mp.info(
                    "Episode %d complete at %s. Starting next episode automatically.",
                    episode_idx,
                    _format_wall_time(),
                )
            episode_idx += 1
            if cfg.persistent_runner_managed:
                logger_mp.info("Persistent debug runner owns the next-run menu; returning after this run.")
                break
    except Exception:
        logger_mp.exception("An error occurred during evaluation.")
    finally:
        _restore_runtime_q(runtime_q)
        if "rtc_execution_logger" in locals():
            rtc_execution_logger.close()
        if robot_interface and cfg.send_real_robot and cfg.motion:
            try:
                logger_mp.info(
                    "Eval shutdown at %s: moving through side-raise waypoint, then returning upper-body control to motion controller.",
                    _format_wall_time(),
                )
                current_arm_q = np.asarray(robot_interface["arm_ctrl"].get_current_dual_arm_q(), dtype=np.float32)
                current_waist_q = robot_interface["arm_ctrl"].get_current_waist_yaw_q()
                side_waypoint_q = _build_side_waypoint_q(current_arm_q)
                _move_controlled_joints_smoothly(
                    robot_interface["arm_ctrl"],
                    robot_interface["arm_ik"],
                    side_waypoint_q,
                    current_waist_q,
                    cfg.frequency,
                    max(1.2, cfg.return_to_zero_duration_s * 0.5),
                )
                time.sleep(0.3)
                returned = robot_interface["arm_ctrl"].return_motion_control(
                    ramp_duration_s=cfg.handover_wait_seconds,
                    settle_seconds=cfg.pre_handover_wait_seconds,
                    timeout_s=max(cfg.pre_handover_wait_seconds + 5.0, 6.0),
                )
                if not returned:
                    logger_mp.warning("Timed out waiting for arms to settle back to the motion-controller pose.")
            except Exception as exc:
                logger_mp.warning("Failed to return motion control on shutdown: %s", exc)
        if image_info:
            cleanup_resources(image_info)
        if robot_interface and hasattr(robot_interface.get("arm_ctrl"), "close"):
            try:
                robot_interface["arm_ctrl"].close()
            except Exception as exc:
                logger_mp.warning("Failed to close arm controller process cleanly: %s", exc)


@parser.wrap()
def eval_main(cfg: EvalRealConfig):
    logging.info(pformat(asdict(cfg)))

    # Check device is available
    device = get_safe_torch_device(cfg.policy.device, log=True)

    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True

    logging.info("Making policy.")

    dataset_root = cfg.root if cfg.root else None
    dataset = LeRobotDataset(repo_id=cfg.repo_id, root=dataset_root, episodes=[cfg.episodes])

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
        logging.info("Overriding saved tokenizer path with: %s", cfg.tokenizer_name_override)

    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=cfg.policy,
        pretrained_path=cfg.policy.pretrained_path,
        dataset_stats=rename_stats(dataset.meta.stats, cfg.rename_map),
        preprocessor_overrides=preprocessor_overrides,
    )

    with torch.no_grad(), torch.autocast(device_type=device.type) if cfg.policy.use_amp else nullcontext():
        eval_policy(cfg, dataset, policy, preprocessor, postprocessor)

    logging.info("End of eval")


if __name__ == "__main__":
    init_logging()
    eval_main()
