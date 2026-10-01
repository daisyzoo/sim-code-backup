"""Check runtime retry metadata against whole recorded/shadow screens, plus corruptions. Not full auditor entry validation."""
from pathlib import Path
import ast,json,copy,hashlib
w=Path(__file__).resolve().parent;probe=w/'staged_joint_edge_retry_probe';stage=w/'staged_joint_edge_retry';p=w/'audit_joint_edge_retry_execution_live.py'
tree=ast.parse(p.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='verify_retry_metadata');env={};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(p),'exec'),env);verify=env[fn.name];count=0;sample=None;inputs={}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['ALL_RECORDS_CHECK.json','SEQUENTIAL_HISTORY_CHECK.json']:
 inputs[name]=sha(probe/name);report=json.loads((probe/name).read_text());assert report['passed']
 for ep in report['episodes']:
  for row in ep['rows']:
   for v in row['variants']:
    rt=v['retry_trace'];tr=dict(override=v['override'],reason=v['reason'],solver_status=v['solver_status'])
    if rt:
     tr['analytic_retry']=rt
     if v['override']:tr['iterations']=rt['retry_iterations'];sample=copy.deepcopy(tr)
    assert verify(tr,v['name']=='retry',True,'top_push')==bool(rt);count+=bool(rt)
assert sample and count==23
mutations=[('disabled',lambda t:None,False,True,'top_push'),('unselected',lambda t:None,True,False,'top_push'),('nonpush',lambda t:None,True,True,'top_press'),('initial_not8',lambda t:t['analytic_retry'].update(initial_solver_status=9),True,True,'top_push'),('not_attempted',lambda t:t['analytic_retry'].update(attempted=False),True,True,'top_push'),('wrong_initial',lambda t:t['analytic_retry'].update(initializer='failed_endpoint'),True,True,'top_push'),('excess_iterations',lambda t:t['analytic_retry'].update(retry_iterations=301),True,True,'top_push'),('bool_status',lambda t:t['analytic_retry'].update(initial_solver_status=True),True,True,'top_push'),('failed_status_accepted',lambda t:t['analytic_retry'].update(retry_solver_status=8),True,True,'top_push'),('iterations_mismatch',lambda t:t.update(iterations=0),True,True,'top_push'),('extra_fields',lambda t:t['analytic_retry'].update(unbounded=True),True,True,'top_push')]
rejected=[]
for name,mut,en,eligible,mode in mutations:
 tr=copy.deepcopy(sample);mut(tr)
 try:verify(tr,en,eligible,mode)
 except AssertionError:rejected.append(name)
 else:raise AssertionError(name)
out=dict(passed=True,real_or_shadow_retry_records=count,corruptions_rejected=rejected,auditor_sha256=sha(p),checker_sha256=sha(Path(__file__)),input_sha256=inputs,scope=__doc__,full_entry_validated=False,training_ready=False)
(stage/'RETRY_METADATA_CHECK.json').write_text(json.dumps(out,indent=2));print('passed',count,'retry records;',len(rejected),'corruptions')
