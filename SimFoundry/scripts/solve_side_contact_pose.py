#!/usr/bin/env python3
"""Explicit collision-face pose IK, followed by geometric checks. Diagnostic only."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
from pxr import Usd,UsdGeom
from probe_sorting_kinematics import ArmFK

p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
asset=Path(__file__).resolve().parents[1]/'assets/robots/g1_23dof_u1_rubber/g1_23dof_rev_1_0_u1_black/payloads/instances.usda'
stage=Usd.Stage.Open(str(asset));results=[]
def gap(v,normals,edges,center,rot,half):
    v=(v-center)@rot;normals=normals@rot;edges=edges@rot
    axes=np.concatenate([normals,np.eye(3)]+[np.cross(edges,k) for k in np.eye(3)])
    lengths=np.linalg.norm(axes,axis=1);axes=axes[lengths>1e-8]/lengths[lengths>1e-8,None]
    proj=v@axes.T;radius=np.abs(axes)@half
    return float(np.maximum(proj.min(axis=0)-radius,-radius-proj.max(axis=0)).max())
for lid,task,side,target in [(66009,'nudge_mailer_to_bin','left','mailer'),(66010,'push_box_to_bin','right','box')]:
    ep=a.root/f'case_{lid}/layout_{lid}_{task}';fk=ArmFK(side);lo,hi=np.asarray(fk.bounds).T;start=13 if side=='left' else 18
    prim=stage.GetPrimAtPath(f'/Instances/{side}_wrist_roll_rubber_hand_1/{side}_wrist_roll_rubber_hand')
    assert prim.GetAttribute('physics:approximation').Get()=='convexHull'
    assert np.allclose(np.asarray(UsdGeom.XformCache().GetLocalToWorldTransform(prim)),np.eye(4))
    pts=np.asarray(UsdGeom.Mesh(prim).GetPointsAttr().Get(),float);hull=ConvexHull(pts);verts=pts[hull.vertices];normals=hull.equations[:,:3]
    faces=pts[hull.simplices];centroids=faces.mean(axis=1)
    areas=np.linalg.norm(np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0]),axis=1)/2
    edges=np.concatenate([faces[:,1]-faces[:,0],faces[:,2]-faces[:,1],faces[:,0]-faces[:,2]])
    # Deterministic spatial/normal diversity among distal collision facets.
    choices=[]
    for i in np.argsort(-areas):
        if centroids[i,0]<.12:continue
        if all(np.linalg.norm(centroids[i]-centroids[j])>.025 or np.dot(normals[i],normals[j])<.8 for j in choices):choices.append(int(i))
        if len(choices)==16:break
    poses={};errors=[]
    with np.load(ep/'raw.npz') as z,np.load(ep/'trace.npz') as tr,np.load(ep/'parcel_orientation.npz') as ori:
        qref=z['q'][57,start:start+5].astype(float)
        for t in [0,40,57,100,159]:errors.append(float(np.linalg.norm(fk.palm(z['q'][t,start:start+5],z['q'][t,12])-tr['palm_'+side][t])))
        for obj,sz in [('box',[.14,.09,.045]),('mailer',[.15,.145,.04])]:poses[obj]=(tr[obj][0].copy(),Rotation.from_quat(ori[obj][0]).as_matrix(),np.asarray(sz)/2)
    assert max(errors)<1e-4
    center,rot,half=poses[target];axis=int(np.argmax(np.abs(rot[0])));sign=1 if rot[0,axis]>=0 else -1;n=sign*rot[:,axis]
    goal=center+n*(half[axis]+.002);goal[2]+=.005
    attempts=[]
    for faceid in choices:
        localpoint=centroids[faceid];localnormal=normals[faceid]
        def residual(q):
            T=fk.pose(q);v=verts@T[:3,:3].T+T[:3,3]
            point=T[:3,:3]@localpoint+T[:3,3];normal=T[:3,:3]@localnormal
            return np.r_[point-goal,.05*(normal+n),4*max(0,.751-v[:,2].min())]
        for seed in [qref,np.zeros(5),np.clip(qref+np.array([-.2,.1,.5,.1,-.5]),lo,hi)]:
            sol=least_squares(residual,seed,bounds=(lo,hi),max_nfev=220,ftol=1e-8,xtol=1e-8,gtol=1e-8)
            T=fk.pose(sol.x);R=T[:3,:3];v=verts@R.T+T[:3,3];point=R@localpoint+T[:3,3];normal=R@localnormal
            err=float(np.linalg.norm(point-goal));angle=float(np.arccos(np.clip(normal@(-n),-1,1)));minimum=float(v[:,2].min())
            # Expensive SAT only for pose candidates satisfying point/normal/table criteria.
            gaps=None
            if err<=.003 and angle<=np.deg2rad(20) and minimum>=.7509:
                gaps={obj:gap(v,normals@R.T,edges@R.T,*pose) for obj,pose in poses.items()}
            passed=gaps is not None and gaps[target]>=-.001 and all(g>=.002 for obj,g in gaps.items() if obj!=target)
            attempts.append(dict(face_id=faceid,local_point=localpoint.tolist(),local_normal=localnormal.tolist(),q=sol.x.tolist(),point=point.tolist(),normal=normal.tolist(),position_error_m=err,normal_error_rad=angle,hand_min_z=minimum,sat_gaps=gaps,static_candidate=bool(passed)))
    attempts.sort(key=lambda x:(not x['static_candidate'],x['position_error_m']+.05*x['normal_error_rad']+4*max(0,.751-x['hand_min_z'])))
    row=dict(layout_id=lid,task=task,goal=goal.tolist(),object_outward_normal=n.tolist(),fk_max_error=max(errors),face_count=len(choices),attempts=attempts,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest());results.append(row)
    print(lid,'candidates',sum(x['static_candidate'] for x in attempts),'of',len(attempts),'best',attempts[0],flush=True)
    a.out.write_text(json.dumps(dict(rows=results,asset_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),training_ready=False,goal_complete=False,limits='Selected distal collision facets and three local seeds each, conservative full-hand table plane. Static candidate only: no arm-link/self collisions, actuator force, continuous trajectory or runtime cooked geometry. Failure is not global infeasibility.'),indent=2))
