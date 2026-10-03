"""Check exact family derivation and final-command bridge against all recorded Z outputs.
These are old Z trajectories, not midpoint rollouts. Cartesian midpoint changes
and full upstream joint reconstruction must be validated separately. The bridge
checks actual recorded parent/output equality and rejects record corruption.
"""
from pathlib import Path
import sys,json,hashlib,ast,datetime,copy
import numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from audit_front_loaded_z_priority_parent import near
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();M=W/'FRONT_CORRIDOR_MIDPOINT_AUDIT_FAMILY_PREPARATION.json';manifest=json.loads(M.read_text());sources={str(M):sha(M)};diffs=[]
for item in manifest['adapters']:
 parent=Path(item['parent']);dest=Path(item['path']);assert sha(parent)==item['parent_sha256'] and sha(dest)==item['sha256'];expected=parent.read_text()
 if item.get('exact_renamed_parent_restoration'):
  for a,b in manifest['global_replacements']:expected=expected.replace(a,b)
 recovered=dest.read_text()
 for e in reversed(item['edits']):
  assert recovered.count(e['new'])==1;recovered=recovered.replace(e['new'],e['old'],1)
 assert recovered==expected,dest
 ast.parse(dest.read_text());sources[str(parent)]=sha(parent);sources[str(dest)]=sha(dest);diffs.append(dict(file=dest.name,exact_declared_diff=True))
p=W/'audit_front_corridor_midpoint_stage_self_clearance.py';tree=ast.parse(p.read_text());loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and ast.unparse(n.target)=='c' and ast.unparse(n.iter)=='coordinates');start=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='priority' for t in n.targets));nodes=loop.body[start:];assert len(nodes)==6 and isinstance(nodes[-1],ast.AugAssign)
program=compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'<actual final-command audit bridge>','exec')
replay={'episodes':[]}
for ep in sorted((W/'front_z_priority_physical_r1').glob('case_*/layout_*')):
 p=ep/'front_loaded_z_priority.json'
 if not p.exists():continue
 log=json.loads(p.read_text());sources[str(p)]=sha(p)
 replay['episodes'].append(dict(episode=ep.name,wait='wait_no_package' in ep.name,rows=[dict(step=r['step'],metadata=r) for r in log['rows']]))
rows=0;applied=0;negative=[];cases=[]
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
 cases.append(dict(episode=e['episode'],recorded_z_command_bridge_rows=count))
assert rows==9592 and applied==328
for n in ['check_front_corridor_midpoint_command_bridge.py','audit_front_loaded_z_priority_parent.py']:sources[str(W/n)]=sha(W/n)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,exact_diff_checks=diffs,recorded_z_command_bridge_rows=rows,recorded_z_applied_count=applied,negative_cases=negative,cases=cases,source_sha256=sources,full_physical_audit_chain_executed=False,simulation_started=False,training_ready=False)
p=W/'FRONT_CORRIDOR_MIDPOINT_COMMAND_BRIDGE_CHECK.json'
with p.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,exact_module_diffs=len(diffs),recorded_z_rows=rows,applied=applied,negative_cases=len(negative),simulation_started=False),indent=2))
