"""eval_policy wrapper that integrates with VLAController.

Replaces the blocking `input("Enter 's' ...")` and infinite `while True` episode loop
with a task-driven state machine:
  IDLE → PREPARING → RUNNING → RETURNING → IDLE

The HTTP server (vla_server.py) runs this loop in a background thread and submits
tasks via VLAController.submit_task().
"""

import time
import logging
from typing import Optional

import numpy as np
import torch
from torch import nn
from contextlib import nullcontext
from multiprocessing.sharedctypes import SynchronizedArray

from lerobot.policies.pretrained import PreTrainedPolicy
from lerobot.utils.utils import get_safe_torch_device
from lerobot.policies.factory import make_policy, make_pre_post_processors
from lerobot.processor.rename_processor import rename_stats

from unitree_lerobot.eval_robot.make_robot import (
    setup_image_client,
    setup_robot_interface,
    process_images_and_observations,
)
from unitree_lerobot.eval_robot.utils.utils import (
    cleanup_resources,
    predict_action,
    to_list,
    to_scalar,
    EvalRealConfig,
)

from .mcp_server.vla_controller import VLAController, VLAState

logger_mp = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers (mirrored from eval_g1.py — keep in sync)
# ---------------------------------------------------------------------------

def _format_wall_time(ts: float | None = None) -> str:
    if ts is None:
        ts = time.time()
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


def _build_robot_state(current_arm_q, arm_ctrl, arm_dof: int, waist_dof: int, left_ee_state, right_ee_state):
    parts = [np.asarray(current_arm_q[:arm_dof], dtype=np.float32)]
    if waist_dof > 0 and hasattr(arm_ctrl, "get_current_waist_yaw_q"):
        parts.append(np.asarray([arm_ctrl.get_current_waist_yaw_q()], dtype=np.float32))
    if left_ee_state.size > 0:
        parts.append(np.asarray(left_ee_state, dtype=np.float32))
    if right_ee_state.size > 0:
        parts.append(np.asarray(right_ee_state, dtype=np.float32))
    return np.concatenate(parts, axis=0)


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


def _move_controlled_joints_smoothly(arm_ctrl, arm_ik, arm_target, waist_target, frequency: float, duration_s: float):
    stage_start_perf = time.perf_counter()
    stage_start_wall = time.time()
    current_arm_q = np.asarray(arm_ctrl.get_current_dual_arm_q(), dtype=np.float32)
    current_waist_q = float(arm_ctrl.get_current_waist_yaw_q()) if waist_target is not None else None
    arm_target = np.asarray(arm_target, dtype=np.float32)
    steps = max(1, int(round(duration_s * frequency)))
    logger_mp.info(
        "Smooth move start at %s: duration_s=%.2f steps=%d waist_target=%s",
        _format_wall_time(stage_start_wall), duration_s, steps,
        "None" if waist_target is None else f"{waist_target:.4f}",
    )
    for i in range(1, steps + 1):
        alpha = i / steps
        arm_q = current_arm_q + alpha * (arm_target - current_arm_q)
        waist_q = current_waist_q + alpha * (float(waist_target) - current_waist_q) \
            if waist_target is not None and current_waist_q is not None else None
        tau = arm_ik.solve_tau(arm_q)
        arm_ctrl.ctrl_dual_arm(arm_q, tau, waist_q)
        time.sleep(max(0.0, 1.0 / frequency))
    logger_mp.info(
        "Smooth move complete at %s: elapsed_s=%.3f",
        _format_wall_time(), time.perf_counter() - stage_start_perf,
    )


# ---------------------------------------------------------------------------
# Task-driven eval_policy (replaces the input/while-True loop)
# ---------------------------------------------------------------------------

def eval_policy_controlled(
    cfg: EvalRealConfig,
    dataset,
    controller: VLAController,
    policy: Optional[PreTrainedPolicy] = None,
    preprocessor=None,
    postprocessor=None,
):
    """Task-driven version of eval_policy.

    Instead of blocking on keyboard input and looping forever, it waits for
    tasks to be submitted via ``controller.submit_task()`` — which is called
    by the HTTP server from another thread.

    Key changes vs eval_g1.py eval_policy():
    - No input() blocking
    - No outer while True auto-loop; single episode per submit_task()
    - task_text comes from VLATask.task_text (dynamic, not cfg.task_override)
    - Each step checks controller.should_stop() for mid-episode interrupt
    """
    assert isinstance(policy, nn.Module), "Policy must be a PyTorch nn module."

    logger_mp.info(f"[VLAController] eval_policy_controlled started with config: {cfg}")

    if policy is not None and preprocessor is not None and postprocessor is not None:
        policy.reset()
        preprocessor.reset()
        postprocessor.reset()

    image_info = None
    try:
        # ── Setup Phase (same as original) ──────────────────────────────────
        image_client, camera_config = setup_image_client(cfg)
        image_info = (image_client, camera_config)
        robot_interface = setup_robot_interface(cfg)

        arm_ctrl, arm_ik, ee_shared_mem, arm_dof, waist_dof, ee_dof = (
            robot_interface[key]
            for key in ["arm_ctrl", "arm_ik", "ee_shared_mem", "arm_dof", "waist_dof", "ee_dof"]
        )

        # Get initial pose from dataset
        from_idx = dataset.meta.episodes["dataset_from_index"][0]
        step = dataset[from_idx]
        init_state = step["observation.state"].cpu().numpy()
        init_arm_pose = init_state[:arm_dof]
        init_waist_yaw = float(init_state[arm_dof]) if waist_dof > 0 else None

        # Global zero-lock at startup (same as original)
        if cfg.send_real_robot:
            if hasattr(robot_interface["arm_ctrl"], "move_all_joints_to_zero_and_lock_non_arm_waist"):
                init_zero_start = time.perf_counter()
                logger_mp.info("Initializing robot at %s: return whole body to zero...", _format_wall_time())
                robot_interface["arm_ctrl"].move_all_joints_to_zero_and_lock_non_arm_waist(
                    duration_s=cfg.return_to_zero_duration_s
                )
                logger_mp.info(
                    "Robot initialization zero-lock complete at %s: elapsed_s=%.3f",
                    _format_wall_time(), time.perf_counter() - init_zero_start,
                )

        controller.set_state(VLAState.IDLE)
        logger_mp.info("[VLAController] VLA service started, waiting for tasks...")

        episode_idx = 0

        # ── Main task loop (replaces while True outer loop) ─────────────────
        while True:
            # ★ Wait for a task — sleep when idle to avoid busy-waiting
            task = controller.pop_task()
            while task is None:
                time.sleep(0.05)
                task = controller.pop_task()

            logger_mp.info("[pop_task] Got task: task_text='%s' state=%s", task.task_text, controller.get_status()["state"])
            task_text = task.task_text          # ★ Dynamic task text from brain
            episode_duration_s = task.duration_s

            controller.set_state(VLAState.PREPARING)

            # Reset state for this episode
            if policy is not None and preprocessor is not None and postprocessor is not None:
                policy.reset()
                preprocessor.reset()
                postprocessor.reset()

            full_state = None
            step_idx = 0
            episode_boundary_start = time.perf_counter()
            episode_boundary_start_wall = _format_wall_time()

            # ── Move to initial pose (same as original) ─────────────────────
            if cfg.send_real_robot:
                move_to_init_start = time.perf_counter()
                logger_mp.info(
                    "Episode %d (%s) boundary start at %s: moving to initial pose...",
                    episode_idx, task.task_id, episode_boundary_start_wall,
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
                    episode_idx, _format_wall_time(),
                    time.perf_counter() - move_to_init_start,
                    time.perf_counter() - episode_boundary_start,
                )

            # ── Inference loop (single episode, replaces inner while True) ─
            controller.set_state(VLAState.RUNNING)
            loop_mode = "real-robot" if cfg.send_real_robot else "dry-run"
            logger_mp.info(
                "Starting %s episode '%s' (task_id=%s) at %.1f Hz for %.1fs.",
                loop_mode, task_text, task.task_id,
                cfg.frequency, episode_duration_s,
            )

            last_heartbeat_time = time.perf_counter()
            episode_start_time = None

            while True:
                # ★ Check external stop signal every step
                if controller.should_stop():
                    logger_mp.info(
                        "Task %s stopped externally at step %d (elapsed_s=%.2f).",
                        task.task_id, step_idx,
                        time.perf_counter() - episode_boundary_start,
                    )
                    break

                # ★ Check duration expiry
                if episode_start_time is not None and \
                   (time.perf_counter() - episode_start_time) >= episode_duration_s:
                    logger_mp.info(
                        "Episode %d (%s) finished after %.2fs (duration limit).",
                        episode_idx, task.task_id, episode_duration_s,
                    )
                    break

                loop_start_time = time.perf_counter()
                observation_start_time = time.perf_counter()
                observation, current_arm_q = process_images_and_observations(
                    image_client, camera_config, arm_ctrl
                )
                observation_elapsed = time.perf_counter() - observation_start_time
                if current_arm_q is None:
                    logger_mp.warning("Current arm state unavailable; skip this cycle.")
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

                policy_start_time = time.perf_counter()
                action = predict_action(
                    observation,
                    policy,
                    get_safe_torch_device(policy.config.device),
                    preprocessor,
                    postprocessor,
                    policy.config.use_amp,
                    task_text,          # ★ Dynamic task text, not cfg.task_override
                    use_dataset=cfg.use_dataset,
                    robot_type=None,
                )
                policy_elapsed = time.perf_counter() - policy_start_time
                action_np = action.cpu().numpy()

                execute_start_time = time.perf_counter()
                arm_action, waist_action, left_ee_action, right_ee_action = _split_robot_action(
                    action_np, arm_dof, waist_dof, ee_dof
                )

                if cfg.send_real_robot:
                    tau = arm_ik.solve_tau(arm_action)
                    arm_ctrl.ctrl_dual_arm(arm_action, tau, waist_action)
                    if episode_start_time is None:
                        episode_start_time = time.perf_counter()
                        logger_mp.info(
                            "Episode %d first action sent at %s; boundary_elapsed_s=%.3f; timing %.2fs.",
                            episode_idx, _format_wall_time(),
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
                    logger_mp.info(
                        "Episode %d first action ready at %s; boundary_elapsed_s=%.3f.",
                        episode_idx, _format_wall_time(),
                        time.perf_counter() - episode_boundary_start,
                    )

                execute_elapsed = time.perf_counter() - execute_start_time

                step_idx += 1
                controller.update_step(step_idx)

                if step_idx <= 3:
                    logger_mp.info(
                        "Eval step=%d observation_s=%.3f policy_s=%.3f execute_s=%.3f",
                        step_idx, observation_elapsed, policy_elapsed, execute_elapsed,
                    )
                elif time.perf_counter() - last_heartbeat_time >= 5.0:
                    logger_mp.info(
                        "Eval heartbeat step=%d policy_s=%.3f action_norm=%.4f",
                        step_idx, policy_elapsed, float(np.linalg.norm(action_np)),
                    )
                    last_heartbeat_time = time.perf_counter()

                time.sleep(max(0, (1.0 / cfg.frequency) - (time.perf_counter() - loop_start_time)))

            # ── Return to initial pose (same as original) ──────────────────────
            controller.set_state(VLAState.RETURNING)
            if cfg.send_real_robot:
                return_init_start = time.perf_counter()
                logger_mp.info(
                    "Episode %d end at %s: moving directly to dataset initial pose and locking non-arm / non-waist joints...",
                    episode_idx, _format_wall_time(),
                )
                if hasattr(robot_interface["arm_ctrl"], "move_all_joints_to_pose_and_lock_non_arm_waist"):
                    robot_interface["arm_ctrl"].move_all_joints_to_pose_and_lock_non_arm_waist(
                        init_arm_pose,
                        init_waist_yaw if init_waist_yaw is not None else 0.0,
                        duration_s=cfg.return_to_zero_duration_s,
                    )
                    logger_mp.info(
                        "Episode %d initial-pose relock complete at %s: elapsed_s=%.3f",
                        episode_idx, _format_wall_time(),
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
                        episode_idx, _format_wall_time(),
                        time.perf_counter() - return_init_start,
                    )

            # ★ Mark episode done and return to IDLE
            completed = not controller.should_stop()
            controller.complete_episode(completed)
            logger_mp.info(
                "Episode %d (task_id=%s) complete at %s. State → IDLE.",
                episode_idx, task.task_id, _format_wall_time(),
            )
            episode_idx += 1

    except Exception as e:
        logger_mp.exception("VLAController eval loop exception: %s", e)
        controller.set_state(VLAState.ERROR)
    finally:
        if image_info:
            cleanup_resources(image_info)


# ---------------------------------------------------------------------------
# Entry point for vla_server.py: runs the loop in a background thread
# ---------------------------------------------------------------------------

def run_eval_with_controller(cfg: EvalRealConfig, controller: VLAController):
    """Build all policy/dataset objects and run the controlled eval loop."""

    from lerobot.datasets.lerobot_dataset import LeRobotDataset

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
        eval_policy_controlled(
            cfg, dataset, controller, policy, preprocessor, postprocessor
        )

    logger_mp.info("VLA eval loop terminated.")