"""Derive a separate full audit family without editing completed-run evidence.
Keep every old inventory entry, replacing the route reconstruction with the
independent verified-goal version and loaded-Z execution with its corrected
rotation representation. This preparation is not physical launch readiness.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
replacements=[('front_z_priority_stage','front_corridor_midpoint_stage'),('FRONT_Z_PRIORITY_STAGE','FRONT_CORRIDOR_MIDPOINT_STAGE'),('audit_front_z_priority_initial_live','audit_front_corridor_midpoint_initial_live'),('staged_front_loaded_z_priority','staged_front_corridor_midpoint_integrated'),('audit_front_z_priority_execution','audit_front_corridor_midpoint_execution'),('FRONT_Z_PRIORITY_EXECUTION_AUDIT','FRONT_CORRIDOR_MIDPOINT_EXECUTION_AUDIT'),('audit_front_diagonal_entry_live','audit_front_corridor_midpoint_diagonal_live'),('FRONT_DIAGONAL_ENTRY_LIVE_AUDIT','FRONT_CORRIDOR_MIDPOINT_DIAGONAL_LIVE_AUDIT')]
def rename(s):
 for a,b in replacements:s=s.replace(a,b)
 return s
records=[]
parents=sorted(W.glob('audit_front_z_priority_stage_*.py'))+[W/'front_z_priority_stage_audit_context.py',W/'audit_front_z_priority_initial_live.py',W/'front_z_priority_stage_run_contract.py']
for p in parents:
 original=p.read_text();s=rename(original);edits=[]
 if p.name=='audit_front_z_priority_stage_self_clearance.py':
  a="priority_validation['applied']";b="priority_validation['loaded_z_applied']";assert s.count(a)==1;s=s.replace(a,b);edits.append(dict(old=a,new=b))
 dest=W/rename(p.name);assert not dest.exists() or dest.read_text()==s;ast.parse(s)
 reverse=s
 for edit in reversed(edits):reverse=reverse.replace(edit['new'],edit['old'],1)
 assert reverse==rename(original)
 dest.write_text(s);records.append(dict(parent=str(p),parent_sha256=sha(p),path=str(dest),sha256=sha(dest),edits=edits,exact_renamed_parent_restoration=True))
p=W/'audit_front_diagonal_entry_live.py';s=p.read_text();edits=[]
a="records,errors=reconstruct(log['rows'],log['plan'],tr,ori,packets,'box' if 'push_box' in p.name else 'mailer')"
b="""from front_corridor_midpoint_stage_source_binding import verify_observation_binding
  verify_observation_binding(p)
  assert not (p.parent/'SOURCE_CONTRACT_FIXTURE.json').exists()
  from audit_front_corridor_midpoint_cop import reconstruct as reconstruct_midpoint
  midpoint=reconstruct_midpoint(log['rows'],log['plan'],tr,ori,packets,'box' if 'push_box' in p.name else 'mailer',midpoint_enabled=True,expected_steps=range(1,len(tr['box'])))
  records,errors=midpoint['records'],midpoint['errors']"""
assert s.count(a)==1;s=s.replace(a,b);edits.append(dict(old=a,new=b));a='FRONT_DIAGONAL_ENTRY_LIVE_AUDIT.json';b='FRONT_CORRIDOR_MIDPOINT_DIAGONAL_LIVE_AUDIT.json';assert s.count(a)==1;s=s.replace(a,b);edits.append(dict(old=a,new=b))
r=s
for edit in reversed(edits):r=r.replace(edit['new'],edit['old'],1)
assert r==p.read_text();dest=W/'audit_front_corridor_midpoint_diagonal_live.py';assert not dest.exists() or dest.read_text()==s;ast.parse(s);dest.write_text(s);records.append(dict(parent=str(p),parent_sha256=sha(p),path=str(dest),sha256=sha(dest),edits=edits,exact_parent_restoration=True))
# Resolve all local imports and literal auditor references before physical work.
queue=[Path(r['path']) for r in records]+[W/'front_corridor_midpoint_stage_source_binding.py',W/'audit_front_corridor_midpoint_execution.py'];seen=set();missing=[]
while queue:
 p=queue.pop()
 if p in seen:continue
 seen.add(p)
 for n in ast.walk(ast.parse(p.read_text())):
  names=[]
  if isinstance(n,ast.ImportFrom) and n.module and '.' not in n.module:names=[n.module+'.py']
  elif isinstance(n,ast.Import):names=[a.name+'.py' for a in n.names if '.' not in a.name]
  elif isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.endswith('.py') and '/' not in n.value and n.value.startswith(('audit_','front_')):names=[n.value]
  for name in names:
   dest=W/name
   if dest.exists():queue.append(dest)
   elif (W/'staged_front_corridor_midpoint_integrated'/name).is_file():queue.append(W/'staged_front_corridor_midpoint_integrated'/name)
   elif name.startswith(('audit_front_corridor_midpoint','front_corridor_midpoint')):missing.append(str(dest))
assert not missing,missing
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=records,global_replacements=replacements,dependency_files=len(seen),dependency_sha256={str(p):sha(p) for p in sorted(seen)},syntax_passed=True,full_dependency_imports_tested=False,command_bridge_tested=False,full_physical_audit_chain_ready=False,simulation_started=False,training_ready=False,generator_sha256=sha(__file__))
with (W/'FRONT_CORRIDOR_MIDPOINT_AUDIT_FAMILY_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(modules=len(records),dependency_files=len(seen),missing=missing,physical_started=False)))
