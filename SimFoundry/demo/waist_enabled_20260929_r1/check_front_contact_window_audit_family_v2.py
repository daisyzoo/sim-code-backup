"""Import and exact original-inventory preservation check; not native execution.
Uses the actual frozen10-condition plan and recorded route selection per task.
"""
from pathlib import Path
import sys,json,hashlib,datetime,importlib,ast,re
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'front_contact_window_preparation_r2';sys.path[:0]=[str(W),str(ROOT)]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={}
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
prep=read(D/'AUDIT_FAMILY_PREPARATION.json');mapping=prep['replacements'];inverse={v:k for k,v in mapping.items()};pat=re.compile('|'.join(map(re.escape,sorted(mapping,key=len,reverse=True))));rev=re.compile('|'.join(map(re.escape,sorted(inverse,key=len,reverse=True))));imports=[];static=[]
for row in prep['adapters']:
 p=Path(row['path']);parent=Path(row['parent']);assert sha(p)==row['sha256'] and sha(parent)==row['parent_sha256'];text=p.read_text()
 for edit in reversed(row['edits']):assert text.endswith(edit['append']);text=text[:-len(edit['append'])]
 assert rev.sub(lambda m:inverse[m.group()],text)==parent.read_text()
 tree=ast.parse(p.read_text());executable=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.ClassDef))]
 cli=any('sys.argv[' in ast.unparse(n) and not (isinstance(n,ast.If) and '__name__' in ast.unparse(n.test)) for n in executable)
 if cli:compile(tree,str(p),'exec');static.append(p.name)
 else:
  module=importlib.import_module(p.stem);assert Path(module.__file__).resolve()==p;imports.append(p.name)
 for n in ast.walk(tree):
  if isinstance(n,ast.ImportFrom):assert n.module not in mapping,(p.name,n.module)
 sources[str(p)]=sha(p);sources[str(parent)]=sha(parent)
from front_contact_window_stage_source_binding_v2 import verify_preparation
used,bound=verify_preparation();assert len(used)==98;sources.update(bound)
parent=importlib.import_module('front_loaded_z_quarter_r1_v4_stage_run_contract');current=importlib.import_module('front_window_r1_v4_stage_run_contract')
extra='audit_front_contact_window_stream_v1.py';assert current.REPORTS[extra]==('FRONT_CONTACT_WINDOW_STREAM_AUDIT_V1.json',('passed',))
protocol=read(W/'front_loaded_z_quarter_physical_r2/PROTOCOL.json');inventory=[];old_total=new_total=0
for command in protocol['plan']['commands']:
 for task in command['tasks']:
  ep=W/'front_loaded_z_quarter_physical_r2'/f"case_{command['layout_id']}"/f"layout_{command['layout_id']}_{task}";wait=command['wait'];plan={} if wait else read(ep/'frontal_bypass.json')['plan']
  original=parent.primary(wait)+['audit_front_loaded_z_quarter_r1_v1_stage_contacts.py','audit_front_loaded_z_quarter_r1_v1_stage_pressure.py']
  if not wait:original+=parent.controls(plan)+parent.ADDITIONAL
  original+=['audit_front_loaded_z_quarter_r1_v1_stage_release.py'];original=list(dict.fromkeys(original))
  proposed=current.primary(wait)+['audit_front_window_r1_v1_stage_contacts.py','audit_front_window_r1_v1_stage_pressure.py']
  if not wait:proposed+=current.controls(plan)+current.ADDITIONAL
  proposed+=['audit_front_window_r1_v1_stage_release.py'];proposed=list(dict.fromkeys(proposed))
  expected=[pat.sub(lambda m:mapping[m.group()],name) for name in original]
  assert [x for x in proposed if x!=extra]==expected and proposed.count(extra)==1
  reports=[]
  for script in proposed:
   assert (W/script).is_file() and script in current.REPORTS;reports.append(current.REPORTS[script][0]);sources[str(W/script)]=sha(W/script)
  assert len(set(reports))==len(reports),('report collision',ep.name)
  old_total+=len(original);new_total+=len(proposed);inventory.append(dict(episode=ep.name,wait=wait,front=bool(plan.get('front_route_selected')),original_count=len(original),new_count=len(proposed),scripts=proposed))
assert len(inventory)==10 and old_total==224 and new_total==234
for p,h in sources.items():assert sha(p)==h,p
sources[str(Path(__file__))]=sha(__file__);sources[str(W/'audit_front_contact_window_stream_v1.py')]=sha(W/'audit_front_contact_window_stream_v1.py')
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,imported_modules=imports,top_level_cli_ast_checks=static,original_invocations=old_total,additional_window_invocations=10,total_invocations=new_total,inventory=inventory,source_sha256=sources,native_execution_checked=False,physical_launch_ready=False,training_ready=False)
with (D/'AUDIT_FAMILY_IMPORT_INVENTORY_CHECK_V2.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,imports=len(imports),static_cli=len(static),conditions=10,original=old_total,additional=10,total=new_total)))
