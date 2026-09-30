#!/usr/bin/env python3
"""Static side-contact search with hand convex hull clipped to parcel height.

No rollout, no training admission, and no global infeasibility conclusion.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
from pxr import Usd, UsdGeom
from probe_sorting_kinematics import ArmFK

p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
project = Path(__file__).resolve().parents[1]
asset = project / 'assets/robots/g1_23dof_u1_rubber/g1_23dof_rev_1_0_u1_black/payloads/instances.usda'
stage = Usd.Stage.Open(str(asset))
rng = np.random.default_rng(2026092911)
results = []
for lid, task, side, obj, size in [(66009, 'nudge_mailer_to_bin', 'left', 'mailer', [.15,.145,.04]),
                                  (66010, 'push_box_to_bin', 'right', 'box', [.14,.09,.045])]:
    ep = a.root / f'case_{lid}/layout_{lid}_{task}'
    prim = stage.GetPrimAtPath(f'/Instances/{side}_wrist_roll_rubber_hand_1/{side}_wrist_roll_rubber_hand')
    assert prim.GetAttribute('physics:approximation').Get() == 'convexHull'
    assert np.allclose(np.asarray(UsdGeom.XformCache().GetLocalToWorldTransform(prim)), np.eye(4))
    points = np.asarray(UsdGeom.Mesh(prim).GetPointsAttr().Get(), dtype=float)
    hull = ConvexHull(points)
    vertices = points[hull.vertices]
    edge_ids = sorted({tuple(sorted((int(i),int(j)))) for tri in hull.simplices for i,j in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]})
    edges = points[np.asarray(edge_ids)]
    fk = ArmFK(side)
    lo, hi = np.asarray(fk.bounds).T
    start = 13 if side == 'left' else 18
    with np.load(ep/'raw.npz') as z, np.load(ep/'trace.npz') as tr, np.load(ep/'parcel_orientation.npz') as ori:
        qref = z['q'][57, start:start+5].astype(float)
        errors = [np.linalg.norm(fk.palm(z['q'][t,start:start+5], z['q'][t,12])-tr['palm_'+side][t]) for t in [0,40,57,100,159]]
        assert max(errors) < 1e-4
        center = tr[obj][0].copy()
        rot = Rotation.from_quat(ori[obj][0]).as_matrix()
    # Axis-aligned rear support plane of initial OBB; conservative side approach.
    extent = np.abs(rot) @ (np.asarray(size)/2)
    face_x = float(center[0]+extent[0])
    contact_goal = np.array([face_x+.002, center[1], center[2]])
    def world_vertices(q):
        pose = fk.pose(q)
        return vertices @ pose[:3,:3].T + pose[:3,3]
    def support_point(q, v):
        pose = fk.pose(q)
        e = edges @ pose[:3,:3].T + pose[:3,3]
        zlo, zhi = center[2]-extent[2], center[2]+extent[2]
        clipped = [v[(v[:,2]>=zlo)&(v[:,2]<=zhi)]]
        for zplane in (zlo,zhi):
            d = e[:,1,2]-e[:,0,2]
            valid = (np.abs(d)>1e-10) & ((e[:,0,2]-zplane)*(e[:,1,2]-zplane)<=0)
            u = (zplane-e[valid,0,2])/d[valid]
            clipped.append(e[valid,0]+u[:,None]*(e[valid,1]-e[valid,0]))
        region = np.concatenate(clipped)
        if len(region): return region[np.argmin(region[:,0])]
        return v[np.argmin(np.abs(v[:,2]-center[2]))]
    def objective(q):
        v = world_vertices(q)
        # Supporting vertex faces -X. Piecewise objective; multistart is local only.
        point = support_point(q, v)
        return np.r_[point-contact_goal, 4*max(0., .752-float(v[:,2].min())), .0001*(q-qref)]
    seeds = [qref, np.zeros(5)] + [np.clip(qref+rng.normal(0,.3,5),lo,hi) for _ in range(4)] + [rng.uniform(lo,hi) for _ in range(4)]
    attempts = []
    for seed in seeds:
        sol = least_squares(objective, np.clip(seed,lo,hi), bounds=(lo,hi), max_nfev=350,
                            ftol=1e-9, xtol=1e-9, gtol=1e-9)
        v = world_vertices(sol.x)
        point = support_point(sol.x, v)
        checks = dict(rear_plane_gap=abs(point[0]-contact_goal[0])<=.003,
                      contact_y_inside=abs(point[1]-center[1])<=extent[1]-.005,
                      contact_z_inside=center[2]-extent[2]+.005<=point[2]<=center[2]+extent[2]-.005,
                      entire_hand_above_table=v[:,2].min()>=.751)
        checks = {k:bool(v) for k,v in checks.items()}
        attempts.append(dict(q=sol.x.tolist(), support_vertex=point.tolist(), palm=fk.palm(sol.x).tolist(),
                             hand_min_z=float(v[:,2].min()), residual=float(np.linalg.norm(point-contact_goal)),
                             checks=checks, static_screen_passed=all(checks.values())))
    attempts.sort(key=lambda x:(not x['static_screen_passed'],x['residual']))
    result=dict(layout_id=lid, task=task, target_contact=contact_goal.tolist(), fk_max_error_m=float(max(errors)),
                raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(), attempts=attempts)
    results.append(result)
    print(lid, 'static passing',sum(x['static_screen_passed'] for x in attempts),'best',attempts[0],flush=True)
a.out.write_text(json.dumps(dict(rows=results, mesh_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),
    limits='Local multistart static search of a -X support point on authored convex hull clipped to parcel vertical extent, with conservative entire-hand table clearance. Rear OBB support plane approximation. No other links, obstacles, trajectory, force, actuator or collision-cooking validation. Neither a valid demonstration nor a global infeasibility proof.',
    training_ready=False, goal_complete=False),indent=2))
