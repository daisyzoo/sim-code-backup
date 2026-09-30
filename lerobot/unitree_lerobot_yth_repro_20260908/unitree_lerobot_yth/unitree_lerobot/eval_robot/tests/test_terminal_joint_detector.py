from pathlib import Path

import numpy as np

from unitree_lerobot.eval_robot.terminal_joint_detector import TerminalJointPoseDetector


CONFIG_PATH = (
    Path(__file__).resolve().parents[1]
    / "assets/g1/pick_cup_terminal_joint_pose_15hz.json"
)


def test_terminal_pose_requires_continuous_hold_after_minimum_elapsed():
    detector = TerminalJointPoseDetector(CONFIG_PATH, frequency=10.0)
    detector.start_episode(timestamp=0.0)
    center = detector.reference_center.copy()

    for timestamp in (3.0 + 0.1 * index for index in range(18)):
        assert not detector.observe(center, timestamp=float(timestamp))
    assert detector.observe(center, timestamp=4.81)
    assert detector.succeeded
    assert detector.success_details["reason"] == "terminal joint pose held"
    detector.close()


def test_a_few_outlier_twitches_are_allowed():
    detector = TerminalJointPoseDetector(CONFIG_PATH, frequency=10.0)
    detector.start_episode(timestamp=0.0)
    center = detector.reference_center.copy()

    for index in range(21):
        sample = center.copy()
        if index in {5, 12}:
            sample[3] = detector.upper_bounds[3] + 0.1
        result = detector.observe(sample, timestamp=3.0 + 0.1 * index)
    assert result
    assert detector.success_details["terminal_inlier_fraction"] >= 0.9
    detector.close()


def test_too_many_outlier_frames_do_not_succeed():
    detector = TerminalJointPoseDetector(CONFIG_PATH, frequency=10.0)
    detector.start_episode(timestamp=0.0)
    center = detector.reference_center.copy()

    for index in range(21):
        sample = center.copy()
        if index in {3, 9, 15}:
            sample[3] = detector.upper_bounds[3] + 0.1
        assert not detector.observe(sample, timestamp=3.0 + 0.1 * index)
    assert not detector.succeeded
    detector.close()


def test_pose_inside_bounds_but_moving_does_not_succeed():
    detector = TerminalJointPoseDetector(CONFIG_PATH, frequency=10.0)
    detector.start_episode(timestamp=0.0)
    center = detector.reference_center.copy()

    for index, timestamp in enumerate(np.arange(3.0, 5.2, 0.1)):
        moving = center.copy()
        moving[1] += 0.035 if index % 2 else -0.035
        assert not detector.observe(moving, timestamp=float(timestamp))
    assert not detector.succeeded
    detector.close()
