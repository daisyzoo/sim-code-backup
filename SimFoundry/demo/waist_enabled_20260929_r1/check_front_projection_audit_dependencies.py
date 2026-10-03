"""Verify selected audit entry points, recursively local imports and script literals.
Includes subprocess audit filenames at every traversed level, unlike the previous
entry-point-only inventory. Records dynamic dispatch sites for explicit review;
static discovery is not a claim that arbitrary Python paths were executed.
"""
from pathlib import Path
import ast,datetime,hashlib,json,sys
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_loaded_projection';sys.path[:0]=[str(W),str(ROOT)]
from front_projection_stage_run_contract import primary,controls,ADDITIONAL,REPORTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();c=W/'front_initial_physical_r1';protocol=json.loads((c/'PROTOCOL.json').read_text());entries=set();cases=[]
for item in protocol['plan']['commands']:
 for task in item['tasks']:
  ep=c/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}";scripts=primary(item['wait'])+['audit_front_projection_stage_contacts.py','audit_front_projection_stage_pressure.py']
  if not item['wait']:scripts+=controls(json.loads((ep/'frontal_bypass.json').read_text())['plan'])+ADDITIONAL
  scripts+=['audit_front_projection_stage_release.py'];scripts=list(dict.fromkeys(scripts));assert all(s in REPORTS for s in scripts);entries.update(W/s for s in scripts);cases.append(dict(episode=ep.name,wait=item['wait'],scripts=scripts))
entries.add(W/'front_projection_stage_run_contract.py');entries.add(W/'audit_front_projection_initial_live.py')
queue=list(entries);seen={};edges=[];missing=[];external=set();dispatch=[]
# Include all known geometry helper roots used by retained independent auditors.
roots=[W,S,ROOT,W/'staged_contact_patch_approach',W/'staged_self_clearance_route',W/'staged_rear_short_recovery']
while queue:
 p=queue.pop().resolve()
 if str(p) in seen:continue
 if not p.is_file():missing.append(str(p));continue
 tree=ast.parse(p.read_text());seen[str(p)]=sha(p)
 for node in ast.walk(tree):
  names=[]
  if isinstance(node,ast.ImportFrom) and node.module:names=[node.module]
  if isinstance(node,ast.Import):names=[x.name for x in node.names]
  for name in names:
   relative=Path(*name.split('.'));resolved=[]
   for root in roots:
    for candidate in [root/relative.with_suffix('.py'),root/relative/'__init__.py']:
     if candidate.is_file():resolved.append(candidate.resolve())
   if resolved:
    # Bind every matching local implementation rather than silently choose the
    # wrong duplicate when a module changes sys.path before importing.
    for child in dict.fromkeys(resolved):edges.append(dict(parent=str(p),kind='local_import',name=name,path=str(child)));queue.append(child)
   else:external.add(name)
  if isinstance(node,ast.Constant) and isinstance(node.value,str):
   value=node.value
   if value.endswith('.py') and value.startswith('audit_') and '/' not in value and '\n' not in value:
    child=W/value;edges.append(dict(parent=str(p),kind='audit_script_literal',name=value,path=str(child)));queue.append(child)
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='subprocess':
   dispatch.append(dict(path=str(p),line=node.lineno,call=ast.unparse(node)[:1400]))
# The formerly omitted full five-level region chain must be reachable, not only present.
for suffix in ['action','causal','continuity','bounds']:
 assert str(W/f'audit_front_projection_stage_region_{suffix}.py') in seen,suffix
assert str(W/'audit_front_projection_stage_rear_xy.py') in seen
assert not (W/'audit_front_initial_stage_region_causal.py').exists()
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=not missing,conditions=len(cases),expected_audit_invocations=sum(len(c['scripts']) for c in cases),entry_scripts=len(entries),local_files_checked=len(seen),missing=sorted(set(missing)),cases=cases,edges=edges,source_sha256=seen,external_imports=sorted(external),subprocess_dispatch_sites=dispatch,python_dynamic_execution_not_proven=True,simulation_started=False,training_ready=False)
out=W/'FRONT_PROJECTION_AUDIT_DEPENDENCIES_CHECK.json';assert not out.exists();out.write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['cases','edges','source_sha256','scope','subprocess_dispatch_sites','external_imports']},indent=2));print('subprocess sites',len(dispatch));assert not missing,missing
