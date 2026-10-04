"""Unissued local linearization diagnostic; ablations are not admissible commands.
Capture the unchanged candidate's exact constraint closures before optimization.
Local LP infeasibility does not prove nonlinear/global infeasibility.
"""
from pathlib import Path
import datetime, hashlib, json, sys, time
import numpy as np
from scipy.optimize import minimize
W=Path(__file__).resolve().parent; ROOT=W.parents[1]; S=W/'staged_front_effective_height_v1'
D=W/'front_xy_nonlinear_conflict_r1'; D.mkdir(exist_ok=False)
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

rows=[]
for t in [1008,1009,1141,1142,1143]:
 c=cs[t];old=c['joint_transport_clearance'];tc=old['collector_context'];z=tc['scene']
 scene=RecontactScene(g,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size'])
 try:
  candidate.propose(step=t,side=z['side'],scene=scene,current=tc['current'],previous_q=tc['previous_q'],previous_command=tc['previous_command'],parent_command=old['parent_command'],decay=tc['decay'],coordinate=c,elbow_reserve_m=.0015,quarter_enabled=True,cross_track_nonreversal=True,route_stage='lateral_y')
 except Captured:pass
 import gzip
 with gzip.open(W/f'front_cross_track_full_stream_probe_r1/contexts/layout_840020_push_box_to_bin_{t}.json.gz','rt') as f:xr=json.load(f)
 original=capture['constraints'];cons=original[0]['fun'];eq=original[1]['fun'];ej=original[1]['jac'];bounds=capture['bounds'];parent=np.array(old['parent_command'],float)
 cases=[('all_constraints_x_seed',xr['proposal']['command'],original,capture['fun']),('free_height_x_seed',xr['proposal']['command'],original[:1],capture['fun'])]
 def height_objective(u):
  h=eq(u);return h*h+1e-6*np.sum((u-parent)**2),2*h*ej(u)+2e-6*(u-parent)
 cases.append(('minimum_height_change',xr['proposal']['command'],original[:1],height_objective))
 local=read(W/f'front_xy_local_feasibility_r2/{t}_parent.json');lp=next(x for x in local['cases'] if x['removed_group']=='none')
 if lp['lp_success']:cases.insert(1,('all_constraints_lp_seed',lp['command'],original,capture['fun']))
 for mode,seed,constraints,objective in cases:
  start=time.monotonic();fit=minimize(objective,np.clip(seed,bounds.lb,bounds.ub),jac=True,bounds=bounds,constraints=constraints,method='SLSQP',options=dict(maxiter=240,ftol=1e-10))
  u=fit.x.astype(np.float32).astype(float); vals=cons(u); h=float(eq(u)); q=np.array(tc['current']);prev=np.array(tc['previous_command'])
  geom=scene.details(u); nominal_elbows=g.geometry.constraints(u)
  row=dict(step=t,mode=mode,solver_success=bool(fit.success),solver_status=int(fit.status),iterations=int(fit.nit),message=fit.message,command=u.tolist(),minimum_inequality_margin_mm=float(vals.min()),signed_xy_mm=vals[-2:].tolist(),normal_margins_scaled=vals[34:36].tolist(),height_change_from_parent_mm=h,all_original_primal_passed=bool(vals.min()>=-.0002 and abs(h)<=.0002 and g.command(u,q,prev)['accepted']),retained_primal_passed=bool(vals.min()>=-.0002 and g.command(u,q,prev)['accepted']),elbow_gaps_mm=(nominal_elbows*1000).tolist(),violations=[dict(index=i,margin_scaled=float(v)) for i,v in enumerate(vals) if v<-.0002],original_objective_value=float(capture['fun'](u)[0]),elapsed_s=time.monotonic()-start,issued=False)
  rows.append(row)
  with (D/f'{t}_{mode}.json').open('x') as f:json.dump(row,f,indent=2,allow_nan=False)
  print(json.dumps({k:v for k,v in row.items() if k not in ['command','violations']}),flush=True)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Nonlinear diagnostic: unchanged full constraints with alternate seeds; height-only planning ablation keeps all other original constraints and XY. No commands issued.',rows=rows,source_sha256={str(p):sha(p) for p in [Path(__file__),Path(candidate.__file__),ep/'coordination.json']},physics_started=False,training_ready=False,limitations=['A feasible height ablation violates the previous expert height equality, and is not an approved candidate.','No independent KKT or continuous path certification here.','Old histories and approximate one-step responses do not establish closed-loop behavior.','Normal margin values are scaled dimensionless errors, not physical millimeters.'])
with (D/'RESULT.json').open('x') as f:json.dump(report,f,indent=2,allow_nan=False)
