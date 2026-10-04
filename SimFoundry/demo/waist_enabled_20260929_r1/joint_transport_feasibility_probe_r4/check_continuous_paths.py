"""Independent static swept-segment certificate for unissued joint11 proposals.
Each midpoint separator is held fixed over its interval. Every vertex displacement
is bounded by the sum of joint travel times conservative downstream radii. This
bounds heights and projected support gaps even when the chosen face rotates.
Covers inactive floor, three hand/parcel gaps, two elbow/torso gaps and joint
bounds. Does not certify dynamics, moving objects, actual contact or task success.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
D=Path(__file__).resolve().parent;W=D.parent;S=W/'staged_inactive_transport_v2';ROOT=W.parents[1]
sys.path[:0]=[str(S),str(W),str(ROOT)]
from audit_front_recontact_center_events import RecoveryEventAudit
A=RecoveryEventAudit(ROOT,S)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources={}
def read(p):
 sources[str(p)]=sha(p);return json.loads(p.read_text())
def radii(chain,vertices):
 radius=np.zeros(11);extent=np.linalg.norm(vertices,axis=1).max()
 for k,(O,axis,index) in enumerate(chain):
  if index is not None:
   assert axis is not None and abs(np.linalg.norm(axis)-1)<1e-9
   radius[index]=extent+sum(np.linalg.norm(O2[:3,3]) for O2,_,_ in chain[k+1:])
 return radius
hand_radii={s:radii(A.hand.chains[s],A.hand.vertices[s]) for s in ['left','right']}
elbow_radii={s:radii([(O,axis,i) for i,O,axis in A.elbows.chains[s]],A.elbows.v[s]) for s in ['left','right']}
labels=['inactive_height','inactive_target','inactive_other','active_other','left_elbow','right_elbow']
def margins(q,scene):
 active=scene['side'];inactive='right' if active=='left' else 'left';I=A.hand.fk(q,inactive);T=A.hand.fk(q,active)
 return np.r_[A.hand.minz(q,inactive)-.84,A.gap(inactive,I,scene['target_xyz'],scene['target_quat'],scene['core_size'])-.01,A.gap(inactive,I,scene['other_xyz'],scene['other_quat'],scene['other_size'])-.01,A.gap(active,T,scene['other_xyz'],scene['other_quat'],scene['other_size'])-.01,A.elbows.gap(q)-.005]
def certify(q,end,scene):
 q=np.asarray(q,float);end=np.asarray(end,float)
 if any(z.shape!=(11,) or not np.isfinite(z).all() for z in [q,end]):raise ValueError('finite11 required')
 lower=A.lo.copy();upper=A.hi.copy();lower[0]=-.98;upper[0]=.98
 if any(np.any(z<lower-2e-7) or np.any(z>upper+2e-7) for z in [q,end]):return dict(passed=False,reason='endpoint_joint_bounds')
 for alpha,z in [(0.,q),(1.,end)]:
  m=margins(z,scene)
  if min(m)<-2e-7:return dict(passed=False,reason='endpoint_geometry',alpha=alpha,margins_m=dict(zip(labels,m.tolist())))
 active=scene['side'];inactive='right' if active=='left' else 'left';d=abs(end-q)
 v=np.array([hand_radii[inactive]@d]*3+[hand_radii[active]@d,elbow_radii['left']@d,elbow_radii['right']@d])
 todo=[(0.,1.,0)];leaves=[];nodes=0;deepest=0
 while todo:
  lo,hi,depth=todo.pop();mid=(lo+hi)/2;m=margins(q+(end-q)*mid,scene);bound=m-v*(hi-lo)/2;nodes+=1;deepest=max(deepest,depth)
  if min(bound)>=-2e-7:
   leaves.append(dict(interval=[lo,hi],lower_bounds_m=bound.tolist()));continue
  if min(m)<-2e-7 or depth>=24 or nodes>=20000:
   return dict(passed=False,reason='violated_or_subdivision_limit',interval=[lo,hi],depth=depth,nodes=nodes,midpoint_margins_m=m.tolist(),lower_bounds_m=bound.tolist())
  todo.extend([(mid,hi,depth+1),(lo,mid,depth+1)])
 return dict(passed=True,nodes=nodes,max_depth=deepest,vertex_travel_bounds_m=dict(zip(labels,v.tolist())),minimum_certified_margin_m=min(min(z['lower_bounds_m']) for z in leaves),leaves=leaves)
def main():
 probe=read(D/'RESULT.json')
 for p,h in probe['source_sha256'].items():assert sha(p)==h,p
 rows=[]
 for r in probe['results']:
  case=r['episode'].split('_')[1];ep=W/'inactive_transport_physical_r1'/('case_'+case)/r['episode'];record=read(ep/'inactive_transport_clearance.json')['rows'][r['step']]['proposal'];q=np.array(record['current']);qp=np.array(record['previous_q']);prev=np.array(record['previous_command']);a=np.array(record['decay']);u=np.array(r['command']);pred=(1-a)*u+a*q+q-prev-a*(qp-prev)
  np.testing.assert_array_equal(q,r['current']);np.testing.assert_allclose(pred,r['predicted_q'],rtol=0,atol=1e-14);assert record['scene']==r['scene']
  paths={name:certify(q,end,record['scene']) for name,end in [('nominal',u),('predicted',pred)]}
  row=dict(step=r['step'],side=r['side'],episode=r['episode'],passed=all(v['passed'] for v in paths.values()),paths=paths);rows.append(row)
  print(json.dumps(dict(step=r['step'],side=r['side'],passed=row['passed'],paths={k:{kk:vv for kk,vv in v.items() if kk!='leaves'} for k,v in paths.items()})),flush=True)
 negatives=[]
 for side,case,name,t in [('left',840023,'nudge_mailer_to_bin',374),('right',840020,'push_box_to_bin',816)]:
  ep=W/'inactive_transport_physical_r1'/f'case_{case}'/f'layout_{case}_{name}'
  with np.load(ep/'raw.npz') as z:q=z['q'][t,12:23].astype(float)
  sources[str(ep/'raw.npz')]=sha(ep/'raw.npz');scene=next(r['scene'] for r in probe['results'] if r['side']==side)
  # Only an isolated frozen-scene geometry negative control, not a rollout.
  v=certify(q,q,scene);assert not v['passed'];negatives.append(dict(side=side,actual_state_step=t,result=v))
 for p in [Path(__file__),S/'audit_front_recontact_center_events.py',S/'audit_unloaded_wrist_prior_live.py',S/'audit_unloaded_wrist_task_optimality.py',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json',S/'elbow_torso_hulls.json']:sources[str(p)]=sha(p)
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=all(r['passed'] for r in rows),results=rows,negative_controls=negatives,source_sha256=sources,physical_command_issued=False,training_ready=False)
 with (D/'CONTINUOUS_STATIC_PATHS.json').open('x') as f:json.dump(out,f,indent=2)
if __name__=='__main__':main()
