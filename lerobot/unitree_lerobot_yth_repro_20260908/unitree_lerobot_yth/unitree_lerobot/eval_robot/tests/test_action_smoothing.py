import numpy as np
import pytest

from unitree_lerobot.eval_robot.action_smoothing import (
    ActionSmoothingConfig,
    JointActionSmoother,
)


def _config(**overrides) -> ActionSmoothingConfig:
    values = {
        "enabled": True,
        "frequency": 10.0,
        "arm_dof": 1,
        "waist_dof": 0,
        "arm_cutoff_hz": 2.0,
        "waist_cutoff_hz": 1.0,
        "chunk_blend_frames": 3,
        "velocity_limits": "1.0",
        "acceleration_limits": "2.0",
    }
    values.update(overrides)
    return ActionSmoothingConfig(**values)


def test_disabled_smoother_preserves_policy_action_exactly():
    smoother = JointActionSmoother(_config(enabled=False, velocity_limits="unused"))
    output, diagnostics = smoother.process([1.25], measured_q=[-0.5])

    np.testing.assert_array_equal(output, np.asarray([1.25], dtype=np.float32))
    assert diagnostics == {"enabled": False}


def test_first_action_starts_from_measured_pose_with_acceleration_limit():
    smoother = JointActionSmoother(_config())
    output, diagnostics = smoother.process([1.0], measured_q=[0.0])

    # a_max * dt^2 = 2.0 * 0.1^2 = 0.02 rad on the first command.
    np.testing.assert_allclose(output, [0.02], atol=1e-6)
    assert diagnostics["acceleration_limited"] is True


def test_velocity_and_acceleration_are_bounded_over_repeated_steps():
    smoother = JointActionSmoother(_config())
    commands = [smoother.process([10.0], measured_q=[0.0])[0][0] for _ in range(20)]
    velocity = np.diff(np.concatenate(([0.0], commands))) * 10.0
    acceleration = np.diff(np.concatenate(([0.0], velocity))) * 10.0

    assert np.max(np.abs(velocity)) <= 1.0 + 1e-6
    assert np.max(np.abs(acceleration)) <= 2.0 + 1e-5


def test_new_rtc_chunk_is_stitched_to_previous_command():
    smoother = JointActionSmoother(_config())
    previous, _ = smoother.process(
        [0.5], measured_q=[0.0], metadata={"inference_index": 1}
    )
    _, diagnostics = smoother.process(
        [5.0], measured_q=[0.0], metadata={"inference_index": 2}
    )

    assert diagnostics["chunk_boundary"] is True
    assert diagnostics["chunk_blend_weight"] == pytest.approx(1.0)
    assert diagnostics["stitched_action"][0] == pytest.approx(float(previous[0]))


def test_enabled_smoother_rejects_wrong_limit_dimension():
    with pytest.raises(ValueError, match="must contain 1 values"):
        JointActionSmoother(_config(velocity_limits="1.0,2.0"))
