#!/usr/bin/env python3
"""Read-only convex-hull/parcel OBB SAT on recorded poses; no contact-force claim."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
from pxr import Usd,UsdGeom
from probe_sorting_kinematics import ArmFK
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
asset=Path(__file__).resolve().parents[1]/'assets/robots/g1_23dof_u1_rubber/g1_23dof_rev_1_0_u1_black/payloads/instances.usda';stage=Usd.Stage.Open(str(asset));hands={};mesh_info={}
for side in ['left','right']:
 prim=stage.GetPrimAtPath(f'/Instances/{side}_wrist_roll_rubber_hand_1/{side}_wrist_roll_rubber_hand')
 assert prim.GetAttribute('physics:approximation').Get()=='convexHull' and prim.GetAttribute('physics:collisionEnabled').Get()
 points=np.asarray(UsdGeom.Mesh(prim).GetPointsAttr().Get(),dtype=float)
 # Collision instance and mesh transforms are identity relative to hand link.
 matrix=np.asarray(UsdGeom.XformCache().GetLocalToWorldTransform(prim));assert np.allclose(matrix,np.eye(4),atol=1e-10)
 hull=ConvexHull(points);vertices=points[hull.vertices];normals=hull.equations[:,:3]
 edge_ids=set()
 for tri in hull.simplices:
  for i,j in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]:edge_ids.add(tuple(sorted((int(i),int(j)))))
 edges=np.array([points[j]-points[i] for i,j in sorted(edge_ids)]);edges/=np.linalg.norm(edges,axis=1)[:,None]
 hands[side]=(vertices,normals,edges,ArmFK(side));mesh_info[side]=dict(prim=str(prim.GetPath()),points=len(points),hull_vertices=len(vertices),hull_faces=len(normals),triangulated_edges=len(edges))
def sat_gap(vertices,normals,edges,rotation,translation,half):
 v=vertices@rotation.T+translation
 axes=[normals@rotation.T,np.eye(3)];e=edges@rotation.T
 for axis in np.eye(3):axes.append(np.cross(e,axis))
 axes=np.concatenate(axes);length=np.linalg.norm(axes,axis=1);axes=axes[length>1e-10]/length[length>1e-10,None]
 proj=v@axes.T;radius=np.abs(axes)@half
 negative=-radius-proj.max(axis=0);positive=proj.min(axis=0)-radius;gaps=np.maximum(negative,positive);i=int(np.argmax(gaps));normal=axes[i] if positive[i]>=negative[i] else -axes[i]
 return float(gaps[i]),normal.tolist()
rows=[]
for raw in sorted(a.root.glob('case_*/layout_*/raw.npz')):
 task=raw.parent.name.split('_',2)[2];obj='box' if task=='push_box_to_bin' else 'mailer';side='right' if obj=='box' else 'left';start=18 if side=='right' else 13;vertices,normals,edges,fk=hands[side];half=np.array([.14,.09,.045] if obj=='box' else [.15,.145,.04])/2
 control=json.loads((raw.parent/'expert_control.json').read_text());frames=[];fk_errors=[]
 with np.load(raw) as z,np.load(raw.parent/'trace.npz') as tr,np.load(raw.parent/'parcel_orientation.npz') as ori:
  meta=json.loads(str(z['collect_meta']));rot=Rotation.from_quat(ori[obj]).as_matrix()
  for t in range(160):
   pose=fk.pose(z['q'][t,start:start+5],z['q'][t,12]);palm=fk.palm(z['q'][t,start:start+5],z['q'][t,12]);fk_errors.append(float(np.linalg.norm(palm-tr['palm_'+side][t])))
   relative_rotation=rot[t].T@pose[:3,:3];relative_translation=rot[t].T@(pose[:3,3]-tr[obj][t]);gap,axis=sat_gap(vertices,normals,edges,relative_rotation,relative_translation,half)
   frames.append(dict(frame=t,mode=control[t]['mode'],sat_max_separation_m=gap,axis_object_frame=axis,palm=palm.tolist(),object_xyz=tr[obj][t].tolist(),commanded_palm=control[t]['target_xyz']))
 assert max(fk_errors)<1e-4
 phases={}
 for mode in sorted({f['mode'] for f in frames}):
  fs=[f for f in frames if f['mode']==mode];g=np.array([f['sat_max_separation_m'] for f in fs]);phases[mode]=dict(frames=len(fs),min_gap_m=float(g.min()),max_gap_m=float(g.max()),overlap_frames=int((g<=0).sum()),within2mm_frames=int((g<=.002).sum()),palm_delta=(np.array(fs[-1]['palm'])-fs[0]['palm']).tolist(),object_delta=(np.array(fs[-1]['object_xyz'])-fs[0]['object_xyz']).tolist())
 row=dict(path=str(raw),raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),orientation_sha256=hashlib.sha256((raw.parent/'parcel_orientation.npz').read_bytes()).hexdigest(),primitive=meta['front_reposition_distance'],fk_max_error=max(fk_errors),phases=phases,frames=frames);rows.append(row)
 print(raw.parent.name,'primitive',row['primitive'],json.dumps({k:v for k,v in phases.items() if k in ['press_x','retreat_x','hold_x']}),flush=True)
a.out.write_text(json.dumps(dict(mesh_asset=str(asset),asset_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),mesh_info=mesh_info,rows=rows,method='Separating-axis test between authored USD hand convex hull transformed by verified recorded-q FK and nominal parcel OBB from measured quaternion. Positive max gap proves geometric separation for these ideal shapes, not Euclidean surface distance; nonpositive means no separating axis.',limits='Not the cooked runtime collision representation, contact margin, contact force or impulse. Does not include other arm links or visual-only geometry. Cannot prove dynamic contact or task infeasibility.',training_ready=False,goal_complete=False),indent=2))
