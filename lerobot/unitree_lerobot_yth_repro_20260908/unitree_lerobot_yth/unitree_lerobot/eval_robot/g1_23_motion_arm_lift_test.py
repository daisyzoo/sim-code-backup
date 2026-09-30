import sys
import time
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SDK_ROOT = REPO_ROOT / "unitree_sdk2_python"
if str(SDK_ROOT) not in sys.path:
    sys.path.insert(0, str(SDK_ROOT))

from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_lerobot.eval_robot.robot_control.robot_arm import G1_23_ArmController
from unitree_lerobot.eval_robot.robot_control.robot_arm_ik import G1_23_ArmIK


def fmt(values):
    return np.array2string(np.asarray(values), precision=3, suppress_small=True)


PRESETS = {
    # raise both arms slightly outward from the torso
    "side_lift": np.array(
        [
            0.00, -0.28, 0.00, 0.12, 0.00,
            0.00,  0.28, 0.00, -0.12, 0.00,
        ],
        dtype=np.float64,
    ),
    # move both arms slightly forward
    "forward_lift": np.array(
        [
            -0.22, 0.00, 0.00, 0.15, 0.00,
            -0.22, 0.00, 0.00, -0.15, 0.00,
        ],
        dtype=np.float64,
    ),
}


def move_joint_target_smoothly(
    arm_ctrl: G1_23_ArmController,
    arm_ik: G1_23_ArmIK,
    start_q: np.ndarray,
    target_q: np.ndarray,
    start_waist: float,
    target_waist: float,
    frequency: float,
    duration_s: float,
):
    steps = max(1, int(round(duration_s * frequency)))
    for i in range(1, steps + 1):
        alpha = i / steps
        q = start_q + alpha * (target_q - start_q)
        waist_q = start_waist + alpha * (target_waist - start_waist)
        tau = arm_ik.solve_tau(q)
        arm_ctrl.ctrl_dual_arm(q, tau, waist_q)
        time.sleep(max(0.0, 1.0 / frequency))


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--network-interface", default="eno1")
    parser.add_argument("--preset", choices=sorted(PRESETS.keys()), default="side_lift")
    parser.add_argument("--frequency", type=float, default=20.0)
    parser.add_argument("--move-duration-s", type=float, default=2.0)
    parser.add_argument("--hold-duration-s", type=float, default=3.0)
    parser.add_argument("--waist-delta", type=float, default=0.15)
    args = parser.parse_args()

    print("WARNING: ensure the robot is clear of obstacles before continuing.")
    print("Expected robot state before running:")
    print("  1. no debug mode")
    print("  2. L2+B -> Damping")
    print("  3. L2+UP -> Locked Standing")
    print("  4. R1+X -> 1-DoF waist regular mode")
    input("Press Enter to continue...")

    ChannelFactoryInitialize(0, networkInterface=args.network_interface)
    print(f"[lift-test] sdk_root={SDK_ROOT}")
    print(f"[lift-test] imported_unitree_sdk2py={Path(sys.modules['unitree_sdk2py'].__file__).resolve()}")

    arm_ctrl = G1_23_ArmController(
        motion_mode=True,
        simulation_mode=False,
        network_interface=args.network_interface,
    )
    arm_ik = G1_23_ArmIK()

    current_q = np.asarray(arm_ctrl.get_current_dual_arm_q(), dtype=np.float64)
    current_waist = float(arm_ctrl.get_current_waist_yaw_q())
    delta_q = PRESETS[args.preset].copy()

    target_q = current_q + delta_q
    target_waist = current_waist + float(args.waist_delta)

    print(f"[lift-test] preset={args.preset}")
    print(f"[lift-test] current_q={fmt(current_q)}")
    print(f"[lift-test] delta_q={fmt(delta_q)}")
    print(f"[lift-test] target_q={fmt(target_q)}")
    print(f"[lift-test] current_waist={current_waist:.3f} target_waist={target_waist:.3f}")

    print("[lift-test] moving to target...")
    move_joint_target_smoothly(
        arm_ctrl,
        arm_ik,
        current_q,
        target_q,
        current_waist,
        target_waist,
        args.frequency,
        args.move_duration_s,
    )

    print("[lift-test] holding target...")
    hold_start = time.time()
    while time.time() - hold_start < args.hold_duration_s:
        tau = arm_ik.solve_tau(target_q)
        arm_ctrl.ctrl_dual_arm(target_q, tau, target_waist)
        time.sleep(max(0.0, 1.0 / args.frequency))

    post_q = np.asarray(arm_ctrl.get_current_dual_arm_q(), dtype=np.float64)
    post_waist = float(arm_ctrl.get_current_waist_yaw_q())
    print(f"[lift-test] post_q={fmt(post_q)}")
    print(f"[lift-test] post_delta={fmt(post_q - current_q)}")
    print(f"[lift-test] post_waist={post_waist:.3f} delta={post_waist - current_waist:.3f}")

    print("[lift-test] returning to start pose...")
    move_joint_target_smoothly(
        arm_ctrl,
        arm_ik,
        post_q,
        current_q,
        post_waist,
        current_waist,
        args.frequency,
        args.move_duration_s,
    )

    print("[lift-test] done.")


if __name__ == "__main__":
    main()
