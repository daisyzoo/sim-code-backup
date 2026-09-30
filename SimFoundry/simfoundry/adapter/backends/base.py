"""Replaceable backends. A-period implementations are stubs or asset-library lookups."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Literal

from simfoundry.schema import ScenePackage, TaskSpec


@dataclass(frozen=True)
class MeshAsset:
    semantic: str
    kind: Literal["primitive", "usd", "glb"]
    primitive: dict[str, Any] | None = None
    uri: str | None = None


class MeshBackend(ABC):
    """image → mesh. A-period: FromLibraryBackend. B-period: Hunyuan / TRELLIS / remote."""

    @abstractmethod
    def generate(self, image: Any | None, *, semantic: str) -> MeshAsset:
        raise NotImplementedError


class VlmBackend(ABC):
    """Scene understanding / task proposal. A-period: hardcoded kitchen tasks. B-period: Gemini."""

    @abstractmethod
    def propose_tasks(self, scene: ScenePackage | dict[str, Any]) -> list[TaskSpec]:
        raise NotImplementedError


class DepthBackend(ABC):
    @abstractmethod
    def infer(self, image: Any) -> Any:
        raise NotImplementedError


class SegBackend(ABC):
    @abstractmethod
    def segment(self, image: Any) -> Any:
        raise NotImplementedError


class PoseBackend(ABC):
    @abstractmethod
    def estimate(self, rgb: Any, depth: Any, mesh: MeshAsset) -> dict[str, Any]:
        raise NotImplementedError


class BackgroundBackend(ABC):
    @abstractmethod
    def reconstruct(self, frames: Any) -> Any:
        raise NotImplementedError


class PhysicsStabilize(ABC):
    @abstractmethod
    def stabilize(self, mesh: MeshAsset) -> MeshAsset:
        raise NotImplementedError
