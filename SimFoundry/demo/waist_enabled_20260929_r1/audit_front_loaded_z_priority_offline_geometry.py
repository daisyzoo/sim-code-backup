"""Independent offline candidate replay, exact support motion and nominal sweep.
Reads full-observation candidates, never imports/calls their solver. Rebuilds
primal/KKT conditions from archived q/actions/task rows, and exact hand FK.
Hand/non-target straight-joint paths use adaptive interval separation bounds:
midpoint separation minus sum(descendant-radius*abs(delta-q))*half-interval.
Non-target is held at the observed pose; this certifies only that nominal path,
not actual dynamics, servo overshoot, full-arm clearance or object stability.
"""
from pathlib import Path
import json,datetime,hashlib,sys,itertools
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from screen_bag_vertical_priority_geometry import Geometry
from audit_unloaded_wrist_prior_live import HandModel
from audit_self_clearance_task_optimality import IndependentElbows
from support_vertex_stationarity import certificate
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
P=W/'FRONT_LOADED_Z_PRIORITY_CLEARANCE_FULL_OBSERVATIONS_PROBE.json';report=json.loads(P.read_text());sources={str(P):sha(P)}
for p,h in report['source_sha256'].items():assert sha(p)==h,p

def evaluate(a,c,x,parent,hand,elbows,g,side):
 x=np.asarray(x,float)
 if x.shape!=(11,) or not np.isfinite(x).all():return dict(passed=False,reason='nonfinite_or_wrong_shape')
 q=np.asarray(a['current']);J=np.asarray(a['jacobian']);e=np.asarray(a['error']);prior=np.asarray(a['preferred_step']);D=np.asarray(a['damping'])**2;zr=5 if side=='right' else 2;d=x-q;dp=parent-q;target=np.array(c['contact_normal_tracking']['target_local_up']);target/=np.linalg.norm(target)
 A=J[6:];v=e[6:];r=A@d-v;pn=float(np.linalg.norm(A@dp-v));rn=float(np.linalg.norm(r));ze=float(J[zr]@d-e[zr]);h=2e-7
 def exact(z):return float(np.linalg.norm(hand.fk(z,side)[:3,:3][2]-target))
 pe=exact(parent);ce=exact(x);gx=np.array([-(exact(x+np.eye(11)[j]*h)-exact(x-np.eye(11)[j]*h))/(2*h) for j in range(11)])
 vals=np.array([ze,-ze,pn-rn,pe-ce]);jac=np.vstack([J[zr],-J[zr],-r@A/max(rn,1e-15),gx]);lo=np.maximum.reduce([a['lower'],q-a['step_limits'],np.asarray(a['previous'])-.055]);hi=np.minimum.reduce([a['upper'],q+a['step_limits'],np.asarray(a['previous'])+.055]);grad=J.T@(J@d-e)+D*(d-prior)
 cert=certificate(geometry=elbows,x=x,gradient=grad,lower=lo,upper=hi,extra_values=vals,extra_jacobian=jac);table=g.table_margins(g.fk(x))
 return dict(passed=bool(cert['passed'] and min(table)>=0 and abs(ze)<=2e-7 and ce<=pe+1e-6 and rn<=pn+2e-7),certificate=cert,nominal_table_margins_m=table,z_error_mm=ze*1000,exact_attitude_delta=ce-pe,linear_attitude_delta_mm=(rn-pn)*1000)

def point(model,q,side,normal,center):
 M=model.fk(q,side);local=M[:3,:3].T@normal;vertices=model.vertices[side];offset=center+local*(np.min(vertices@local)-center@local);return M[:3,3]+M[:3,:3]@offset

def radii(hand,side):
 chain=hand.chains[side];out=np.zeros(11);extent=float(np.linalg.norm(hand.vertices[side],axis=1).max())
 for k,(_,axis,i) in enumerate(chain):
  if i is not None:assert abs(np.linalg.norm(axis)-1)<1e-9;out[i]=extent+sum(np.linalg.norm(O[:3,3]) for O,_,_ in chain[k+1:])
 return out

def sweep(g,hand,q,x,side,xyz,rotation,size):
 travel=float(radii(hand,side)@abs(x-q));intervals=[(0.,1.,0)];leaves=[];samples=[]
 while intervals:
  a,b,depth=intervals.pop();m=(a+b)/2;pose=g.fk(q+(x-q)*m);gap=g.hand_box_gap(pose,side,xyz,rotation,size);lower=gap-travel*(b-a)/2;samples.append(dict(fraction=m,gap_m=gap,interval=[a,b],lower_bound_m=lower))
  if lower>0:leaves.append(lower);continue
  if gap<=0 or depth>=12:return dict(certified=False,reason='sample_has_no_separation_witness' if gap<=0 else 'subdivision_limit',travel_bound_m=travel,samples=samples)
  intervals.extend([(a,m,depth+1),(m,b,depth+1)])
 return dict(certified=True,minimum_certified_gap_lower_bound_m=min(leaves),travel_bound_m=travel,samples=samples)

episodes=[];negative=[];C=W/'front_initial_physical_r1'
for original in report['episodes']:
 ep=next(C.glob('case_*/'+original['episode']));selected=json.loads((ep/'front_initial_center.json').read_text());assert selected['selected']==original['selected']
 if not original['selected']:episodes.append(dict(episode=ep.name,selected=False,applied=False));continue
 coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};fr=json.loads((ep/'frontal_bypass.json').read_text());frs={r['step']:r for r in fr['rows']};g=Geometry(ep.parent);sources.update(g.sources)
 def archived(name):
  ps=[Path(p) for p in g.sources if p.endswith('/'+name)];assert len(ps)==1;return ps[0]
 hand=HandModel(archived('g1_23dof_rev_1_0_u1_black.urdf'),archived('g1_hand_support_vertices.json'));elbows=IndependentElbows(archived('elbow_torso_hulls.json'),archived('g1_23dof_rev_1_0_u1_black.urdf'));side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';rows=[]
 scene=next(r['context']['scene'] for r in selected['rows'] if r.get('context',{}).get('scene'));other_size=np.array(scene['other_size'])
 # Conservative planner envelope, not a claim that it is the physical mesh/core.
 with np.load(ep/'raw.npz') as z:states=z['q'][:,12:23].astype(float);actions=z['action'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:otherxyz=z[other].copy()
 with np.load(ep/'parcel_orientation.npz') as z:otherrot=Rotation.from_quat(z[other]).as_matrix();normal=Rotation.from_quat(z[key]).as_matrix()[:,:,2]
 for count,r in enumerate(original['rows']):
  t=r['step'];c=coords[t];a=c['task_inputs'];q=np.asarray(a['current']);parent=np.asarray(r['parent_command']);x=np.asarray(r['candidate_command']);np.testing.assert_allclose(q,states[t],atol=1e-7,rtol=0);np.testing.assert_allclose(a['previous'],actions[t-1],atol=1e-7,rtol=0);np.testing.assert_allclose(parent,actions[t],atol=1e-7,rtol=0)
  ev=evaluate(a,c,x,parent,hand,elbows,g,side);assert ev['passed']==r['independent_nominal_primal_and_kkt_passed'];center=np.asarray(c['active_support_reference']['center_local']);observed=point(hand,q,side,normal[t],center);np.testing.assert_allclose(observed,frs[t]['observed_support_xyz'],atol=2e-6,rtol=0)
  dp=point(hand,parent,side,normal[t],center)-observed;dx=point(hand,x,side,normal[t],center)-observed;target=np.asarray(frs[t]['target_xyz']);npath={s:sweep(g,hand,q,x,s,otherxyz[t],otherrot[t],other_size) for s in ['left','right']}
  rows.append(dict(step=t,independent_nominal_passed=ev['passed'],stationarity_residual=ev['certificate']['stationarity_residual'],nominal_parent_support_delta_mm=(dp*1000).tolist(),nominal_candidate_support_delta_mm=(dx*1000).tolist(),original_requested_z_mm=float(np.asarray(a['error'])[5 if side=='right' else 2]*1000),nominal_candidate_downward=bool(dx[2]<0),nominal_more_downward_than_parent=bool(dx[2]<dp[2]),nominal_straight_path_hands_non_target=npath))
  if count in [0,len(original['rows'])//2,len(original['rows'])-1]:
   zrow=np.asarray(a['jacobian'])[5 if side=='right' else 2];badz=x+zrow/(zrow@zrow)*.00025
   cases={'wrong_shape':x[:10], 'nan':np.r_[np.nan,x[1:]],'violated_downward_equality':badz,'joint_outside_bound':np.r_[a['upper'][0]+.1,x[1:]]}
   for name,bad in cases.items():
    result=evaluate(a,c,bad,parent,hand,elbows,g,side);assert not result['passed'],(ep.name,t,name)
    negative.append(dict(episode=ep.name,step=t,mutation=name,rejected=True,reason=result.get('reason') or result['certificate']['reason']))
  if count%100==0:print(ep.name,count,len(original['rows']),flush=True)
 episodes.append(dict(episode=ep.name,selected=True,records=len(rows),all_independent_nominal_passed=all(r['independent_nominal_passed'] for r in rows),nominal_candidate_downward=sum(r['nominal_candidate_downward'] for r in rows),nominal_more_downward_than_parent=sum(r['nominal_more_downward_than_parent'] for r in rows),nominal_hand_non_target_straight_path_certified=sum(all(v['certified'] for v in r['nominal_straight_path_hands_non_target'].values()) for r in rows),obstacle_envelope_size_xyz_m=other_size.tolist(),rows=rows))
 for n in ['raw.npz','coordination.json','frontal_bypass.json','front_initial_center.json','trace.npz','parcel_orientation.npz']:sources[str(ep/n)]=sha(ep/n)
for n in ['audit_front_loaded_z_priority_offline_geometry.py','screen_bag_vertical_priority_geometry.py','audit_unloaded_wrist_prior_live.py','audit_self_clearance_task_optimality.py','support_vertex_stationarity.py']:sources[str(W/n)]=sha(W/n)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=episodes,negative_cases=negative,source_sha256=sources,physical_dynamics_verified=False,non_target_actual_stability_proven=False,training_ready=False)
p=W/'FRONT_LOADED_Z_PRIORITY_FULL_OFFLINE_GEOMETRY_AUDIT.json'
with p.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps([dict((k,v) for k,v in e.items() if k!='rows') for e in episodes],indent=2));print('negatives',len(negative))
