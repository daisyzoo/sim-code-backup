"""B-period backend placeholders. Calling them is a hard error until resources land."""

from __future__ import annotations

from typing import Any

from simfoundry.adapter.backends.base import (
    BackgroundBackend,
    DepthBackend,
    MeshAsset,
    PhysicsStabilize,
    PoseBackend,
    SegBackend,
)


class UnimplementedBackendError(RuntimeError):
    pass


def _ban(name: str) -> None:
    raise UnimplementedBackendError(
        f"{name} is reserved for SimFoundry B-period. A-period uses FromLibraryBackend / StubVlmBackend."
    )


class DepthAnythingBackend(DepthBackend):
    def infer(self, image: Any) -> Any:
        _ban("DepthBackend")


class Sam3Backend(SegBackend):
    def segment(self, image: Any) -> Any:
        _ban("SegBackend")


class FoundationPoseBackend(PoseBackend):
    def estimate(self, rgb: Any, depth: Any, mesh: MeshAsset) -> dict[str, Any]:
        _ban("PoseBackend")


class SplatfactoBackend(BackgroundBackend):
    def reconstruct(self, frames: Any) -> Any:
        _ban("BackgroundBackend")


class CoacdBulletStabilize(PhysicsStabilize):
    def stabilize(self, mesh: MeshAsset) -> MeshAsset:
        _ban("PhysicsStabilize")
