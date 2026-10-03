"""Version original uncapped first-center audit family, preserving all old gates.
Restore its previously omitted causal helper via the already reviewed margin
parent. Only command-chain insertion is new, backed by independent whole-record
validation; actual q and previous u are never replaced. Not launch readiness.
"""
from pathlib import Path
import json,hashlib,ast,datetime
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();records=[]
replacements=[('audit_front_initial_center_live_v2','audit_front_z_priority_initial_live'),('front_initial_center_stage_source_binding','front_z_priority_stage_source_binding'),('front_initial_stage','front_z_priority_stage'),('FRONT_INITIAL_STAGE','FRONT_Z_PRIORITY_STAGE'),('staged_front_initial_center','staged_front_loaded_z_priority')]
def rename(s):
 for a,b in replacements:s=s.replace(a,b)
 return s

def write(parent,name,source,edits=None):
 dest=W/name;assert not dest.exists(),dest;ast.parse(source);dest.write_text(source);records.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest),global_replacements=replacements,edits=edits or []))
for parent in sorted(W.glob('audit_front_initial_stage_*.py')):
 s=rename(parent.read_text());edits=[]
 if parent.name=='audit_front_initial_stage_self_clearance.py':
  old=' # Reconstruct the command chain, preserving the original subsequent overrides.'
  new=''' # New final refinement is verified independently against actual raw history.
 from audit_front_z_priority_execution import inspect as inspect_priority
 priority_validation=inspect_priority(ep)
 assert priority_validation['passed'] and not priority_validation['fixture_only']
 priority_records={r['step']:r for r in json.loads((ep/'front_loaded_z_priority.json').read_text())['rows']}
'''+old
  assert s.count(old)==1;s=s.replace(old,new);edits.append(dict(old=old,new=new))
  old='  near(target,u[t],0);controller_frames+=1'
  new='''  priority=priority_records[t];assert c['front_loaded_z_priority']==priority
  near(target,priority['context']['parent_command'],0)
  if priority['applied']:target=np.asarray(priority['output_command'],dtype=np.float32)
  near(target,u[t],0);controller_frames+=1'''
  assert s.count(old)==1;s=s.replace(old,new);edits.append(dict(old=old,new=new))
  old='return dict(passed=True,executed_frames=count,';new="return dict(passed=True,priority_execution_applied=priority_validation['applied'],priority_execution_source_sha256=priority_validation['source_sha256'],executed_frames=count,"
  assert s.count(old)==1;s=s.replace(old,new);edits.append(dict(old=old,new=new))
 write(parent,rename(parent.name),s,edits)
for name in ['front_initial_stage_audit_context.py','audit_front_initial_center_live_v2.py']:
 p=W/name;write(p,rename(name),rename(p.read_text()))
p=W/'audit_terminal_margin_stage_region_causal.py';s=p.read_text().replace('terminal_margin_stage','front_z_priority_stage').replace('TERMINAL_MARGIN_STAGE','FRONT_Z_PRIORITY_STAGE').replace('staged_terminal_release_margin','staged_front_loaded_z_priority');write(p,'audit_front_z_priority_stage_region_causal.py',s,[dict(kind='name_only_restore_reviewed_causal_dependency')])
p=W/'front_initial_stage_run_contract.py';s=rename(p.read_text());edits=[]
a=" return (['audit_front_z_priority_stage_self_clearance.py'";b=" return ['audit_front_z_priority_execution.py']+(['audit_front_z_priority_stage_self_clearance.py'";assert s.count(a)==1;s=s.replace(a,b);edits.append(dict(old=a,new=b))
s+="\nREPORTS['audit_front_z_priority_execution.py']=('FRONT_Z_PRIORITY_EXECUTION_AUDIT.json',('passed',))\n";edits.append(dict(kind='add_distinct_execution_report'))
write(p,rename(p.name),s,edits)
# Generated family explicitly leaves old failed/missing helper and all frozen
# runs untouched. Record all static local import/subprocess dependencies.
queue=[Path(r['path']) for r in records]+[W/'front_z_priority_stage_source_binding.py',W/'audit_front_z_priority_execution.py'];seen=set();edges=[];missing=[]
while queue:
 p=queue.pop()
 if p in seen:continue
 seen.add(p);tree=ast.parse(p.read_text())
 for n in ast.walk(tree):
  names=[]
  if isinstance(n,ast.ImportFrom) and n.module and '.' not in n.module:names=[n.module+'.py']
  elif isinstance(n,ast.Import):names=[a.name+'.py' for a in n.names if '.' not in a.name]
  elif isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.endswith('.py') and '/' not in n.value and n.value.startswith(('audit_','front_')):names=[n.value]
  for name in names:
   dest=W/name
   if dest.exists():edges.append(dict(source=str(p),dependency=str(dest)));queue.append(dest)
   elif name.startswith(('audit_front_z_priority','front_z_priority')):missing.append(dict(source=str(p),missing=name))
assert not missing,missing
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=records,original_missing_helper_preserved=not (W/'audit_front_initial_stage_region_causal.py').exists(),dependency_files=len(seen),dependency_sha256={str(p):sha(p) for p in sorted(seen)},static_edges=edges,syntax_passed=True,full_dependency_imports_tested=False,command_bridge_tested=False,full_physical_audit_chain_ready=False,simulation_started=False,training_ready=False,generator_sha256=sha(__file__))
with (W/'FRONT_Z_PRIORITY_AUDIT_FAMILY_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(prepared_modules=len(records),dependency_files=len(seen),missing_local_dependencies=missing,simulation_started=False),indent=2))
