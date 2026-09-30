import os
import sys
import json
import tempfile
import time
from threading import Event
from types import SimpleNamespace

import torch
from torch import nn

from lerobot.utils.constants import ACTION
from unitree_lerobot.eval_robot.eval_g1_rtc import predict_action_rtc
from unitree_lerobot.eval_robot.pi05_rtc_runtime import (
    PI05RTCConfig,
    PI05RTCPolicyAdapter,
    RTCActionQueue,
    RTCProcessor,
)


def test_prefix_weights_are_monotonic_and_bounded():
    processor = RTCProcessor(
        PI05RTCConfig(prefix_attention_schedule="exp", execution_horizon=5)
    )
    weights = processor.get_prefix_weights(start=2, end=5, total=8)

    assert weights.shape == (8,)
    assert torch.allclose(weights[:2], torch.ones(2))
    assert torch.allclose(weights[5:], torch.zeros(3))
    assert torch.all(weights[:-1] >= weights[1:])
    assert torch.all((0 <= weights) & (weights <= 1))


def test_rtc_denoise_without_prefix_is_unchanged():
    processor = RTCProcessor(PI05RTCConfig())
    x_t = torch.randn(1, 4, 3)

    actual = processor.denoise_step(
        x_t=x_t,
        prev_chunk_left_over=None,
        inference_delay=0,
        time_value=torch.tensor([0.5]),
        original_denoise_step=lambda x: x * 0.25,
    )

    assert torch.allclose(actual, x_t * 0.25)


def test_rtc_guidance_changes_only_weighted_prefix():
    processor = RTCProcessor(
        PI05RTCConfig(
            prefix_attention_schedule="ones",
            execution_horizon=2,
            max_guidance_weight=10.0,
        )
    )
    x_t = torch.zeros(1, 4, 1)
    prev = torch.ones(2, 1)

    guided = processor.denoise_step(
        x_t=x_t,
        prev_chunk_left_over=prev,
        inference_delay=0,
        time_value=torch.tensor([0.5]),
        original_denoise_step=torch.zeros_like,
    )

    assert torch.all(guided[:, :2] < 0)
    assert torch.allclose(guided[:, 2:], torch.zeros_like(guided[:, 2:]))


def test_rtc_guidance_matches_lerobot_reference_example():
    processor = RTCProcessor(
        PI05RTCConfig(
            prefix_attention_schedule="linear",
            execution_horizon=10,
            max_guidance_weight=10.0,
            use_autograd_jacobian=False,
        )
    )
    x_t = torch.ones(1, 20, 1)
    prev = torch.full((1, 20, 1), 0.1)

    guided = processor.denoise_step(
        x_t=x_t,
        prev_chunk_left_over=prev,
        inference_delay=5,
        time_value=torch.tensor([0.5]),
        original_denoise_step=lambda x: x * 0.5,
    )

    expected = torch.tensor(
        [1.8, 1.8, 1.8, 1.8, 1.8, 1.583333, 1.366667, 1.15, 0.933333, 0.716667]
        + [0.5] * 10
    ).reshape(1, 20, 1)
    assert torch.allclose(guided, expected, atol=1e-5)


def test_rtc_autograd_guidance_uses_denoiser_jacobian():
    processor = RTCProcessor(
        PI05RTCConfig(
            prefix_attention_schedule="ones",
            execution_horizon=1,
            max_guidance_weight=10.0,
            use_autograd_jacobian=True,
        )
    )
    x_t = torch.ones(1, 2, 1)
    prev = torch.full((1, 1, 1), 0.1)

    guided = processor.denoise_step(
        x_t=x_t,
        prev_chunk_left_over=prev,
        inference_delay=0,
        time_value=torch.tensor([0.5]),
        original_denoise_step=lambda x: x * 0.5,
    )

    # x1 = x - 0.5*(0.5*x) = 0.75*x, so the guided prefix uses
    # J^T*error = 0.75*(0.1 - 0.75), not the identity approximation.
    assert torch.allclose(guided, torch.tensor([[[1.475], [0.5]]]), atol=1e-6)


def test_action_queue_replaces_chunk_after_consumed_prefix():
    queue = RTCActionQueue()
    original = torch.arange(12, dtype=torch.float32).reshape(6, 2)
    processed = original + 100
    queue.merge(original, processed, consumed_during_inference=2)

    assert len(queue) == 4
    assert torch.equal(queue.get(), processed[2])
    assert torch.equal(queue.get_left_over(), original[3:])


def test_execution_budget_cannot_exceed_guidance_horizon():
    try:
        PI05RTCConfig(execution_horizon=10, max_actions_during_inference=11)
    except ValueError as exc:
        assert "must not exceed execution_horizon" in str(exc)
    else:
        raise AssertionError("Expected an invalid RTC execution budget to be rejected")


class _FakePolicy(nn.Module):
    def __init__(self):
        super().__init__()
        self.config = SimpleNamespace(
            type="pi05",
            chunk_size=6,
            max_action_dim=2,
            output_features={ACTION: SimpleNamespace(shape=(2,))},
            device="cpu",
            use_amp=False,
        )
        self.reset_count = 0

    def reset(self):
        self.reset_count += 1


class _IdentityPostprocessor:
    def __call__(self, actions):
        return actions


class _FakeRTCAdapter(PI05RTCPolicyAdapter):
    def __init__(self, *args, **kwargs):
        self.calls = []
        self.inference_started = Event()
        self.fake_latency_s = 0.01
        super().__init__(*args, **kwargs)

    def _predict_action_chunk(self, batch, inference_delay, prev_chunk_left_over):
        self.calls.append((inference_delay, prev_chunk_left_over))
        self.inference_started.set()
        time.sleep(self.fake_latency_s)
        value = float(len(self.calls))
        return torch.full((1, 6, 2), value)


def test_async_adapter_produces_first_chunk_and_stops_cleanly():
    adapter = _FakeRTCAdapter(
        _FakePolicy(),
        _IdentityPostprocessor(),
        PI05RTCConfig(queue_threshold=2, inference_timeout_s=2.0),
        frequency=20.0,
    )
    try:
        action = adapter.select_action({"dummy": torch.tensor([1.0])})
        assert action.shape == (1, 2)
        assert torch.equal(action, torch.ones_like(action))
        assert adapter.calls[0][1] is None
    finally:
        adapter.close()


def test_async_adapter_holds_after_execution_budget_until_chunk_is_ready():
    adapter = _FakeRTCAdapter(
        _FakePolicy(),
        _IdentityPostprocessor(),
        PI05RTCConfig(
            execution_horizon=2,
            max_actions_during_inference=1,
            queue_threshold=2,
            inference_timeout_s=2.0,
        ),
        frequency=20.0,
    )
    adapter.fake_latency_s = 0.15
    batch = {"dummy": torch.tensor([1.0])}
    try:
        adapter.select_action(batch)  # Initial blocking chunk, five actions remain.
        adapter.inference_started.clear()
        adapter.select_action(batch)
        adapter.select_action(batch)
        adapter.select_action(batch)  # Two actions remain; background refill starts.
        assert adapter.inference_started.wait(timeout=1.0)

        adapter.select_action(batch)  # One old action is allowed during inference.
        wait_start = time.perf_counter()
        action_after_hold = adapter.select_action(batch)
        hold_s = time.perf_counter() - wait_start

        assert hold_s >= 0.05
        assert torch.equal(action_after_hold, torch.full((1, 2), 2.0))
        assert adapter.calls[1][0] == 1
    finally:
        adapter.close()


def test_async_adapter_stops_at_maximum_episode_wall_time():
    adapter = _FakeRTCAdapter(
        _FakePolicy(),
        _IdentityPostprocessor(),
        PI05RTCConfig(queue_threshold=2, inference_timeout_s=2.0),
        frequency=20.0,
        max_episode_wall_time_s=0.05,
    )
    batch = {"dummy": torch.tensor([1.0])}
    try:
        assert adapter.select_action(batch) is not None
        time.sleep(0.06)
        assert adapter.select_action(batch) is None
        assert "maximum wall time reached" in adapter.episode_stop_reason
    finally:
        adapter.close()


def test_async_adapter_accepts_external_mcp_stop():
    stop_event = Event()
    adapter = _FakeRTCAdapter(
        _FakePolicy(),
        _IdentityPostprocessor(),
        PI05RTCConfig(queue_threshold=2, inference_timeout_s=2.0),
        frequency=20.0,
        external_stop_requested=stop_event.is_set,
        enable_terminal_control=False,
    )
    batch = {"dummy": torch.tensor([1.0])}
    try:
        assert adapter.select_action(batch) is not None
        stop_event.set()
        assert adapter.select_action(batch) is None
        assert adapter.episode_stop_reason == "external stop requested"
    finally:
        adapter.close()


def test_eval_wrapper_preserves_normal_stop_sentinel():
    class _StoppedAdapter:
        def __init__(self):
            self._last_predict_action_profile = None

        def select_action(self, observation, snapshot_observation=None):
            return None

    adapter = _StoppedAdapter()
    result = predict_action_rtc(
        observation={"observation.state": torch.zeros(2)},
        policy=adapter,
        device=torch.device("cpu"),
        preprocessor=lambda observation: observation,
        postprocessor=None,
        use_amp=False,
    )

    assert result is None
    assert adapter._last_predict_action_profile["select_action_s"] >= 0


def test_inference_snapshot_saves_raw_image_and_state_metadata():
    with tempfile.TemporaryDirectory() as snapshot_dir:
        adapter = _FakeRTCAdapter(
            _FakePolicy(),
            _IdentityPostprocessor(),
            PI05RTCConfig(queue_threshold=2, inference_timeout_s=2.0),
            frequency=20.0,
            snapshot_dir=snapshot_dir,
        )
        try:
            snapshot = {
                "observation.images.cam_high": torch.full((8, 12, 3), 127, dtype=torch.uint8),
                "observation.state": torch.tensor([0.1, 0.2]),
                "observed_wall_time_ns": time.time_ns(),
                "observed_monotonic_ns": time.monotonic_ns(),
            }
            adapter._save_inference_snapshot(
                snapshot,
                queue_size_before=30,
                predicted_delay=10,
            )

            jpg_files = [name for name in os.listdir(snapshot_dir) if name.endswith(".jpg")]
            json_files = [name for name in os.listdir(snapshot_dir) if name.endswith(".json")]
            assert len(jpg_files) == 1
            assert len(json_files) == 1
            with open(os.path.join(snapshot_dir, json_files[0]), encoding="utf-8") as metadata_file:
                metadata = json.load(metadata_file)
            assert metadata["queue_size_before"] == 30
            assert metadata["predicted_delay_frames"] == 10
            assert abs(metadata["observation_state"][0] - 0.1) < 1e-6
            assert abs(metadata["observation_state"][1] - 0.2) < 1e-6
            assert metadata["observation_to_inference_ms"] >= 0
        finally:
            adapter.close()


def test_runtime_q_is_read_without_enter_from_a_terminal():
    master_fd, slave_fd = os.openpty()
    terminal_input = os.fdopen(os.dup(slave_fd), "r", buffering=1)
    original_stdin = sys.stdin
    adapter = None
    try:
        sys.stdin = terminal_input
        adapter = _FakeRTCAdapter(
            _FakePolicy(),
            _IdentityPostprocessor(),
            PI05RTCConfig(queue_threshold=2, inference_timeout_s=2.0),
            frequency=20.0,
        )
        adapter._enable_terminal_keys()
        os.write(master_fd, b"q")
        assert adapter._runtime_stop_requested()
        assert adapter.episode_stop_reason == "operator pressed q"
    finally:
        if adapter is not None:
            adapter.close()
        sys.stdin = original_stdin
        terminal_input.close()
        os.close(master_fd)
        os.close(slave_fd)
