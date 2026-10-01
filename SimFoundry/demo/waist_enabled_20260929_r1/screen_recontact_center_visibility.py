"""Offline endpoint trade-off using actual recovery starts, never execution.
Keep original geometry and .98 command waist bound. Test preference for a
central real supporting vertex and measured camera view; all candidate failures
retained. Does not prove contact stability, path feasibility or model learning.
"""
from pathlib import Path
import sys,json,hashlib,datetime,ast
import numpy as np
from scipy.optimize import minimize,Bounds
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;stage=w/'staged_recontact_pose';repo=w.parents[1];sys.path[:0]=[str(stage),str(repo)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
guard=ClearanceGuard(repo,stage)
ep=w/'recontact_pose_groups_r1/case_840001/layout_840001_push_box_to_bin'
events=json.loads((ep/'recontact_pose.json').read_text())['rows'];starts=[];seen=set()
for r in events:
 if r['kind']=='command' and r.get('planning') is not None and r['planning']['step'] not in seen:starts.append(r);seen.add(r['planning']['step'])
starts=[starts[0],starts[len(starts)//2],starts[-1]]
view=json.loads((ep/'viewer_observer.json').read_text())['frames'][0];assert view['pre_action_step']==0
Ropt=Rotation.from_quat(view['policy_camera_quat_ros_xyzw']).as_matrix();cam0=np.array(view['policy_camera_position_world']);torso=np.array([.0760365,0.,.837]);camoff=cam0-torso;K=np.array(view['policy_camera_intrinsics'])
rows=[]
for row in starts:
 context=row['context'];q=np.array(context['current']);scene=RecontactScene(guard,**context['scene']);half=scene.core[:2]/2-.012;assert scene.check(q)['accepted']
 def cons(x):
  g=scene.details(x);p=g['point'];J=g['jacobian'];return np.r_[half-p[:2],half+p[:2],p[2]-scene.core[2]/2-.006,scene.core[2]/2+.007-p[2],g['inactive_z']-.84,guard.geometry.constraints(x)-.005],np.vstack([-J[:2],J[:2],J[2],-J[2],g['inactive_z_jacobian'],guard.geometry.jacobian(x)])
 def view_cost(yaw):
  Rz=Rotation.from_euler('z',yaw).as_matrix();cp=torso+Rz@camoff;R=Rz@Ropt;uv=[]
  for pos in [scene.target,scene.other]:
   p=(pos-cp)@R;v=K@p;uv.append(v[:2]/v[2])
  # Soft central image region only; not a claimed visibility certificate.
  uv=np.array(uv);lo=np.array([80.,60.]);hi=np.array([560.,420.]);miss=np.maximum(lo-uv,0)+np.maximum(uv-hi,0)
  return float(np.sum((miss/640.)**2)),uv.tolist()
 variants=[]
 for name,central,visible in [('original',0.,0.),('center',100.,0.),('center_view',100.,1.)]:
  def cost(x):
   d=x-q;g=scene.details(x);c=float(x[10]**2+.002*(d@d)+central*(g['point'][:2]@g['point'][:2]));grad=2*np.eye(11)[10]*x[10]+.004*d+2*central*g['point'][:2]@g['jacobian'][:2]
   if visible:
    c+=visible*view_cost(x[0])[0];h=1e-6;grad[0]+=visible*(view_cost(x[0]+h)[0]-view_cost(x[0]-h)[0])/(2*h)
   return c,grad
  attempts=[]
  original=np.array(row['planning']['endpoint']);zero=q.copy();zero[10]=0
  # Both seeds available from current observed state or current causal plan.
  for seed in [original,zero]:
   fit=minimize(cost,np.clip(seed,guard.lower,guard.upper),jac=True,bounds=Bounds(guard.lower,guard.upper),constraints=[dict(type='ineq',fun=lambda x:cons(x)[0],jac=lambda x:cons(x)[1]),dict(type='ineq',fun=lambda x:np.array(list(scene.details(x)['gaps'].values()))-.01)],method='SLSQP',options={'maxiter':220,'ftol':1e-12})
   x=fit.x;g=scene.details(x);minimum=float(min(cons(x)[0]));ok=bool(fit.success and minimum>=-2e-7 and min(g['gaps'].values())>=.01-2e-7)
   attempts.append({'accepted':ok,'solver_status':int(fit.status),'iterations':int(fit.nit),'objective':float(fit.fun),'minimum_constraint':minimum,'q':x.tolist(),'point_local_mm':(g['point']*1000).tolist(),'core_margins_mm':((scene.core[:2]/2-abs(g['point'][:2]))*1000).tolist(),'hand_parcel_gaps_m':g['gaps'],'waist_rad':float(x[0]),'wrist_rad':float(x[10]),'camera_center_uv':view_cost(x[0])[1]})
  best=min(attempts,key=lambda x:(not x['accepted'],x['objective']));variants.append({'name':name,'best':best,'attempts':attempts});print(row['step'],name,'accepted',best['accepted'],'xy',best['point_local_mm'][:2],'waist',best['waist_rad'],'uv',best['camera_center_uv'],flush=True)
 rows.append({'step':row['step'],'variants':variants})
 out={'scope':__doc__,'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':rows,'source_sha256':{str(p):sha(p) for p in [Path(__file__),ep/'recontact_pose.json',ep/'viewer_observer.json',stage/'recontact_scene.py',stage/'clearance_runtime.py',stage/'articulated_hand_geometry.py']},'model_sources':guard.model.source_sha256,'physical_validation':False,'controller_changed':False,'training_ready':False}
 (w/'RECONTACT_CENTER_VISIBILITY_SCREEN.json').write_text(json.dumps(out,indent=2))
