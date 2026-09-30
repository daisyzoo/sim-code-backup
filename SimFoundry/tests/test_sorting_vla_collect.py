from __future__ import annotations

import unittest

from simfoundry.data.prompts import VLA_SORTING_UNIFIED_PROMPT
from simfoundry.data.scripted import scripted_action
from simfoundry.data.sorting_quality import (
    SortingStepSnapshot,
    evaluate_episode,
    sample_wait_horizon,
)
from simfoundry.scene_package import filter_tasks, load_named_scene


def _snap(**kwargs) -> SortingStepSnapshot:
    defaults = dict(
        palm_left=(0.4, 0.2, 0.84),
        palm_right=(0.4, -0.2, 0.84),
        wrist_left=(0.35, 0.2, 0.84),
        wrist_right=(0.35, -0.2, 0.84),
        box_x=0.4,
        box_y=-0.16,
        box_z=0.79,
        mailer_x=5.0,
        mailer_y=5.0,
        mailer_z=3.0,
        phase=0.5,
    )
    defaults.update(kwargs)
    return SortingStepSnapshot(**defaults)


class SortingVlaCollectTests(unittest.TestCase):
    def test_unified_prompt_on_sorting_tasks(self) -> None:
        package = load_named_scene("sorting_station_g1_23")
        stump = {t.task_id: t for t in filter_tasks(package, "stump")}
        self.assertIn("wait_no_package", stump)
        for tid in ("push_box_to_bin", "nudge_mailer_to_bin", "wait_no_package"):
            self.assertEqual(stump[tid].instruction, VLA_SORTING_UNIFIED_PROMPT)

    def test_wait_script_is_idle(self) -> None:
        act = scripted_action("wait_no_package", 10, 22)
        self.assertTrue((act == 0).all())

    def test_wait_gate_accepts_idle_empty_table(self) -> None:
        trail = [
            _snap(phase=i / 59, box_y=5.0, mailer_y=5.0, box_z=3.0, mailer_z=3.0)
            for i in range(60)
        ]
        report = evaluate_episode("wait_no_package", trail, horizon=60)
        self.assertTrue(report.passed, report.reasons)

    def test_box_gate_accepts_stable_lateral_sort(self) -> None:
        trail = []
        for i in range(120):
            t = min(1.0, i / 94)
            trail.append(
                _snap(
                    phase=i / 119,
                    palm_right=(0.4, 0.07 - 0.37 * t, 0.84),
                    wrist_right=(0.35, 0.07 - 0.37 * t, 0.84),
                    box_y=-0.24 * t,
                    box_z=0.79,
                    mailer_y=5.0,
                    mailer_z=3.0,
                )
            )
        report = evaluate_episode("push_box_to_bin", trail, horizon=120)
        self.assertTrue(report.passed, report.reasons)
        self.assertGreaterEqual(report.stable_zone_frames, 10)

    def test_box_gate_rejects_drop_even_after_sideways_push(self) -> None:
        trail = []
        for i in range(120):
            t = min(1.0, i / 94)
            trail.append(
                _snap(
                    phase=i / 119,
                    palm_right=(0.4, 0.07 - 0.37 * t, 0.84),
                    wrist_right=(0.35, 0.07 - 0.37 * t, 0.84),
                    box_y=-0.24 * t,
                    box_z=0.79 if i < 105 else 0.20,
                    mailer_y=5.0,
                    mailer_z=3.0,
                )
            )
        report = evaluate_episode("push_box_to_bin", trail, horizon=120)
        self.assertFalse(report.passed)
        self.assertTrue(any("dropped" in reason for reason in report.reasons))

    def test_box_gate_rejects_peak_crossing_that_rebounds(self) -> None:
        trail = []
        for i in range(120):
            if i < 90:
                y = -0.25 * (i / 89)
            else:
                y = -0.25 + 0.13 * ((i - 90) / 29)
            trail.append(
                _snap(
                    phase=i / 119,
                    palm_right=(0.4, y, 0.84),
                    wrist_right=(0.35, y, 0.84),
                    box_y=y,
                    mailer_y=5.0,
                    mailer_z=3.0,
                )
            )
        report = evaluate_episode("push_box_to_bin", trail, horizon=120)
        self.assertFalse(report.passed)
        self.assertTrue(any("not stable" in reason for reason in report.reasons))

    def test_box_gate_rejects_no_push(self) -> None:
        trail = [
            _snap(phase=i / 119, palm_right=(0.4, -0.19, 0.84), box_y=-0.16, mailer_y=5.0, mailer_z=3.0)
            for i in range(120)
        ]
        report = evaluate_episode("push_box_to_bin", trail, horizon=120)
        self.assertFalse(report.passed)

    def test_box_gate_rejects_wrong_way_prefix(self) -> None:
        trail = []
        for i in range(120):
            if i < 25:
                y = 0.05 * (i / 24)
            else:
                y = 0.05 - 0.29 * ((i - 25) / 94)
            trail.append(
                _snap(
                    phase=i / 119,
                    palm_right=(0.4, 0.08 - 0.38 * min(1.0, i / 94), 0.84),
                    wrist_right=(0.35, 0.08 - 0.38 * min(1.0, i / 94), 0.84),
                    box_y=y,
                    mailer_y=5.0,
                    mailer_z=3.0,
                )
            )
        report = evaluate_episode("push_box_to_bin", trail, horizon=120)
        self.assertFalse(report.passed)
        self.assertGreater(report.wrong_way_excursion_y, 0.035)
        self.assertTrue(any("wrong-way" in reason for reason in report.reasons))

    def test_box_gate_rejects_unsafe_front_edge_start(self) -> None:
        trail = []
        for i in range(120):
            t = min(1.0, i / 94)
            trail.append(
                _snap(
                    phase=i / 119,
                    palm_right=(0.34, 0.07 - 0.37 * t, 0.84),
                    wrist_right=(0.30, 0.07 - 0.37 * t, 0.84),
                    box_x=0.33,
                    box_y=-0.24 * t,
                    mailer_y=5.0,
                    mailer_z=3.0,
                )
            )
        report = evaluate_episode("push_box_to_bin", trail, horizon=120)
        self.assertFalse(report.passed)
        self.assertTrue(any("table front" in reason for reason in report.reasons))

    def test_box_gate_rejects_palm_core_crossing_table(self) -> None:
        trail = []
        for i in range(120):
            t = min(1.0, i / 94)
            trail.append(
                _snap(
                    phase=i / 119,
                    palm_right=(0.4, 0.07 - 0.37 * t, 0.79),
                    wrist_right=(0.35, 0.07 - 0.37 * t, 0.84),
                    box_y=-0.24 * t,
                    mailer_y=5.0,
                    mailer_z=3.0,
                )
            )
        report = evaluate_episode("push_box_to_bin", trail, horizon=120)
        self.assertFalse(report.passed)
        self.assertTrue(any("table penetration" in reason for reason in report.reasons))

    def test_wait_horizon_range(self) -> None:
        import numpy as np

        rng = np.random.default_rng(0)
        vals = [sample_wait_horizon(rng) for _ in range(40)]
        self.assertGreaterEqual(min(vals), 50)
        self.assertLessEqual(max(vals), 70)

    def test_box_plan_contacts_toward_right_bin(self) -> None:
        from simfoundry.data.sorting_push_assist import plan_palm_push

        plan = plan_palm_push("right", 0.40, -0.18)
        self.assertGreater(plan.y_contact, -0.18)
        self.assertLess(plan.y_bin, -0.18)
        self.assertGreaterEqual(plan.x_reach, 0.40)
        self.assertGreater(plan.sign, 0.0)

    def test_mailer_plan_contacts_toward_left_bin(self) -> None:
        from simfoundry.data.sorting_push_assist import plan_palm_push

        plan = plan_palm_push("left", 0.40, 0.18)
        self.assertLess(plan.y_contact, 0.18)
        self.assertGreater(plan.y_bin, 0.18)
        self.assertLess(plan.sign, 0.0)

    def test_contact_sweep_keeps_sweeping_if_parcel_still(self) -> None:
        import numpy as np
        from simfoundry.data.sorting_push_assist import (
            ContactSweepState,
            contact_sweep_step,
            plan_palm_push,
        )
        from simfoundry.embodiment import G1_23DOF_JOINT_NAMES

        right_roll = G1_23DOF_JOINT_NAMES.index("right_shoulder_roll_joint")
        left_roll = G1_23DOF_JOINT_NAMES.index("left_shoulder_roll_joint")
        plan = plan_palm_push("right", 0.40, -0.18)
        state = ContactSweepState(plan=plan)
        press = np.zeros(23, dtype=np.float32)
        # Hovering palm: stay in press, no inboard plant (0.08 already shoved the box +Y).
        contact_sweep_step(
            press,
            task_id="push_box_to_bin",
            state=state,
            plan=plan,
            palm=(0.35, -0.19, 0.84),
            parcel=(0.40, -0.18, 0.79),
        )
        self.assertEqual(state.mode, "press")
        self.assertLess(abs(float(press[right_roll])), 0.05)

        # Two frames of pad-down contact → sweep, even if the box has not moved.
        state = ContactSweepState(plan=plan)
        for _ in range(2):
            act = np.zeros(23, dtype=np.float32)
            contact_sweep_step(
                act,
                task_id="push_box_to_bin",
                state=state,
                plan=plan,
                palm=(0.36, -0.18, 0.82),
                parcel=(0.40, -0.18, 0.79),
            )
        self.assertEqual(state.mode, "sweep")
        for _ in range(70):
            act = np.zeros(23, dtype=np.float32)
            contact_sweep_step(
                act,
                task_id="push_box_to_bin",
                state=state,
                plan=plan,
                palm=(0.36, -0.20, 0.82),
                parcel=(0.40, -0.18, 0.79),
            )
        self.assertEqual(state.mode, "sweep")
        self.assertLess(float(act[right_roll]), 0.0)

        plan_l = plan_palm_push("left", 0.40, 0.18)
        state_l = ContactSweepState(plan=plan_l, mode="sweep", t_mode=40, sweep_s=0.70)
        sweep_l = np.zeros(23, dtype=np.float32)
        contact_sweep_step(
            sweep_l,
            task_id="nudge_mailer_to_bin",
            state=state_l,
            plan=plan_l,
            palm=(0.36, 0.22, 0.82),
            parcel=(0.40, 0.18, 0.79),
        )
        self.assertGreater(float(sweep_l[left_roll]), 0.0)

        dumped = ContactSweepState(plan=plan, mode="sweep", t_mode=20, sweep_s=0.2)
        dump_act = np.zeros(23, dtype=np.float32)
        contact_sweep_step(
            dump_act,
            task_id="push_box_to_bin",
            state=dumped,
            plan=plan,
            palm=(0.33, -0.20, 0.82),
            parcel=(0.22, -0.18, 0.01),
        )
        self.assertEqual(dumped.mode, "sweep")

        hover = ContactSweepState(plan=plan, mode="sweep", t_mode=0, sweep_s=0.0)
        hover_act = np.zeros(23, dtype=np.float32)
        for _ in range(20):
            contact_sweep_step(
                hover_act,
                task_id="push_box_to_bin",
                state=hover,
                plan=plan,
                palm=(0.35, -0.19, 0.89),
                parcel=(0.40, -0.18, 0.79),
            )
        self.assertGreater(hover.sweep_s, 0.15)
        self.assertEqual(hover.mode, "sweep")

        done = ContactSweepState(plan=plan, mode="sweep", t_mode=10)
        hold = np.zeros(23, dtype=np.float32)
        contact_sweep_step(
            hold,
            task_id="push_box_to_bin",
            state=done,
            plan=plan,
            palm=(0.33, -0.30, 0.82),
            parcel=(0.36, -0.30, 0.79),
        )
        self.assertEqual(done.mode, "hold")

    def test_cartesian_path_lifts_then_stages_inside_and_sweeps_out(self) -> None:
        from simfoundry.data.sorting_cartesian_expert import (
            APPROACH_END,
            CartesianSweepState,
            LIFT_END,
            PRESS_END,
            SWEEP_END,
            cartesian_target,
        )

        right = CartesianSweepState("right", 0.40, -0.18, start_palm=(0.35, -0.19, 0.84))
        right_lift = cartesian_target(right, LIFT_END - 1)
        right_stage = cartesian_target(right, APPROACH_END - 1)
        right_contact = cartesian_target(right, PRESS_END - 1)
        right_exit = cartesian_target(right, SWEEP_END)
        self.assertAlmostEqual(right_lift[1], -0.19)
        self.assertGreater(right_lift[2], 0.90)
        self.assertAlmostEqual(right_stage[1], -0.05)
        self.assertAlmostEqual(right_stage[0], 0.440)
        self.assertGreater(right_stage[2], right_contact[2])
        self.assertLess(right_exit[1], -0.22)

        left = CartesianSweepState("left", 0.40, 0.18, start_palm=(0.35, 0.19, 0.84))
        left_stage = cartesian_target(left, APPROACH_END - 1)
        left_exit = cartesian_target(left, SWEEP_END)
        self.assertAlmostEqual(left_stage[1], 0.05)
        self.assertGreater(left_exit[1], 0.22)

    def test_cartesian_dls_step_is_bounded(self) -> None:
        import torch
        from simfoundry.data.sorting_cartesian_expert import damped_position_step

        jacobian = torch.zeros(3, 5)
        jacobian[:, :3] = torch.eye(3)
        dq = damped_position_step(jacobian, torch.tensor([1.0, -1.0, 0.5]))
        self.assertEqual(tuple(dq.shape), (5,))
        self.assertLessEqual(float(torch.max(torch.abs(dq))), 0.055001)


if __name__ == "__main__":
    unittest.main()
