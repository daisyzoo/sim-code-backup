"""New names for existing audit family; only semantic profile changes2mm to1mm.
Runtime controller mathematics and all thresholds unchanged; new CLI-only stage explicitly bound.
No completed report or frozen source is overwritten.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;P=W/'front_drive_1mm_preparation_r2';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
replacements=[('staged_front_corridor_midpoint_integrated','staged_front_drive_1mm'),('front_corridor_midpoint_stage','front_drive_1mm_v2_stage'),('FRONT_CORRIDOR_MIDPOINT_STAGE','FRONT_DRIVE_1MM_V2_STAGE'),('audit_front_corridor_midpoint_initial_live','audit_front_drive_1mm_v2_initial_live'),('audit_front_corridor_midpoint_z_execution','audit_front_drive_1mm_v2_z_execution'),('FRONT_CORRIDOR_MIDPOINT_Z_EXECUTION_AUDIT','FRONT_DRIVE_1MM_V2_Z_EXECUTION_AUDIT'),('audit_front_corridor_midpoint_execution','audit_front_drive_1mm_v2_execution'),('FRONT_CORRIDOR_MIDPOINT_EXECUTION_AUDIT','FRONT_DRIVE_1MM_V2_EXECUTION_AUDIT'),('audit_front_corridor_midpoint_diagonal_live','audit_front_drive_1mm_v2_diagonal_live'),('FRONT_CORRIDOR_MIDPOINT_DIAGONAL_LIVE_AUDIT','FRONT_DRIVE_1MM_V2_DIAGONAL_LIVE_AUDIT')]
def rename(s):
 for a,b in replacements:s=s.replace(a,b)
 return s
old=json.loads((W/'FRONT_CORRIDOR_MIDPOINT_AUDIT_FAMILY_PREPARATION.json').read_text());parents=[Path(x['path']) for x in old['adapters']]+[W/'front_corridor_midpoint_stage_source_binding.py',W/'audit_front_corridor_midpoint_execution.py',W/'audit_front_corridor_midpoint_z_execution.py'];assert len(set(parents))==len(parents)
records=[]
for p in parents:
 s=rename(p.read_text());edits=[]
 if p.name=='front_corridor_midpoint_stage_source_binding.py':
  original=s[s.index('def verify_preparation():'):s.index('def verify_trial_provenance(case):')]
  replacement="""def verify_preparation():
 from front_corridor_midpoint_stage_source_binding import verify_preparation as verify_parent
 old_sources,parent_bound=verify_parent()
 prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());parent=Path(prep['parent_stage']);assert parent==W/'staged_front_corridor_midpoint_integrated'
 for p,h in prep['source_sha256'].items():assert sha(p)==h,p
 expected=prep['stage_sha256'];assert len(expected)==71 and set(expected)==set(old_sources)
 for n,h in expected.items():assert sha(S/n)==h,n
 assert {n for n in expected if expected[n]!=old_sources[n]}=={'collect_paired_sorting.py'}
 restored=(S/'collect_paired_sorting.py').read_text()
 for e in reversed(prep['edits']):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert restored==(parent/'collect_paired_sorting.py').read_text()
 check=json.loads((S/'CLI_PARAMETER_CHECK.json').read_text());assert check['passed'] and check['original2mm_parser_semantics_identical'] and check['exact_cli_only_reverse_restore']
 for p,h in check['source_sha256'].items():assert sha(p)==h,p
 parent_bound.update({str(S/'COLLECTOR_PREPARATION.json'):sha(S/'COLLECTOR_PREPARATION.json'),str(S/'CLI_PARAMETER_CHECK.json'):sha(S/'CLI_PARAMETER_CHECK.json')})
 return expected,parent_bound

"""
  assert s.count(original)==1;s=s.replace(original,replacement);edits.append(dict(old=original,new=replacement))
  old_reports="REPORTS=['COLLECTOR_WIRING_CHECK.json','INDEPENDENT_RECORD_CHECK.json','CONTINUOUS_OBSERVATION_CHECK.json','CONTINUOUS_COP_CHECK.json']";new_reports="REPORTS=['CLI_PARAMETER_CHECK.json']";assert s.count(old_reports)==1;s=s.replace(old_reports,new_reports);edits.append(dict(old=old_reports,new=new_reports))
  a="S / 'COLLECTOR_WIRING_CHECK.json'";b="S / 'CLI_PARAMETER_CHECK.json'";assert s.count(a)==1;s=s.replace(a,b);edits.append(dict(old=a,new=b))
  a="W/'staged_closed_peak_trial/TRIAL_PROFILE.json'";b="W/'front_drive_1mm_preparation_r2/TRIAL_PROFILE.json'";assert s.count(a)==1;s=s.replace(a,b);edits.append(dict(old=a,new=b))
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
   elif 'front_drive_1mm_v2' in name:missing.append(name)
assert not missing,missing
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=records,global_replacements=replacements,dependency_sha256={str(p):sha(p) for p in sorted(seen)},source_sha256={str(p):sha(p) for p in [Path(__file__),P/'PLAN.json',P/'TRIAL_PROFILE.json',W/'FRONT_CORRIDOR_MIDPOINT_AUDIT_FAMILY_PREPARATION.json']},syntax_passed=True,missing_dependencies=missing,full_dependency_imports_tested=False,source_contract_executed=False,physics_started=False,training_ready=False)
with (W/'FRONT_DRIVE_1MM_V2_AUDIT_FAMILY_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(modules=len(records),dependencies=len(seen),physics_started=False)))
