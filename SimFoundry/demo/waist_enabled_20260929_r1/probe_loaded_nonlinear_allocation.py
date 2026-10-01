"""Local nonlinear allocation screen, preserving baseline geometric residuals."""
from pathlib import Path
import json,sys,hashlib,importlib.util
import numpy as np
from scipy.optimize import minimize
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def mod(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
rp=w/'loaded_coupled_allocation_probe_r1/RESULT.json';gp=rp.with_name('PROJECTED_GEOMETRY_CHECK.json');prior=json.loads(rp.read_text());assert json.loads(gp.read_text())['passed'];reports=[]
for case in prior['episodes']:
 ep=w/case['run']/('case_'+case['episode'].split('_')[1])/case['episode'];src=json.loads((ep.parent/'provenance.json').read_text())['source_sha256'];snap=ep.parent/'source_snapshot';gr=next(n for n in src if n.endswith('/articulated_hand_geometry.py'));pr='simfoundry/data/projected_support_reference.py'
 for n in [gr,pr]:assert sha(snap/n)==src[n]
 for n,h in case['asset_sha256'].items():assert sha(repo/n)==h
 for n,h in case['source_sha256'].items():assert sha(ep/n)==h
 model=mod(snap/gr,'ng').ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');pm=mod(snap/pr,'np');side='right' if 'push_box' in ep.name else 'left';inactive='left' if side=='right' else 'right';cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};fs={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']}
 with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float);us=z['action'][:,12:23].astype(float)
 lo=np.array(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.array(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98;step=np.full(11,.04);step[0]=.015;rows=[]
 for sample in case['rows']:
  if not sample['loaded']:continue
  t=sample['step'];c=cs[t];f=fs[t];q=qs[t];base=us[t];ref=c['active_support_reference'];n=np.array(ref['world_normal']);center=np.array(ref['center_local']);goal=np.array(f['target_xyz']);anchor=np.array(c['inactive_anchor']);target_up=np.array(c['contact_normal_tracking']['target_local_up']);current=np.array(c['control_point_positions'][side]);desired=current+np.clip(.72*(goal-current),-.035,.035)
  lower=np.maximum.reduce([lo,q-step,us[t-1]-.055]);upper=np.minimum.reduce([hi,q+step,us[t-1]+.055]);cache={}
  def evaluate(cmd):
   key=cmd.tobytes()
   if key in cache:return cache[key]
   T,_,_=model.fk(side,cmd);Ti,_,_=model.fk(inactive,cmd);r=pm.projected_support_reference(model.vertices[side],T[:3,:3],n,center_local=center);point=T[:3,3]+T[:3,:3]@r['reference_local'];ip=Ti[:3,3]+Ti[:3,:3]@np.array([.2,0,.007]);up=T[:3,:3].T@np.array([0.,0.,1.]);keep=np.r_[point[1:]-desired[1:],ip-anchor,.15*(up-target_up)];val=(point,keep,ip,up);cache[key]=val;return val
  bp,bk,bi,bu=evaluate(base);tol=abs(bk)+1e-7
  def obj(cmd):return ((evaluate(cmd)[0][0]-desired[0])*1000)**2+1e-6*float(np.sum(((cmd-base)/step)**2))
  def constraint(cmd):return (tol-abs(evaluate(cmd)[1]))*1000
  fit=minimize(obj,np.clip(base,lower,upper),method='SLSQP',bounds=list(zip(lower,upper)),constraints=[dict(type='ineq',fun=constraint)],options=dict(maxiter=150,ftol=1e-10))
  cmd=np.asarray(fit.x,dtype=np.float32).astype(float);cp,ck,ci,cu=evaluate(cmd);valid=bool(np.all(abs(ck)<=tol+2e-8) and np.all(cmd>=lower-1e-7) and np.all(cmd<=upper+1e-7));row=dict(step=t,optimizer_success=bool(fit.success),message=str(fit.message),iterations=int(fit.nit),float32_candidate_constraints_passed=valid,baseline_step_x_residual_mm=float(abs(bp[0]-desired[0])*1000),candidate_step_x_residual_mm=float(abs(cp[0]-desired[0])*1000),baseline_goal_x_residual_mm=float(abs(bp[0]-goal[0])*1000),candidate_goal_x_residual_mm=float(abs(cp[0]-goal[0])*1000),baseline_inactive_error_mm=float(np.linalg.norm(bi-anchor)*1000),candidate_inactive_error_mm=float(np.linalg.norm(ci-anchor)*1000),max_other_component_worsening_m=float(np.max(abs(ck)-abs(bk))),baseline_normal_angle_rad=float(np.arccos(np.clip(bu@target_up,-1,1))),candidate_normal_angle_rad=float(np.arccos(np.clip(cu@target_up,-1,1))),candidate_command=cmd.tolist())
  rows.append(row);print(case['run'],t,valid,round(row['baseline_step_x_residual_mm'],3),round(row['candidate_step_x_residual_mm'],3),flush=True)
 reports.append(dict(run=case['run'],episode=case['episode'],rows=rows))
out=dict(episodes=reports,source_replay_sha256=sha(rp),geometry_check_sha256=sha(gp),checker_sha256=sha(Path(__file__)),training_ready=False,scope='Local nonlinear static geometry only. Minimize active projected X error to original .72 clipped step target, keeping activeYZ, inactiveXYZ and normal-vector component errors no worse than baseline within 1e-7m. Original joint/step/slew bounds; float32 candidate verified. No dynamics/contact stability prediction, global infeasibility or runtime readiness claim.')
p=rp.with_name('NONLINEAR_ALLOCATION.json');assert not p.exists();p.write_text(json.dumps(out,indent=2))
