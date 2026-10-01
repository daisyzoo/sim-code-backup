"""Unexecuted recovery of nominal edge commands on recorded loaded states.
Compare existing refinement explicitly enabled with a multistart analytic solve
of its same task cost and edge/forward constraints plus original elbow margin.
Actual prior mode and same recontact count preserve genuine first-push steps.
No simulation state is changed; independent FK verifies final float32 commands.
Nominal success is neither contact stability nor permission to execute.
"""
from pathlib import Path
import sys,json,hashlib,datetime,collections
import numpy as np
from scipy.optimize import minimize,Bounds
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_recontact_pose';sys.path[:0]=[str(w),str(stage),str(repo)]
from clearance_runtime import ClearanceGuard
from articulated_hand_geometry import skew
from joint_edge_command import refine_rear_command
from audit_unloaded_wrist_prior_live import HandModel
from audit_unloaded_wrist_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';verts=repo/'assets/robots/g1_hand_support_vertices.json';hand=HandModel(urdf,verts);elbows=IndependentElbows(stage/'elbow_torso_hulls.json',urdf)
source=w/'LOADED_RELATIVE_CONTACT_MOTION.json';diag=json.loads(source.read_text());reports=[]
for item in diag['rows']:
 if item['run']!='recontact_pose_groups_r1':continue
 cid=840001 if 'push_box' in item['episode'] else 840004;side='right' if cid==840001 else 'left';direction=-1 if side=='right' else 1;active=[3,4,5] if side=='right' else [0,1,2]
 ep=w/item['run']/f'case_{cid}'/item['episode'];fr=json.loads((ep/'frontal_bypass.json').read_text());fs={r['step']:r for r in fr['rows']};cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};core=np.array(fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'])
 from scipy.spatial.transform import Rotation
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['box' if side=='right' else 'mailer']).as_matrix()
 with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float);us=z['action'][:,12:23].astype(float)
 chosen=[r for r in item['records'] if r['near_x_edge'] and r['inward_x_nominal_mm']<-.0001]
 records=[]
 for row in chosen:
  t=row['step'];f=fs[t];c=cs[t];inp=c['task_inputs'];q=qs[t];parent=us[t];prev=us[t-1];offset=np.array(f['control_offset_local']);R=rot[t];cop=np.array(row['cop_local_mm'])/1000
  assert fs[t-1]['mode']=='top_push' and fs[t-1]['recontacts']==f['recontacts'] and row['load_n']>=.3
  J=np.array(inp['jacobian']);error=np.array(inp['error']);damping=np.array(inp['damping']);lo=np.array(inp['lower']);hi=np.array(inp['upper']);limits=np.array(inp['step_limits']);assert J.shape==(9,11)
  def point(x):T,_,_=guard.model.fk(side,x);return T[:3,3]+T[:3,:3]@offset
  def jac(x):T,jl,jw=guard.model.fk(side,x);return jl-skew(T[:3,:3]@offset)@jw
  def independent_point(x):T=hand.fk(x,side);return T[:3,3]+T[:3,:3]@offset
  assert np.max(abs(point(q)-independent_point(q)))<1e-8
  baseline=refine_rear_command(enabled=True,mode='top_push',selected=True,current=q,previous=prev,parent_command=parent,jacobian=J,error=error,damping=damping,lower=lo,upper=hi,step_limits=limits,object_rotation=R,cop_local=cop,core_size=core,direction=direction,active_rows=active,point_fn=point,analytic_retry=True,point_jacobian_fn=jac)
  axes=[k for k in [0,1] if core[k]/2-abs(cop[k])<=.01];N=np.array([-np.sign(cop[k])*R[:,k] for k in axes]);A=np.vstack([N,[0,direction,0]]);origin=point(q);low=np.maximum.reduce([lo,q-limits,prev-.055]);high=np.minimum.reduce([hi,q+limits,prev+.055]);D=damping*damping
  def fun(x):d=x-q;res=J@d-error;return 5000*float(res@res+np.sum(D*d*d)),10000*(J.T@res+D*d)
  def constraints(x):return np.r_[A@(point(x)-origin),guard.geometry.constraints(x)-.005]
  def cj(x):return np.vstack([A@jac(x),guard.geometry.jacobian(x)])
  def verify(x):
   x=np.asarray(x,dtype=np.float32).astype(float);edge=A@(independent_point(x)-independent_point(q));gaps=elbows.gap(x);ok=bool(np.min(edge)>=-1e-7 and np.min(gaps)>=.005-2e-7 and np.min(x-low)>=-2e-7 and np.min(high-x)>=-2e-7)
   return {'accepted':ok,'command':x.tolist(),'independent_direction_m':edge.tolist(),'independent_elbow_gaps_m':gaps.tolist(),'cost':fun(x)[0]}
  if baseline.get('override'):baseline['independent_final_check']=verify(baseline['command'])
  attempts=[]
  for label,seed in [('current',q),('parent',parent),('previous',prev)]:
   fit=minimize(fun,np.clip(seed,low,high),jac=True,bounds=Bounds(low,high),constraints=[{'type':'ineq','fun':constraints,'jac':cj}],method='SLSQP',options={'maxiter':300,'ftol':1e-11})
   check=verify(fit.x);check.update(seed=label,solver_success=bool(fit.success),status=int(fit.status),iterations=int(fit.nit));check['accepted']=bool(check['accepted'] and fit.success);attempts.append(check)
  best=min(attempts,key=lambda r:(not r['accepted'],r['cost']));records.append({'step':t,'original_reason':row['command_refinement_reason'],'original_inward_x_nominal_mm':row['inward_x_nominal_mm'],'baseline':baseline,'multistart_best':best,'multistart_attempts':attempts});print(item['episode'],t,'enable_only',baseline.get('override',False),'multi',best['accepted'],flush=True)
 reports.append({'episode':item['episode'],'records':records,'original_bad_steps':len(chosen),'enable_only_accepted':sum(r['baseline'].get('independent_final_check',{}).get('accepted',False) for r in records),'multistart_accepted':sum(r['multistart_best']['accepted'] for r in records),'source_sha256':{n:sha(ep/n) for n in ['raw.npz','coordination.json','frontal_bypass.json','parcel_orientation.npz']}})
 out={'scope':__doc__,'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':reports,'source_sha256':{str(p):sha(p) for p in [Path(__file__),source,stage/'joint_edge_command.py',stage/'clearance_runtime.py',stage/'articulated_hand_geometry.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py',urdf,verts,stage/'elbow_torso_hulls.json']},'controller_changed':False,'physical_validation':False,'training_ready':False};(w/'LOADED_EDGE_COVERAGE_SCREEN.json').write_text(json.dumps(out,indent=2));print('SUMMARY',item['episode'],reports[-1]['enable_only_accepted'],reports[-1]['multistart_accepted'],len(chosen),flush=True)
