"""One-step frozen-geometry screen, not predicted COP or physical success.

Given the recorded rear-X command and unchanged Z, ask if scaling only the
recorded forward-Y increment can avoid an outward local-XY reference direction
at currently near-edge COP. Includes every audited override from closed runs.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import linprog
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[]
for run in ['rear_core_slice_groups_r1','rear_core_slice_motion_groups_r1','front_drive_increment_groups_r1']:
 root=w/run;closed=json.loads((root/'RESULT.json').read_text());assert closed['actual_review_complete']
 for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
  ep=root/f'case_{cid}/layout_{cid}_{task}';auditname='REAR_CORE_SLICE_MOTION_LIVE_AUDIT.json' if 'motion_groups' in run else 'REAR_COP_CORE_SLICE_LIVE_AUDIT.json';audit=json.loads((ep/auditname).read_text());assert audit['passed'] and not audit['errors']
  for name,h in audit['source_sha256'].items():assert sha(ep/name)==h
  fr=json.loads((ep/'frontal_bypass.json').read_text());core=np.array(fr['plan']['rear_cop_centering']['actual_core_size_xyz']);key='box' if 'push_box' in task else 'mailer';direction=-1 if key=='box' else 1
  with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
  with np.load(ep/'trace.npz') as z:obj=z[key].astype(float)
  samples=[]
  for prev,row in zip(fr['rows'],fr['rows'][1:]):
   f=row.get('rear_cop_centering',{})
   if not f.get('override'):continue
   t=row['step'];assert t==prev['step']+1
   cop=rot[t].T@(np.array(f['cop_world'])-obj[t]);margin=core[:2]/2-abs(cop[:2]);near=np.flatnonzero(margin<.010)
   delta=np.array(row['target_xyz'])-np.array(prev['target_xyz']);assert abs(delta[0]-f['command_delta_x_m'])<1e-9
   s=dict(step=t,local_cop_mm=(cop*1000).tolist(),local_xy_margin_mm=(margin*1000).tolist(),parent_delta_mm=(delta*1000).tolist(),near_axes=near.tolist(),normal_mode_unchanged=True)
   if direction*delta[1]<-1e-10:
    s.update(status='parent_nonforward_preserved',scale=1.);samples.append(s);continue
   lo,hi=0.,1.;constraints=[]
   for i in near:
    sign=1. if cop[i]>=0 else -1.
    # sign * local reference movement <=0 at threatened boundary.
    a=sign*(rot[t,0,i]*delta[0]+rot[t,2,i]*delta[2]);b=sign*rot[t,1,i]*delta[1];constraints.append((float(a),float(b)))
    if abs(b)<1e-14:
     if a>1e-12:lo,hi=1.,0.
    elif b>0:hi=min(hi,-a/b)
    else:lo=max(lo,-a/b)
   lp=linprog([-1.],A_ub=[[b] for a,b in constraints] if constraints else None,b_ub=[-a for a,b in constraints] if constraints else None,bounds=[(0,1)],method='highs')
   feasible=lo<=hi+1e-10 and hi>=-1e-10 and lo<=1+1e-10
   # HiGHS default feasibility tolerance is looser; reject its borderline
   # solutions using the original metre-domain inequalities as well.
   lpfeasible=lp.success and all(a+b*lp.x[0]<=1e-10 for a,b in constraints)
   assert feasible==lpfeasible,(t,lo,hi,lp)
   if not feasible:s.update(status='no_Y_only_direction',scale=None)
   else:
    scale=float(np.clip(hi,0,1));new=delta.copy();new[1]*=scale
    assert all(a+b*scale<=1e-10 for a,b in constraints)
    assert abs(new[1])<=abs(delta[1])+1e-12 and direction*new[1]>=-1e-10
    assert abs(scale-lp.x[0])<1e-7
    s.update(status='reduced' if scale<1-1e-8 else 'unchanged',scale=scale,candidate_delta_mm=(new*1000).tolist(),projected_local_xy_delta_mm=((rot[t].T@new)[:2]*1000).tolist())
   s['constraints']=constraints;samples.append(s)
  feasible=[s for s in samples if s['scale'] is not None and s['status']!='parent_nonforward_preserved'];forward=sum(max(0,direction*s['parent_delta_mm'][1]) for s in feasible);remaining=sum(max(0,direction*s['candidate_delta_mm'][1]) for s in feasible)
  summary=dict(overrides=len(samples),near_edge_steps=sum(bool(s['near_axes']) for s in samples),unchanged=sum(s['status']=='unchanged' for s in samples),reduced=sum(s['status']=='reduced' for s in samples),no_Y_only_direction=sum(s['status']=='no_Y_only_direction' for s in samples),parent_nonforward=sum(s['status']=='parent_nonforward_preserved' for s in samples),feasible_zero_or_nearly_zero_Y=sum(s['scale'] is not None and s['scale']<.01 for s in samples),feasible_recorded_forward_command_mm=forward,feasible_scaled_forward_command_mm=remaining,retained_recorded_forward_fraction=remaining/forward if forward else None)
  reports.append(dict(run=run,episode=ep.name,summary=summary,samples=samples,source_sha256={n:sha(ep/n) for n in [auditname,'frontal_bypass.json','trace.npz','parcel_orientation.npz']},result_sha256=sha(root/'RESULT.json')));print(run,key,summary,flush=True)
p=w/'REAR_COUPLED_PROGRESS_SCREEN.json';assert not p.exists();p.write_text(json.dumps(dict(episodes=reports,checker_sha256=sha(Path(__file__)),training_ready=False,scope='Frozen observed geometry only. Per-step analytic feasible interval checked against independent LP. Candidate scales existing forward-Y command0..1, preserves actual recorded X/Z, guards and nonforward commands. Near-axis test uses original10mm inset. This is a reference direction screen, NOT prediction of COP motion, physical feasibility, continuous contact, task success or runtime gain. Infeasible or nearzeroY cases cannot be hidden by claiming contact solved; no collector change or physical candidate.'),indent=2))
