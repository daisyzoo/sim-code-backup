"""layout.json → Isaac Lab spawn configs. Import only after AppLauncher."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import isaaclab.sim as sim_utils
from isaaclab.assets import AssetBaseCfg, RigidObjectCfg
from isaaclab.sim.spawners.materials import PreviewSurfaceCfg, UsdPhysicsRigidBodyMaterialCfg
from isaaclab.sim import schemas
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR
from isaaclab_newton.sim.spawners.materials import NewtonMaterialCfg
from pxr import Gf, Usd, UsdGeom

from simfoundry.scene_bridge.textures import bind_image_texture, bind_label_texture, paint_meshes_black
from simfoundry.scene_bridge.transforms import world_pose
from simfoundry.schema import Pose, SceneObject, ScenePackage

_SIMFOUNDRY_ROOT = Path(__file__).resolve().parents[2]
_TEX = _SIMFOUNDRY_ROOT / "assets" / "textures" / "sorting_station"

# Kinematic cuboids that still need RigidObject TensorAPI so demos can swing / press them.
_KINEMATIC_WRITABLE = frozenset(
    {
        "door",
        "wall_button",
        "table_switch",
        "bin_box",
        "bin_mailer",
        "mailer_label",
        "mailer_b",
        "mailer_b_label",
        "parcel_box_label",
    }
)

# Visual-only stickers: collision against the parent parcel causes z-jitter / clipping.
_NO_COLLISION = frozenset(
    {
        "mailer_label",
        "parcel_box_label",
        "mailer_b_label",
        "mailer_c_label",
        "mailer_d_label",
        "parcel_box_b_label",
    }
)

# Prefer Nucleus Axis_Aligned so Materials/Textures resolve next to the USD.
_YCB_NUCLEUS = {
    "assets/objects/025_mug.usd": f"{ISAAC_NUCLEUS_DIR}/Props/YCB/Axis_Aligned/025_mug.usd",
    "assets/objects/024_bowl.usd": f"{ISAAC_NUCLEUS_DIR}/Props/YCB/Axis_Aligned/024_bowl.usd",
    "assets/objects/006_mustard_bottle.usd": f"{ISAAC_NUCLEUS_DIR}/Props/YCB/Axis_Aligned/006_mustard_bottle.usd",
    "assets/objects/003_cracker_box.usd": f"{ISAAC_NUCLEUS_DIR}/Props/YCB/Axis_Aligned/003_cracker_box.usd",
    "assets/objects/small_KLT.usd": f"{ISAAC_NUCLEUS_DIR}/Props/KLT_Bin/small_KLT.usd",
}

_USD_SCALE: dict[str, tuple[float, float, float]] = {
    "assets/objects/small_KLT.usd": (1.9, 1.4, 0.85),
    "assets/objects/003_cracker_box.usd": (1.35, 1.05, 0.42),
}

def _load_parcel_photos() -> dict[str, dict[str, Any]]:
    """Per-object albedo from pick_demo (name, not semantic). Missing files fall back to _TEXTURES."""
    manifest = _TEX / "parcels" / "manifest.json"
    if not manifest.is_file():
        return {}
    raw = json.loads(manifest.read_text(encoding="utf-8"))
    mapping: dict[str, str] = raw.get("object_to_file", {})
    photos: dict[str, dict[str, Any]] = {}
    normals: dict[str, str] = raw.get("object_to_normal", {})
    for name, filename in mapping.items():
        is_bag = name.startswith("mailer")
        spec: dict[str, Any] = {
            "file": f"parcels/{filename}",
            "uv_scale": (1.0, 1.0),
            "uv_mode": "box",
            "wrap": "clamp",
            "side_uv": (0.50, 0.50) if is_bag else (0.04, 0.04),
            "roughness": 0.22 if is_bag else 0.86,
            "metallic": 0.04 if is_bag else 0.0,
            "fallback_color": (0.04, 0.04, 0.045) if is_bag else (0.78, 0.62, 0.40),
        }
        if is_bag:
            # Original tiled wrinkle map — Sobel-from-photo reads as a black brick.
            spec["normal"] = "mailer_normal.png"
            spec["normal_uv_scale"] = (2.5, 2.0)
            spec["normal_wrap"] = "repeat"
        else:
            nfile = normals.get(name)
            if nfile:
                spec["normal"] = f"parcels/{nfile}"
        photos[name] = spec
    return photos


# Semantic → cropped / procedural texture (relative to _TEX).
_TEXTURES: dict[str, dict[str, Any]] = {
    "sorting_table": {
        "file": "table_top.jpg",
        "uv_scale": (1.2, 1.8),
        "roughness": 0.58,
        "fallback_color": (0.56, 0.70, 0.76),
    },
    "table_edge_wear": {
        "file": "table_edge.jpg",
        "uv_scale": (1.0, 1.0),
        "roughness": 0.72,
        "fallback_color": (0.92, 0.92, 0.90),
    },
    "floor": {
        "file": "floor_carpet.jpg",
        "uv_scale": (4.0, 4.0),
        "roughness": 0.94,
        "fallback_color": (0.40, 0.41, 0.42),
    },
    "backdrop_panel": {
        "file": "backdrop.jpg",
        "uv_scale": (1.0, 1.0),
        "roughness": 0.38,
        "fallback_color": (0.88, 0.88, 0.86),
    },
    "equipment_wrap": {
        "file": "backdrop.jpg",
        "uv_scale": (0.6, 1.2),
        "roughness": 0.22,
        "fallback_color": (0.94, 0.94, 0.93),
    },
    "mailer": {
        "file": "mailer_albedo.jpg",
        "normal": "mailer_normal.png",
        "uv_scale": (2.5, 2.0),
        "roughness": 0.22,
        "metallic": 0.04,
        "fallback_color": (0.04, 0.04, 0.045),
    },
    "klt_bin": {
        "file": "klt_black.jpg",
        "uv_scale": (1.5, 1.2),
        "roughness": 0.42,
        "metallic": 0.10,
        "fallback_color": (0.07, 0.07, 0.08),
    },
    "parcel_box": {
        "file": "kraft_box.jpg",
        "uv_scale": (1.0, 1.0),
        "roughness": 0.88,
        "fallback_color": (0.78, 0.62, 0.40),
    },
    "parcel_box_label": {"file": "shipping_label.jpg", "uv_scale": (1.0, 1.0), "roughness": 0.65},
    "mailer_label": {"file": "shipping_label.jpg", "uv_scale": (1.0, 1.0), "roughness": 0.65},
    "mailer_b_label": {"file": "shipping_label.jpg", "uv_scale": (1.0, 1.0), "roughness": 0.65},
    "mailer_c_label": {"file": "shipping_label.jpg", "uv_scale": (1.0, 1.0), "roughness": 0.65},
    "mailer_d_label": {"file": "shipping_label.jpg", "uv_scale": (1.0, 1.0), "roughness": 0.65},
    "parcel_box_b_label": {"file": "kraft_box.jpg", "uv_scale": (1.0, 1.0), "roughness": 0.82},
}

# Photo albedos already include shipping labels; skip extra sticker cuboids.
_PARCEL_PHOTOS = _load_parcel_photos()
_SKIP_LABEL_TEXTURES = True

# Semantic → (roughness, metallic). Tuned against pic/*.mp4 real capture.
_LOOK = {
    "mailer": (0.22, 0.04),
    "mailer_label": (0.65, 0.0),
    "parcel_box": (0.88, 0.0),
    "parcel_box_label": (0.65, 0.0),
    "sorting_table": (0.62, 0.0),
    "table_edge_wear": (0.70, 0.0),
    "table_leg": (0.40, 0.35),
    "klt_bin": (0.42, 0.12),
    "backdrop_panel": (0.35, 0.0),
    "equipment_wrap": (0.18, 0.0),
    "pc_tower": (0.55, 0.05),
    "metal_rack": (0.30, 0.55),
    "floor": (0.90, 0.0),
    "yellow_chair": (0.55, 0.0),
    "decor": (0.50, 0.0),
}


def _visual(obj: SceneObject) -> PreviewSurfaceCfg:
    roughness, metallic = _LOOK.get(obj.semantic, (0.4, 0.0))
    return PreviewSurfaceCfg(diffuse_color=obj.color, roughness=roughness, metallic=metallic)


def _resolve_usd(path: str) -> str:
    if path in _YCB_NUCLEUS:
        return _YCB_NUCLEUS[path]
    p = Path(path)
    if p.is_file():
        return str(p.resolve())
    candidate = _SIMFOUNDRY_ROOT / path
    if candidate.is_file():
        return str(candidate.resolve())
    raise FileNotFoundError(f"USD asset not found: {path} (tried {_SIMFOUNDRY_ROOT / path})")


def _spec_file_path(spec: dict[str, Any] | None) -> Path | None:
    if spec is None or not spec.get("file"):
        return None
    path = _TEX / spec["file"]
    return path if path.is_file() else None


def _texture_spec(obj: SceneObject) -> dict[str, Any] | None:
    """File textures only on parcels. Table/floor/backdrop keep layout.json PreviewSurface colors."""
    if _SKIP_LABEL_TEXTURES and ("label" in obj.name or "label" in obj.semantic):
        return None
    photo = _PARCEL_PHOTOS.get(obj.name)
    if _spec_file_path(photo) is not None:
        return photo
    if obj.semantic in ("parcel_box", "mailer"):
        spec = _TEXTURES.get(obj.semantic)
        return spec if _spec_file_path(spec) is not None else None
    return None


def _wrap_textured_spawn(
    base_cfg: sim_utils.CuboidCfg | sim_utils.CylinderCfg | sim_utils.MeshCuboidCfg, spec: dict[str, Any]
) -> Callable:
    tex_path = _spec_file_path(spec)
    if tex_path is None:
        return base_cfg.func  # type: ignore[return-value]

    base_func = base_cfg.func

    def _spawn(
        prim_path: str,
        cfg: sim_utils.CuboidCfg | sim_utils.CylinderCfg | sim_utils.MeshCuboidCfg,
        translation: tuple[float, float, float] | None = None,
        orientation: tuple[float, float, float, float] | None = None,
        **kwargs,
    ) -> Usd.Prim:
        prim = base_func(prim_path, cfg, translation, orientation, **kwargs)
        if spec.get("label"):
            bind_label_texture(prim_path, tex_path)
        else:
            normal = spec.get("normal")
            normal_path = (_TEX / normal) if normal else None
            bind_image_texture(
                prim_path,
                tex_path,
                uv_scale=tuple(spec.get("uv_scale", (1.0, 1.0))),
                roughness=float(spec.get("roughness", 0.5)),
                metallic=float(spec.get("metallic", 0.0)),
                normal_path=normal_path if normal_path and normal_path.is_file() else None,
                fallback_color=tuple(spec.get("fallback_color", (0.45, 0.45, 0.45))),
                uv_mode=str(spec.get("uv_mode", "xy")),
                wrap=str(spec.get("wrap", "repeat")),
                side_uv=tuple(spec["side_uv"]) if spec.get("side_uv") else None,
                normal_uv_scale=tuple(spec["normal_uv_scale"]) if spec.get("normal_uv_scale") else None,
                normal_wrap=str(spec["normal_wrap"]) if spec.get("normal_wrap") else None,
            )
        return prim

    return _spawn


def _add_parcel_visual_shell(
    root: Usd.Prim,
    *,
    size: tuple[float, float, float],
    soft_wrap: bool,
) -> None:
    """Hide the convex collision core and add a collision-free parcel shell.

    The mailer is a semi-rigid parcel in the real task: a cardboard core
    wrapped by black plastic.  A full cloth solver is unnecessary for a push
    skill and makes replay nondeterministic, so the outer mesh only conveys
    rounded corners, uneven fill and plastic wrinkles.  Physics remains on a
    slightly inset convex core created by ``MeshCuboidCfg``.
    """
    collision_visuals = [p for p in Usd.PrimRange(root) if p.GetTypeName() in ("Mesh", "Cube")]
    for collision_visual in collision_visuals:
        UsdGeom.Imageable(collision_visual).CreateVisibilityAttr().Set(UsdGeom.Tokens.invisible)

    x, y, z = (float(v) for v in size)
    hx, hy, hz = 0.5 * x, 0.5 * y, 0.5 * z
    bevel = min(x, y) * (0.12 if soft_wrap else 0.045)
    ring = [
        (-hx + bevel, -hy),
        (hx - bevel, -hy),
        (hx, -hy + bevel),
        (hx, hy - bevel),
        (hx - bevel, hy),
        (-hx + bevel, hy),
        (-hx, hy - bevel),
        (-hx, -hy + bevel),
    ]
    if soft_wrap:
        # Millimetre-scale asymmetry reads as a filled shipping bag while the
        # collision core remains rectangular and stable.
        offsets = ((0.000, -0.002), (0.002, -0.001), (0.001, 0.001),
                   (-0.001, 0.002), (-0.002, 0.001), (-0.001, -0.001),
                   (0.001, -0.002), (0.002, 0.000))
        top_z = (0.000, 0.0015, -0.0005, 0.0020, 0.0005, 0.0018, -0.0008, 0.0010)
    else:
        offsets = ((0.0, 0.0),) * 8
        top_z = (0.0,) * 8

    points = [Gf.Vec3f(px, py, -hz) for px, py in ring]
    points.extend(
        Gf.Vec3f(px + dx, py + dy, hz + dz)
        for (px, py), (dx, dy), dz in zip(ring, offsets, top_z)
    )
    points.append(Gf.Vec3f(0.0, 0.0, hz + (0.0012 if soft_wrap else 0.0)))

    counts: list[int] = [8]
    indices: list[int] = list(reversed(range(8)))
    for i in range(8):
        j = (i + 1) % 8
        counts.append(4)
        indices.extend((i, j, 8 + j, 8 + i))
    for i in range(8):
        j = (i + 1) % 8
        counts.append(3)
        indices.extend((16, 8 + i, 8 + j))

    shell = UsdGeom.Mesh.Define(root.GetStage(), f"{root.GetPath()}/VisualShell")
    shell.CreatePointsAttr(points)
    shell.CreateFaceVertexCountsAttr(counts)
    shell.CreateFaceVertexIndicesAttr(indices)
    shell.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
    shell.CreateDoubleSidedAttr(False)
    shell.CreateExtentAttr([Gf.Vec3f(-hx, -hy, -hz), Gf.Vec3f(hx, hy, hz + 0.002)])


def _wrap_parcel_shell_spawn(
    base_cfg: sim_utils.MeshCuboidCfg,
    spec: dict[str, Any] | None,
    *,
    visual_size: tuple[float, float, float],
    soft_wrap: bool,
) -> Callable:
    base_func = base_cfg.func

    def _spawn(
        prim_path: str,
        cfg: sim_utils.MeshCuboidCfg,
        translation: tuple[float, float, float] | None = None,
        orientation: tuple[float, float, float, float] | None = None,
        **kwargs,
    ) -> Usd.Prim:
        root = base_func(prim_path, cfg, translation, orientation, **kwargs)
        _add_parcel_visual_shell(root, size=visual_size, soft_wrap=soft_wrap)
        if spec is not None:
            tex_path = _spec_file_path(spec)
            if tex_path is not None:
                normal = spec.get("normal")
                normal_path = (_TEX / normal) if normal else None
                bind_image_texture(
                    prim_path,
                    tex_path,
                    uv_scale=tuple(spec.get("uv_scale", (1.0, 1.0))),
                    roughness=float(spec.get("roughness", 0.5)),
                    metallic=float(spec.get("metallic", 0.0)),
                    normal_path=normal_path if normal_path and normal_path.is_file() else None,
                    fallback_color=tuple(spec.get("fallback_color", (0.45, 0.45, 0.45))),
                    uv_mode="box",
                    wrap=str(spec.get("wrap", "clamp")),
                    side_uv=tuple(spec["side_uv"]) if spec.get("side_uv") else None,
                    normal_uv_scale=tuple(spec["normal_uv_scale"]) if spec.get("normal_uv_scale") else None,
                    normal_wrap=str(spec["normal_wrap"]) if spec.get("normal_wrap") else None,
                )
        return root

    return _spawn


def textured_floor_cuboid_cfg(size: tuple[float, float, float]) -> sim_utils.CuboidCfg:
    """Floor slab using layout-era PreviewSurface gray (no file texture on Cube)."""
    return sim_utils.CuboidCfg(
        size=size,
        collision_props=sim_utils.CollisionBaseCfg(collision_enabled=False),
        visual_material=PreviewSurfaceCfg(diffuse_color=(0.40, 0.41, 0.42), roughness=0.92),
    )


def spawn_visual_usd_with_physics(
    prim_path: str,
    cfg: sim_utils.UsdFileCfg,
    translation: tuple[float, float, float] | None = None,
    orientation: tuple[float, float, float, float] | None = None,
    **kwargs,
) -> Usd.Prim:
    """Spawn a visual-only USD (e.g. YCB Axis_Aligned) and author rigid + convexHull collision."""
    mass = float(kwargs.pop("simfoundry_mass", 0.1))
    prim = sim_utils.spawn_from_usd(prim_path, cfg, translation, orientation, **kwargs)
    root_path = prim.GetPath().pathString
    for mesh in sim_utils.get_all_matching_child_prims(root_path, lambda child: child.GetTypeName() == "Mesh"):
        mesh_path = mesh.GetPath().pathString
        schemas.define_collision_properties(mesh_path, schemas.CollisionBaseCfg(collision_enabled=True))
        schemas.define_mesh_collision_properties(
            mesh_path, schemas.MeshCollisionBaseCfg(mesh_approximation_name="convexHull")
        )
    schemas.define_rigid_body_properties(
        root_path,
        sim_utils.RigidBodyPropertiesCfg(
            kinematic_enabled=False,
            disable_gravity=False,
            solver_position_iteration_count=4,
            max_depenetration_velocity=1.0,
        ),
    )
    schemas.define_mass_properties(root_path, schemas.MassPropertiesCfg(mass=mass))
    return prim


def _spawn_primitive(obj: SceneObject) -> sim_utils.CuboidCfg | sim_utils.CylinderCfg | sim_utils.MeshCuboidCfg:
    collision = sim_utils.CollisionBaseCfg(collision_enabled=obj.name not in _NO_COLLISION)
    is_parcel = obj.semantic in ("parcel_box", "mailer")
    dynamic_iters = 32 if is_parcel else 24
    dynamic_contact_k = 4.5e4 if is_parcel else 2.0e4
    dynamic_contact_d = 1.2e3 if is_parcel else 8.0e2
    rigid = sim_utils.RigidBodyPropertiesCfg(
        kinematic_enabled=obj.kinematic,
        disable_gravity=obj.kinematic,
        max_depenetration_velocity=0.04 if not obj.kinematic else 1.0,
        solver_position_iteration_count=dynamic_iters if not obj.kinematic else 6,
        solver_velocity_iteration_count=10 if not obj.kinematic else 1,
        # Heavy damping kills residual bounce that looks like "shaking without contact".
        linear_damping=(4.0 if is_parcel else 1.2) if not obj.kinematic else 0.0,
        angular_damping=(6.0 if is_parcel else 2.0) if not obj.kinematic else 0.0,
    )
    mass = sim_utils.MassPropertiesCfg(mass=obj.mass)
    if obj.kinematic:
        material = UsdPhysicsRigidBodyMaterialCfg(
            static_friction=obj.friction,
            dynamic_friction=obj.friction,
            restitution=0.0,
        )
    else:
        # Newton MJWarp reads newton:* contact damping; PhysX-only damping is not enough.
        material = [
            UsdPhysicsRigidBodyMaterialCfg(
                static_friction=obj.friction,
                dynamic_friction=obj.friction,
                restitution=0.0,
            ),
            NewtonMaterialCfg(
                # Low rolling/torsion so a light palm sweep can slide parcels out of frame.
                torsional_friction=0.03 if is_parcel else 0.10,
                rolling_friction=0.02 if is_parcel else 0.10,
                contact_stiffness=dynamic_contact_k,
                contact_damping=dynamic_contact_d,
                contact_friction_gain=2.5e2,
            ),
        ]
    common = dict(
        rigid_props=rigid,
        collision_props=collision,
        mass_props=mass,
        physics_material=material,
        visual_material=_visual(obj),
    )
    if obj.shape == "cuboid":
        assert obj.size is not None
        if is_parcel:
            # X/Y are inset so the plastic/cardboard shell can visually
            # compress at contact. Z stays equal to the shell so the object
            # cannot settle with its rendered bottom below the tabletop.
            core_scale = (0.90, 0.88, 1.0) if obj.semantic == "mailer" else (0.96, 0.96, 1.0)
            core_size = tuple(float(v * scale) for v, scale in zip(obj.size, core_scale))
            # Use an analytic box for contact.  A triangulated convex cuboid
            # produced a persistent one-sided Newton contact force (up to
            # 11 cm of mailer drift in a zero-action rollout).
            cfg = sim_utils.CuboidCfg(size=core_size, **common)
        else:
            cfg = sim_utils.CuboidCfg(size=obj.size, **common)
    else:
        assert obj.radius is not None and obj.height is not None
        cfg = sim_utils.CylinderCfg(radius=obj.radius, height=obj.height, axis="Z", **common)
    tex = _texture_spec(obj)
    if is_parcel:
        assert obj.size is not None
        cfg = cfg.replace(
            func=_wrap_parcel_shell_spawn(
                cfg,
                tex,
                visual_size=obj.size,
                soft_wrap=obj.semantic == "mailer",
            )
        )
    elif tex is not None:
        cfg = cfg.replace(func=_wrap_textured_spawn(cfg, tex))
    return cfg


def _usd_file_cfg(obj: SceneObject, *, dynamic: bool) -> sim_utils.UsdFileCfg:
    assert obj.usd_path is not None
    usd_path = _resolve_usd(obj.usd_path)
    scale = _USD_SCALE.get(obj.usd_path)
    kwargs: dict[str, Any] = {"usd_path": usd_path}
    if scale is not None:
        kwargs["scale"] = scale
    if dynamic:
        kwargs["func"] = spawn_visual_usd_with_physics
    return sim_utils.UsdFileCfg(**kwargs)


def object_to_cfg(
    obj: SceneObject, table_frame: Pose, env_ns: str = "{ENV_REGEX_NS}"
) -> AssetBaseCfg | RigidObjectCfg:
    pose = world_pose(table_frame, obj)
    init = dict(pos=pose.pos, rot=pose.rot_xyzw)
    prim_path = f"{env_ns}/{obj.name}"

    if obj.shape == "usd":
        assert obj.usd_path is not None
        mass = obj.mass

        def _spawn_fn(
            prim_path: str,
            cfg: sim_utils.UsdFileCfg,
            translation: tuple[float, float, float] | None = None,
            orientation: tuple[float, float, float, float] | None = None,
            **kwargs,
        ) -> Usd.Prim:
            return spawn_visual_usd_with_physics(
                prim_path,
                cfg,
                translation,
                orientation,
                simfoundry_mass=mass,
                **kwargs,
            )

        scale = _USD_SCALE.get(obj.usd_path)
        spawn_kwargs: dict[str, Any] = {"usd_path": _resolve_usd(obj.usd_path)}
        if scale is not None:
            spawn_kwargs["scale"] = scale
        if obj.kinematic:
            spawn = sim_utils.UsdFileCfg(**spawn_kwargs)
            if obj.name in _KINEMATIC_WRITABLE:
                return RigidObjectCfg(
                    prim_path=prim_path,
                    spawn=spawn,
                    init_state=RigidObjectCfg.InitialStateCfg(**init),
                )
            return AssetBaseCfg(
                prim_path=prim_path,
                spawn=spawn,
                init_state=AssetBaseCfg.InitialStateCfg(**init),
            )
        spawn_kwargs["func"] = _spawn_fn
        return RigidObjectCfg(
            prim_path=prim_path,
            spawn=sim_utils.UsdFileCfg(**spawn_kwargs),
            init_state=RigidObjectCfg.InitialStateCfg(**init),
        )

    spawn = _spawn_primitive(obj)
    if obj.kinematic and obj.name not in _KINEMATIC_WRITABLE:
        return AssetBaseCfg(
            prim_path=prim_path,
            spawn=spawn,
            init_state=AssetBaseCfg.InitialStateCfg(**init),
        )
    return RigidObjectCfg(
        prim_path=prim_path,
        spawn=spawn,
        init_state=RigidObjectCfg.InitialStateCfg(**init),
    )


def apply_layout_to_scene(scene_cfg: Any, package: ScenePackage) -> Any:
    """Set scene_cfg.<object_name> from the scene package. Names must already exist as fields."""
    for obj in package.objects:
        if not hasattr(scene_cfg, obj.name):
            raise AttributeError(
                f"InteractiveSceneCfg has no field {obj.name!r}; add it so A/B scene packages stay swappable"
            )
        setattr(scene_cfg, obj.name, object_to_cfg(obj, package.table_frame))
    return scene_cfg
