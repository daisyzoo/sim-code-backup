"""New names for existing audit family; only semantic profile changes2mm to1mm.
Runtime collector, source stage and all audit mathematics/thresholds unchanged.
No completed report or frozen source is overwritten.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;P=W/'front_drive_1mm_preparation_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
replacements=[('front_corridor_midpoint_stage','front_drive_1mm_stage'),('FRONT_CORRIDOR_MIDPOINT_STAGE','FRONT_DRIVE_1MM_STAGE'),('audit_front_corridor_midpoint_initial_live','audit_front_drive_1mm_initial_live'),('audit_front_corridor_midpoint_z_execution','audit_front_drive_1mm_z_execution'),('FRONT_CORRIDOR_MIDPOINT_Z_EXECUTION_AUDIT','FRONT_DRIVE_1MM_Z_EXECUTION_AUDIT'),('audit_front_corridor_midpoint_execution','audit_front_drive_1mm_execution'),('FRONT_CORRIDOR_MIDPOINT_EXECUTION_AUDIT','FRONT_DRIVE_1MM_EXECUTION_AUDIT'),('audit_front_corridor_midpoint_diagonal_live','audit_front_drive_1mm_diagonal_live'),('FRONT_CORRIDOR_MIDPOINT_DIAGONAL_LIVE_AUDIT','FRONT_DRIVE_1MM_DIAGONAL_LIVE_AUDIT')]
def rename(s):
 for a,b in replacements:s=s.replace(a,b)
 return s
old=json.loads((W/'FRONT_CORRIDOR_MIDPOINT_AUDIT_FAMILY_PREPARATION.json').read_text());parents=[Path(x['path']) for x in old['adapters']]+[W/'front_corridor_midpoint_stage_source_binding.py',W/'audit_front_corridor_midpoint_execution.py',W/'audit_front_corridor_midpoint_z_execution.py'];assert len(set(parents))==len(parents)
records=[]
for p in parents:
 s=rename(p.read_text());edits=[]
 if p.name=='front_corridor_midpoint_stage_source_binding.py':
  a="W/'staged_closed_peak_trial/TRIAL_PROFILE.json'";b="W/'front_drive_1mm_preparation_r1/TRIAL_PROFILE.json'";assert s.count(a)==1;s=s.replace(a,b);edits.append(dict(old=a,new=b))
 dest=W/rename(p.name);assert dest!=p and not dest.exists();ast.parse(s)
 rev=s
 for e in reversed(edits):assert rev.count(e['new'])==1;rev=rev.replace(e['new'],e['old'])
 assert rev==rename(p.read_text());dest.write_text(s);records.append(dict(parent=str(p),parent_sha256=sha(p),path=str(dest),sha256=sha(dest),edits=edits,exact_declared_diff=True))
queue=[Path(x['path']) for x in records];seen=set();missing=[]
while queue:
 p=queue.pop()
 if p in seen:continue
 seen.add(p)
 for n in ast.walk(ast.parse(p.read_text())):
  names=[]
  if isinstance(n,ast.ImportFrom) and n.module and '.' not in n.module:names=[n.module+'.py']
  elif isinstance(n,ast.Import):names=[a.name+'.py' for a in n.names if '.' not in a.name]
  elif isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.endswith('.py') and '/' not in n.value:names=[n.value]
  for name in names:
   dst=W/name
   if dst.exists():queue.append(dst)
   elif (W/'staged_front_corridor_midpoint_integrated'/name).is_file():queue.append(W/'staged_front_corridor_midpoint_integrated'/name)
   elif 'front_drive_1mm' in name:missing.append(name)
assert not missing,missing
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=records,global_replacements=replacements,dependency_sha256={str(p):sha(p) for p in sorted(seen)},source_sha256={str(p):sha(p) for p in [Path(__file__),P/'PLAN.json',P/'TRIAL_PROFILE.json',W/'FRONT_CORRIDOR_MIDPOINT_AUDIT_FAMILY_PREPARATION.json']},syntax_passed=True,missing_dependencies=missing,full_dependency_imports_tested=False,source_contract_executed=False,physics_started=False,training_ready=False)
with (W/'FRONT_DRIVE_1MM_AUDIT_FAMILY_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(modules=len(records),dependencies=len(seen),physics_started=False)))
