"""Bind file textures onto spawned cuboids (A-period Real2Sim look)."""

from __future__ import annotations

from pathlib import Path

from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade

from isaaclab.sim.utils.stage import get_current_stage


def _ensure_mesh_st(mesh_prim: Usd.Prim, *, force: bool = False) -> None:
    """Author a simple planar ``st`` UV if the mesh has none (needed by UsdUVTexture)."""
    mesh = UsdGeom.Mesh(mesh_prim)
    pv_api = UsdGeom.PrimvarsAPI(mesh_prim)
    existing = pv_api.GetPrimvar("st")
    if existing and existing.HasValue() and not force:
        return
    points = mesh.GetPointsAttr().Get()
    if not points:
        return
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    dx = max(max_x - min_x, 1e-6)
    dy = max(max_y - min_y, 1e-6)
    uvs = [Gf.Vec2f((float(p[0]) - min_x) / dx, (float(p[1]) - min_y) / dy) for p in points]
    primvar = pv_api.CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.vertex)
    primvar.Set(uvs)


def _ensure_box_st(
    mesh_prim: Usd.Prim, *, side_uv: tuple[float, float] | None = None
) -> None:
    """Per-face cuboid UVs: +Z gets the photo; other faces sample ``side_uv`` (plastic/kraft fill)."""
    mesh = UsdGeom.Mesh(mesh_prim)
    points = mesh.GetPointsAttr().Get()
    counts = mesh.GetFaceVertexCountsAttr().Get()
    indices = mesh.GetFaceVertexIndicesAttr().Get()
    if not points or not counts or not indices:
        _ensure_mesh_st(mesh_prim, force=True)
        return
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    zs = [float(p[2]) for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)
    dx = max(max_x - min_x, 1e-6)
    dy = max(max_y - min_y, 1e-6)
    dz = max(max_z - min_z, 1e-6)

    def _uv(p, axis: int) -> Gf.Vec2f:
        x, y, z = float(p[0]), float(p[1]), float(p[2])
        if axis == 2:
            return Gf.Vec2f((x - min_x) / dx, (y - min_y) / dy)
        if axis == 0:
            return Gf.Vec2f((y - min_y) / dy, (z - min_z) / dz)
        return Gf.Vec2f((x - min_x) / dx, (z - min_z) / dz)

    uvs: list[Gf.Vec2f] = []
    cursor = 0
    for count in counts:
        n = int(count)
        face_idx = [int(indices[cursor + i]) for i in range(n)]
        cursor += n
        p0, p1, p2 = points[face_idx[0]], points[face_idx[1]], points[face_idx[min(2, n - 1)]]
        nx = (float(p1[1]) - float(p0[1])) * (float(p2[2]) - float(p0[2])) - (float(p1[2]) - float(p0[2])) * (
            float(p2[1]) - float(p0[1])
        )
        ny = (float(p1[2]) - float(p0[2])) * (float(p2[0]) - float(p0[0])) - (float(p1[0]) - float(p0[0])) * (
            float(p2[2]) - float(p0[2])
        )
        nz = (float(p1[0]) - float(p0[0])) * (float(p2[1]) - float(p0[1])) - (float(p1[1]) - float(p0[1])) * (
            float(p2[0]) - float(p0[0])
        )
        an = (abs(nx), abs(ny), abs(nz))
        axis = int(max(range(3), key=lambda i: an[i]))
        face_z = sum(float(points[vi][2]) for vi in face_idx) / max(n, 1)
        is_top = axis == 2 and face_z >= (min_z + max_z) * 0.5
        for vi in face_idx:
            if is_top:
                uvs.append(_uv(points[vi], 2))
            elif side_uv is not None:
                uvs.append(Gf.Vec2f(float(side_uv[0]), float(side_uv[1])))
            else:
                uvs.append(_uv(points[vi], axis))

    pv_api = UsdGeom.PrimvarsAPI(mesh_prim)
    primvar = pv_api.CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.faceVarying)
    primvar.Set(uvs)


def _bind_targets(root: Usd.Prim) -> list[Usd.Prim]:
    """Bind only Mesh. Cube cuboids keep PreviewSurfaceCfg (table/floor/backdrop)."""
    return [child for child in Usd.PrimRange(root) if child.GetTypeName() == "Mesh"]


def bind_image_texture(
    prim_path: str,
    image_path: str | Path,
    *,
    uv_scale: tuple[float, float] = (1.0, 1.0),
    roughness: float = 0.5,
    metallic: float = 0.0,
    normal_path: str | Path | None = None,
    fallback_color: tuple[float, float, float] = (0.5, 0.5, 0.5),
    uv_mode: str = "xy",
    wrap: str = "repeat",
    side_uv: tuple[float, float] | None = None,
    normal_uv_scale: tuple[float, float] | None = None,
    normal_wrap: str | None = None,
) -> None:
    """Author UsdPreviewSurface + UsdUVTexture on ``prim_path`` (cuboid root)."""
    stage = get_current_stage()
    image_path = Path(image_path).resolve()
    if not image_path.is_file():
        raise FileNotFoundError(image_path)

    root = stage.GetPrimAtPath(prim_path)
    if not root.IsValid():
        return

    mat_path = f"{prim_path}/Looks/image_mat"
    material = UsdShade.Material.Define(stage, mat_path)
    shader = UsdShade.Shader.Define(stage, f"{mat_path}/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(float(fallback_color[0]), float(fallback_color[1]), float(fallback_color[2]))
    )
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(float(roughness))
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(float(metallic))
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")

    st_reader = UsdShade.Shader.Define(stage, f"{mat_path}/st_reader")
    st_reader.CreateIdAttr("UsdPrimvarReader_float2")
    st_reader.CreateInput("varname", Sdf.ValueTypeNames.Token).Set("st")
    st_reader.CreateOutput("result", Sdf.ValueTypeNames.Float2)

    wrap_token = "clamp" if wrap == "clamp" else "repeat"
    uv_tex = UsdShade.Shader.Define(stage, f"{mat_path}/diffuse_texture")
    uv_tex.CreateIdAttr("UsdUVTexture")
    uv_tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(str(image_path))
    uv_tex.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token).Set("sRGB")
    uv_tex.CreateInput("wrapS", Sdf.ValueTypeNames.Token).Set(wrap_token)
    uv_tex.CreateInput("wrapT", Sdf.ValueTypeNames.Token).Set(wrap_token)
    uv_tex.CreateInput("scale", Sdf.ValueTypeNames.Float2).Set(Gf.Vec2f(float(uv_scale[0]), float(uv_scale[1])))
    uv_tex.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
    uv_tex.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(st_reader.ConnectableAPI(), "result")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(uv_tex.ConnectableAPI(), "rgb")

    if normal_path is not None:
        npath = Path(normal_path).resolve()
        if npath.is_file():
            n_tex = UsdShade.Shader.Define(stage, f"{mat_path}/normal_texture")
            n_tex.CreateIdAttr("UsdUVTexture")
            n_tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(str(npath))
            n_tex.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token).Set("raw")
            n_wrap = "clamp" if (normal_wrap or wrap) == "clamp" else "repeat"
            n_scale = normal_uv_scale if normal_uv_scale is not None else uv_scale
            n_tex.CreateInput("wrapS", Sdf.ValueTypeNames.Token).Set(n_wrap)
            n_tex.CreateInput("wrapT", Sdf.ValueTypeNames.Token).Set(n_wrap)
            n_tex.CreateInput("scale", Sdf.ValueTypeNames.Float2).Set(
                Gf.Vec2f(float(n_scale[0]), float(n_scale[1]))
            )
            n_tex.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
            n_tex.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(
                st_reader.ConnectableAPI(), "result"
            )
            shader.CreateInput("normal", Sdf.ValueTypeNames.Normal3f).ConnectToSource(
                n_tex.ConnectableAPI(), "rgb"
            )

    for child in _bind_targets(root):
        if uv_mode == "box":
            _ensure_box_st(child, side_uv=side_uv)
        else:
            _ensure_mesh_st(child)
        UsdShade.MaterialBindingAPI(child).Bind(material)


def set_diffuse_texture_file(
    prim_path: str,
    image_path: str | Path,
    *,
    roughness: float = 0.5,
    metallic: float = 0.0,
    fallback_color: tuple[float, float, float] = (0.5, 0.5, 0.5),
    uv_mode: str = "box",
    wrap: str = "clamp",
    normal_path: str | Path | None = None,
) -> None:
    """Swap albedo on an already-bound cuboid. Leave the bound normal map alone unless given."""
    stage = get_current_stage()
    image_path = Path(image_path).resolve()
    if not image_path.is_file():
        return
    shader_prim = stage.GetPrimAtPath(f"{prim_path}/Looks/image_mat/diffuse_texture")
    if shader_prim.IsValid():
        UsdShade.Shader(shader_prim).CreateInput("file", Sdf.ValueTypeNames.Asset).Set(str(image_path))
        n_prim = stage.GetPrimAtPath(f"{prim_path}/Looks/image_mat/normal_texture")
        if normal_path is not None and n_prim.IsValid():
            UsdShade.Shader(n_prim).CreateInput("file", Sdf.ValueTypeNames.Asset).Set(str(Path(normal_path).resolve()))
        return
    bind_image_texture(
        prim_path,
        image_path,
        uv_scale=(1.0, 1.0),
        roughness=roughness,
        metallic=metallic,
        fallback_color=fallback_color,
        uv_mode=uv_mode,
        wrap=wrap,
        normal_path=normal_path,
    )


def bind_label_texture(prim_path: str, image_path: str | Path) -> None:
    """Small decal-style label on a thin cuboid."""
    bind_image_texture(
        prim_path,
        image_path,
        uv_scale=(1.0, 1.0),
        roughness=0.65,
        metallic=0.0,
        fallback_color=(0.97, 0.97, 0.95),
        wrap="clamp",
    )


def paint_meshes_black(prim_path: str, *, roughness: float = 0.45, metallic: float = 0.08) -> None:
    """Override all Mesh materials under ``prim_path`` to matte black (for Nucleus KLT)."""
    stage = get_current_stage()
    root = stage.GetPrimAtPath(prim_path)
    if not root.IsValid():
        return
    mat_path = f"{prim_path}/Looks/black_mat"
    material = UsdShade.Material.Define(stage, mat_path)
    shader = UsdShade.Shader.Define(stage, f"{mat_path}/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.06, 0.06, 0.07))
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(float(roughness))
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(float(metallic))
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    for child in Usd.PrimRange(root):
        if child.GetTypeName() in ("Mesh", "Cube"):
            UsdShade.MaterialBindingAPI(child).Bind(material)
