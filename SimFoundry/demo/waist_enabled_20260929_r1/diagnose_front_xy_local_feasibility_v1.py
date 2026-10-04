"""Unissued local linearization diagnostic; ablations are not admissible commands.
Capture the unchanged candidate's exact constraint closures before optimization.
Local LP infeasibility does not prove nonlinear/global infeasibility.
"""
from pathlib import Path
import datetime, hashlib, json, sys, time
import numpy as np
from scipy.optimize import linprog
W=Path(__file__).resolve().parent; ROOT=W.parents[1]; S=W/'staged_front_effective_height_v1'
D=W/'front_xy_local_feasibility_r1'; D.mkdir(exist_ok=False)
sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
import front_xy_nonreversal_solver_candidate_v1 as candidate
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ep=W/'front_effective_height_physical_r1/case_840020/layout_840020_push_box_to_bin'
cs={c['step']:c for c in read(ep/'coordination.json')}
g=ClearanceGuard(ROOT,S)
class Captured(BaseException): pass
capture={}
def intercept(fun,x0,**kwargs):
 capture.update(fun=fun,x0=x0,**kwargs)
 raise Captured()
candidate.minimize=intercept
names=[]
for prefix in ['nominal','predicted']:
 names += [prefix+'_'+n for n in ['inactive_height','inactive_target','inactive_other','active_other','elbow_left','elbow_right']]
names += ['predicted_lower_'+str(i) for i in range(11)]+['predicted_upper_'+str(i) for i in range(11)]
names += ['normal_linear','normal_exact']
for prefix in ['nominal','predicted']:
 for alpha in [.25,.5,.75]:
  names += [f'{prefix}_path_{alpha}_{n}' for n in ['inactive_height','inactive_target','inactive_other','active_other','elbow_left','elbow_right']]
names += ['cross_x','forward_y']
ablations=['none','height_equality','normal','inactive_height','elbows','parcel_gaps','predicted_joint_bounds','command_bounds','cross_x','forward_y']
rows=[]
for t in [1008,1009,1141,1142,1143]:
 c=cs[t]; old=c['joint_transport_clearance']; tc=old['collector_context']; z=tc['scene']
 scene=RecontactScene(g,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size'])
 try:
  candidate.propose(step=t,side=z['side'],scene=scene,current=tc['current'],previous_q=tc['previous_q'],previous_command=tc['previous_command'],parent_command=old['parent_command'],decay=tc['decay'],coordinate=c,elbow_reserve_m=.0015,quarter_enabled=True,cross_track_nonreversal=True,route_stage='lateral_y')
 except Captured: pass
 cons=capture['constraints'][0]['fun']; eq=capture['constraints'][1]['fun']; ej=capture['constraints'][1]['jac']; bounds=capture['bounds']
 import gzip
 with gzip.open(W/f'front_cross_track_full_stream_probe_r1/contexts/layout_840020_push_box_to_bin_{t}.json.gz','rt') as f: xr=json.load(f)
 if t==1008: print('saved_x_keys',list(xr),flush=True)
 # Parent and old final are authoritative actual commands. Failed XY is an unissued iterate.
 bases={'parent':old['parent_command'],'actual_final':c['joint_transport_clearance']['command'],'failed_xy':read(W/f'front_xy_nonreversal_probe_r1/CONTEXT_{t}.json')['proposal']['command']}
 for label,values in bases.items():
  base=np.array(values,float); start=time.monotonic(); f=cons(base); assert len(f)==len(names),(len(f),len(names)); jac=np.zeros((len(f),11)); eps=2e-7
  for k in range(11):
   delta=np.zeros(11);delta[k]=eps
   jac[:,k]=(cons(base+delta)-cons(base-delta))/(2*eps)
  equality=float(eq(base)); equality_jac=np.asarray(ej(base),float)
  cases=[]
  for drop in ablations:
   keep=np.ones(len(f),dtype=bool)
   for i,n in enumerate(names):
    if (drop=='normal' and n.startswith('normal_')) or (drop=='inactive_height' and n.endswith('inactive_height')) or (drop=='elbows' and '_elbow_' in n) or (drop=='parcel_gaps' and any(n.endswith(s) for s in ['inactive_target','inactive_other','active_other'])) or (drop=='predicted_joint_bounds' and n.startswith(('predicted_lower_','predicted_upper_'))) or n==drop:keep[i]=False
   lb=bounds.lb-base;ub=bounds.ub-base
   if drop=='command_bounds':lb=g.lower-base;ub=g.upper-base
   fit=linprog(np.zeros(11),A_ub=-jac[keep],b_ub=f[keep],A_eq=None if drop=='height_equality' else equality_jac[None,:],b_eq=None if drop=='height_equality' else [-equality],bounds=list(zip(lb,ub)),method='highs',options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
   case=dict(removed_group=drop,lp_success=bool(fit.success),status=int(fit.status),message=fit.message)
   if fit.success:
    u=base+fit.x; actual=cons(u)
    case.update(command=u.tolist(),linear_min_margin_mm=float((f+jac@fit.x)[keep].min()),nonlinear_retained_min_margin_mm=float(actual[keep].min()),nonlinear_original_min_margin_mm=float(actual.min()),height_residual_mm=float(eq(u)),signed_xy_mm=actual[-2:].tolist(),original_violations=[dict(name=names[i],margin_mm=float(v)) for i,v in enumerate(actual) if v<-.0002])
   cases.append(case)
  row=dict(step=t,base=label,base_command=base.tolist(),base_height_residual_mm=equality,base_signed_xy_mm=f[-2:].tolist(),base_violations=[dict(name=names[i],margin_mm=float(v)) for i,v in enumerate(f) if v<-.0002],constraint_names=names,constraint_values_mm=f.tolist(),constraint_jacobian_mm_per_rad=jac.tolist(),height_jacobian_mm_per_rad=equality_jac.tolist(),cases=cases,elapsed_s=time.monotonic()-start)
  rows.append(row)
  with (D/f'{t}_{label}.json').open('x') as out:json.dump(row,out,indent=2,allow_nan=False)
  print(json.dumps(dict(step=t,base=label,feasible_ablations=[x['removed_group'] for x in cases if x['lp_success']],elapsed_s=row['elapsed_s'])),flush=True)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256={str(p):sha(p) for p in [Path(__file__),Path(candidate.__file__),ep/'coordination.json']},physics_started=False,training_ready=False,limitations=['Finite difference local linearization only, not a global infeasibility certificate.','Ablations identify sensitivity; none are authorized physical commands or changes to quality gates.','Old actual causal histories retained. Nonlinear and continuous-path safety are not inferred from LP feasibility.'])
with (D/'RESULT.json').open('x') as out:json.dump(report,out,indent=2,allow_nan=False)
