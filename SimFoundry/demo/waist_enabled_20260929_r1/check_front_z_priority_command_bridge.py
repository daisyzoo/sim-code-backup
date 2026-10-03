"""Exact generated audit diff plus real command-bridge AST one-step fixtures.
The fixture supplies original parent and an UNISSUED expected output; no q/u
history is replaced and no full candidate trajectory/physical success is claimed.
Whole record validation and original controller reconstruction remain separate.
"""
from pathlib import Path
import sys,json,hashlib,ast,datetime,copy
import numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from audit_front_loaded_z_priority_parent import near
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();M=W/'FRONT_Z_PRIORITY_AUDIT_FAMILY_PREPARATION.json';manifest=json.loads(M.read_text());sources={str(M):sha(M)};diffs=[]
for item in manifest['adapters']:
 parent=Path(item['parent']);dest=Path(item['path']);assert sha(parent)==item['parent_sha256'] and sha(dest)==item['sha256'];expected=parent.read_text()
 if any(e.get('kind')=='name_only_restore_reviewed_causal_dependency' for e in item['edits']):expected=expected.replace('terminal_margin_stage','front_z_priority_stage').replace('TERMINAL_MARGIN_STAGE','FRONT_Z_PRIORITY_STAGE').replace('staged_terminal_release_margin','staged_front_loaded_z_priority');assert dest.read_text()==expected
 else:
  for a,b in item['global_replacements']:expected=expected.replace(a,b)
  recovered=dest.read_text()
  for e in reversed(item['edits']):
   if e.get('kind')=='add_distinct_execution_report':
    extra="\nREPORTS['audit_front_z_priority_execution.py']=('FRONT_Z_PRIORITY_EXECUTION_AUDIT.json',('passed',))\n";assert recovered.endswith(extra);recovered=recovered[:-len(extra)]
   else:assert recovered.count(e['new'])==1;recovered=recovered.replace(e['new'],e['old'])
  assert recovered==expected,dest
 ast.parse(dest.read_text());sources[str(parent)]=sha(parent);sources[str(dest)]=sha(dest);diffs.append(dict(file=dest.name,exact_declared_diff=True))
p=W/'audit_front_z_priority_stage_self_clearance.py';tree=ast.parse(p.read_text());loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and ast.unparse(n.target)=='c' and ast.unparse(n.iter)=='coordinates');start=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='priority' for t in n.targets));nodes=loop.body[start:];assert len(nodes)==6 and isinstance(nodes[-1],ast.AugAssign)
program=compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'<actual final-command audit bridge>','exec')
replay=json.loads((W/'FRONT_LOADED_Z_PRIORITY_NATIVE_FULL10_REPLAY.json').read_text());sources[str(W/'FRONT_LOADED_Z_PRIORITY_NATIVE_FULL10_REPLAY.json')]=sha(W/'FRONT_LOADED_Z_PRIORITY_NATIVE_FULL10_REPLAY.json');rows=0;applied=0;negative=[];cases=[]
for e in replay['episodes']:
 if e['wait']:continue
 seen=set();count=0
 for r in e['rows']:
  t=r['step'];m=r['metadata']
  if t==0:continue
  context=dict(np=np,near=near,t=t,c={'front_loaded_z_priority':m},priority_records={t:m},target=np.asarray(m['context']['parent_command']),u={t:np.asarray(m['output_command'])},controller_frames=0)
  exec(program,context);assert context['controller_frames']==1;near(context['target'],m['output_command']);rows+=1;count+=1;applied+=m['applied']
  if m['reason'] not in seen:
   seen.add(m['reason'])
   for name in ['wrong_reconstructed_parent','wrong_raw_output','coordination_log_mismatch']:
    bad=dict(context);bad['controller_frames']=0;bad['target']=np.asarray(m['context']['parent_command']).copy();bad['u']={t:np.asarray(m['output_command']).copy()}
    if name=='wrong_reconstructed_parent':bad['target'][0]+=.001
    elif name=='wrong_raw_output':bad['u'][t][0]+=.001
    else:bad['c']={'front_loaded_z_priority':dict(m,step=t+1)}
    try:exec(program,bad)
    except (AssertionError,KeyError):negative.append(dict(episode=e['episode'],step=t,mutation=name,rejected=True))
    else:raise AssertionError(('negative accepted',name))
 cases.append(dict(episode=e['episode'],one_step_command_bridge_fixtures=count))
assert rows==9592 and applied==658
for n in ['check_front_z_priority_command_bridge.py','audit_front_loaded_z_priority_parent.py']:sources[str(W/n)]=sha(W/n)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,exact_diff_checks=diffs,unissued_single_step_fixtures=rows,applied_fixture_count=applied,negative_cases=negative,cases=cases,source_sha256=sources,full_physical_audit_chain_executed=False,simulation_started=False,training_ready=False)
p=W/'FRONT_Z_PRIORITY_COMMAND_BRIDGE_CHECK.json'
with p.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,exact_module_diffs=len(diffs),single_step_fixtures=rows,applied=applied,negative_cases=len(negative),simulation_started=False),indent=2))
