#!/usr/bin/env python3
"""Regenerate g1 u1_black hand_partitioned.usda: plane-cut + densify + circularize.

Produces a clean circumferential silver/black GeomSubset seam at x=CUT without
the face-centroid sawtooth of the original partition.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from pxr import Gf, Usd, UsdGeom

ROOT = Path(__file__).resolve().parents[1] / "assets/robots/g1_23dof_u1_rubber/g1_23dof_rev_1_0_u1_black/payloads"
GEOM = ROOT.parents[1] / "g1_23dof_rev_1_0/payloads/geometries.usd"
CUT = 0.088
# Convexification fills the gaps between splayed fingers.  Keep the official
# black-hand length (and therefore its established kinematic reference), but
# inset the hull laterally/vertically so collision stays inside the rendering.
COLLISION_Y_SCALE = 1.0
COLLISION_Z_SCALE = 1.0
MAX_EDGE = 0.0009


def triangulate(counts, indices):
    faces = []
    i = 0
    for c in counts:
        poly = indices[i : i + c]
        i += c
        for k in range(1, c - 1):
            faces.append([int(poly[0]), int(poly[k]), int(poly[k + 1])])
    return faces


def cut_mesh(points, faces, cut_x):
    pts = [tuple(map(float, p)) for p in points]
    edge_cache = {}

    def side(i):
        return pts[i][0] < cut_x

    def edge_hit(i, j):
        a, b = (i, j) if i < j else (j, i)
        if (a, b) in edge_cache:
            return edge_cache[(a, b)]
        pa, pb = np.asarray(pts[a]), np.asarray(pts[b])
        t = 0.5 if abs(pb[0] - pa[0]) < 1e-12 else (cut_x - pa[0]) / (pb[0] - pa[0])
        t = float(np.clip(t, 0.0, 1.0))
        p = (1 - t) * pa + t * pb
        p[0] = cut_x
        idx = len(pts)
        pts.append(tuple(p.tolist()))
        edge_cache[(a, b)] = idx
        return idx

    silver, black = [], []
    for i0, i1, i2 in faces:
        s0, s1, s2 = side(i0), side(i1), side(i2)
        n = int(s0) + int(s1) + int(s2)
        if n == 3:
            silver.append([i0, i1, i2])
            continue
        if n == 0:
            black.append([i0, i1, i2])
            continue
        verts = [i0, i1, i2]
        sides = [s0, s1, s2]
        if n == 1:
            si = sides.index(True)
            a, b, c = verts[si], verts[(si + 1) % 3], verts[(si + 2) % 3]
            ab, ac = edge_hit(a, b), edge_hit(a, c)
            silver.append([a, ab, ac])
            black += [[b, c, ac], [b, ac, ab]]
        else:
            bi = sides.index(False)
            a, b, c = verts[bi], verts[(bi + 1) % 3], verts[(bi + 2) % 3]
            ab, ac = edge_hit(a, b), edge_hit(a, c)
            black.append([a, ab, ac])
            silver += [[b, c, ac], [b, ac, ab]]
    return pts, silver, black


def densify_ring(pts, silver, black, cut_x, max_edge):
    pts = list(pts)
    silver = [list(t) for t in silver]
    black = [list(t) for t in black]

    def on_plane(i):
        return abs(pts[i][0] - cut_x) < 1e-7

    for _ in range(20):
        edges = {}
        for faces in (silver, black):
            for tri in faces:
                for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
                    if on_plane(a) and on_plane(b):
                        key = (a, b) if a < b else (b, a)
                        edges[key] = True
        long_edges = [
            e for e in edges if np.linalg.norm(np.subtract(pts[e[0]], pts[e[1]])) > max_edge
        ]
        if not long_edges:
            break
        split_mids = {}
        for a, b in long_edges:
            mid = tuple(((np.asarray(pts[a]) + np.asarray(pts[b])) * 0.5).tolist())
            mid = (cut_x, mid[1], mid[2])
            mi = len(pts)
            pts.append(mid)
            split_mids[(a, b)] = mi

        def split_faces(faces):
            out = []
            for tri in faces:
                mids = []
                for i in range(3):
                    u, v = tri[i], tri[(i + 1) % 3]
                    key = (u, v) if u < v else (v, u)
                    if key in split_mids:
                        mids.append((i, split_mids[key], u, v))
                if not mids:
                    out.append(tri)
                    continue
                i, mi, u, v = mids[0]
                w = tri[(i + 2) % 3]
                if tri[i] == u:
                    out += [[u, mi, w], [mi, v, w]]
                else:
                    out += [[v, mi, w], [mi, u, w]]
            return out

        silver = split_faces(silver)
        black = split_faces(black)
    return pts, silver, black


def circularize(pts, cut_x):
    P = np.asarray(pts, dtype=float)
    on = np.where(np.abs(P[:, 0] - cut_x) < 1e-7)[0]
    if len(on) < 8:
        return pts
    yz = P[on][:, 1:3]
    c = yz.mean(axis=0)
    r = np.linalg.norm(yz - c, axis=1)
    lo, hi = np.percentile(r, [15, 92])
    keep = on[(r >= lo) & (r <= hi)]
    yz = P[keep][:, 1:3]
    c = yz.mean(axis=0)
    rad = float(np.median(np.linalg.norm(yz - c, axis=1)))
    for i in on:
        v = P[i, 1:3] - c
        d = np.linalg.norm(v)
        if d < 1e-8 or d < lo * 0.85:
            continue
        P[i, 1:3] = c + rad * (v / d)
        P[i, 0] = cut_x
    return [tuple(p) for p in P]


def face_normals(pts, tris):
    P = np.asarray(pts)
    v0, v1, v2 = P[[t[0] for t in tris]], P[[t[1] for t in tris]], P[[t[2] for t in tris]]
    n = np.cross(v1 - v0, v2 - v0)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    return n


def main() -> None:
    gstage = Usd.Stage.Open(str(GEOM))
    out_path = ROOT / "hand_partitioned.usda"
    if out_path.exists():
        out_path.unlink()
    out = Usd.Stage.CreateNew(str(out_path))
    out.SetMetadata("metersPerUnit", 1.0)
    out.SetMetadata("upAxis", "Z")
    UsdGeom.Scope.Define(out, "/HandPartitioned")

    collision_path = ROOT / "hand_collision.usda"
    if collision_path.exists():
        collision_path.unlink()
    collision = Usd.Stage.CreateNew(str(collision_path))
    collision.SetMetadata("metersPerUnit", 1.0)
    collision.SetMetadata("upAxis", "Z")
    UsdGeom.Scope.Define(collision, "/HandCollision")

    for side in ("left", "right"):
        src = UsdGeom.Mesh(
            gstage.GetPrimAtPath(f"/Geometries/{side}_wrist_roll_rubber_hand/{side}_wrist_roll_rubber_hand")
        )
        pts0 = np.array(src.GetPointsAttr().Get(), dtype=np.float64)
        faces = triangulate(
            np.array(src.GetFaceVertexCountsAttr().Get()),
            np.array(src.GetFaceVertexIndicesAttr().Get()),
        )
        pts, silver, black = cut_mesh(pts0, faces, CUT)
        pts, silver, black = densify_ring(pts, silver, black, CUT, MAX_EDGE)
        pts = circularize(pts, CUT)
        all_tris = silver + black
        vn = np.zeros((len(pts), 3))
        for t, n in zip(all_tris, face_normals(pts, all_tris)):
            for i in t:
                vn[i] += n
        vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)

        UsdGeom.Xform.Define(out, f"/HandPartitioned/{side}_wrist_roll_rubber_hand")
        mesh = UsdGeom.Mesh.Define(
            out, f"/HandPartitioned/{side}_wrist_roll_rubber_hand/{side}_wrist_roll_rubber_hand"
        )
        mesh.CreatePointsAttr([Gf.Vec3f(*p) for p in pts])
        mesh.CreateFaceVertexCountsAttr([3] * len(all_tris))
        mesh.CreateFaceVertexIndicesAttr([i for t in all_tris for i in t])
        mesh.CreateNormalsAttr([Gf.Vec3f(*n) for n in vn])
        mesh.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
        mesh.CreateSubdivisionSchemeAttr().Set(UsdGeom.Tokens.none)
        subset = UsdGeom.Subset.Define(
            out,
            f"/HandPartitioned/{side}_wrist_roll_rubber_hand/{side}_wrist_roll_rubber_hand/forearm_silver",
        )
        subset.CreateElementTypeAttr().Set(UsdGeom.Tokens.face)
        subset.CreateFamilyNameAttr().Set("materialBind")
        subset.CreateIndicesAttr(list(range(len(silver))))

        # Collision must cover the black hand only.  The upstream collision
        # referenced the complete wrist/forearm mesh; its convex hull therefore
        # reached the parcel before the visible palm did.
        used = sorted({i for tri in black for i in tri})
        remap = {old: new for new, old in enumerate(used)}
        raw_collision_pts = np.asarray([pts[i] for i in used], dtype=float)
        centre = raw_collision_pts.mean(axis=0)
        raw_collision_pts[:, 1] = centre[1] + COLLISION_Y_SCALE * (
            raw_collision_pts[:, 1] - centre[1]
        )
        raw_collision_pts[:, 2] = centre[2] + COLLISION_Z_SCALE * (
            raw_collision_pts[:, 2] - centre[2]
        )
        collision_pts = [tuple(p) for p in raw_collision_pts]
        collision_tris = [[remap[i] for i in tri] for tri in black]
        UsdGeom.Xform.Define(collision, f"/HandCollision/{side}_wrist_roll_rubber_hand")
        collision_mesh = UsdGeom.Mesh.Define(
            collision,
            f"/HandCollision/{side}_wrist_roll_rubber_hand/{side}_wrist_roll_rubber_hand",
        )
        collision_mesh.CreatePointsAttr([Gf.Vec3f(*p) for p in collision_pts])
        collision_mesh.CreateFaceVertexCountsAttr([3] * len(collision_tris))
        collision_mesh.CreateFaceVertexIndicesAttr([i for t in collision_tris for i in t])
        collision_mesh.CreateSubdivisionSchemeAttr().Set(UsdGeom.Tokens.none)
        print(side, "pts", len(pts), "silver", len(silver), "black", len(black))

    out.GetRootLayer().Save()
    collision.GetRootLayer().Save()
    print("wrote", out_path)
    print("wrote", collision_path)


if __name__ == "__main__":
    main()
