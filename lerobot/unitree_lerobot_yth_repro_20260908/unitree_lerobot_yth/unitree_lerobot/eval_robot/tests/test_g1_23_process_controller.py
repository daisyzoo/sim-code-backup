import time
import unittest

import numpy as np

from unitree_lerobot.eval_robot.robot_control.g1_23_process_controller import G1_23_ProcessController


class G123ProcessControllerTest(unittest.TestCase):
    def test_dummy_child_relay_and_shutdown(self):
        controller = G1_23_ProcessController(_use_dummy=True, startup_timeout_s=10.0)
        process = controller._process
        try:
            target = np.linspace(-0.2, 0.2, 10, dtype=np.float64)
            controller.ctrl_dual_arm(target, np.zeros(10), waist_yaw_target=0.15)
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                if np.allclose(controller.get_current_dual_arm_q(), target) and abs(
                    controller.get_current_waist_yaw_q() - 0.15
                ) < 1e-6:
                    break
                time.sleep(0.01)
            self.assertTrue(np.allclose(controller.get_current_dual_arm_q(), target))
            self.assertAlmostEqual(controller.get_current_waist_yaw_q(), 0.15)
            self.assertTrue(process.is_alive())
        finally:
            controller.close()
        self.assertFalse(process.is_alive())


if __name__ == "__main__":
    unittest.main()
