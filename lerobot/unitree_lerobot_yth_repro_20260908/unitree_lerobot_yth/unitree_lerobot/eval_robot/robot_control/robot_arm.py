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

import numpy as np
import threading
import time
import json
from enum import IntEnum

from unitree_sdk2py.core.channel import ChannelPublisher, ChannelSubscriber, ChannelFactoryInitialize  # dds
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_ as hg_LowCmd, LowState_ as hg_LowState  # idl for g1, h1_2
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
from unitree_sdk2py.utils.crc import CRC

from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowCmd_ as go_LowCmd, LowState_ as go_LowState  # idl for h1
from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowCmd_
from unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient, action_map
from unitree_sdk2py.comm.motion_switcher.motion_switcher_client import MotionSwitcherClient
from unitree_sdk2py.g1.arm.g1_arm_action_api import ARM_ACTION_SERVICE_NAME, ROBOT_API_ID_ARM_ACTION_EXECUTE_ACTION
from unitree_sdk2py.comm.motion_switcher.motion_switcher_api import MOTION_SWITCHER_SERVICE_NAME

import logging_mp

logger_mp = logging_mp.getLogger(__name__)
logger_mp.setLevel(logging_mp.INFO)

kTopicLowCommand_Debug = "rt/lowcmd"
kTopicLowCommand_Motion = "rt/arm_sdk"
kTopicLowState = "rt/lowstate"

G1_29_Num_Motors = 35
G1_23_Num_Motors = 35
H1_2_Num_Motors = 35
H1_Num_Motors = 20


class MotorState:
    def __init__(self):
        self.q = None
        self.dq = None


class G1_29_LowState:
    def __init__(self):
        self.motor_state = [MotorState() for _ in range(G1_29_Num_Motors)]


class G1_23_LowState:
    def __init__(self):
        self.motor_state = [MotorState() for _ in range(G1_23_Num_Motors)]


class H1_2_LowState:
    def __init__(self):
        self.motor_state = [MotorState() for _ in range(H1_2_Num_Motors)]


class H1_LowState:
    def __init__(self):
        self.motor_state = [MotorState() for _ in range(H1_Num_Motors)]


class DataBuffer:
    def __init__(self):
        self.data = None
        self.lock = threading.Lock()

    def GetData(self):
        with self.lock:
            return self.data

    def SetData(self, data):
        with self.lock:
            self.data = data


def _try_release_g1_arm():
    action_name = "release arm"
    action_id = action_map.get(action_name)
    request_parameter = json.dumps({"data": action_id})

    logger_mp.info("[G1 arm] release arm client=%s", ARM_ACTION_SERVICE_NAME)
    logger_mp.info("[G1 arm] release arm request api_id=%s parameter=%s", ROBOT_API_ID_ARM_ACTION_EXECUTE_ACTION, request_parameter)

    try:
        msc = MotionSwitcherClient()
        msc.SetTimeout(3.0)
        msc.Init()
        mode_code, mode_result = msc.CheckMode()
        logger_mp.info(
            "[G1 arm] motion_switcher client=%s check_mode code=%s result=%s",
            MOTION_SWITCHER_SERVICE_NAME,
            mode_code,
            mode_result,
        )
    except Exception as exc:
        logger_mp.warning("[G1 arm] motion_switcher check_mode failed: %s", exc)

    try:
        arm_action_client = G1ArmActionClient()
        arm_action_client.SetTimeout(3.0)
        arm_action_client.Init()
        release_code = arm_action_client.ExecuteAction(action_id)
        if release_code == 3102:
            logger_mp.warning("[G1 arm] release arm rpc send request error or no route to service (client code 3102)")
        elif release_code == 3104:
            logger_mp.warning("[G1 arm] release arm rpc timeout waiting for response (client code 3104)")
        else:
            logger_mp.info("[G1 arm] release arm rpc returned code=%s", release_code)
        logger_mp.info(
            "[G1 arm] release arm final status: code=%s meaning=%s",
            release_code,
            "client_send_error" if release_code == 3102 else "client_timeout" if release_code == 3104 else "server_or_ok_response",
        )
        return release_code
    except Exception as exc:
        logger_mp.warning("[G1 arm] release arm rpc failed: %s", exc)
        return None


class G1_29_ArmController:
    def __init__(self, motion_mode=False, simulation_mode=False, network_interface=None):
        logger_mp.info("Initialize G1_29_ArmController...")
        self.q_target = np.zeros(14)
        self.tauff_target = np.zeros(14)
        self.motion_mode = motion_mode
        self.simulation_mode = simulation_mode
        self.kp_high = 300.0
        self.kd_high = 3.0
        self.kp_low = 80.0
        self.kd_low = 3.0
        self.kp_wrist = 40.0
        self.kd_wrist = 1.5

        self.all_motor_q = None
        self.arm_velocity_limit = 20.0
        self.waist_velocity_limit = 0.8
        self.control_dt = 1.0 / 250.0

        self._speed_gradual_max = False
        self._gradual_start_time = None
        self._gradual_time = None
        self._motion_weight = 0.0 if self.motion_mode else None
        self._motion_weight_start_time = None
        self._motion_weight_ramp_duration = 1.0

        if self.motion_mode:
            self.lowcmd_publisher = ChannelPublisher(kTopicLowCommand_Motion, hg_LowCmd)
        else:
            self.lowcmd_publisher = ChannelPublisher(kTopicLowCommand_Debug, hg_LowCmd)
        self.lowcmd_publisher.Init()
        self.lowstate_subscriber = ChannelSubscriber(kTopicLowState, hg_LowState)
        self.lowstate_subscriber.Init()
        self.lowstate_buffer = DataBuffer()

        # initialize subscribe thread
        self.subscribe_thread = threading.Thread(target=self._subscribe_motor_state)
        self.subscribe_thread.daemon = True
        self.subscribe_thread.start()

        while not self.lowstate_buffer.GetData():
            time.sleep(0.1)
            logger_mp.warning("[G1_29_ArmController] Waiting to subscribe dds...")
        logger_mp.info("[G1_29_ArmController] Subscribe dds ok.")

        # initialize hg's lowcmd msg
        self.crc = CRC()
        self.msg = unitree_hg_msg_dds__LowCmd_()
        self.msg.mode_pr = 0
        self.msg.mode_machine = self.get_mode_machine()
        if self.motion_mode:
            self.msg.motor_cmd[G1_23_JointIndex.kNotUsedJoint0].q = 1.0
        logger_mp.info("[G1_23_ArmController] mode_machine=%s", self.msg.mode_machine)

        self.all_motor_q = self.get_current_motor_q()
        logger_mp.info(f"Current all body motor state q:\n{self.all_motor_q} \n")
        logger_mp.info(f"Current two arms motor state q:\n{self.get_current_dual_arm_q()}\n")
        logger_mp.info("Lock all joints except two arms...\n")

        arm_indices = {member.value for member in G1_29_JointArmIndex}
        for id in G1_29_JointIndex:
            self.msg.motor_cmd[id].mode = 1
            if id.value in arm_indices:
                if self._Is_wrist_motor(id):
                    self.msg.motor_cmd[id].kp = self.kp_wrist
                    self.msg.motor_cmd[id].kd = self.kd_wrist
                else:
                    self.msg.motor_cmd[id].kp = self.kp_low
                    self.msg.motor_cmd[id].kd = self.kd_low
            else:
                if self._Is_weak_motor(id):
                    self.msg.motor_cmd[id].kp = self.kp_low
                    self.msg.motor_cmd[id].kd = self.kd_low
                else:
                    self.msg.motor_cmd[id].kp = self.kp_high
                    self.msg.motor_cmd[id].kd = self.kd_high
            self.msg.motor_cmd[id].q = self.all_motor_q[id]
        logger_mp.info("Lock OK!\n")

        # initialize publish thread
        self.publish_thread = threading.Thread(target=self._ctrl_motor_state)
        self.ctrl_lock = threading.Lock()
        self.publish_thread.daemon = True
        self.publish_thread.start()

        logger_mp.info("Initialize G1_29_ArmController OK!\n")

    def _subscribe_motor_state(self):
        while True:
            msg = self.lowstate_subscriber.Read()
            if msg is not None:
                lowstate = G1_29_LowState()
                for id in range(G1_29_Num_Motors):
                    lowstate.motor_state[id].q = msg.motor_state[id].q
                    lowstate.motor_state[id].dq = msg.motor_state[id].dq
                self.lowstate_buffer.SetData(lowstate)
            time.sleep(0.002)

    def clip_arm_q_target(self, target_q, velocity_limit):
        current_q = self.get_current_dual_arm_q()
        delta = target_q - current_q
        motion_scale = np.max(np.abs(delta)) / (velocity_limit * self.control_dt)
        clipped_arm_q_target = current_q + delta / max(motion_scale, 1.0)
        return clipped_arm_q_target

    def clip_waist_yaw_target(self, target_q, velocity_limit):
        current_q = self.get_current_waist_yaw_q()
        max_delta = velocity_limit * self.control_dt
        clipped_delta = np.clip(target_q - current_q, -max_delta, max_delta)
        return float(current_q + clipped_delta)

    def clip_waist_yaw_target(self, target_q, velocity_limit):
        current_q = self.get_current_waist_yaw_q()
        max_delta = velocity_limit * self.control_dt
        clipped_delta = np.clip(target_q - current_q, -max_delta, max_delta)
        return float(current_q + clipped_delta)

    def _ctrl_motor_state(self):
        if self.motion_mode:
            self.msg.motor_cmd[G1_29_JointIndex.kNotUsedJoint0].q = 1.0

        while True:
            start_time = time.time()

            with self.ctrl_lock:
                arm_q_target = self.q_target
                arm_tauff_target = self.tauff_target

            if self.simulation_mode:
                clipped_arm_q_target = arm_q_target
            else:
                clipped_arm_q_target = self.clip_arm_q_target(arm_q_target, velocity_limit=self.arm_velocity_limit)

            for idx, id in enumerate(G1_29_JointArmIndex):
                self.msg.motor_cmd[id].q = clipped_arm_q_target[idx]
                self.msg.motor_cmd[id].dq = 0
                self.msg.motor_cmd[id].tau = arm_tauff_target[idx]

            self.msg.crc = self.crc.Crc(self.msg)
            self.lowcmd_publisher.Write(self.msg)

            if self._speed_gradual_max is True:
                t_elapsed = start_time - self._gradual_start_time
                self.arm_velocity_limit = 20.0 + (10.0 * min(1.0, t_elapsed / 5.0))

            current_time = time.time()
            all_t_elapsed = current_time - start_time
            sleep_time = max(0, (self.control_dt - all_t_elapsed))
            time.sleep(sleep_time)
            # logger_mp.debug(f"arm_velocity_limit:{self.arm_velocity_limit}")
            # logger_mp.debug(f"sleep_time:{sleep_time}")

    def ctrl_dual_arm(self, q_target, tauff_target, waist_yaw_target=None):
        """Set control target values q & tau of the left and right arm motors."""
        with self.ctrl_lock:
            self.q_target = q_target
            self.tauff_target = tauff_target
            self.waist_yaw_target = waist_yaw_target

    def get_mode_machine(self):
        """Return current dds mode machine."""
        return self.lowstate_subscriber.Read().mode_machine

    def get_current_motor_q(self):
        """Return current state q of all body motors."""
        return np.array([self.lowstate_buffer.GetData().motor_state[id].q for id in G1_29_JointIndex])

    def get_current_dual_arm_q(self):
        """Return current state q of the left and right arm motors."""
        return np.array([self.lowstate_buffer.GetData().motor_state[id].q for id in G1_29_JointArmIndex])

    def get_current_dual_arm_dq(self):
        """Return current state dq of the left and right arm motors."""
        return np.array([self.lowstate_buffer.GetData().motor_state[id].dq for id in G1_29_JointArmIndex])

    def ctrl_dual_arm_go_home(self):
        """Move both the left and right arms of the robot to their home position by setting the target joint angles (q) and torques (tau) to zero."""
        logger_mp.info("[G1_29_ArmController] ctrl_dual_arm_go_home start...")
        max_attempts = 100
        current_attempts = 0
        with self.ctrl_lock:
            self.q_target = np.zeros(14)
            # self.tauff_target = np.zeros(14)
        tolerance = 0.05  # Tolerance threshold for joint angles to determine "close to zero", can be adjusted based on your motor's precision requirements
        while current_attempts < max_attempts:
            current_q = self.get_current_dual_arm_q()
            if np.all(np.abs(current_q) < tolerance):
                if self.motion_mode:
                    for weight in np.linspace(1, 0, num=101):
                        self.msg.motor_cmd[G1_29_JointIndex.kNotUsedJoint0].q = weight
                        time.sleep(0.02)
                logger_mp.info("[G1_29_ArmController] both arms have reached the home position.")
                break
            current_attempts += 1
            time.sleep(0.05)

    def speed_gradual_max(self, t=5.0):
        """Parameter t is the total time required for arms velocity to gradually increase to its maximum value, in seconds. The default is 5.0."""
        self._gradual_start_time = time.time()
        self._gradual_time = t
        self._speed_gradual_max = True

    def speed_instant_max(self):
        """set arms velocity to the maximum value immediately, instead of gradually increasing."""
        self.arm_velocity_limit = 30.0

    def _Is_weak_motor(self, motor_index):
        weak_motors = [
            G1_29_JointIndex.kLeftAnklePitch.value,
            G1_29_JointIndex.kRightAnklePitch.value,
            # Left arm
            G1_29_JointIndex.kLeftShoulderPitch.value,
            G1_29_JointIndex.kLeftShoulderRoll.value,
            G1_29_JointIndex.kLeftShoulderYaw.value,
            G1_29_JointIndex.kLeftElbow.value,
            # Right arm
            G1_29_JointIndex.kRightShoulderPitch.value,
            G1_29_JointIndex.kRightShoulderRoll.value,
            G1_29_JointIndex.kRightShoulderYaw.value,
            G1_29_JointIndex.kRightElbow.value,
        ]
        return motor_index.value in weak_motors

    def _Is_wrist_motor(self, motor_index):
        wrist_motors = [
            G1_29_JointIndex.kLeftWristRoll.value,
            G1_29_JointIndex.kLeftWristPitch.value,
            G1_29_JointIndex.kLeftWristyaw.value,
            G1_29_JointIndex.kRightWristRoll.value,
            G1_29_JointIndex.kRightWristPitch.value,
            G1_29_JointIndex.kRightWristYaw.value,
        ]
        return motor_index.value in wrist_motors


class G1_29_JointArmIndex(IntEnum):
    # Left arm
    kLeftShoulderPitch = 15
    kLeftShoulderRoll = 16
    kLeftShoulderYaw = 17
    kLeftElbow = 18
    kLeftWristRoll = 19
    kLeftWristPitch = 20
    kLeftWristyaw = 21

    # Right arm
    kRightShoulderPitch = 22
    kRightShoulderRoll = 23
    kRightShoulderYaw = 24
    kRightElbow = 25
    kRightWristRoll = 26
    kRightWristPitch = 27
    kRightWristYaw = 28


class G1_29_JointIndex(IntEnum):
    # Left leg
    kLeftHipPitch = 0
    kLeftHipRoll = 1
    kLeftHipYaw = 2
    kLeftKnee = 3
    kLeftAnklePitch = 4
    kLeftAnkleRoll = 5

    # Right leg
    kRightHipPitch = 6
    kRightHipRoll = 7
    kRightHipYaw = 8
    kRightKnee = 9
    kRightAnklePitch = 10
    kRightAnkleRoll = 11

    kWaistYaw = 12
    kWaistRoll = 13
    kWaistPitch = 14

    # Left arm
    kLeftShoulderPitch = 15
    kLeftShoulderRoll = 16
    kLeftShoulderYaw = 17
    kLeftElbow = 18
    kLeftWristRoll = 19
    kLeftWristPitch = 20
    kLeftWristyaw = 21

    # Right arm
    kRightShoulderPitch = 22
    kRightShoulderRoll = 23
    kRightShoulderYaw = 24
    kRightElbow = 25
    kRightWristRoll = 26
    kRightWristPitch = 27
    kRightWristYaw = 28

    # not used
    kNotUsedJoint0 = 29
    kNotUsedJoint1 = 30
    kNotUsedJoint2 = 31
    kNotUsedJoint3 = 32
    kNotUsedJoint4 = 33
    kNotUsedJoint5 = 34


class G1_23_ArmController:
    def __init__(self, motion_mode=False, simulation_mode=False, network_interface=None):
        self.simulation_mode = simulation_mode
        self.motion_mode = motion_mode

        logger_mp.info("Initialize G1_23_ArmController...")
        self.q_target = np.zeros(10)
        self.tauff_target = np.zeros(10)
        self.waist_yaw_target = None

        self.kp_high = 300.0
        self.kd_high = 3.0
        self.kp_low = 80.0
        self.kd_low = 3.0
        self.kp_wrist = 40.0
        self.kd_wrist = 1.5

        self.all_motor_q = None
        self.arm_velocity_limit = 20.0
        self.control_dt = 1.0 / 250.0

        self._speed_gradual_max = False
        self._gradual_start_time = None
        self._gradual_time = None
        self._motion_weight = 0.0 if self.motion_mode else None
        self._motion_weight_target = 0.0 if self.motion_mode else None
        self._motion_weight_transition_start = 0.0 if self.motion_mode else None
        self._motion_weight_transition_start_time = None
        self._motion_weight_transition_duration = 1.0
        self._controller_home_q = None
        self._idle_publish_mode = "hold"
        self._episode_active = False

        if self.motion_mode:
            self.lowcmd_publisher = ChannelPublisher(kTopicLowCommand_Motion, hg_LowCmd)
        else:
            self.lowcmd_publisher = ChannelPublisher(kTopicLowCommand_Debug, hg_LowCmd)
        self.lowcmd_publisher.Init()
        self.lowstate_subscriber = ChannelSubscriber(kTopicLowState, hg_LowState)
        self.lowstate_subscriber.Init()
        self.lowstate_buffer = DataBuffer()

        # initialize subscribe thread
        self.subscribe_thread = threading.Thread(target=self._subscribe_motor_state)
        self.subscribe_thread.daemon = True
        self.subscribe_thread.start()

        while not self.lowstate_buffer.GetData():
            time.sleep(0.1)
            logger_mp.warning("[G1_23_ArmController] Waiting to subscribe dds...")
        logger_mp.info("[G1_23_ArmController] Subscribe dds ok.")

        if self.motion_mode:
            _try_release_g1_arm()
            time.sleep(0.5)

        # initialize hg's lowcmd msg
        self.crc = CRC()
        self.msg = unitree_hg_msg_dds__LowCmd_()
        self.msg.mode_pr = 0
        self.msg.mode_machine = self.get_mode_machine()

        self.all_motor_q = self.get_current_motor_q()
        self.waist_yaw_target = float(self.all_motor_q[G1_23_JointIndex.kWaistYaw.value])
        self.q_target = self.get_current_dual_arm_q().copy()
        self.tauff_target = np.zeros(10)
        self._controller_home_q = self.q_target.copy()
        logger_mp.info(f"Current all body motor state q:\n{self.all_motor_q} \n")
        logger_mp.info(f"Current two arms motor state q:\n{self.get_current_dual_arm_q()}\n")
        logger_mp.info("Lock all joints except two arms...\n")

        arm_indices = {member.value for member in G1_23_JointArmIndex}
        for id in G1_23_JointIndex:
            self.msg.motor_cmd[id].mode = 1
            if id.value in arm_indices:
                if self._Is_wrist_motor(id):
                    self.msg.motor_cmd[id].kp = self.kp_wrist
                    self.msg.motor_cmd[id].kd = self.kd_wrist
                else:
                    self.msg.motor_cmd[id].kp = self.kp_low
                    self.msg.motor_cmd[id].kd = self.kd_low
            else:
                if self._Is_weak_motor(id):
                    self.msg.motor_cmd[id].kp = self.kp_low
                    self.msg.motor_cmd[id].kd = self.kd_low
                else:
                    self.msg.motor_cmd[id].kp = self.kp_high
                    self.msg.motor_cmd[id].kd = self.kd_high
            self.msg.motor_cmd[id].q = self.all_motor_q[id]
        if self.motion_mode:
            self.msg.motor_cmd[G1_23_JointIndex.kNotUsedJoint0].q = 0.0
            self._motion_weight = 0.0
            self._motion_weight_target = 0.0
            self._motion_weight_transition_start = 0.0
            self._motion_weight_transition_start_time = None
        logger_mp.info("Lock OK!\n")
        if self.motion_mode:
            logger_mp.info(
                "[G1_23_ArmController] arm_sdk weight joint index=%s initial_q=%s ramp_duration_s=%s",
                G1_23_JointIndex.kNotUsedJoint0.value,
                self.msg.motor_cmd[G1_23_JointIndex.kNotUsedJoint0].q,
                self._motion_weight_transition_duration,
            )

        # initialize publish thread
        self.publish_thread = threading.Thread(target=self._ctrl_motor_state)
        self.ctrl_lock = threading.Lock()
        self._control_diag_lock = threading.Lock()
        self._control_diag_window_start = time.perf_counter()
        self._control_diag_iterations = 0
        self._control_diag_published = 0
        self._control_diag_work_total_s = 0.0
        self._control_diag_work_max_s = 0.0
        self._control_diag_overruns = 0
        self.publish_thread.daemon = True
        self.publish_thread.start()

        logger_mp.info("Initialize G1_23_ArmController OK!\n")

    def _subscribe_motor_state(self):
        while True:
            msg = self.lowstate_subscriber.Read()
            if msg is not None:
                lowstate = G1_23_LowState()
                for id in range(G1_23_Num_Motors):
                    lowstate.motor_state[id].q = msg.motor_state[id].q
                    lowstate.motor_state[id].dq = msg.motor_state[id].dq
                self.lowstate_buffer.SetData(lowstate)
            time.sleep(0.002)

    def clip_arm_q_target(self, target_q, velocity_limit):
        current_q = self.get_current_dual_arm_q()
        delta = target_q - current_q
        motion_scale = np.max(np.abs(delta)) / (velocity_limit * self.control_dt)
        clipped_arm_q_target = current_q + delta / max(motion_scale, 1.0)
        return clipped_arm_q_target

    def _ctrl_motor_state(self):
        while True:
            work_start = time.perf_counter()
            start_time = time.time()

            with self.ctrl_lock:
                arm_q_target = self.q_target
                arm_tauff_target = self.tauff_target
                waist_yaw_target = self.waist_yaw_target
                motion_weight = self._motion_weight
                motion_weight_target = self._motion_weight_target
                motion_weight_transition_start = self._motion_weight_transition_start
                motion_weight_transition_start_time = self._motion_weight_transition_start_time
                motion_weight_transition_duration = self._motion_weight_transition_duration
                idle_publish_mode = self._idle_publish_mode
                episode_active = self._episode_active

            should_publish = episode_active or idle_publish_mode == "hold"

            if self.motion_mode:
                if motion_weight_transition_start_time is not None and motion_weight_transition_duration > 0.0:
                    alpha = min(
                        1.0,
                        max(0.0, (start_time - motion_weight_transition_start_time) / motion_weight_transition_duration),
                    )
                    motion_weight = (1.0 - alpha) * motion_weight_transition_start + alpha * motion_weight_target
                    with self.ctrl_lock:
                        self._motion_weight = motion_weight
                        if alpha >= 1.0:
                            self._motion_weight_transition_start_time = None
                            self._motion_weight_transition_start = motion_weight_target
                else:
                    motion_weight = motion_weight_target
                    with self.ctrl_lock:
                        self._motion_weight = motion_weight
                if should_publish:
                    self.msg.motor_cmd[G1_23_JointIndex.kNotUsedJoint0].q = motion_weight

            if should_publish:
                if self.simulation_mode:
                    clipped_arm_q_target = arm_q_target
                else:
                    clipped_arm_q_target = self.clip_arm_q_target(arm_q_target, velocity_limit=self.arm_velocity_limit)

                for idx, id in enumerate(G1_23_JointArmIndex):
                    self.msg.motor_cmd[id].q = clipped_arm_q_target[idx]
                    self.msg.motor_cmd[id].dq = 0
                    self.msg.motor_cmd[id].tau = arm_tauff_target[idx]

                if waist_yaw_target is not None:
                    self.msg.motor_cmd[G1_23_JointIndex.kWaistYaw].q = waist_yaw_target
                    self.msg.motor_cmd[G1_23_JointIndex.kWaistYaw].dq = 0
                    self.msg.motor_cmd[G1_23_JointIndex.kWaistYaw].tau = 0

                self.msg.crc = self.crc.Crc(self.msg)
                self.lowcmd_publisher.Write(self.msg)

            if self._speed_gradual_max is True:
                t_elapsed = start_time - self._gradual_start_time
                self.arm_velocity_limit = 20.0 + (10.0 * min(1.0, t_elapsed / 5.0))

            current_time = time.time()
            all_t_elapsed = current_time - start_time
            work_elapsed = time.perf_counter() - work_start
            with self._control_diag_lock:
                self._control_diag_iterations += 1
                self._control_diag_published += int(should_publish)
                self._control_diag_work_total_s += work_elapsed
                self._control_diag_work_max_s = max(self._control_diag_work_max_s, work_elapsed)
                self._control_diag_overruns += int(work_elapsed >= self.control_dt)
            sleep_time = max(0, (self.control_dt - all_t_elapsed))
            time.sleep(sleep_time)
            # logger_mp.debug(f"arm_velocity_limit:{self.arm_velocity_limit}")
            # logger_mp.debug(f"sleep_time:{sleep_time}")

    def ctrl_dual_arm(self, q_target, tauff_target, waist_yaw_target=None):
        """Set control target values q & tau of the left and right arm motors."""
        with self.ctrl_lock:
            self.q_target = q_target
            self.tauff_target = tauff_target
            self.waist_yaw_target = waist_yaw_target

    def set_idle_publish_mode(self, mode: str):
        if mode not in {"hold", "freeze"}:
            raise ValueError(f"Unsupported idle publish mode: {mode!r}")
        with self.ctrl_lock:
            changed = self._idle_publish_mode != mode
            self._idle_publish_mode = mode
        if changed:
            logger_mp.info("[G1_23_ArmController] idle publish mode -> %s", mode)

    def set_episode_active(self, active: bool):
        with self.ctrl_lock:
            active = bool(active)
            changed = self._episode_active != active
            self._episode_active = active
        if changed:
            logger_mp.info("[G1_23_ArmController] episode_active -> %s", active)

    def _set_motion_weight_target(self, target_weight, duration_s=1.0):
        if not self.motion_mode:
            return
        target_weight = float(max(0.0, min(1.0, target_weight)))
        duration_s = max(0.0, float(duration_s))
        with self.ctrl_lock:
            current_weight = float(self._motion_weight)
            self._motion_weight_transition_start = current_weight
            self._motion_weight_target = target_weight
            self._motion_weight_transition_duration = duration_s
            if duration_s == 0.0:
                self._motion_weight = target_weight
                self._motion_weight_transition_start = target_weight
                self._motion_weight_transition_start_time = None
            else:
                self._motion_weight_transition_start_time = time.time()

    def wait_for_motion_weight(self, target_weight, tolerance=0.02, timeout_s=3.0):
        if not self.motion_mode:
            return True
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            with self.ctrl_lock:
                current_weight = float(self._motion_weight)
            if abs(current_weight - target_weight) <= tolerance:
                return True
            time.sleep(0.02)
        return False

    def wait_for_motion_controller_pose(self, stable_seconds=0.8, timeout_s=6.0, velocity_tolerance=0.08):
        if not self.motion_mode:
            return True
        stable_start = None
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            current_dq = self.get_current_dual_arm_dq()
            if np.max(np.abs(current_dq)) <= velocity_tolerance:
                if stable_start is None:
                    stable_start = time.time()
                elif time.time() - stable_start >= stable_seconds:
                    self._controller_home_q = self.get_current_dual_arm_q().copy()
                    return True
            else:
                stable_start = None
            time.sleep(0.02)
        self._controller_home_q = self.get_current_dual_arm_q().copy()
        return False

    def start_motion_handover(self, ramp_duration_s=1.0):
        if not self.motion_mode:
            return
        current_all_q = self.get_current_motor_q().copy()
        current_arm_q = self.get_current_dual_arm_q().copy()
        with self.ctrl_lock:
            self.q_target = current_arm_q
            self.tauff_target = np.zeros(10)
            self.waist_yaw_target = float(current_all_q[G1_23_JointIndex.kWaistYaw.value])
        self._set_motion_weight_target(1.0, ramp_duration_s)

    def return_motion_control(
        self,
        ramp_duration_s=1.0,
        settle_seconds=0.8,
        timeout_s=6.0,
        position_tolerance=0.20,
        velocity_tolerance=0.08,
    ):
        if not self.motion_mode:
            return True
        current_all_q = self.get_current_motor_q().copy()
        current_arm_q = self.get_current_dual_arm_q().copy()
        with self.ctrl_lock:
            self.q_target = current_arm_q
            self.tauff_target = np.zeros(10)
            self.waist_yaw_target = float(current_all_q[G1_23_JointIndex.kWaistYaw.value])
        self._set_motion_weight_target(0.0, ramp_duration_s)
        self.wait_for_motion_weight(0.0, timeout_s=max(1.0, ramp_duration_s + 1.0))

        deadline = time.time() + timeout_s
        stable_start = None
        while time.time() < deadline:
            current_q = self.get_current_dual_arm_q()
            current_dq = self.get_current_dual_arm_dq()
            near_home = self._controller_home_q is not None and np.max(np.abs(current_q - self._controller_home_q)) <= position_tolerance
            low_velocity = np.max(np.abs(current_dq)) <= velocity_tolerance
            if near_home and low_velocity:
                if stable_start is None:
                    stable_start = time.time()
                elif time.time() - stable_start >= settle_seconds:
                    return True
            else:
                stable_start = None
            time.sleep(0.02)
        return False

    def get_mode_machine(self):
        """Return current dds mode machine."""
        return self.lowstate_subscriber.Read().mode_machine

    def get_control_loop_diagnostics(self, reset=False):
        """Return lightweight timing statistics for the 250 Hz command loop."""
        now = time.perf_counter()
        with self._control_diag_lock:
            window_s = max(0.0, now - self._control_diag_window_start)
            iterations = self._control_diag_iterations
            published = self._control_diag_published
            work_total_s = self._control_diag_work_total_s
            work_max_s = self._control_diag_work_max_s
            overruns = self._control_diag_overruns
            if reset:
                self._control_diag_window_start = now
                self._control_diag_iterations = 0
                self._control_diag_published = 0
                self._control_diag_work_total_s = 0.0
                self._control_diag_work_max_s = 0.0
                self._control_diag_overruns = 0

        return {
            "window_s": window_s,
            "iterations": iterations,
            "published": published,
            "actual_hz": iterations / window_s if window_s > 0.0 else 0.0,
            "work_avg_ms": (work_total_s / iterations * 1000.0) if iterations else 0.0,
            "work_max_ms": work_max_s * 1000.0,
            "overruns": overruns,
            "overrun_ratio": overruns / iterations if iterations else 0.0,
        }

    def get_current_motor_q(self):
        """Return current state q of all body motors."""
        lowstate = self.lowstate_buffer.GetData()
        return np.array([lowstate.motor_state[id].q for id in G1_23_JointIndex])

    def get_current_dual_arm_q(self):
        """Return current state q of the left and right arm motors."""
        lowstate = self.lowstate_buffer.GetData()
        return np.array([lowstate.motor_state[id].q for id in G1_23_JointArmIndex])

    def get_current_dual_arm_dq(self):
        """Return current state dq of the left and right arm motors."""
        lowstate = self.lowstate_buffer.GetData()
        return np.array([lowstate.motor_state[id].dq for id in G1_23_JointArmIndex])

    def get_current_waist_yaw_q(self):
        """Return current state q of the waist yaw joint."""
        lowstate = self.lowstate_buffer.GetData()
        return float(lowstate.motor_state[G1_23_JointIndex.kWaistYaw].q)

    def ctrl_dual_arm_go_home(self):
        """Move both the left and right arms of the robot to their home position by setting the target joint angles (q) and torques (tau) to zero."""
        logger_mp.info("[G1_23_ArmController] ctrl_dual_arm_go_home start...")
        max_attempts = 100
        current_attempts = 0
        with self.ctrl_lock:
            self.q_target = np.zeros(10)
            # self.tauff_target = np.zeros(10)
        tolerance = 0.05  # Tolerance threshold for joint angles to determine "close to zero", can be adjusted based on your motor's precision requirements
        while current_attempts < max_attempts:
            current_q = self.get_current_dual_arm_q()
            if np.all(np.abs(current_q) < tolerance):
                if self.motion_mode:
                    self.return_motion_control()
                logger_mp.info("[G1_23_ArmController] both arms have reached the home position.")
                break
            current_attempts += 1
            time.sleep(0.05)

    def move_all_joints_to_pose_and_lock_non_arm_waist(
        self,
        arm_target,
        waist_target,
        tolerance=0.05,
        max_attempts=160,
        duration_s=3.0,
    ):
        """
        Smoothly drive arms and waist to the requested pose once, then keep every non-arm / non-waist joint locked at zero.
        Arms and waist remain controllable after initialization.
        """
        stage_start = time.perf_counter()
        logger_mp.info("[G1_23_ArmController] move_all_joints_to_pose_and_lock_non_arm_waist start...")
        arm_indices = {member.value for member in G1_23_JointArmIndex}
        current_all_q = self.get_current_motor_q()
        current_arm_q = self.get_current_dual_arm_q()
        current_waist_q = self.get_current_waist_yaw_q()
        arm_target = np.asarray(arm_target, dtype=np.float32)
        waist_target = float(waist_target)
        steps = max(1, int(round(duration_s / self.control_dt)))
        smooth_zero_start = time.perf_counter()

        for i in range(1, steps + 1):
            alpha = i / steps
            arm_q = current_arm_q + alpha * (arm_target - current_arm_q)
            waist_q = current_waist_q + alpha * (waist_target - current_waist_q)
            with self.ctrl_lock:
                self.q_target = arm_q
                self.tauff_target = np.zeros(10)
                self.waist_yaw_target = float(waist_q)
                for motor_index in G1_23_JointIndex:
                    if motor_index.value in arm_indices or motor_index == G1_23_JointIndex.kWaistYaw:
                        continue
                    self.msg.motor_cmd[motor_index].q = float(current_all_q[motor_index.value] * (1.0 - alpha))
                    self.msg.motor_cmd[motor_index].dq = 0.0
                    self.msg.motor_cmd[motor_index].tau = 0.0
            time.sleep(self.control_dt)
        logger_mp.info(
            "[G1_23_ArmController] target-pose smooth drive complete: elapsed_s=%.3f steps=%d",
            time.perf_counter() - smooth_zero_start,
            steps,
        )

        with self.ctrl_lock:
            self.q_target = arm_target.copy()
            self.tauff_target = np.zeros(10)
            self.waist_yaw_target = waist_target
            for motor_index in G1_23_JointIndex:
                if motor_index.value not in arm_indices and motor_index != G1_23_JointIndex.kWaistYaw:
                    self.msg.motor_cmd[motor_index].q = 0.0
                self.msg.motor_cmd[motor_index].dq = 0.0
                self.msg.motor_cmd[motor_index].tau = 0.0
                if motor_index.value in arm_indices:
                    if self._Is_wrist_motor(motor_index):
                        self.msg.motor_cmd[motor_index].kp = self.kp_wrist
                        self.msg.motor_cmd[motor_index].kd = self.kd_wrist
                    else:
                        self.msg.motor_cmd[motor_index].kp = self.kp_low
                        self.msg.motor_cmd[motor_index].kd = self.kd_low
                elif motor_index == G1_23_JointIndex.kWaistYaw:
                    self.msg.motor_cmd[motor_index].kp = self.kp_low
                    self.msg.motor_cmd[motor_index].kd = self.kd_low
                elif self._Is_weak_motor(motor_index):
                    self.msg.motor_cmd[motor_index].kp = self.kp_low
                    self.msg.motor_cmd[motor_index].kd = self.kd_low
                else:
                    self.msg.motor_cmd[motor_index].kp = self.kp_high
                    self.msg.motor_cmd[motor_index].kd = self.kd_high

        current_attempts = 0
        settle_start = time.perf_counter()
        while current_attempts < max_attempts:
            arm_q = self.get_current_dual_arm_q()
            waist_q = self.get_current_waist_yaw_q()
            if np.all(np.abs(arm_q - arm_target) < tolerance) and abs(waist_q - waist_target) < tolerance:
                logger_mp.info(
                    "[G1_23_ArmController] robot reached target pose; settle_elapsed_s=%.3f total_elapsed_s=%.3f attempts=%d",
                    time.perf_counter() - settle_start,
                    time.perf_counter() - stage_start,
                    current_attempts,
                )
                return
            current_attempts += 1
            time.sleep(0.05)

        logger_mp.warning(
            "[G1_23_ArmController] target-pose initialization timed out: settle_elapsed_s=%.3f total_elapsed_s=%.3f attempts=%d; continuing with requested targets still applied.",
            time.perf_counter() - settle_start,
            time.perf_counter() - stage_start,
            current_attempts,
        )

    def move_all_joints_to_zero_and_lock_non_arm_waist(self, tolerance=0.05, max_attempts=160, duration_s=3.0):
        """
        Smoothly drive the whole body to zero once, then keep every non-arm / non-waist joint locked at zero.
        Arms and waist remain controllable after initialization.
        """
        self.move_all_joints_to_pose_and_lock_non_arm_waist(
            np.zeros(10, dtype=np.float32),
            0.0,
            tolerance=tolerance,
            max_attempts=max_attempts,
            duration_s=duration_s,
        )

    def speed_gradual_max(self, t=5.0):
        """Parameter t is the total time required for arms velocity to gradually increase to its maximum value, in seconds. The default is 5.0."""
        self._gradual_start_time = time.time()
        self._gradual_time = t
        self._speed_gradual_max = True

    def speed_instant_max(self):
        """set arms velocity to the maximum value immediately, instead of gradually increasing."""
        self.arm_velocity_limit = 30.0

    def _Is_weak_motor(self, motor_index):
        weak_motors = [
            G1_23_JointIndex.kLeftAnklePitch.value,
            G1_23_JointIndex.kRightAnklePitch.value,
            # Left arm
            G1_23_JointIndex.kLeftShoulderPitch.value,
            G1_23_JointIndex.kLeftShoulderRoll.value,
            G1_23_JointIndex.kLeftShoulderYaw.value,
            G1_23_JointIndex.kLeftElbow.value,
            # Right arm
            G1_23_JointIndex.kRightShoulderPitch.value,
            G1_23_JointIndex.kRightShoulderRoll.value,
            G1_23_JointIndex.kRightShoulderYaw.value,
            G1_23_JointIndex.kRightElbow.value,
        ]
        return motor_index.value in weak_motors

    def _Is_wrist_motor(self, motor_index):
        wrist_motors = [
            G1_23_JointIndex.kLeftWristRoll.value,
            G1_23_JointIndex.kRightWristRoll.value,
        ]
        return motor_index.value in wrist_motors


class G1_23_ArmStateReader:
    """
    Passive state reader for dry-run evaluation.
    It subscribes to lowstate but never publishes lowcmd.
    """

    def __init__(self, simulation_mode=False, network_interface=None):
        self.simulation_mode = simulation_mode

        logger_mp.info("Initialize G1_23_ArmStateReader...")
        self.lowstate_subscriber = ChannelSubscriber(kTopicLowState, hg_LowState)
        self.lowstate_subscriber.Init()
        self.lowstate_buffer = DataBuffer()

        self.subscribe_thread = threading.Thread(target=self._subscribe_motor_state)
        self.subscribe_thread.daemon = True
        self.subscribe_thread.start()

        while not self.lowstate_buffer.GetData():
            time.sleep(0.1)
            logger_mp.warning("[G1_23_ArmStateReader] Waiting to subscribe dds...")
        logger_mp.info("[G1_23_ArmStateReader] Subscribe dds ok.")

    def _subscribe_motor_state(self):
        while True:
            msg = self.lowstate_subscriber.Read()
            if msg is not None:
                lowstate = G1_23_LowState()
                for motor_id in range(G1_23_Num_Motors):
                    lowstate.motor_state[motor_id].q = msg.motor_state[motor_id].q
                    lowstate.motor_state[motor_id].dq = msg.motor_state[motor_id].dq
                self.lowstate_buffer.SetData(lowstate)
            time.sleep(0.002)

    def get_current_motor_q(self):
        return np.array([self.lowstate_buffer.GetData().motor_state[motor_id].q for motor_id in G1_23_JointIndex])

    def get_current_dual_arm_q(self):
        return np.array([self.lowstate_buffer.GetData().motor_state[motor_id].q for motor_id in G1_23_JointArmIndex])

    def get_current_dual_arm_dq(self):
        return np.array([self.lowstate_buffer.GetData().motor_state[motor_id].dq for motor_id in G1_23_JointArmIndex])

    def get_current_waist_yaw_q(self):
        return float(self.lowstate_buffer.GetData().motor_state[G1_23_JointIndex.kWaistYaw].q)


class G1_23_DummyArmController:
    """
    Dummy arm controller for dry-run evaluation without DDS connection.
    Returns zero states and silently ignores all control commands.
    Useful when only ROS2 image input is needed and no robot is connected.
    """

    def __init__(self, arm_dof=10, waist_dof=1):
        self._arm_dof = arm_dof
        self._waist_dof = waist_dof
        self._arm_q = np.zeros(arm_dof, dtype=np.float32)
        self._waist_q = 0.0
        self.simulation_mode = True
        self.motion_mode = False
        logger_mp.info(
            "Initialize G1_23_DummyArmController (arm_dof=%d, waist_dof=%d). No DDS connection required.",
            arm_dof,
            waist_dof,
        )

    def get_current_motor_q(self):
        """Return zero array for all 35 motors."""
        return np.zeros(G1_23_Num_Motors, dtype=np.float32)

    def get_current_dual_arm_q(self):
        """Return current arm joint angles (zeros initially, updated by ctrl_dual_arm)."""
        return self._arm_q.copy()

    def get_current_dual_arm_dq(self):
        """Return zero velocities."""
        return np.zeros(self._arm_dof, dtype=np.float32)

    def get_current_waist_yaw_q(self):
        """Return current waist yaw angle."""
        return self._waist_q

    def ctrl_dual_arm(self, q_target, tauff_target, waist_yaw_target=None):
        """Silently record the target (for state tracking in dry-run)."""
        self._arm_q = np.asarray(q_target[: self._arm_dof], dtype=np.float32).copy()
        if waist_yaw_target is not None:
            self._waist_q = float(waist_yaw_target)

    def ctrl_dual_arm_go_home(self):
        """No-op for dummy controller."""
        self._arm_q = np.zeros(self._arm_dof, dtype=np.float32)
        self._waist_q = 0.0

    def move_all_joints_to_pose_and_lock_non_arm_waist(self, arm_target, waist_target, **kwargs):
        """No-op for dummy controller."""
        pass

    def start_motion_handover(self, *args, **kwargs):
        """No-op for dummy controller."""
        pass

    def return_motion_control(self, *args, **kwargs):
        """No-op for dummy controller."""
        return True

    def wait_for_motion_controller_pose(self, *args, **kwargs):
        """No-op for dummy controller."""
        return True

    def wait_for_motion_weight(self, *args, **kwargs):
        """No-op for dummy controller."""
        return True


class G1_23_JointArmIndex(IntEnum):
    # Left arm
    kLeftShoulderPitch = 15
    kLeftShoulderRoll = 16
    kLeftShoulderYaw = 17
    kLeftElbow = 18
    kLeftWristRoll = 19

    # Right arm
    kRightShoulderPitch = 22
    kRightShoulderRoll = 23
    kRightShoulderYaw = 24
    kRightElbow = 25
    kRightWristRoll = 26


class G1_23_JointIndex(IntEnum):
    # Left leg
    kLeftHipPitch = 0
    kLeftHipRoll = 1
    kLeftHipYaw = 2
    kLeftKnee = 3
    kLeftAnklePitch = 4
    kLeftAnkleRoll = 5

    # Right leg
    kRightHipPitch = 6
    kRightHipRoll = 7
    kRightHipYaw = 8
    kRightKnee = 9
    kRightAnklePitch = 10
    kRightAnkleRoll = 11

    kWaistYaw = 12
    kWaistRollNotUsed = 13
    kWaistPitchNotUsed = 14

    # Left arm
    kLeftShoulderPitch = 15
    kLeftShoulderRoll = 16
    kLeftShoulderYaw = 17
    kLeftElbow = 18
    kLeftWristRoll = 19
    kLeftWristPitchNotUsed = 20
    kLeftWristyawNotUsed = 21

    # Right arm
    kRightShoulderPitch = 22
    kRightShoulderRoll = 23
    kRightShoulderYaw = 24
    kRightElbow = 25
    kRightWristRoll = 26
    kRightWristPitchNotUsed = 27
    kRightWristYawNotUsed = 28

    # not used
    kNotUsedJoint0 = 29
    kNotUsedJoint1 = 30
    kNotUsedJoint2 = 31
    kNotUsedJoint3 = 32
    kNotUsedJoint4 = 33
    kNotUsedJoint5 = 34


class H1_2_ArmController:
    def __init__(self, simulation_mode=False):
        self.simulation_mode = simulation_mode

        logger_mp.info("Initialize H1_2_ArmController...")
        self.q_target = np.zeros(14)
        self.tauff_target = np.zeros(14)

        self.kp_high = 300.0
        self.kd_high = 5.0
        self.kp_low = 140.0
        self.kd_low = 3.0
        self.kp_wrist = 50.0
        self.kd_wrist = 2.0

        self.all_motor_q = None
        self.arm_velocity_limit = 20.0
        self.control_dt = 1.0 / 250.0

        self._speed_gradual_max = False
        self._gradual_start_time = None
        self._gradual_time = None

        # initialize lowcmd publisher and lowstate subscriber
        if self.simulation_mode:
            ChannelFactoryInitialize(1)
        else:
            ChannelFactoryInitialize(0)
        self.lowcmd_publisher = ChannelPublisher(kTopicLowCommand_Debug, hg_LowCmd)
        self.lowcmd_publisher.Init()
        self.lowstate_subscriber = ChannelSubscriber(kTopicLowState, hg_LowState)
        self.lowstate_subscriber.Init()
        self.lowstate_buffer = DataBuffer()

        # initialize subscribe thread
        self.subscribe_thread = threading.Thread(target=self._subscribe_motor_state)
        self.subscribe_thread.daemon = True
        self.subscribe_thread.start()

        while not self.lowstate_buffer.GetData():
            time.sleep(0.1)
            logger_mp.warning("[H1_2_ArmController] Waiting to subscribe dds...")
        logger_mp.info("[H1_2_ArmController] Subscribe dds ok.")

        # initialize hg's lowcmd msg
        self.crc = CRC()
        self.msg = unitree_hg_msg_dds__LowCmd_()
        self.msg.mode_pr = 0
        self.msg.mode_machine = self.get_mode_machine()

        self.all_motor_q = self.get_current_motor_q()
        logger_mp.info(f"Current all body motor state q:\n{self.all_motor_q} \n")
        logger_mp.info(f"Current two arms motor state q:\n{self.get_current_dual_arm_q()}\n")
        logger_mp.info("Lock all joints except two arms...\n")

        arm_indices = {member.value for member in H1_2_JointArmIndex}
        for id in H1_2_JointIndex:
            self.msg.motor_cmd[id].mode = 1
            if id.value in arm_indices:
                if self._Is_wrist_motor(id):
                    self.msg.motor_cmd[id].kp = self.kp_wrist
                    self.msg.motor_cmd[id].kd = self.kd_wrist
                else:
                    self.msg.motor_cmd[id].kp = self.kp_low
                    self.msg.motor_cmd[id].kd = self.kd_low
            else:
                if self._Is_weak_motor(id):
                    self.msg.motor_cmd[id].kp = self.kp_low
                    self.msg.motor_cmd[id].kd = self.kd_low
                else:
                    self.msg.motor_cmd[id].kp = self.kp_high
                    self.msg.motor_cmd[id].kd = self.kd_high
            self.msg.motor_cmd[id].q = self.all_motor_q[id]
        logger_mp.info("Lock OK!\n")

        # initialize publish thread
        self.publish_thread = threading.Thread(target=self._ctrl_motor_state)
        self.ctrl_lock = threading.Lock()
        self.publish_thread.daemon = True
        self.publish_thread.start()

        logger_mp.info("Initialize H1_2_ArmController OK!\n")

    def _subscribe_motor_state(self):
        while True:
            msg = self.lowstate_subscriber.Read()
            if msg is not None:
                lowstate = H1_2_LowState()
                for id in range(H1_2_Num_Motors):
                    lowstate.motor_state[id].q = msg.motor_state[id].q
                    lowstate.motor_state[id].dq = msg.motor_state[id].dq
                self.lowstate_buffer.SetData(lowstate)
            time.sleep(0.002)

    def clip_arm_q_target(self, target_q, velocity_limit):
        current_q = self.get_current_dual_arm_q()
        delta = target_q - current_q
        motion_scale = np.max(np.abs(delta)) / (velocity_limit * self.control_dt)
        clipped_arm_q_target = current_q + delta / max(motion_scale, 1.0)
        return clipped_arm_q_target

    def _ctrl_motor_state(self):
        while True:
            start_time = time.time()

            with self.ctrl_lock:
                arm_q_target = self.q_target
                arm_tauff_target = self.tauff_target

            if self.simulation_mode:
                clipped_arm_q_target = arm_q_target
            else:
                clipped_arm_q_target = self.clip_arm_q_target(arm_q_target, velocity_limit=self.arm_velocity_limit)

            for idx, id in enumerate(H1_2_JointArmIndex):
                self.msg.motor_cmd[id].q = clipped_arm_q_target[idx]
                self.msg.motor_cmd[id].dq = 0
                self.msg.motor_cmd[id].tau = arm_tauff_target[idx]

            self.msg.crc = self.crc.Crc(self.msg)
            self.lowcmd_publisher.Write(self.msg)

            if self._speed_gradual_max is True:
                t_elapsed = start_time - self._gradual_start_time
                self.arm_velocity_limit = 20.0 + (10.0 * min(1.0, t_elapsed / 5.0))

            current_time = time.time()
            all_t_elapsed = current_time - start_time
            sleep_time = max(0, (self.control_dt - all_t_elapsed))
            time.sleep(sleep_time)
            # logger_mp.debug(f"arm_velocity_limit:{self.arm_velocity_limit}")
            # logger_mp.debug(f"sleep_time:{sleep_time}")

    def ctrl_dual_arm(self, q_target, tauff_target, waist_yaw_target=None):
        """Set control target values q & tau of the left and right arm motors."""
        with self.ctrl_lock:
            self.q_target = q_target
            self.tauff_target = tauff_target
            self.waist_yaw_target = waist_yaw_target

    def get_mode_machine(self):
        """Return current dds mode machine."""
        return self.lowstate_subscriber.Read().mode_machine

    def get_current_motor_q(self):
        """Return current state q of all body motors."""
        return np.array([self.lowstate_buffer.GetData().motor_state[id].q for id in H1_2_JointIndex])

    def get_current_dual_arm_q(self):
        """Return current state q of the left and right arm motors."""
        return np.array([self.lowstate_buffer.GetData().motor_state[id].q for id in H1_2_JointArmIndex])

    def get_current_dual_arm_dq(self):
        """Return current state dq of the left and right arm motors."""
        return np.array([self.lowstate_buffer.GetData().motor_state[id].dq for id in H1_2_JointArmIndex])

    def ctrl_dual_arm_go_home(self):
        """Move both the left and right arms of the robot to their home position by setting the target joint angles (q) and torques (tau) to zero."""
        logger_mp.info("[H1_2_ArmController] ctrl_dual_arm_go_home start...")
        max_attempts = 100
        current_attempts = 0
        with self.ctrl_lock:
            self.q_target = np.zeros(14)
            # self.tauff_target = np.zeros(14)
        tolerance = 0.05  # Tolerance threshold for joint angles to determine "close to zero", can be adjusted based on your motor's precision requirements
        while current_attempts < max_attempts:
            current_q = self.get_current_dual_arm_q()
            if np.all(np.abs(current_q) < tolerance):
                logger_mp.info("[H1_2_ArmController] both arms have reached the home position.")
                break
            current_attempts += 1
            time.sleep(0.05)

    def speed_gradual_max(self, t=5.0):
        """Parameter t is the total time required for arms velocity to gradually increase to its maximum value, in seconds. The default is 5.0."""
        self._gradual_start_time = time.time()
        self._gradual_time = t
        self._speed_gradual_max = True

    def speed_instant_max(self):
        """set arms velocity to the maximum value immediately, instead of gradually increasing."""
        self.arm_velocity_limit = 30.0

    def _Is_weak_motor(self, motor_index):
        weak_motors = [
            H1_2_JointIndex.kLeftAnkle.value,
            H1_2_JointIndex.kRightAnkle.value,
            # Left arm
            H1_2_JointIndex.kLeftShoulderPitch.value,
            H1_2_JointIndex.kLeftShoulderRoll.value,
            H1_2_JointIndex.kLeftShoulderYaw.value,
            H1_2_JointIndex.kLeftElbowPitch.value,
            # Right arm
            H1_2_JointIndex.kRightShoulderPitch.value,
            H1_2_JointIndex.kRightShoulderRoll.value,
            H1_2_JointIndex.kRightShoulderYaw.value,
            H1_2_JointIndex.kRightElbowPitch.value,
        ]
        return motor_index.value in weak_motors

    def _Is_wrist_motor(self, motor_index):
        wrist_motors = [
            H1_2_JointIndex.kLeftElbowRoll.value,
            H1_2_JointIndex.kLeftWristPitch.value,
            H1_2_JointIndex.kLeftWristyaw.value,
            H1_2_JointIndex.kRightElbowRoll.value,
            H1_2_JointIndex.kRightWristPitch.value,
            H1_2_JointIndex.kRightWristYaw.value,
        ]
        return motor_index.value in wrist_motors


class H1_2_JointArmIndex(IntEnum):
    # Left arm
    kLeftShoulderPitch = 13
    kLeftShoulderRoll = 14
    kLeftShoulderYaw = 15
    kLeftElbowPitch = 16
    kLeftElbowRoll = 17
    kLeftWristPitch = 18
    kLeftWristyaw = 19

    # Right arm
    kRightShoulderPitch = 20
    kRightShoulderRoll = 21
    kRightShoulderYaw = 22
    kRightElbowPitch = 23
    kRightElbowRoll = 24
    kRightWristPitch = 25
    kRightWristYaw = 26


class H1_2_JointIndex(IntEnum):
    # Left leg
    kLeftHipYaw = 0
    kLeftHipRoll = 1
    kLeftHipPitch = 2
    kLeftKnee = 3
    kLeftAnkle = 4
    kLeftAnkleRoll = 5

    # Right leg
    kRightHipYaw = 6
    kRightHipRoll = 7
    kRightHipPitch = 8
    kRightKnee = 9
    kRightAnkle = 10
    kRightAnkleRoll = 11

    kWaistYaw = 12

    # Left arm
    kLeftShoulderPitch = 13
    kLeftShoulderRoll = 14
    kLeftShoulderYaw = 15
    kLeftElbowPitch = 16
    kLeftElbowRoll = 17
    kLeftWristPitch = 18
    kLeftWristyaw = 19

    # Right arm
    kRightShoulderPitch = 20
    kRightShoulderRoll = 21
    kRightShoulderYaw = 22
    kRightElbowPitch = 23
    kRightElbowRoll = 24
    kRightWristPitch = 25
    kRightWristYaw = 26

    kNotUsedJoint0 = 27
    kNotUsedJoint1 = 28
    kNotUsedJoint2 = 29
    kNotUsedJoint3 = 30
    kNotUsedJoint4 = 31
    kNotUsedJoint5 = 32
    kNotUsedJoint6 = 33
    kNotUsedJoint7 = 34


class H1_ArmController:
    def __init__(self, simulation_mode=False):
        self.simulation_mode = simulation_mode

        logger_mp.info("Initialize H1_ArmController...")
        self.q_target = np.zeros(8)
        self.tauff_target = np.zeros(8)

        self.kp_high = 300.0
        self.kd_high = 5.0
        self.kp_low = 140.0
        self.kd_low = 3.0

        self.all_motor_q = None
        self.arm_velocity_limit = 20.0
        self.control_dt = 1.0 / 250.0

        self._speed_gradual_max = False
        self._gradual_start_time = None
        self._gradual_time = None

        # initialize lowcmd publisher and lowstate subscriber
        if self.simulation_mode:
            ChannelFactoryInitialize(1)
        else:
            ChannelFactoryInitialize(0)
        self.lowcmd_publisher = ChannelPublisher(kTopicLowCommand_Debug, go_LowCmd)
        self.lowcmd_publisher.Init()
        self.lowstate_subscriber = ChannelSubscriber(kTopicLowState, go_LowState)
        self.lowstate_subscriber.Init()
        self.lowstate_buffer = DataBuffer()

        # initialize subscribe thread
        self.subscribe_thread = threading.Thread(target=self._subscribe_motor_state)
        self.subscribe_thread.daemon = True
        self.subscribe_thread.start()

        while not self.lowstate_buffer.GetData():
            time.sleep(0.1)
            logger_mp.warning("[H1_ArmController] Waiting to subscribe dds...")
        logger_mp.info("[H1_ArmController] Subscribe dds ok.")

        # initialize h1's lowcmd msg
        self.crc = CRC()
        self.msg = unitree_go_msg_dds__LowCmd_()
        self.msg.head[0] = 0xFE
        self.msg.head[1] = 0xEF
        self.msg.level_flag = 0xFF
        self.msg.gpio = 0

        self.all_motor_q = self.get_current_motor_q()
        logger_mp.info(f"Current all body motor state q:\n{self.all_motor_q} \n")
        logger_mp.info(f"Current two arms motor state q:\n{self.get_current_dual_arm_q()}\n")
        logger_mp.info("Lock all joints except two arms...\n")

        for id in H1_JointIndex:
            if self._Is_weak_motor(id):
                self.msg.motor_cmd[id].kp = self.kp_low
                self.msg.motor_cmd[id].kd = self.kd_low
                self.msg.motor_cmd[id].mode = 0x01
            else:
                self.msg.motor_cmd[id].kp = self.kp_high
                self.msg.motor_cmd[id].kd = self.kd_high
                self.msg.motor_cmd[id].mode = 0x0A
            self.msg.motor_cmd[id].q = self.all_motor_q[id]
        logger_mp.info("Lock OK!\n")

        # initialize publish thread
        self.publish_thread = threading.Thread(target=self._ctrl_motor_state)
        self.ctrl_lock = threading.Lock()
        self.publish_thread.daemon = True
        self.publish_thread.start()

        logger_mp.info("Initialize H1_ArmController OK!\n")

    def _subscribe_motor_state(self):
        while True:
            msg = self.lowstate_subscriber.Read()
            if msg is not None:
                lowstate = H1_LowState()
                for id in range(H1_Num_Motors):
                    lowstate.motor_state[id].q = msg.motor_state[id].q
                    lowstate.motor_state[id].dq = msg.motor_state[id].dq
                self.lowstate_buffer.SetData(lowstate)
            time.sleep(0.002)

    def clip_arm_q_target(self, target_q, velocity_limit):
        current_q = self.get_current_dual_arm_q()
        delta = target_q - current_q
        motion_scale = np.max(np.abs(delta)) / (velocity_limit * self.control_dt)
        clipped_arm_q_target = current_q + delta / max(motion_scale, 1.0)
        return clipped_arm_q_target

    def _ctrl_motor_state(self):
        while True:
            start_time = time.time()

            with self.ctrl_lock:
                arm_q_target = self.q_target
                arm_tauff_target = self.tauff_target

            if self.simulation_mode:
                clipped_arm_q_target = arm_q_target
            else:
                clipped_arm_q_target = self.clip_arm_q_target(arm_q_target, velocity_limit=self.arm_velocity_limit)

            for idx, id in enumerate(H1_JointArmIndex):
                self.msg.motor_cmd[id].q = clipped_arm_q_target[idx]
                self.msg.motor_cmd[id].dq = 0
                self.msg.motor_cmd[id].tau = arm_tauff_target[idx]

            self.msg.crc = self.crc.Crc(self.msg)
            self.lowcmd_publisher.Write(self.msg)

            if self._speed_gradual_max is True:
                t_elapsed = start_time - self._gradual_start_time
                self.arm_velocity_limit = 20.0 + (10.0 * min(1.0, t_elapsed / 5.0))

            current_time = time.time()
            all_t_elapsed = current_time - start_time
            sleep_time = max(0, (self.control_dt - all_t_elapsed))
            time.sleep(sleep_time)
            # logger_mp.debug(f"arm_velocity_limit:{self.arm_velocity_limit}")
            # logger_mp.debug(f"sleep_time:{sleep_time}")

    def ctrl_dual_arm(self, q_target, tauff_target, waist_yaw_target=None):
        """Set control target values q & tau of the left and right arm motors."""
        with self.ctrl_lock:
            self.q_target = q_target
            self.tauff_target = tauff_target
            self.waist_yaw_target = waist_yaw_target

    def get_current_motor_q(self):
        """Return current state q of all body motors."""
        return np.array([self.lowstate_buffer.GetData().motor_state[id].q for id in H1_JointIndex])

    def get_current_dual_arm_q(self):
        """Return current state q of the left and right arm motors."""
        return np.array([self.lowstate_buffer.GetData().motor_state[id].q for id in H1_JointArmIndex])

    def get_current_dual_arm_dq(self):
        """Return current state dq of the left and right arm motors."""
        return np.array([self.lowstate_buffer.GetData().motor_state[id].dq for id in H1_JointArmIndex])

    def ctrl_dual_arm_go_home(self):
        """Move both the left and right arms of the robot to their home position by setting the target joint angles (q) and torques (tau) to zero."""
        logger_mp.info("[H1_ArmController] ctrl_dual_arm_go_home start...")
        max_attempts = 100
        current_attempts = 0
        with self.ctrl_lock:
            self.q_target = np.zeros(8)
            # self.tauff_target = np.zeros(8)
        tolerance = 0.05  # Tolerance threshold for joint angles to determine "close to zero", can be adjusted based on your motor's precision requirements
        while current_attempts < max_attempts:
            current_q = self.get_current_dual_arm_q()
            if np.all(np.abs(current_q) < tolerance):
                logger_mp.info("[H1_ArmController] both arms have reached the home position.")
                break
            current_attempts += 1
            time.sleep(0.05)

    def speed_gradual_max(self, t=5.0):
        """Parameter t is the total time required for arms velocity to gradually increase to its maximum value, in seconds. The default is 5.0."""
        self._gradual_start_time = time.time()
        self._gradual_time = t
        self._speed_gradual_max = True

    def speed_instant_max(self):
        """set arms velocity to the maximum value immediately, instead of gradually increasing."""
        self.arm_velocity_limit = 30.0

    def _Is_weak_motor(self, motor_index):
        weak_motors = [
            H1_JointIndex.kLeftAnkle.value,
            H1_JointIndex.kRightAnkle.value,
            # Left arm
            H1_JointIndex.kLeftShoulderPitch.value,
            H1_JointIndex.kLeftShoulderRoll.value,
            H1_JointIndex.kLeftShoulderYaw.value,
            H1_JointIndex.kLeftElbow.value,
            # Right arm
            H1_JointIndex.kRightShoulderPitch.value,
            H1_JointIndex.kRightShoulderRoll.value,
            H1_JointIndex.kRightShoulderYaw.value,
            H1_JointIndex.kRightElbow.value,
        ]
        return motor_index.value in weak_motors


class H1_JointArmIndex(IntEnum):
    # Unlike G1 and H1_2, the arm order in DDS messages for H1 is right then left.
    # Therefore, the purpose of switching the order here is to maintain consistency with G1 and H1_2.
    # Left arm
    kLeftShoulderPitch = 16
    kLeftShoulderRoll = 17
    kLeftShoulderYaw = 18
    kLeftElbow = 19
    # Right arm
    kRightShoulderPitch = 12
    kRightShoulderRoll = 13
    kRightShoulderYaw = 14
    kRightElbow = 15


class H1_JointIndex(IntEnum):
    kRightHipRoll = 0
    kRightHipPitch = 1
    kRightKnee = 2
    kLeftHipRoll = 3
    kLeftHipPitch = 4
    kLeftKnee = 5
    kWaistYaw = 6
    kLeftHipYaw = 7
    kRightHipYaw = 8
    kNotUsedJoint = 9
    kLeftAnkle = 10
    kRightAnkle = 11
    # Right arm
    kRightShoulderPitch = 12
    kRightShoulderRoll = 13
    kRightShoulderYaw = 14
    kRightElbow = 15
    # Left arm
    kLeftShoulderPitch = 16
    kLeftShoulderRoll = 17
    kLeftShoulderYaw = 18
    kLeftElbow = 19


if __name__ == "__main__":
    from robot_arm_ik import G1_29_ArmIK
    import pinocchio as pin

    arm_ik = G1_29_ArmIK(Unit_Test=True, Visualization=False)
    arm = G1_29_ArmController(simulation_mode=True)
    # arm_ik = G1_23_ArmIK(Unit_Test = True, Visualization = False)
    # arm = G1_23_ArmController()
    # arm_ik = H1_2_ArmIK(Unit_Test = True, Visualization = False)
    # arm = H1_2_ArmController()
    # arm_ik = H1_ArmIK(Unit_Test = True, Visualization = True)
    # arm = H1_ArmController()

    # initial position
    L_tf_target = pin.SE3(
        pin.Quaternion(1, 0, 0, 0),
        np.array([0.25, +0.25, 0.1]),
    )

    R_tf_target = pin.SE3(
        pin.Quaternion(1, 0, 0, 0),
        np.array([0.25, -0.25, 0.1]),
    )

    rotation_speed = 0.005  # Rotation speed in radians per iteration

    user_input = input("Please enter the start signal (enter 's' to start the subsequent program): \n")
    if user_input.lower() == "s":
        step = 0
        arm.speed_gradual_max()
        while True:
            if step <= 120:
                angle = rotation_speed * step
                L_quat = pin.Quaternion(np.cos(angle / 2), 0, np.sin(angle / 2), 0)  # y axis
                R_quat = pin.Quaternion(np.cos(angle / 2), 0, 0, np.sin(angle / 2))  # z axis

                L_tf_target.translation += np.array([0.001, 0.001, 0.001])
                R_tf_target.translation += np.array([0.001, -0.001, 0.001])
            else:
                angle = rotation_speed * (240 - step)
                L_quat = pin.Quaternion(np.cos(angle / 2), 0, np.sin(angle / 2), 0)  # y axis
                R_quat = pin.Quaternion(np.cos(angle / 2), 0, 0, np.sin(angle / 2))  # z axis

                L_tf_target.translation -= np.array([0.001, 0.001, 0.001])
                R_tf_target.translation -= np.array([0.001, -0.001, 0.001])

            L_tf_target.rotation = L_quat.toRotationMatrix()
            R_tf_target.rotation = R_quat.toRotationMatrix()

            current_lr_arm_q = arm.get_current_dual_arm_q()
            current_lr_arm_dq = arm.get_current_dual_arm_dq()

            sol_q, sol_tauff = arm_ik.solve_ik(
                L_tf_target.homogeneous, R_tf_target.homogeneous, current_lr_arm_q, current_lr_arm_dq
            )

            arm.ctrl_dual_arm(sol_q, sol_tauff)

            step += 1
            if step > 240:
                step = 0
            time.sleep(0.01)
