"""A-period mesh backend: YCB USD for tabletop items; primitives as fallback."""

from __future__ import annotations

from typing import Any

from simfoundry.adapter.backends.base import MeshAsset, MeshBackend

LIBRARY: dict[str, dict[str, Any]] = {
    "counter": {
        "shape": "cuboid",
        "size": [0.60, 1.20, 0.78],
        "mass": 40.0,
        "friction": 0.6,
        "kinematic": True,
        "color": [0.55, 0.42, 0.32],
    },
    # YCB Axis_Aligned visual meshes (physics authored at spawn time).
    "cup": {
        "shape": "usd",
        "usd_path": "assets/objects/025_mug.usd",
        "radius": 0.04,
        "height": 0.10,
        "mass": 0.12,
        "friction": 0.6,
        "kinematic": False,
        "color": [0.78, 0.22, 0.18],
    },
    "bowl": {
        "shape": "usd",
        "usd_path": "assets/objects/024_bowl.usd",
        "radius": 0.08,
        "height": 0.055,
        "mass": 0.18,
        "friction": 0.5,
        "kinematic": False,
        "color": [0.90, 0.88, 0.82],
    },
    "plate": {
        "shape": "cylinder",
        "radius": 0.09,
        "height": 0.012,
        "mass": 0.25,
        "friction": 0.4,
        "kinematic": False,
        "color": [0.93, 0.93, 0.90],
    },
    "bottle": {
        "shape": "usd",
        "usd_path": "assets/objects/006_mustard_bottle.usd",
        "radius": 0.035,
        "height": 0.19,
        "mass": 0.20,
        "friction": 0.45,
        "kinematic": False,
        "color": [0.15, 0.42, 0.55],
    },
    "sorting_table": {
        "shape": "cuboid",
        "size": [0.60, 1.50, 0.025],
        "mass": 35.0,
        "friction": 0.55,
        "kinematic": True,
        "color": [0.55, 0.72, 0.82],
    },
    "parcel_box": {
        "shape": "cuboid",
        "size": [0.13, 0.08, 0.025],
        "mass": 0.12,
        "friction": 0.22,
        "kinematic": False,
        "color": [0.78, 0.62, 0.40],
    },
    "mailer": {
        "shape": "cuboid",
        "size": [0.15, 0.15, 0.030],
        "mass": 0.09,
        "friction": 0.22,
        "kinematic": False,
        "color": [0.04, 0.04, 0.045],
    },
    "mailer_label": {
        "shape": "cuboid",
        "size": [0.06, 0.035, 0.0015],
        "mass": 0.01,
        "friction": 0.40,
        "kinematic": True,
        "color": [0.97, 0.97, 0.95],
    },
    "parcel_box_label": {
        "shape": "cuboid",
        "size": [0.06, 0.04, 0.0015],
        "mass": 0.01,
        "friction": 0.40,
        "kinematic": True,
        "color": [0.97, 0.97, 0.95],
    },
    "table_edge_wear": {
        "shape": "cuboid",
        "size": [0.012, 1.48, 0.004],
        "mass": 0.05,
        "friction": 0.5,
        "kinematic": True,
        "color": [0.92, 0.92, 0.90],
    },
    "klt_bin": {
        "shape": "cuboid",
        "size": [0.38, 0.28, 0.17],
        "mass": 1.2,
        "friction": 0.55,
        "kinematic": True,
        "color": [0.07, 0.07, 0.08],
    },
    "backdrop_panel": {
        "shape": "cuboid",
        "size": [0.08, 2.2, 1.8],
        "mass": 20.0,
        "friction": 0.5,
        "kinematic": True,
        "color": [0.88, 0.88, 0.86],
    },
    "pc_tower": {
        "shape": "cuboid",
        "size": [0.22, 0.45, 0.42],
        "mass": 8.0,
        "friction": 0.5,
        "kinematic": True,
        "color": [0.08, 0.08, 0.09],
    },
    "metal_rack": {
        "shape": "cuboid",
        "size": [0.08, 0.08, 1.6],
        "mass": 12.0,
        "friction": 0.5,
        "kinematic": True,
        "color": [0.12, 0.12, 0.13],
    },
}


class FromLibraryBackend(MeshBackend):
    def __init__(self, library: dict[str, dict[str, Any]] | None = None) -> None:
        self.library = library if library is not None else LIBRARY

    def generate(self, image: Any | None, *, semantic: str) -> MeshAsset:
        if semantic not in self.library:
            raise KeyError(f"no library asset for semantic={semantic!r}")
        spec = dict(self.library[semantic])
        spec["semantic"] = semantic
        kind = "usd" if spec.get("shape") == "usd" else "primitive"
        return MeshAsset(semantic=semantic, kind=kind, primitive=spec)
