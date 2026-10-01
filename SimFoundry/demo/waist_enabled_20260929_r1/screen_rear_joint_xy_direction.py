"""Observed-geometry screen for joint rear X/Y reference direction, never physics.
Maximize retained original forward Y; among ties minimize change to parent X.
Original X slew/lead intersection, Z and near-edge non-outward conditions remain.
Independent vertex enumeration checks LP optima on every actual audited override.
"""
from pathlib import Path
import json,hashlib,itertools
import numpy as np
from scipy.optimize import linprog
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[]
for run in ['front_edge_speed_groups_r1','rear_coupled_progress_groups_r1']:
 for cid,task,key,direction in [(840001,'push_box_to_bin','box',-1),(840004,'nudge_mailer_to_bin','mailer',1)]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';an='REAR_COUPLED_PROGRESS_LIVE_AUDIT.json' if run.startswith('rear_coupled') else 'REAR_COP_CORE_SLICE_LIVE_AUDIT.json';audit=json.loads((ep/an).read_text());assert audit['passed']
  for n,h in audit['source_sha256'].items():assert sha(ep/n)==h
  fr=json.loads((ep/'frontal_bypass.json').read_text());core=np.asarray(fr['plan']['rear_cop_centering']['actual_core_size_xyz'])
  with np.load(ep/'trace.npz') as z:obj=z[key].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
  samples=[]
  for prev,row in zip(fr['rows'],fr['rows'][1:]):
   f=row.get('rear_cop_centering',{})
   if not f.get('override'):continue
   t=row['step'];assert t==prev['step']+1;prior=np.asarray(prev['target_xyz']);parent=np.asarray(f['command_xyz']);delta=parent-prior;actual=np.asarray(row['target_xyz'])-prior;assert abs(delta[0]-f['command_delta_x_m'])<1e-10
   local=rot[t].T@(np.asarray(f['cop_world'])-obj[t]);near=np.flatnonzero(core[:2]/2-abs(local[:2])<.010)
   if direction*delta[1]<-1e-10:continue
   # Use millimetres for dx to keep LP and independent vertex tolerance explicit.
   low,high=(np.asarray(f['feasible_x_interval_m'])-prior[0])*1000
   A=[];b=[]
   for axis in near:
    sign=1. if local[axis]>=0 else -1.
    A.append([sign*rot[t,0,axis],sign*rot[t,1,axis]*delta[1]*1000]);b.append(-sign*rot[t,2,axis]*delta[2]*1000)
   A.extend([[-1,0],[1,0],[0,-1],[0,1]]);b.extend([-low,high,0,1]);A=np.asarray(A);b=np.asarray(b)
   lp=linprog([0,-1],A_ub=A,b_ub=b,bounds=[(None,None),(None,None)],method='highs',options={'dual_feasibility_tolerance':1e-9,'primal_feasibility_tolerance':1e-9})
   vertices=[]
   for i,j in itertools.combinations(range(len(b)),2):
    M=A[[i,j]]
    if abs(np.linalg.det(M))<1e-12:continue
    v=np.linalg.solve(M,b[[i,j]])
    if max(A@v-b)<=1e-8:vertices.append(v)
   assert bool(vertices)==bool(lp.success),(t,lp.message)
   record=dict(step=t,near_axes=near.tolist(),parent_delta_mm=(delta*1000).tolist(),actual_delta_mm=(actual*1000).tolist(),local_cop_mm=(local*1000).tolist(),feasible=bool(vertices))
   if vertices:
    alpha=float(np.clip(max(v[1] for v in vertices),0,1));assert abs(alpha-lp.x[1])<1e-7
    xmin,xmax=low,high
    for a,rhs in zip(A,b):
     rhs=rhs-a[1]*alpha
     if abs(a[0])<1e-12:assert rhs>=-1e-8
     elif a[0]>0:xmax=min(xmax,rhs/a[0])
     else:xmin=max(xmin,rhs/a[0])
    assert xmin<=xmax+1e-8
    dx=float(np.clip(delta[0]*1000,xmin,xmax));assert max(A@np.array([dx,alpha])-b)<=1e-8
    candidate=delta.copy();candidate[0]=dx/1000;candidate[1]*=alpha
    assert low-1e-8<=dx<=high+1e-8 and abs(candidate[0])<=.002+1e-10
    record.update(alpha=alpha,candidate_delta_mm=(candidate*1000).tolist(),candidate_command_xyz=(prior+candidate).tolist(),x_change_from_parent_mm=dx-delta[0]*1000,near_slew_bound=abs(dx)>=1.9999,reference_local_delta_mm=((rot[t].T@candidate)*1000).tolist())
   samples.append(record)
  feasible=[r for r in samples if r['feasible']];forward=lambda r,k:max(0,direction*r[k][1]);parenttotal=sum(forward(r,'parent_delta_mm') for r in feasible);actualtotal=sum(forward(r,'actual_delta_mm') for r in feasible);candidate=sum(forward(r,'candidate_delta_mm') for r in feasible)
  summary=dict(audited_overrides=len(samples),feasible=len(feasible),infeasible=len(samples)-len(feasible),full_Y_feasible=sum(r['alpha']>1-1e-8 for r in feasible),x_changed_steps=sum(bool(abs(r['x_change_from_parent_mm'])>1e-5) for r in feasible),x_at_2mm_slew=sum(r['near_slew_bound'] for r in feasible),median_abs_x_change_mm=float(np.median([abs(r['x_change_from_parent_mm']) for r in feasible])),retained_parent_Y_fraction=candidate/parenttotal if parenttotal else None,actual_retained_parent_Y_fraction=actualtotal/parenttotal if parenttotal else None,median_scale=float(np.median([r['alpha'] for r in feasible])))
  reports.append(dict(run=run,episode=ep.name,summary=summary,rows=samples,source_sha256={n:sha(ep/n) for n in [an,'frontal_bypass.json','trace.npz','parcel_orientation.npz']}));print(run,key,summary)
out=dict(episodes=reports,checker_sha256=sha(Path(__file__)),training_ready=False,scope='Frozen observed geometry only, LP independently checked by vertex enumeration. Maximum original Y fraction with X allowed within SAME recorded2mm slew/30mm lead interval, fixed Z, threatened-core-edge reference direction non-outward. Parent history retained; no recursive rollout, measured IK feasibility, physical COP prediction, contact stability or task success claim. No collector/controller changes.')
p=w/'REAR_JOINT_XY_DIRECTION_SCREEN.json';assert not p.exists();p.write_text(json.dumps(out,indent=2))
