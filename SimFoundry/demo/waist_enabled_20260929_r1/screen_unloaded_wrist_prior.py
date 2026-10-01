"""Full recorded-state one-step screen, not recursive physics or training data.
Candidate uses same solver as baseline, retains task rows/damping/bounds/normal;
only declared high-unloaded rear wrist regularization prior changes. Check both
elbow geometry and next nominal hand height before counting viable candidates.
"""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_micro_clearance_return';probe=w/'staged_unloaded_wrist_prior_probe';sys.path[:0]=[str(probe),str(stage),str(repo)]
from unloaded_wrist_prior import wrist_prior
from task_ik import solve
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);out=[]
# All8 complete episodes, including unchanged front/easy conditions.
run=w/'rear_short_recovery_groups_r1';assert json.loads((run/'RESULT.json').read_text())['push_total']==8
for ep in sorted(run.glob('case_*/layout_*')):
 if 'wait' in ep.name:continue
 fr=json.loads((ep/'frontal_bypass.json').read_text());cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};selected=bool(fr['plan'].get('rear_joint_xy_progress',{}).get('enabled'));side='right' if 'push_box' in ep.name else 'left';wi=10 if side=='right' else 5;rows=[];counts=collections.Counter()
 def height(q):
  T=guard.model.fk(side,q)[0];return float((guard.model.vertices[side]@T[:3,:3].T+T[:3,3])[:,2].min())
 for r in fr['rows']:
  c=cs[r['step']];inp=c['task_inputs'];q=np.array(inp['current']);prior=np.array(inp['preferred_step']);z=height(q);load=r.get('contact_load')
  if load is None:
   assert r['mode'] not in ['top_lift','top_cross','top_descend','top_press','top_push','top_release'];counts['frames']+=1;counts['unchanged']+=1;counts['pre_top_without_load_record']+=1;continue
  context=dict(selected=selected,side=side,mode=r['mode'],recontacts=r['recontacts'],observed_load_n=load['observed_vertical_load_n'],filtered_load_n=load['filtered_vertical_load_n'],min_hand_z_m=z)
  disabled,_=wrist_prior(q,prior,enabled=False,**context);assert np.array_equal(disabled,prior)
  new,meta=wrist_prior(q,prior,enabled=True,**context);counts['frames']+=1
  if not meta['eligible']:
   assert np.array_equal(new,prior);counts['unchanged']+=1
   continue
  assert r['mode'] in ['top_lift','top_cross'] and c['contact_normal_tracking'] is not None
  base,bm=solve(enabled=True,geometry=guard.geometry,**inp);assert base is not None
  candidate,cm=solve(enabled=True,geometry=guard.geometry,**dict(inp,preferred_step=new));record=dict(step=r['step'],mode=r['mode'],eligibility=meta,current_wrist_rad=float(q[wi]),baseline_wrist_rad=float(base[wi]),current_min_hand_z_m=z,solver_accepted=candidate is not None)
  if candidate is not None:
   checked=guard.command(candidate,q,np.array(inp['previous']));newz=height(candidate);J=np.array(inp['jacobian']);error=np.array(inp['error']);active=slice(3,6) if side=='right' else slice(0,3);rb=J@(base-q)-error;rc=J@(candidate-q)-error
   record.update(command_check=checked,candidate_min_hand_z_m=newz,viable=bool(checked['accepted'] and newz>=.84),wrist_reduction_vs_baseline_rad=float(abs(base[wi])-abs(candidate[wi])),baseline_active_residual_mm=float(np.linalg.norm(rb[active])*1000),candidate_active_residual_mm=float(np.linalg.norm(rc[active])*1000),baseline_normal_residual=float(np.linalg.norm(rb[6:])),candidate_normal_residual=float(np.linalg.norm(rc[6:])),max_command_difference_rad=float(max(abs(candidate-base))),prior=new.tolist(),candidate_command=candidate.tolist())
  rows.append(record)
 viable=[x for x in rows if x.get('viable')];summary=dict(counts=counts,selected=selected,eligible=len(rows),viable=len(viable),wrist_reducing=sum(x['wrist_reduction_vs_baseline_rad']>1e-7 for x in viable),wrist_increasing=sum(x['wrist_reduction_vs_baseline_rad']< -1e-7 for x in viable),median_wrist_reduction_vs_baseline_rad=float(np.median([x['wrist_reduction_vs_baseline_rad'] for x in viable])) if viable else None,max_active_residual_increase_mm=max((x['candidate_active_residual_mm']-x['baseline_active_residual_mm'] for x in viable),default=0.))
 item=dict(episode=ep.name,summary=summary,records=rows,source_sha256={n:sha(ep/n) for n in ['coordination.json','frontal_bypass.json']});out.append(item);print(ep.name,json.dumps(summary),flush=True)
report=dict(scope=__doc__,episodes=out,source_sha256={str(p):sha(p) for p in [Path(__file__),probe/'unloaded_wrist_prior.py',stage/'task_ik.py',stage/'clearance_runtime.py',stage/'articulated_hand_geometry.py',stage/'self_clearance.py',stage/'elbow_torso_hulls.json',repo/'simfoundry/data/bounded_ik.py',run/'RESULT.json']},model_source_sha256=guard.model.source_sha256,collector_integrated=False,physical_validation=False,training_ready=False)
(probe/'RECORDED_STEP_SCREEN.json').write_text(json.dumps(report,indent=2))
