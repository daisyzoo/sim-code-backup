"""Frozen current-history residual surrogate; never claims physical rollout."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_tracking_region_approach';sys.path[:0]=[str(stage),str(w/'staged_contact_patch_approach'),str(repo)]
from tracking_region_approach_refined import tracking_region_step
from contact_patch_approach import contact_patch_step
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');lo=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98;limits=np.r_[.015,np.full(10,.04)];damping=np.r_[.12,np.full(10,.045)];reports=[]
paths=[w/'fresh_lateral_00_trial_v2_r1/case_840001/layout_840001_push_box_to_bin',w/'fresh_diagonal_02_trial_v2_r1/case_840004/layout_840004_nudge_mailer_to_bin',w/'region_patch_groups_r1/case_840001/layout_840001_push_box_to_bin',w/'region_patch_groups_r1/case_840004/layout_840004_nudge_mailer_to_bin']
for ep in paths:
 with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float);us=z['action'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
 rows=json.loads((ep/'frontal_bypass.json').read_text())['rows'];coords={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);osize=(.15,.145,.04) if key=='box' else (.14,.09,.045);eligible=[]
 for x in rows:
  t=x['step']
  if t<4 or x['mode'] not in ['top_cross','top_descend'] or coords[t]['contact_normal_tracking'] is not None or x.get('contact_load',{}).get('observed_vertical_load_n',0.)>=.2:continue
  g=model.scene_geometry(side,qs[t],target_xyz=tr[key][t],target_quat=ori[key][t],other_xyz=tr[other][t],other_quat=ori[other][t],other_size=osize);pts=(g['vertices']@g['hand_rotation'].T+g['hand_xyz']-g['target_xyz'])@g['target_rotation'];p=pts[int(pts[:,2].argmin())]
  if not np.all(abs(p[:2])<=size[:2]/2-.01) or p[2]<size[2]/2+.004:continue
  residuals=qs[t-2:t+1]-us[t-3:t];stable=bool(np.max(abs(np.diff(qs[t-3:t+1],axis=0)))<.004 and np.max(abs(np.diff(residuals,axis=0)))<.002)
  eligible.append((t,stable))
 starts=[('first_eligible',eligible[0][0])] if eligible else []
 stable=next((t for t,b in eligible if b),None)
 if stable is not None:starts.append(('first_causally_stable',stable))
 for label,t in starts:
  q=qs[t].copy();residual=q-us[t-1];anchor=np.asarray(coords[t]['inactive_anchor']);history=[]
  def geometry(q):return model.scene_geometry(side,q,target_xyz=tr[key][t],target_quat=ori[key][t],other_xyz=tr[other][t],other_quat=ori[other][t],other_size=osize)
  kw=dict(lower=lo,upper=hi,step_limits=limits,damping=damping,target_size=size,inactive_anchor=anchor)
  default=contact_patch_step(q,geometry,**kw);zero=tracking_region_step(q,geometry,tracking_residual=np.zeros(11),**kw);assert zero['accepted'];zero_difference=float(np.max(abs(np.asarray(default['next_q'])-zero['next_q'])))
  for step in range(600):
   try:s=tracking_region_step(q,geometry,tracking_residual=residual,**kw)
   except ValueError as exc:s=dict(accepted=False,reached=False,reason=str(exc),next_q=q.tolist())
   history.append(dict(step=step,measured_q=q.tolist(),**s))
   if s['reached'] or not s['accepted'] or s['reason']=='stagnation':break
   q=np.asarray(s['next_q'])+residual
  result=dict(episode=str(ep),start_kind=label,actual_start_frame=t,constant_tracking_residual_rad=residual.tolist(),steps=len(history),reached=history[-1]['reached'],stop=history[-1]['reason'],zero_residual_first_step_delta_rad=zero_difference,history=history);reports.append(result);print(json.dumps({k:v for k,v in result.items() if k not in ['history','constant_tracking_residual_rad']}),flush=True)
 if stable is None:print('No stable eligible frame under this recorded controller:',ep,flush=True)
report=dict(rows=reports,scope='Original exact measured starts; stable predicate uses only last3 observed q velocities<.004rad/frame and residual differences<.002rad. Pure bounded solver requires nominal and measured-residual predicted geometry. Simulated response command+constant first residual and frozen objects is an explicit UNVERIFIED surrogate, not Isaac, successful contact, collision certificate or training data.',training_ready=False,candidate_sha256=hashlib.sha256((stage/'tracking_region_approach_refined.py').read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(stage/'CONSTANT_RESIDUAL_REFINED_SCREEN.json').write_text(json.dumps(report,indent=2))
