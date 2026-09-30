"""Single-request controlled real-robot eval for MCP.

This entry keeps the direct eval_g1.py episode execution behavior, but runs at
most one policy action chunk per MCP request. After the chunk is consumed, the
robot returns to the ready pose and the server goes back to idle.
"""

import time
import logging

import numpy as np
import torch
from contextlib import nullcontext
from multiprocessing.sharedctypes import SynchronizedArray
from torch import nn
from typing import Any, Callable

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies.factory import make_policy, make_pre_post_processors
from lerobot.policies.pretrained import PreTrainedPolicy
from lerobot.processor import PolicyAction, PolicyProcessorPipeline
from lerobot.processor.rename_processor import rename_stats
from lerobot.utils.utils import get_safe_torch_device
from unitree_lerobot.eval_robot.eval_g1 import (
    _build_robot_state,
    _build_side_waypoint_q,
    _format_wall_time,
    _move_controlled_joints_via_prepare_waypoints,
    _move_controlled_joints_smoothly,
    _move_controlled_joints_via_side_waypoint,
    _split_robot_action,
)
from unitree_lerobot.eval_robot.make_robot import (
    process_images_and_observations,
    setup_image_client,
    setup_robot_interface,
)
from unitree_lerobot.eval_robot.mcp_server.vla_controller import VLAController, VLAState
from unitree_lerobot.eval_robot.rtc_execution_log import RTCExecutionLogger
from unitree_lerobot.eval_robot.utils.utils import (
    EvalRealConfig,
    cleanup_resources,
    predict_action,
    to_list,
    to_scalar,
)

import logging_mp

logger_mp = logging_mp.getLogger(__name__)
logger_mp.setLevel(logging_mp.INFO)


def eval_policy_controlled_loop(
    cfg: EvalRealConfig,
    dataset: LeRobotDataset,
    controller: VLAController,
    policy: PreTrainedPolicy | None = None,
    preprocessor: PolicyProcessorPipeline[dict[str, Any], dict[str, Any]] | None = None,
    postprocessor: PolicyProcessorPipeline[PolicyAction, PolicyAction] | None = None,
    *,
    predict_action_fn: Callable[..., Any] = predict_action,
    single_chunk_per_request: bool = True,
    max_action_duration_s: float = 0.0,
    terminal_joint_detector: Any | None = None,
):
    assert isinstance(policy, nn.Module), "Policy must be a PyTorch nn module."

    logger_mp.info("Arguments: %s", cfg)

    if policy is not None and preprocessor is not None and postprocessor is not None:
        policy.reset()
        preprocessor.reset()
        postprocessor.reset()

    image_info = None
    robot_interface = None
    motion_handover_active = False
    try:
        image_client, camera_config = setup_image_client(cfg)
        image_info = (image_client, camera_config)
        robot_interface = setup_robot_interface(cfg)

        arm_ctrl, arm_ik, ee_shared_mem, arm_dof, waist_dof, ee_dof = (
            robot_interface[key] for key in ["arm_ctrl", "arm_ik", "ee_shared_mem", "arm_dof", "waist_dof", "ee_dof"]
        )
        rtc_execution_logger = RTCExecutionLogger(
            str(getattr(cfg, "rtc_execution_log_path", ""))
        )
        if rtc_execution_logger.enabled:
            logger_mp.info("RTC executed-action JSONL logging enabled: %s", rtc_execution_logger.path)
        if terminal_joint_detector is not None:
            if terminal_joint_detector.state_dim != arm_dof + waist_dof:
                raise ValueError(
                    "Terminal detector state dimension does not match controlled arm/waist dimensions: "
                    f"{terminal_joint_detector.state_dim} != {arm_dof} + {waist_dof}"
                )

            def read_terminal_joint_state() -> np.ndarray:
                arm_state = np.asarray(arm_ctrl.get_current_dual_arm_q(), dtype=np.float64)
                if waist_dof > 0:
                    waist_state = np.asarray([arm_ctrl.get_current_waist_yaw_q()], dtype=np.float64)
                    return np.concatenate((arm_state, waist_state))
                return arm_state

            terminal_joint_detector.start_monitor(read_terminal_joint_state)
        if hasattr(arm_ctrl, "set_idle_publish_mode"):
            arm_ctrl.set_idle_publish_mode(cfg.idle_publish_mode)
        if hasattr(arm_ctrl, "set_episode_active"):
            arm_ctrl.set_episode_active(False)

        from_idx = dataset.meta.episodes["dataset_from_index"][0]
        step = dataset[from_idx]
        init_state = step["observation.state"].cpu().numpy()
        init_arm_pose = init_state[:arm_dof]
        init_waist_yaw = float(init_state[arm_dof]) if waist_dof > 0 else None
        default_task_text = cfg.task_override if cfg.task_override else step["task"]

        if cfg.send_real_robot:
            if not cfg.motion and hasattr(robot_interface["arm_ctrl"], "move_all_joints_to_zero_and_lock_non_arm_waist"):
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

        controller.set_state(VLAState.IDLE)
        logger_mp.info("[VLAController] Controlled eval service started, waiting for /vla/execute ...")

        current_session_id = None
        episode_idx = 0

        while True:
            task = controller.pop_task()
            while task is None:
                time.sleep(0.05)
                task = controller.pop_task()

            if task.task_id != current_session_id:
                current_session_id = task.task_id
                episode_idx = 0
                logger_mp.info(
                    "[session] Start controlled task task_id=%s task_text='%s' duration_s=%.2f",
                    task.task_id,
                    task.task_text,
                    task.duration_s,
                )

            task_text = task.task_text or default_task_text
            requested_duration_s = float(task.duration_s)
            if requested_duration_s <= 0.0:
                requested_duration_s = float(cfg.episode_duration_s)
            episode_duration_s = requested_duration_s
            if max_action_duration_s > 0.0:
                episode_duration_s = min(episode_duration_s, max_action_duration_s)
            if episode_duration_s <= 0.0:
                raise ValueError("MCP action duration must be greater than zero")

            if episode_duration_s != float(task.duration_s):
                logger_mp.info(
                    "Task %s duration adjusted from %.2fs to %.2fs (configured hard limit %.2fs).",
                    task.task_id,
                    float(task.duration_s),
                    episode_duration_s,
                    max_action_duration_s,
                )

            if policy is not None and preprocessor is not None and postprocessor is not None:
                policy.reset()
                if hasattr(policy, "max_episode_wall_time_s"):
                    policy.max_episode_wall_time_s = episode_duration_s
                preprocessor.reset()
                postprocessor.reset()
            if terminal_joint_detector is not None:
                terminal_joint_detector.reset()

            full_state = None
            step_idx = 0
            episode_boundary_start = time.perf_counter()
            episode_boundary_start_wall = _format_wall_time()
            current_arm_q = np.asarray(arm_ctrl.get_current_dual_arm_q(), dtype=np.float32)
            current_waist_q = float(arm_ctrl.get_current_waist_yaw_q()) if waist_dof > 0 else None
            ready_arm_delta_max = float(np.max(np.abs(current_arm_q - init_arm_pose)))
            ready_waist_delta = (
                abs(current_waist_q - init_waist_yaw)
                if current_waist_q is not None and init_waist_yaw is not None
                else 0.0
            )
            already_at_ready_pose = ready_arm_delta_max < 0.08 and ready_waist_delta < 0.05

            controller.set_state(VLAState.PREPARING)
            if cfg.send_real_robot and hasattr(arm_ctrl, "set_episode_active"):
                arm_ctrl.set_episode_active(True)
            if cfg.send_real_robot and cfg.motion:
                if not motion_handover_active:
                    logger_mp.info(
                        "Episode %d (%s) preparing at %s: wait for motion-controller pose, then hand over to arm_sdk.",
                        episode_idx,
                        task.task_id,
                        episode_boundary_start_wall,
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
                    time.sleep(cfg.handover_wait_seconds)
                    motion_handover_active = True

                if already_at_ready_pose:
                    logger_mp.info(
                        "Episode %d (%s) boundary start at %s: already at ready pose, skip preparing waypoints (arm_delta_max=%.4f waist_delta=%.4f).",
                        episode_idx,
                        task.task_id,
                        episode_boundary_start_wall,
                        ready_arm_delta_max,
                        ready_waist_delta,
                    )
                else:
                    move_to_init_start = time.perf_counter()
                    logger_mp.info(
                        "Episode %d (%s) boundary start at %s: moving through prepare waypoints to dataset initial pose...",
                        episode_idx,
                        task.task_id,
                        episode_boundary_start_wall,
                    )
                    _move_controlled_joints_via_prepare_waypoints(
                        arm_ctrl,
                        arm_ik,
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
            elif cfg.send_real_robot and episode_idx == 0 and not cfg.motion:
                move_to_init_start = time.perf_counter()
                logger_mp.info(
                    "Episode %d (%s) boundary start at %s: moving controlled joints to dataset initial pose...",
                    episode_idx,
                    task.task_id,
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
                    "Episode %d (%s) boundary start at %s: skip initial-pose move because previous episode already ended at dataset initial pose.",
                    episode_idx,
                    task.task_id,
                    episode_boundary_start_wall,
                )

            if cfg.send_real_robot and hasattr(arm_ctrl, "set_episode_active"):
                arm_ctrl.set_episode_active(False)
                logger_mp.info(
                    "Episode %d (%s) ready pose reached; pause low-level publish before first policy chunk refill "
                    "(idle_publish_mode=%s).",
                    episode_idx,
                    task.task_id,
                    cfg.idle_publish_mode,
                )

            controller.set_state(VLAState.RUNNING)
            logger_mp.info(
                "Starting controlled %s evaluation loop at %.1f Hz for %.1fs (%s).",
                "real-robot" if cfg.send_real_robot else "dry-run",
                cfg.frequency,
                episode_duration_s,
                "single chunk per request" if single_chunk_per_request else "continuous RTC chunk refills",
            )

            last_heartbeat_time = time.perf_counter()
            episode_start_time = None
            inference_end_margin_s = max(1.0 / cfg.frequency, 0.2)
            target_episode_steps = max(1, int(round(episode_duration_s * cfg.frequency)))
            chunk_refilled_once = False
            chunk_drained = False
            episode_stop_reason = ""

            while True:
                if terminal_joint_detector is not None and terminal_joint_detector.succeeded:
                    episode_stop_reason = terminal_joint_detector.success_details.get(
                        "reason", "terminal joint pose held"
                    )
                    logger_mp.info(
                        "Task %s automatically completed at step %d: %s.",
                        task.task_id,
                        step_idx,
                        episode_stop_reason,
                    )
                    break
                if controller.should_stop():
                    episode_stop_reason = "external stop requested"
                    logger_mp.info(
                        "Task %s stop requested at step %d (boundary_elapsed_s=%.3f).",
                        task.task_id,
                        step_idx,
                        time.perf_counter() - episode_boundary_start,
                    )
                    break

                if episode_start_time is not None and (time.perf_counter() - episode_start_time) >= episode_duration_s:
                    episode_stop_reason = "requested action duration reached"
                    logger_mp.info(
                        "Episode %d (%s) finished after %.2fs.",
                        episode_idx,
                        task.task_id,
                        episode_duration_s,
                    )
                    break

                if step_idx >= target_episode_steps:
                    episode_stop_reason = "requested action step count reached"
                    logger_mp.info(
                        "Episode %d (%s) finished after %d steps (target=%d).",
                        episode_idx,
                        task.task_id,
                        step_idx,
                        target_episode_steps,
                    )
                    break

                loop_start_time = time.perf_counter()
                observation_start_time = time.perf_counter()
                observation, current_arm_q = process_images_and_observations(
                    image_client, camera_config, arm_ctrl
                )
                observation_elapsed = time.perf_counter() - observation_start_time
                if current_arm_q is None:
                    logger_mp.warning("Current arm state is unavailable; skip this cycle.")
                    time.sleep(max(0, (1.0 / cfg.frequency) - (time.perf_counter() - loop_start_time)))
                    continue

                left_ee_state = right_ee_state = np.array([])
                if cfg.ee:
                    with ee_shared_mem["lock"]:
                        full_state = np.array(ee_shared_mem["state"][:])
                        left_ee_state = full_state[:ee_dof]
                        right_ee_state = full_state[ee_dof:]
                state_tensor = torch.from_numpy(
                    _build_robot_state(current_arm_q, arm_ctrl, arm_dof, waist_dof, left_ee_state, right_ee_state)
                ).float()
                observation["observation.state"] = state_tensor

                if episode_start_time is not None:
                    elapsed_s = time.perf_counter() - episode_start_time
                    remaining_s = episode_duration_s - elapsed_s
                    if remaining_s <= inference_end_margin_s:
                        episode_stop_reason = "insufficient time for another inference"
                        logger_mp.info(
                            "Episode %d (%s) stopping before inference at %s: remaining_s=%.3f <= margin_s=%.3f",
                            episode_idx,
                            task.task_id,
                            _format_wall_time(),
                            remaining_s,
                            inference_end_margin_s,
                        )
                        break

                queue_len_before = None
                if hasattr(policy, "_action_queue"):
                    queue_len_before = len(policy._action_queue)
                    if single_chunk_per_request and chunk_refilled_once and queue_len_before == 0:
                        chunk_drained = True
                        episode_stop_reason = "single action chunk consumed"
                        logger_mp.info(
                            "Episode %d (%s) action chunk fully consumed after %d steps; finishing request without refilling.",
                            episode_idx,
                            task.task_id,
                            step_idx,
                        )
                        break

                policy_start_time = time.perf_counter()
                try:
                    action = predict_action_fn(
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
                except TimeoutError as exc:
                    episode_stop_reason = f"inference timeout: {exc}"
                    logger_mp.error(
                        "Episode %d (%s) %s; stopping actions and entering the normal return path.",
                        episode_idx,
                        task.task_id,
                        episode_stop_reason,
                    )
                    break
                policy_elapsed = time.perf_counter() - policy_start_time
                if action is None:
                    stop_reason = getattr(policy, "episode_stop_reason", "") or "policy requested episode stop"
                    if terminal_joint_detector is not None and terminal_joint_detector.succeeded:
                        stop_reason = terminal_joint_detector.success_details.get(
                            "reason", "terminal joint pose held"
                        )
                    episode_stop_reason = stop_reason
                    logger_mp.info(
                        "Episode %d (%s) stopping without another action: %s.",
                        episode_idx,
                        task.task_id,
                        stop_reason,
                    )
                    break
                if terminal_joint_detector is not None and terminal_joint_detector.succeeded:
                    episode_stop_reason = terminal_joint_detector.success_details.get(
                        "reason", "terminal joint pose held"
                    )
                    logger_mp.info(
                        "Episode %d (%s) terminal pose completed while waiting for policy; "
                        "discarding the newly returned action.",
                        episode_idx,
                        task.task_id,
                    )
                    break
                queue_len_after = None
                if hasattr(policy, "_action_queue"):
                    queue_len_after = len(policy._action_queue)
                action_np = action.cpu().numpy()

                chunk_refill = queue_len_before == 0 if queue_len_before is not None else step_idx == 0
                if chunk_refill:
                    if single_chunk_per_request and chunk_refilled_once:
                        episode_stop_reason = "unexpected second chunk refill"
                        logger_mp.warning(
                            "Episode %d (%s) detected an unexpected second chunk refill; stopping request.",
                            episode_idx,
                            task.task_id,
                        )
                        break
                    chunk_refilled_once = True
                    logger_mp.info(
                        "Episode %d (%s) chunk refill: queue_before=%s queue_after=%s",
                        episode_idx,
                        task.task_id,
                        "None" if queue_len_before is None else str(queue_len_before),
                        "None" if queue_len_after is None else str(queue_len_after),
                    )

                execute_start_time = time.perf_counter()
                arm_action, waist_action, left_ee_action, right_ee_action = _split_robot_action(
                    action_np, arm_dof, waist_dof, ee_dof
                )
                if cfg.send_real_robot:
                    tau = arm_ik.solve_tau(arm_action)
                    arm_ctrl.ctrl_dual_arm(arm_action, tau, waist_action)
                    if episode_start_time is None:
                        if hasattr(arm_ctrl, "set_episode_active"):
                            arm_ctrl.set_episode_active(True)
                        episode_start_time = time.perf_counter()
                        if terminal_joint_detector is not None:
                            terminal_joint_detector.start_episode(timestamp=episode_start_time)
                        logger_mp.info(
                            "Episode %d first action sent at %s; boundary_elapsed_s=%.3f; timing %.2fs from first command.",
                            episode_idx,
                            _format_wall_time(),
                            time.perf_counter() - episode_boundary_start,
                            episode_duration_s,
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
                    if terminal_joint_detector is not None:
                        terminal_joint_detector.start_episode(timestamp=episode_start_time)
                    logger_mp.info(
                        "Episode %d first action ready at %s; boundary_elapsed_s=%.3f; timing %.2fs from first action.",
                        episode_idx,
                        _format_wall_time(),
                        time.perf_counter() - episode_boundary_start,
                        episode_duration_s,
                    )
                execute_elapsed = time.perf_counter() - execute_start_time

                rtc_metadata = (
                    policy.get_last_action_metadata()
                    if hasattr(policy, "get_last_action_metadata")
                    else None
                )
                rtc_execution_logger.write(
                    {
                        "episode_index": episode_idx,
                        "mcp_task_id": task.task_id,
                        "control_step_index": step_idx,
                        "sent_to_real_robot": bool(cfg.send_real_robot),
                        "policy_action": np.asarray(action_np).reshape(-1).tolist(),
                        "arm_q_target": np.asarray(arm_action).reshape(-1).tolist(),
                        "waist_q_target": waist_action,
                        "left_ee_target": np.asarray(left_ee_action).reshape(-1).tolist(),
                        "right_ee_target": np.asarray(right_ee_action).reshape(-1).tolist(),
                        "arm_tau_command": (
                            np.asarray(tau).reshape(-1).tolist() if cfg.send_real_robot else None
                        ),
                        "policy_elapsed_s": policy_elapsed,
                        "execute_elapsed_s": execute_elapsed,
                        "queue_len_before": queue_len_before,
                        "queue_len_after": queue_len_after,
                        "rtc_source": rtc_metadata,
                    }
                )

                step_idx += 1
                controller.update_step(step_idx)

                if step_idx <= 3:
                    logger_mp.info(
                        "Eval loop step=%d observation_s=%.3f policy_s=%.3f execute_s=%.3f total_s=%.3f",
                        step_idx,
                        observation_elapsed,
                        policy_elapsed,
                        execute_elapsed,
                        time.perf_counter() - loop_start_time,
                    )
                elif policy_elapsed > 1.0:
                    logger_mp.warning(
                        "SLOW_POLICY episode=%d step=%d observation_s=%.3f policy_s=%.3f execute_s=%.3f action_norm=%.4f action_mean=%.4f waist=%s",
                        episode_idx,
                        step_idx,
                        observation_elapsed,
                        policy_elapsed,
                        execute_elapsed,
                        float(np.linalg.norm(action_np)),
                        float(np.mean(action_np)),
                        "None" if waist_action is None else f"{waist_action:.4f}",
                    )
                elif time.perf_counter() - last_heartbeat_time >= 5.0:
                    logger_mp.info(
                        "Eval loop heartbeat step=%d last_policy_s=%.3f action_norm=%.4f action_mean=%.4f waist=%s queue_after=%s",
                        step_idx,
                        policy_elapsed,
                        float(np.linalg.norm(action_np)),
                        float(np.mean(action_np)),
                        "None" if waist_action is None else f"{waist_action:.4f}",
                        "None" if queue_len_after is None else str(queue_len_after),
                    )
                    last_heartbeat_time = time.perf_counter()
                time.sleep(max(0, (1.0 / cfg.frequency) - (time.perf_counter() - loop_start_time)))

            if hasattr(policy, "on_episode_end"):
                policy.on_episode_end()
            if terminal_joint_detector is not None:
                terminal_joint_detector.stop_episode()
            controller.set_state(VLAState.RETURNING)
            if cfg.send_real_robot:
                if hasattr(arm_ctrl, "set_episode_active"):
                    arm_ctrl.set_episode_active(True)
                return_init_start = time.perf_counter()
                if cfg.post_action_shoulder_roll_nudge_rad != 0.0:
                    if arm_dof == 5:
                        nudge_start = time.perf_counter()
                        current_arm_q = np.asarray(arm_ctrl.get_current_dual_arm_q(), dtype=np.float32)
                        current_waist_q = float(arm_ctrl.get_current_waist_yaw_q()) if waist_dof > 0 else None
                        nudge_arm_q = current_arm_q.copy()
                        nudge_arm_q[1] += float(cfg.post_action_shoulder_roll_nudge_rad)
                        logger_mp.info(
                            "Episode %d post-action shoulder-roll nudge at %s: q[1] %.4f -> %.4f "
                            "(delta=%.4f duration_s=%.2f hold_s=%.2f).",
                            episode_idx,
                            _format_wall_time(),
                            float(current_arm_q[1]),
                            float(nudge_arm_q[1]),
                            float(cfg.post_action_shoulder_roll_nudge_rad),
                            cfg.post_action_nudge_duration_s,
                            cfg.post_action_nudge_hold_s,
                        )
                        _move_controlled_joints_smoothly(
                            robot_interface["arm_ctrl"],
                            robot_interface["arm_ik"],
                            nudge_arm_q,
                            current_waist_q,
                            cfg.frequency,
                            cfg.post_action_nudge_duration_s,
                        )
                        if cfg.post_action_nudge_hold_s > 0.0:
                            time.sleep(cfg.post_action_nudge_hold_s)
                        logger_mp.info(
                            "Episode %d post-action shoulder-roll nudge complete at %s: elapsed_s=%.3f",
                            episode_idx,
                            _format_wall_time(),
                            time.perf_counter() - nudge_start,
                        )
                    else:
                        logger_mp.warning(
                            "Skip post-action shoulder-roll nudge: expected arm_dof=5 for right-arm-only view, got %d.",
                            arm_dof,
                        )
                if cfg.motion:
                    logger_mp.info(
                        "Episode %d end at %s: moving directly back to dataset initial pose for the next episode...",
                        episode_idx,
                        _format_wall_time(),
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

            stop_requested = controller.should_stop()
            inference_timed_out = episode_stop_reason.startswith("inference timeout:")
            completed = (
                not stop_requested
                and not inference_timed_out
                and (chunk_refilled_once or chunk_drained or step_idx > 0)
            )
            if hasattr(arm_ctrl, "set_episode_active"):
                arm_ctrl.set_episode_active(False)
            controller.complete_episode(
                completed=completed,
                restart_loop=False,
                reason=episode_stop_reason,
                details=(
                    terminal_joint_detector.success_details
                    if terminal_joint_detector is not None and terminal_joint_detector.succeeded
                    else None
                ),
            )

            if stop_requested:
                logger_mp.info(
                    "Task_id=%s stopped at %s. State -> IDLE and waiting for next /vla/execute.",
                    task.task_id,
                    _format_wall_time(),
                )
                current_session_id = None
                continue

            logger_mp.info(
                "Episode %d complete at %s. Request finished for task_id=%s; state -> IDLE.",
                episode_idx,
                _format_wall_time(),
                task.task_id,
            )
            current_session_id = None

    except Exception as exc:
        logger_mp.exception("Controlled eval loop exception: %s", exc)
        controller.set_state(VLAState.ERROR)
    finally:
        if "rtc_execution_logger" in locals():
            rtc_execution_logger.close()
        if terminal_joint_detector is not None:
            terminal_joint_detector.close()
        if robot_interface and cfg.send_real_robot and cfg.motion and motion_handover_active:
            try:
                if hasattr(robot_interface["arm_ctrl"], "set_episode_active"):
                    robot_interface["arm_ctrl"].set_episode_active(True)
                logger_mp.info(
                    "Controlled eval shutdown at %s: moving through side-raise waypoint, then returning upper-body control to motion controller.",
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
                logger_mp.warning("Failed to return motion control on controlled-eval shutdown: %s", exc)
        if image_info:
            cleanup_resources(image_info)


def run_eval_with_controller(cfg: EvalRealConfig, controller: VLAController):
    device = get_safe_torch_device(cfg.policy.device, log=True)
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True

    logger_mp.info("Making policy.")
    dataset_root = cfg.root if cfg.root else None
    dataset = LeRobotDataset(repo_id=cfg.repo_id, root=dataset_root, episodes=[cfg.episodes])

    policy = make_policy(cfg=cfg.policy, ds_meta=dataset.meta)
    policy.eval()
    if hasattr(policy, "model") and hasattr(policy.model, "gradient_checkpointing_disable"):
        policy.model.gradient_checkpointing_disable()
        logger_mp.info("Disabled gradient checkpointing for evaluation.")

    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=cfg.policy,
        pretrained_path=cfg.policy.pretrained_path,
        dataset_stats=rename_stats(dataset.meta.stats, cfg.rename_map),
        preprocessor_overrides={
            "device_processor": {"device": cfg.policy.device},
            "rename_observations_processor": {"rename_map": cfg.rename_map},
        },
    )

    with torch.no_grad(), torch.autocast(device_type=device.type) if cfg.policy.use_amp else nullcontext():
        eval_policy_controlled_loop(cfg, dataset, controller, policy, preprocessor, postprocessor)
