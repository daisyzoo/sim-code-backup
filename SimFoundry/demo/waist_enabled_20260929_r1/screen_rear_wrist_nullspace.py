"""Recorded-state diagnostic, not a controller or recursive rollout.
Can wrist recentering preserve the original full linear task? Optimize only its
nullspace, retaining original measured/previous-command bounds and bilateral
elbow margin. Check actual nonlinear elbow geometry and FK before accepting a
single candidate. Later rear edge refinement is not included. No gate changes.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.optimize import linprog
w=Path(__file__).resolve().parent; repo=w.parents[1];stage=w/'staged_task_ik_precision'
sys.path[:0]=[str(stage),str(repo)]
from task_ik_precision import solve
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
guard=ClearanceGuard(repo,stage);out=[]
for run in ['micro_clearance_groups_r1','rear_short_recovery_groups_r1']:
 for cid,task,side,wi in [(840001,'push_box_to_bin','right',10),(840004,'nudge_mailer_to_bin','left',5)]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}'
  fr=json.loads((ep/'frontal_bypass.json').read_text());cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};records=[];last=None
  for r in fr['rows']:
   is_start=r['mode']=='top_push' and last!='top_push';last=r['mode']
   if not is_start:continue
   c=cs[r['step']];inp=c['task_inputs'];J=np.array(inp['jacobian']);q=np.array(inp['current']);prev=np.array(inp['previous']);base,meta=solve(enabled=True,geometry=guard.geometry,**inp);assert base is not None
   base=base.astype(float);lo=np.maximum.reduce([inp['lower'],q-np.array(inp['step_limits']),prev-.055]);hi=np.minimum.reduce([inp['upper'],q+np.array(inp['step_limits']),prev+.055]);sign=np.sign(base[wi]);objective=np.zeros(11);objective[wi]=sign
   if sign>0:lo[wi]=max(lo[wi],0.)
   else:hi[wi]=min(hi[wi],0.)
   _,sv,vh=np.linalg.svd(J,full_matrices=True);rank=int(np.sum(sv>1e-9));eq=vh[:rank]
   gaps=guard.geometry.constraints(base);G=guard.geometry.jacobian(base)
   fit=linprog(objective,A_ub=-G,b_ub=gaps-.005,A_eq=eq,b_eq=np.zeros(rank),bounds=list(zip(lo-base,hi-base)),method='highs')
   row=dict(step=r['step'],original_wrist_rad=float(base[wi]),task_rank=rank,singular_values=sv.tolist(),linear_program_success=bool(fit.success),reason=str(fit.message))
   if fit.success:
    cand=base+fit.x;task_change=J@(cand-base);geometry=guard.command(cand,q,prev);bound_error=max(float(max(lo-cand)),float(max(cand-hi)),0.);assert max(abs(task_change))<1e-8 and bound_error<2e-7
    def point(x):
     T=guard.model.fk(side,x)[0];return T[:3,3]+T[:3,:3]@np.array(c['active_point_offset_local'])
    Rb=guard.model.fk(side,base)[0][:3,:3];Rc=guard.model.fk(side,cand)[0][:3,:3]
    row.update(candidate_wrist_rad=float(cand[wi]),wrist_abs_reduction_rad=float(abs(base[wi])-abs(cand[wi])),waist_delta_rad=float(cand[0]-base[0]),command_max_delta_rad=float(max(abs(cand-base))),preserved_linear_task_error=float(max(abs(task_change))),nonlinear_active_material_point_delta_mm=float(np.linalg.norm(point(cand)-point(base))*1000),nonlinear_local_up_delta=float(np.linalg.norm(Rc[2]-Rb[2])),independent_command_check=geometry,accepted=geometry['accepted'],candidate_command=cand.tolist())
   records.append(row)
  accepted=[r for r in records if r.get('accepted')];summary=dict(bouts=len(records),accepted=len(accepted),max_wrist_reduction_rad=max((r['wrist_abs_reduction_rad'] for r in accepted),default=0.),median_wrist_reduction_rad=float(np.median([r['wrist_abs_reduction_rad'] for r in accepted])) if accepted else None,early=records[0],late=records[-1])
  out.append(dict(run=run,episode=ep.name,summary=summary,records=records,source_sha256={n:sha(ep/n) for n in ['frontal_bypass.json','coordination.json']}));print(run,ep.name,json.dumps({k:v for k,v in summary.items() if k not in ['early','late']}),flush=True)
report=dict(scope=__doc__,episodes=out,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'task_ik_precision.py',stage/'clearance_runtime.py',stage/'articulated_hand_geometry.py',stage/'self_clearance.py',stage/'elbow_torso_hulls.json',repo/'simfoundry/data/bounded_ik.py']},model_source_sha256=guard.model.source_sha256,controller_changed=False,training_ready=False)
(w/'REAR_WRIST_NULLSPACE_SCREEN.json').write_text(json.dumps(report,indent=2))
