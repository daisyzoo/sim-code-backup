"""Compare a soft XY centering objective with frozen region-continuity baseline; offline only."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];out=w/'staged_region_center_then_descend';sys.path[:0]=[str(w/'staged_contact_patch_approach'),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');lo=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98
cases=[x for x in json.loads((w/'staged_tracking_region_approach/CONSTANT_RESIDUAL_REFINED_SCREEN.json').read_text())['rows'] if x['start_kind']=='first_eligible']
cases.append(dict(episode=str(w/'tracking_region_groups_r1/case_840001/layout_840001_push_box_to_bin'),actual_start_frame=119))
cases.append(dict(episode=str(w/'region_continuity_groups_r1/case_840001/layout_840001_push_box_to_bin'),actual_start_frame=119))
reports=[];hashes={}
for variant,path in [('continuity_baseline',w/'staged_region_handover_continuity/contact_patch_approach.py'),('center_then_descend',out/'contact_patch_approach.py')]:
 spec=importlib.util.spec_from_file_location(variant,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);hashes[variant]=hashlib.sha256(path.read_bytes()).hexdigest()
 for case in cases:
  ep=Path(case['episode']).resolve();t=case['actual_start_frame'];side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box';size=np.array([.14,.09,.045] if side=='right' else [.15,.145,.04]);osize=(.15,.145,.04) if side=='right' else (.14,.09,.045)
  with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float);us=z['action'][:,12:23].astype(float)
  with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
  with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
  co={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};anchor=np.asarray(co[t]['inactive_anchor']);fr=json.loads((ep/'frontal_bypass.json').read_text())['rows'];stop=max(t+1,next((x['step'] for x in fr if x.get('region_guard_reason')),min(t+60,len(qs)-1)))
  def geometry(q):return model.scene_geometry(side,q,target_xyz=tr[key][t],target_quat=ori[key][t],other_xyz=tr[other][t],other_quat=ori[other][t],other_size=osize)
  q=qs[t].copy();previous=us[t-1].copy();history=[]
  hold_height=None
  for step in range(600):
   kwargs={}
   if variant=='center_then_descend' and step<60:
    if hold_height is None:
     g=geometry(q);points=((g['vertices']@g['hand_rotation'].T+g['hand_xyz'])-g['target_xyz'])@g['target_rotation'];hold_height=max(.005,float(points[:,2].min()-size[2]/2))
    kwargs['hold_height_m']=hold_height
   try:s=mod.contact_patch_step(q,geometry,tracking_residual=q-previous,lower=lo,upper=hi,step_limits=np.r_[.015,np.full(10,.04)],damping=np.r_[.12,np.full(10,.045)],target_size=size,inactive_anchor=anchor,**kwargs)
   except ValueError as exc:s=dict(accepted=False,reached=False,reason=str(exc),next_q=q.tolist())
   h=dict(step=step,measured_q=q.tolist(),solver=s);history.append(h)
   if s['reached'] or not s['accepted'] or s['reason']=='stagnation':break
   event=min(t+step+1,stop);external=qs[event]-us[event-1];command=np.asarray(s['next_q']);q=command+external;previous=command;h.update(disturbance_source_frame=event,exogenous_residual_rad=external.tolist())
  r=dict(variant=variant,episode=str(ep),actual_start_frame=t,disturbance_end_frame=stop,steps=len(history),reached=history[-1]['solver']['reached'],stop=history[-1]['solver']['reason'],history=history,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),final_local_xy_m=history[-1]['solver'].get('physical_point_local_xyz',[])[:2],final_gap_m=history[-1]['solver'].get('top_gap_m'));reports.append(r);print(json.dumps({k:v for k,v in r.items() if k not in {'history','raw_sha256'}}),flush=True)
 report=dict(rows=reports,helper_sha256=hashes,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Frozen objects at first eligible actual pose; recorded exogenous q[t+1]-u[t] disturbance to guard then held. Solver only sees current q and previous own command. No real physical response model, handover/load or collision certificate. Original gate and full raw data unchanged.',training_ready=False)
 (out/'CENTER_THEN_DESCEND_SCREEN.json').write_text(json.dumps(report,indent=2))
