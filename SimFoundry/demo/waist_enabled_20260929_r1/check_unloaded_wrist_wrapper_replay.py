"""Actual coordinator branch replay on all recorded eligibility states; fallback tests.
Not physics: measured inputs remain recorded and no candidate feeds later states.
"""
from pathlib import Path
import ast,sys,json,hashlib,copy,types
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_unloaded_wrist_prior';sys.path[:0]=[str(stage),str(repo)]
from task_ik import solve
from clearance_runtime import ClearanceGuard
import unloaded_wrist_task as module
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage)
tree=ast.parse((stage/'waist_coordination_clearance.py').read_text());block=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='wrist_prior_context is not None');program=compile(ast.Module(body=[block],type_ignores=[]),'<actual coordinator prior branch>','exec');old=json.loads((w/'staged_unloaded_wrist_prior_probe/RECORDED_STEP_SCREEN.json').read_text());out=[];sample=None
for e in old['episodes']:
 ep=next((w/'rear_short_recovery_groups_r1').glob('case_*/'+e['episode']));fr=json.loads((ep/'frontal_bypass.json').read_text());cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};selected=e['summary']['selected'];side='right' if 'push_box' in ep.name else 'left';counts=dict(frames=0,contexts=0,applied=0,default_off=0,unchanged=0);prior_rows={r['step']:r for r in e['records']};actual=[]
 for r in fr['rows']:
  counts['frames']+=1;inp=cs[r['step']]['task_inputs'];q=np.array(inp['current']);T=guard.model.fk(side,q)[0];z=float((guard.model.vertices[side]@T[:3,:3].T+T[:3,3])[:,2].min());context=None
  if 'contact_load' in r:
   load=r['contact_load'];context=dict(selected=selected,side=side,mode=r['mode'],recontacts=int(r['recontacts']),observed_load_n=load['observed_vertical_load_n'],filtered_load_n=load['filtered_vertical_load_n'],min_hand_z_m=z);counts['contexts']+=1
  eligible=r['step'] in prior_rows
  baseline=solve(enabled=True,geometry=guard.geometry,**inp) if eligible else (np.array(inp['previous']),dict(sentinel='unchanged'))
  ns=dict(wrist_prior_context=None,target=baseline[0],clearance_record=copy.deepcopy(baseline[1]),task_inputs=copy.deepcopy(inp),clearance_geometry=guard.geometry);exec(program,ns);assert ns['task_inputs']==inp and np.array_equal(ns['target'],baseline[0]);counts['default_off']+=1
  ns['wrist_prior_context']=context;exec(program,ns)
  if context is None:counts['unchanged']+=1;continue
  record=ns['clearance_record']['unloaded_wrist_prior'];assert record['eligible']==eligible
  if not eligible:
   assert ns['task_inputs']==inp and np.array_equal(ns['target'],baseline[0]) and not record['applied'];counts['unchanged']+=1
  else:
   assert record['applied'];assert ns['task_inputs']['jacobian']==inp['jacobian'] and ns['task_inputs']['error']==inp['error'] and ns['task_inputs']['damping']==inp['damping'];checked=guard.command(ns['target'],q,np.array(inp['previous']));assert checked['accepted'] and record['candidate_nominal_min_hand_z_m']>=.84
   counts['applied']+=1;actual.append(dict(step=r['step'],record=record,command=ns['target'].tolist(),probe_command_max_delta_rad=float(max(abs(ns['target']-np.array(prior_rows[r['step']]['candidate_command']))))))
   if sample is None:sample=(inp,context,baseline)
 out.append(dict(episode=ep.name,counts=counts,applied_records=actual,source_sha256={n:sha(ep/n) for n in ['coordination.json','frontal_bypass.json']}));print(ep.name,counts,flush=True)
assert sum(e['counts']['frames'] for e in out)==9592 and sum(e['counts']['applied'] for e in out)==54
inp,context,baseline=sample;tests=[];real=module.solve
try:
 module.solve=lambda **kw:(None,dict(accepted=False))
 target,meta,chosen,record=module.solve_recovery_task(inp,guard.geometry,context,baseline);assert np.array_equal(target,baseline[0]) and chosen==inp and not record['applied'] and record['fallback_reason']=='no_verified_prior_command';tests.append('solver_failure_returns_original_command_and_prior')
 module.solve=lambda **kw:real(**kw)
 class LowModel:
  vertices=guard.model.vertices
  def fk(self,side,q):
   T,jl,jw=guard.model.fk(side,q);T=T.copy();T[2,3]-=1.;return T,jl,jw
 fake=types.SimpleNamespace(model=LowModel(),constraints=guard.geometry.constraints,jacobian=guard.geometry.jacobian)
 target,meta,chosen,record=module.solve_recovery_task(inp,fake,context,baseline);assert np.array_equal(target,baseline[0]) and chosen==inp and not record['applied'] and record['fallback_reason']=='nominal_hand_height';tests.append('low_nominal_hand_returns_original_command_and_prior')
finally:module.solve=real
report=dict(passed=True,scope=__doc__,episodes=out,fallback_tests=tests,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'collect_paired_sorting.py',stage/'waist_coordination_clearance.py',stage/'unloaded_wrist_task.py',stage/'unloaded_wrist_prior.py',stage/'task_ik.py',stage/'INTEGRATION_CHECK.json',w/'staged_unloaded_wrist_prior_probe/RECORDED_STEP_SCREEN.json']},physical_validation=False,training_ready=False)
(stage/'RECORDED_WRAPPER_REPLAY.json').write_text(json.dumps(report,indent=2));print('passed full9592 defaults,54 actual branch candidates,2 fallback failures')
