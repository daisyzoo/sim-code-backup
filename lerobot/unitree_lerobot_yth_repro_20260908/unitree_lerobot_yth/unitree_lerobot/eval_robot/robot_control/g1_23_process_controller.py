"""Process-isolated G1-23 controller proxy.

The child process owns the Unitree DDS objects and the controller's 250 Hz
publisher/subscriber threads.  The policy process exchanges high-rate targets
and state through shared memory and uses a pipe only for infrequent blocking
controller operations.
"""

from __future__ import annotations

import multiprocessing as mp
import threading
import time
import traceback
from typing import Any

import numpy as np


_ARM_DOF = 10
_MOTOR_DOF = 35


def _copy_into(shared_array, values) -> None:
    shared_array[:] = np.asarray(values, dtype=np.float64).reshape(-1)


def _controller_worker(
    connection,
    stop_event,
    target_lock,
    target_q,
    target_tau,
    target_waist,
    target_waist_valid,
    target_sequence,
    state_lock,
    state_motor_q,
    state_arm_q,
    state_arm_dq,
    state_waist,
    state_ready,
    motion_mode: bool,
    simulation_mode: bool,
    network_interface: str | None,
    use_dummy: bool,
) -> None:
    controller = None
    try:
        # Imports stay in the child so the parent never constructs DDS objects.
        from unitree_lerobot.eval_robot.robot_control.robot_arm import (
            G1_23_ArmController,
            G1_23_DummyArmController,
        )

        if use_dummy:
            controller = G1_23_DummyArmController(arm_dof=_ARM_DOF, waist_dof=1)
        else:
            from unitree_sdk2py.core.channel import ChannelFactoryInitialize

            ChannelFactoryInitialize(1 if simulation_mode else 0, networkInterface=network_interface)
            controller = G1_23_ArmController(
                motion_mode=motion_mode,
                simulation_mode=simulation_mode,
                network_interface=network_interface,
            )

        def mirror_state() -> None:
            while not stop_event.is_set():
                try:
                    motor_q = controller.get_current_motor_q()
                    arm_q = controller.get_current_dual_arm_q()
                    arm_dq = controller.get_current_dual_arm_dq()
                    waist_q = controller.get_current_waist_yaw_q()
                    with state_lock:
                        _copy_into(state_motor_q, motor_q)
                        _copy_into(state_arm_q, arm_q)
                        _copy_into(state_arm_dq, arm_dq)
                        state_waist.value = float(waist_q)
                        state_ready.value = True
                except Exception:
                    pass
                stop_event.wait(0.004)

        def relay_targets() -> None:
            last_sequence = 0
            while not stop_event.is_set():
                with target_lock:
                    sequence = int(target_sequence.value)
                    if sequence != last_sequence:
                        q = np.frombuffer(target_q, dtype=np.float64).copy()
                        tau = np.frombuffer(target_tau, dtype=np.float64).copy()
                        waist = float(target_waist.value) if target_waist_valid.value else None
                    else:
                        q = tau = waist = None
                if sequence != last_sequence:
                    controller.ctrl_dual_arm(q, tau, waist)
                    last_sequence = sequence
                stop_event.wait(0.002)

        threading.Thread(target=mirror_state, daemon=True).start()
        threading.Thread(target=relay_targets, daemon=True).start()
        connection.send({"ok": True, "event": "ready"})

        while not stop_event.is_set():
            if not connection.poll(0.1):
                continue
            request = connection.recv()
            if request["method"] == "close":
                connection.send({"ok": True, "result": None})
                break
            try:
                result = getattr(controller, request["method"])(*request["args"], **request["kwargs"])
                connection.send({"ok": True, "result": result})
            except Exception:
                connection.send({"ok": False, "error": traceback.format_exc()})
    except Exception:
        try:
            connection.send({"ok": False, "event": "startup", "error": traceback.format_exc()})
        except Exception:
            pass
    finally:
        stop_event.set()
        try:
            connection.close()
        except Exception:
            pass


class G1_23_ProcessController:
    """Parent-side API-compatible proxy for :class:`G1_23_ArmController`."""

    def __init__(
        self,
        motion_mode: bool = False,
        simulation_mode: bool = False,
        network_interface: str | None = None,
        startup_timeout_s: float = 60.0,
        *,
        _use_dummy: bool = False,
    ) -> None:
        self.motion_mode = motion_mode
        self.simulation_mode = simulation_mode
        self.control_dt = 1.0 / 250.0
        self._closed = False
        self._rpc_lock = threading.Lock()
        ctx = mp.get_context("spawn")
        self._stop_event = ctx.Event()
        self._target_lock = ctx.Lock()
        self._target_q = ctx.RawArray("d", _ARM_DOF)
        self._target_tau = ctx.RawArray("d", _ARM_DOF)
        self._target_waist = ctx.RawValue("d", 0.0)
        self._target_waist_valid = ctx.RawValue("b", False)
        self._target_sequence = ctx.RawValue("Q", 0)
        self._state_lock = ctx.Lock()
        self._state_motor_q = ctx.RawArray("d", _MOTOR_DOF)
        self._state_arm_q = ctx.RawArray("d", _ARM_DOF)
        self._state_arm_dq = ctx.RawArray("d", _ARM_DOF)
        self._state_waist = ctx.RawValue("d", 0.0)
        self._state_ready = ctx.RawValue("b", False)
        parent_connection, child_connection = ctx.Pipe()
        self._connection = parent_connection
        self._process = ctx.Process(
            target=_controller_worker,
            name="g1-23-control",
            args=(
                child_connection,
                self._stop_event,
                self._target_lock,
                self._target_q,
                self._target_tau,
                self._target_waist,
                self._target_waist_valid,
                self._target_sequence,
                self._state_lock,
                self._state_motor_q,
                self._state_arm_q,
                self._state_arm_dq,
                self._state_waist,
                self._state_ready,
                motion_mode,
                simulation_mode,
                network_interface,
                _use_dummy,
            ),
            daemon=True,
        )
        self._process.start()
        child_connection.close()
        if not self._connection.poll(startup_timeout_s):
            self.close(force=True)
            raise TimeoutError(f"G1-23 control process did not initialize within {startup_timeout_s:.1f}s")
        response = self._connection.recv()
        if not response.get("ok"):
            self.close(force=True)
            raise RuntimeError(f"G1-23 control process failed to start:\n{response.get('error', '')}")
        deadline = time.monotonic() + min(5.0, startup_timeout_s)
        while not self._state_ready.value and time.monotonic() < deadline:
            time.sleep(0.01)
        if not self._state_ready.value:
            self.close(force=True)
            raise TimeoutError("G1-23 control process started but did not publish an initial state")

    def _rpc(self, method: str, *args, **kwargs) -> Any:
        if self._closed or not self._process.is_alive():
            raise RuntimeError("G1-23 control process is not running")
        with self._rpc_lock:
            self._connection.send({"method": method, "args": args, "kwargs": kwargs})
            response = self._connection.recv()
        if not response.get("ok"):
            raise RuntimeError(f"G1-23 control process {method} failed:\n{response.get('error', '')}")
        return response.get("result")

    def ctrl_dual_arm(self, q_target, tauff_target, waist_yaw_target=None) -> None:
        q = np.asarray(q_target, dtype=np.float64).reshape(_ARM_DOF)
        tau = np.asarray(tauff_target, dtype=np.float64).reshape(_ARM_DOF)
        with self._target_lock:
            _copy_into(self._target_q, q)
            _copy_into(self._target_tau, tau)
            self._target_waist_valid.value = waist_yaw_target is not None
            if waist_yaw_target is not None:
                self._target_waist.value = float(waist_yaw_target)
            self._target_sequence.value += 1

    def _state_copy(self, shared_array) -> np.ndarray:
        with self._state_lock:
            return np.frombuffer(shared_array, dtype=np.float64).copy()

    def get_current_motor_q(self) -> np.ndarray:
        return self._state_copy(self._state_motor_q)

    def get_current_dual_arm_q(self) -> np.ndarray:
        return self._state_copy(self._state_arm_q)

    def get_current_dual_arm_dq(self) -> np.ndarray:
        return self._state_copy(self._state_arm_dq)

    def get_current_waist_yaw_q(self) -> float:
        with self._state_lock:
            return float(self._state_waist.value)

    def set_idle_publish_mode(self, mode: str) -> None:
        self._rpc("set_idle_publish_mode", mode)

    def set_episode_active(self, active: bool) -> None:
        self._rpc("set_episode_active", active)

    def wait_for_motion_controller_pose(self, **kwargs):
        return self._rpc("wait_for_motion_controller_pose", **kwargs)

    def start_motion_handover(self, **kwargs) -> None:
        self._rpc("start_motion_handover", **kwargs)

    def wait_for_motion_weight(self, *args, **kwargs):
        return self._rpc("wait_for_motion_weight", *args, **kwargs)

    def return_motion_control(self, **kwargs):
        return self._rpc("return_motion_control", **kwargs)

    def move_all_joints_to_pose_and_lock_non_arm_waist(self, *args, **kwargs) -> None:
        self._rpc("move_all_joints_to_pose_and_lock_non_arm_waist", *args, **kwargs)

    def ctrl_dual_arm_go_home(self) -> None:
        self._rpc("ctrl_dual_arm_go_home")

    def get_control_loop_diagnostics(self, reset=False):
        return self._rpc("get_control_loop_diagnostics", reset=reset)

    def close(self, force: bool = False) -> None:
        if self._closed:
            return
        if not force and self._process.is_alive():
            try:
                self._rpc("close")
            except Exception:
                force = True
        self._closed = True
        self._stop_event.set()
        self._process.join(timeout=3.0)
        if self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout=2.0)
        self._connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback_value):
        self.close()
