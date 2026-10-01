"""Measured initial-top tilt-recovery states, fixed parcels, instantaneous IK only."""
from pathlib import Path
import sys,ast,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent;repo=root.parents[1];sys.path.insert(0,str(repo))
source=(root/'audit_terminal_reach.py').read_text();exec(compile(source.split("p=root/'contact_x_ablation")[0],'<cached_fk>','exec'))
tree=ast.parse((root/'audit_front_short_recovery_kinematics.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fk'],type_ignores=[]),'<analytic_fk>','exec'))
from simfoundry.data.projected_support_reference import projected_support_reference,projected_support_jacobian,skew
from simfoundry.data.initial_top_route import InitialTopRouteState
from simfoundry.data.frontal_bypass import FrontalBypassState
from simfoundry.data.bounded_ik import bounded_damped_step
from simfoundry.data.hand_obstacle_clearance import hand_face_separation
from simfoundry.data.contact_normal_constraint import contact_normal_constraint
for node in ast.parse((repo/'simfoundry/robots/g1_assets.py').read_text()).body:
 if isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in ['U1_JOINT_LIMIT_LO','U1_JOINT_LIMIT_HI']:globals()[node.target.id]=np.array(ast.literal_eval(node.value))[12:]
lo=U1_JOINT_LIMIT_LO.copy();hi=U1_JOINT_LIMIT_HI.copy();lo[0]=-.98;hi[0]=.98
limits=np.full(11,.04);limits[0]=.015;damping=np.full(11,.045);damping[0]=.12
p=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with np.load(p/'raw.npz') as z:qs=z['q']
with np.load(p/'trace.npz') as z:tr={k:z[k] for k in z.files}
with np.load(p/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
log=json.loads((p/'frontal_bypass.json').read_text());coords={x['step']:x for x in json.loads((p/'coordination.json').read_text())}
assert 'push_box' in p.name
side='right';inactive='left';size=np.array([.14,.09,.045]);other_size=(.15,.145,.04)
vertices=np.array(json.loads((repo/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'][side]);events=[];count=0
for r in log['rows']:
 if r['recontacts']>count:events.append(r)
 count=r['recontacts']
results=[]
for event in events:
 t=event['step'];q0=qs[t,12:23].astype(float);target=tr['box'][t].copy();obstacle=tr['mailer'][t].copy();quat=ori['box'][t];other_quat=ori['mailer'][t];normal=Rotation.from_quat(quat).as_matrix()[:,2];coord=coords[t];anchor=np.array(coord['inactive_anchor']);normal_anchor=coord['contact_normal_tracking']['target_local_up']
 fkerrors={}
 for side_ in ['left','right']:
  m,_,_=fk(side_,q0);fkerrors[side_]=float(np.linalg.norm(m[:3,3]+m[:3,:3]@np.array([.20,0,.007])-tr['palm_'+side_][t]))
 assert max(fkerrors.values())<.0001,fkerrors
 for height in [.91,.86]:
  q=q0.copy();s=InitialTopRouteState(FrontalBypassState(log['plan']),side,tuple(size),obstacle_size=other_size,guarded_descent=True,continuous_drag=True,alignment_tolerance_m=.010,front_inset_fraction=log['plan']['top_recontact']['effective_top_fraction'],recontact_travel_z=height,tilt_recontact_rad=.03,confirm_terminal_release=True)
  s.proposal=log['plan']['initial_top_proposal'];s.top_mode='top_lift';s.recontacts=event['recontacts'];s.start=tuple(event['observed_support_xyz']);s.load.desired_n=5.;history=[]
  for k in range(240):
   m,jl,jw=fk(side,q);r=m[:3,:3];ref=projected_support_reference(vertices,r,normal);offset=ref['reference_local'];point=m[:3,3]+r@offset;ja=projected_support_jacobian(jl,jw,r,ref)
   mi,jli,jwi=fk(inactive,q);po=np.array([.20,0,.007]);pi=mi[:3,3]+mi[:3,:3]@po;ji=jli-skew(mi[:3,:3]@po)@jwi
   gap=hand_face_separation(side).gap(m[:3,3],Rotation.from_matrix(r).as_quat(),obstacle,other_quat,(.15*.90,.145*.88,.04))
   row=s.update(point,target,obstacle,.07,.075,tip=point,quat=quat,obstacle_quat=other_quat,control_offset_local=offset,load_n=0.,hand_obstacle_gap_m=gap)
   history.append(dict(step=k,mode=row['mode'],hand_other_gap_m=gap,hand_min_z_m=float((vertices@r.T+m[:3,3])[:,2].min()),q=q.tolist(),waypoint=row['target_xyz']))
   if row['mode'] in ['top_press','initial_top_guard_lift']:break
   nc=contact_normal_constraint(r,jw,normal_anchor);jac=np.vstack([ja,ji,nc['jacobian']]);err=np.r_[np.clip(.72*(np.array(row['target_xyz'])-point),-.035,.035),np.clip(.72*(anchor-pi),-.035,.035),nc['error']]
   q+=bounded_damped_step(jac,err,q,lo,hi,limits,damping)
  res=dict(frame=t,height_m=height,kinematic_steps=len(history),reached_press=history[-1]['mode']=='top_press',min_hand_other_gap_m=min(x['hand_other_gap_m'] for x in history),min_hand_z_m=min(x['hand_min_z_m'] for x in history),recorded_fk_errors_m=fkerrors,history=history)
  results.append(res);print(json.dumps({k:v for k,v in res.items() if k!='history'}),flush=True)
result=dict(rows=results,raw_sha256=sha(p/'raw.npz'),script_sha256=sha(Path(__file__)),initial_top_source_sha256=sha(repo/'simfoundry/data/initial_top_route.py'),scope='Actual9 tilt recontact states; original target top fraction, inactive anchor, captured contact-normal anchor, projected support Jacobian, bounded working joints; frozen tilted parcels and instantaneous joint tracking. Sampled whole-hand-other gap and hand world Z only. No physical settling/load, full-arm/table/continuous collision, camera or task success proof. Recovery height comparison only; initial approach untouched; does not authorize execution of solved q.',training_ready=False)
(p/'INITIAL_TOP_RECOVERY_SCREEN.json').write_text(json.dumps(result,indent=2))
