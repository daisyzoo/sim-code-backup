import sys
import importlib.util
from pathlib import Path


def _ensure_unitree_sdk2py_on_path():
    if importlib.util.find_spec("unitree_sdk2py") is not None:
        return

    candidate_roots = [
        Path("/home/igs/Desktop/project/vla/unitree_lerobot/unitree_sdk2_python"),
        Path("/home/igs/develop/unitree_sdk2_python"),
        Path("/home/igs/unitree_sdk2_python"),
    ]
    for root in candidate_roots:
        if (root / "unitree_sdk2py").is_dir():
            root_str = str(root)
            if root_str not in sys.path:
                sys.path.insert(0, root_str)
            return


_ensure_unitree_sdk2py_on_path()

from multiprocessing import shared_memory, Value, Array, Lock
from typing import Any
import numpy as np
import argparse
import threading
import torch
import cv2
from unitree_lerobot.eval_robot.image_server.image_client import ImageClient
from unitree_lerobot.eval_robot.robot_control.robot_arm import (
    G1_29_ArmController,
    G1_23_ArmController,
    G1_23_ArmStateReader,
    G1_23_DummyArmController,
)
from unitree_lerobot.eval_robot.robot_control.g1_23_process_controller import G1_23_ProcessController
from unitree_lerobot.eval_robot.robot_control.robot_arm_ik import G1_29_ArmIK, G1_23_ArmIK
from unitree_lerobot.eval_robot.robot_control.robot_hand_unitree import (
    Dex3_1_Controller,
    Dex1_1_Gripper_Controller,
)

from unitree_lerobot.eval_robot.utils.episode_writer import EpisodeWriter

from unitree_lerobot.eval_robot.robot_control.robot_hand_inspire import Inspire_Controller
from unitree_lerobot.eval_robot.robot_control.robot_hand_brainco import Brainco_Controller
from unitree_lerobot.eval_robot.robot_control.mobile_control import G1_Mobile_Lift_Controller


from unitree_sdk2py.core.channel import ChannelPublisher
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.idl.std_msgs.msg.dds_ import String_

import logging_mp

logger_mp = logging_mp.getLogger(__name__)
logger_mp.setLevel(logging_mp.INFO)

# Configuration for robot arms
ARM_CONFIG = {
    "G1_29": {"controller": G1_29_ArmController, "ik_solver": G1_29_ArmIK, "dof": 14},
    "G1_23": {"controller": G1_23_ArmController, "ik_solver": G1_23_ArmIK, "dof": 10, "waist_dof": 1},
    "G1_23_RightArm5": {"controller": G1_23_ArmController, "ik_solver": G1_23_ArmIK, "dof": 5, "waist_dof": 1},
    # Add other arms here
}

# Configuration for end-effectors
EE_CONFIG: dict[str, dict[str, Any]] = {
    "dex3": {
        "controller": Dex3_1_Controller,
        "dof": 7,
        "shared_mem_type": "Array",
        "shared_mem_size": 7,
        # "out_len": 14,
    },
    "dex1": {
        "controller": Dex1_1_Gripper_Controller,
        "dof": 1,
        "shared_mem_type": "Value",
        # "out_len": 2,
    },
    "inspire1": {
        "controller": Inspire_Controller,
        "dof": 6,
        "shared_mem_type": "Array",
        "shared_mem_size": 6,
        # "out_len": 12,
    },
    "brainco": {
        "controller": Brainco_Controller,
        "dof": 6,
        "shared_mem_type": "Array",
        "shared_mem_size": 6,
        # "out_len": 12,
    },
}


class G1_23_RightArm5_View:
    """Expose a right-arm-only 5 DoF control view on top of the 10 DoF G1_23 controller."""

    _RIGHT_SLICE = slice(5, 10)

    def __init__(self, base_ctrl: G1_23_ArmController | G1_23_ArmStateReader):
        self._base = base_ctrl
        self._left_lock_q = np.asarray(self._base.get_current_dual_arm_q()[:5], dtype=np.float32).copy()

    def _combine_full_arm_q(self, right_arm_q: np.ndarray) -> np.ndarray:
        full_q = np.asarray(self._base.get_current_dual_arm_q(), dtype=np.float32).copy()
        full_q[:5] = self._left_lock_q
        full_q[self._RIGHT_SLICE] = np.asarray(right_arm_q, dtype=np.float32)
        return full_q

    def _combine_full_arm_tau(self, right_arm_tau: np.ndarray) -> np.ndarray:
        full_tau = np.zeros(10, dtype=np.float32)
        full_tau[self._RIGHT_SLICE] = np.asarray(right_arm_tau, dtype=np.float32)
        return full_tau

    def ctrl_dual_arm(self, q_target, tauff_target, waist_yaw_target=None):
        full_q = self._combine_full_arm_q(q_target)
        full_tau = self._combine_full_arm_tau(tauff_target)
        self._base.ctrl_dual_arm(full_q, full_tau, waist_yaw_target)

    def get_current_dual_arm_q(self):
        full_q = np.asarray(self._base.get_current_dual_arm_q(), dtype=np.float32)
        return full_q[self._RIGHT_SLICE].copy()

    def get_current_dual_arm_dq(self):
        full_dq = np.asarray(self._base.get_current_dual_arm_dq(), dtype=np.float32)
        return full_dq[self._RIGHT_SLICE].copy()

    def get_current_waist_yaw_q(self):
        return float(self._base.get_current_waist_yaw_q())

    def set_left_lock_q(self, left_arm_q: np.ndarray):
        self._left_lock_q = np.asarray(left_arm_q, dtype=np.float32).copy()

    def move_left_arm_to_pose_and_lock(self, left_arm_target: np.ndarray, duration_s: float = 2.0):
        if not hasattr(self._base, "move_all_joints_to_pose_and_lock_non_arm_waist"):
            raise AttributeError("Base controller does not support moving all joints to a target pose.")

        current_full_arm_q = np.asarray(self._base.get_current_dual_arm_q(), dtype=np.float32).copy()
        current_full_arm_q[:5] = np.asarray(left_arm_target, dtype=np.float32)
        current_waist_q = float(self._base.get_current_waist_yaw_q())
        self._base.move_all_joints_to_pose_and_lock_non_arm_waist(
            current_full_arm_q,
            current_waist_q,
            duration_s=duration_s,
        )
        self.set_left_lock_q(left_arm_target)

    def __getattr__(self, name):
        return getattr(self._base, name)


class G1_23_RightArm5_IKView:
    """Expose right-arm-only gravity torques while keeping the left arm fixed."""

    _RIGHT_SLICE = slice(5, 10)

    def __init__(self, base_ik: G1_23_ArmIK, base_ctrl: G1_23_ArmController | G1_23_ArmStateReader):
        self._base_ik = base_ik
        self._base_ctrl = base_ctrl
        self._left_lock_q = np.asarray(self._base_ctrl.get_current_dual_arm_q()[:5], dtype=np.float32).copy()

    def solve_tau(self, right_arm_q):
        full_q = np.asarray(self._base_ctrl.get_current_dual_arm_q(), dtype=np.float32).copy()
        full_q[:5] = self._left_lock_q
        full_q[self._RIGHT_SLICE] = np.asarray(right_arm_q, dtype=np.float32)
        full_tau = np.asarray(self._base_ik.solve_tau(full_q), dtype=np.float32)
        return full_tau[self._RIGHT_SLICE].copy()


def setup_image_client(args: argparse.Namespace) -> dict[str, Any]:
    """Initializes and starts the image client and shared memory."""
    # image client: img_config should be the same as the configuration in image_server.py (of Robot's development computing unit)
    
    image_client = ImageClient(host=args.image_host, request_bgr=True)
    image_config = image_client.get_cam_config()
    return image_client, image_config


def _resolve_out_len(spec: dict[str, Any]) -> int:
    return int(spec.get("out_len", 2 * int(spec["dof"])))


def setup_robot_interface(args: argparse.Namespace) -> dict[str, Any]:
    """
    Initializes robot controllers and IK solvers based on configuration.
    """
    # ---------- Arm ----------
    arm_spec = ARM_CONFIG[args.arm]
    is_sim = getattr(args, "sim", False)
    send_real_robot = getattr(args, "send_real_robot", False)
    network_interface = getattr(args, "network_interface", "") or None
    use_arm_process = bool(
        send_real_robot
        and not is_sim
        and args.arm in {"G1_23", "G1_23_RightArm5"}
        and getattr(args, "arm_controller_process", False)
    )
    if not use_arm_process:
        ChannelFactoryInitialize(1 if is_sim else 0, networkInterface=network_interface)
    if args.arm in {"G1_23", "G1_23_RightArm5"} and not send_real_robot:
        dummy_arm_dof = 10 if args.arm == "G1_23_RightArm5" else int(arm_spec["dof"])
        base_arm_ctrl = G1_23_DummyArmController(
            arm_dof=dummy_arm_dof,
            waist_dof=int(arm_spec.get("waist_dof", 0)),
        )
    elif use_arm_process:
        base_arm_ctrl = G1_23_ProcessController(
            motion_mode=args.motion,
            simulation_mode=is_sim,
            network_interface=network_interface,
        )
        logger_mp.info("G1-23 DDS control is running in child process pid=%d", base_arm_ctrl._process.pid)
    else:
        base_arm_ctrl = arm_spec["controller"](
            motion_mode=args.motion,
            simulation_mode=is_sim,
            network_interface=network_interface,
        )
    base_arm_ik = arm_spec["ik_solver"]()
    if args.arm == "G1_23_RightArm5":
        arm_ctrl = G1_23_RightArm5_View(base_arm_ctrl)
        arm_ik = G1_23_RightArm5_IKView(base_arm_ik, base_arm_ctrl)
    else:
        arm_ctrl = base_arm_ctrl
        arm_ik = base_arm_ik

    # ---------- End Effector (optional) ----------
    ee_ctrl, ee_shared_mem, ee_dof = None, {}, 0

    if ee_key := getattr(args, "ee", "").lower():
        if ee_key not in EE_CONFIG:
            raise ValueError(f"Unknown end-effector '{args.ee}'. Available: {list(EE_CONFIG.keys())}")

        spec = EE_CONFIG[ee_key]
        mem_type, out_len, ee_dof = spec["shared_mem_type"].lower(), _resolve_out_len(spec), spec["dof"]
        data_lock = Lock()

        left_in, right_in = (
            (Array("d", spec["shared_mem_size"], lock=True), Array("d", spec["shared_mem_size"], lock=True))
            if mem_type == "array"
            else (Value("d", 0.0, lock=True), Value("d", 0.0, lock=True))
        )

        state_arr, action_arr = Array("d", out_len, lock=False), Array("d", out_len, lock=False)

        ee_ctrl = spec["controller"](left_in, right_in, data_lock, state_arr, action_arr, simulation_mode=is_sim)

        ee_shared_mem = {
            "left": left_in,
            "right": right_in,
            "state": state_arr,
            "action": action_arr,
            "lock": data_lock,
        }

    # ---------- Mobile Base / Lift (optional) ----------
    mobile_ctrl = None
    mobile_action_dim = 0
    base_type = getattr(args, "base_type", "legs")
    if base_type != "legs":
        mobile_ctrl = G1_Mobile_Lift_Controller(
            base_type=base_type,
            r3_controller=False,
            fps=float(getattr(args, "frequency", 30.0)),
            simulation_mode=is_sim,
        )
        mobile_action_dim = 3 if base_type == "mobile_lift" else 1

    # ---------- Simulation helpers (optional) ----------
    episode_writer = None
    if is_sim:
        reset_pose_publisher = ChannelPublisher("rt/reset_pose/cmd", String_)
        reset_pose_publisher.Init()
        from unitree_lerobot.eval_robot.utils.sim_state_topic import (
            start_sim_state_subscribe,
            start_sim_reward_subscribe,
        )

        sim_state_subscriber = start_sim_state_subscribe()
        sim_reward_subscriber = start_sim_reward_subscribe()
        if getattr(args, "save_data", False) and getattr(args, "task_dir", None):
            episode_writer = EpisodeWriter(args.task_dir, frequency=30, image_size=[640, 480])
        return {
            "arm_ctrl": arm_ctrl,
            "arm_ik": arm_ik,
            "ee_ctrl": ee_ctrl,
            "ee_shared_mem": ee_shared_mem,
            "arm_dof": int(arm_spec["dof"]),
            "waist_dof": int(arm_spec.get("waist_dof", 0)),
            "ee_dof": ee_dof,
            "mobile_ctrl": mobile_ctrl,
            "mobile_action_dim": mobile_action_dim,
            "sim_state_subscriber": sim_state_subscriber,
            "sim_reward_subscriber": sim_reward_subscriber,
            "episode_writer": episode_writer,
            "reset_pose_publisher": reset_pose_publisher,
        }
    return {
        "arm_ctrl": arm_ctrl,
        "arm_ik": arm_ik,
        "ee_ctrl": ee_ctrl,
        "ee_shared_mem": ee_shared_mem,
        "arm_dof": int(arm_spec["dof"]),
        "waist_dof": int(arm_spec.get("waist_dof", 0)),
        "ee_dof": ee_dof,
        "mobile_ctrl": mobile_ctrl,
        "mobile_action_dim": mobile_action_dim,
    }


def process_images_and_observations(img_client, camera_config, arm_ctrl):
    status = {"image_ok": False, "arm_ok": False}
    try:
        """Processes images and generates observations."""
        observation = {}
        def to_tensor_rgb(img, camera_name: str):
            if img is None:
                logger_mp.warning("%s image bgr is None", camera_name)
                return None
            if not hasattr(img, "size") or img.size == 0:
                logger_mp.warning("%s image bgr is empty", camera_name)
                return None
            if img.ndim != 3 or img.shape[2] != 3:
                logger_mp.warning("%s image has invalid shape: %s", camera_name, getattr(img, "shape", None))
                return None
            return torch.from_numpy(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        def add_image(name: str, img, camera_name: str):
            tensor = to_tensor_rgb(img, camera_name)
            if tensor is not None:
                observation[name] = tensor

        if camera_config['head_camera']['enable_zmq']:
            head_img = img_client.get_head_frame()
            if head_img is not None:
                head_rgb = to_tensor_rgb(head_img.bgr, "head")
                if head_rgb is not None:
                    observation["observation.images.cam_high"] = head_rgb
                    add_image(
                        "observation.images.cam_left_high",
                        head_img.bgr[:, :camera_config['head_camera']['image_shape'][1]//2],
                        "head_left",
                    )
                    add_image(
                        "observation.images.cam_right_high",
                        head_img.bgr[:, camera_config['head_camera']['image_shape'][1]//2:],
                        "head_right",
                    )
            else:
                logger_mp.warning("Head image is None!")

        if camera_config['left_wrist_camera']['enable_zmq']:
            left_wrist = img_client.get_left_wrist_frame()
            if left_wrist is not None:
                add_image("observation.images.cam_left_wrist", left_wrist.bgr, "left_wrist")
            else:
                logger_mp.warning("left_wrist image is None!")
        if camera_config['right_wrist_camera']['enable_zmq']:
            right_wrist = img_client.get_right_wrist_frame()
            if right_wrist is not None:
                add_image("observation.images.cam_right_wrist", right_wrist.bgr, "right_wrist")
            else:
                logger_mp.warning("right_wrist image is None!")

        status["image_ok"] = any(value is not None for value in observation.values())

    except Exception as e:
        logger_mp.error(f"[process_images_and_observations] Failed to process images: {e}")
        observation = {
            "observation.images.cam_high": None,
            "observation.images.cam_left_high": None,
            "observation.images.cam_right_high": None,
            "observation.images.cam_left_wrist": None,
            "observation.images.cam_right_wrist": None,
        }
    try:
        current_arm_q = arm_ctrl.get_current_dual_arm_q()
        status["arm_ok"] = True
    except Exception as e:
        logger_mp.error(f"[process_images_and_observations] Failed to get arm state: {e}")
        current_arm_q = None

    return observation, current_arm_q


def publish_reset_category(category: int, publisher):  # Scene Reset signal
    msg = String_(data=str(category))
    publisher.Write(msg)
    logger_mp.info(f"published reset category: {category}")
