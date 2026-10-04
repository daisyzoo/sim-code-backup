"""Verify inverse-identical audit adapters and full214 inventory per original case.
Audit import and inventory evidence alone is not a successful physical trial.
"""
from pathlib import Path
import ast,datetime,hashlib,importlib,json,re,sys
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_joint_transport_reserve_v1';D=W/'joint_transport_reserve_preparation_r1';sys.path[:0]=[str(W),str(ROOT)]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((D/'AUDIT_FAMILY_V2_PREPARATION.json').read_text());mapping=prep['replacements'];inverse={v:k for k,v in mapping.items()};pattern=re.compile('|'.join(re.escape(k) for k in sorted(inverse,key=len,reverse=True)));imports=[];static=[]
for r in prep['adapters']:
 p=Path(r['path']);parent=Path(r['parent']);assert sha(p)==r['sha256'] and sha(parent)==r['parent_sha256'];text=p.read_text()
 for e in reversed(r['edits']):
  assert text.count(e['new'])==1;text=text.replace(e['new'],e['old'])
 assert pattern.sub(lambda m:inverse[m.group()],text)==parent.read_text()
 tree=ast.parse(p.read_text());executable=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.ClassDef))]
 cli=any('sys.argv[' in ast.unparse(n) and not (isinstance(n,ast.If) and '__name__' in ast.unparse(n.test)) for n in executable)
 if cli:static.append(p.name)
 else:
  m=importlib.import_module(p.stem);assert Path(m.__file__).resolve()==p;imports.append(p.name)
 # Every direct dependency on the changed family must point to the new version.
 for n in ast.walk(tree):
  if isinstance(n,ast.ImportFrom):assert n.module not in mapping,(p.name,n.module)
for r in prep['shared_unchanged_adapters']:
 assert sha(r['path'])==r['sha256'] and sha(r['parent'])==r['parent_sha256']
from joint_transport_reserve_r2_v4_stage_run_contract import primary,controls,ADDITIONAL,REPORTS
from joint_transport_reserve_r1_v4_stage_run_contract import primary as old_primary,controls as old_controls,ADDITIONAL as old_additional,REPORTS as old_reports
plan=json.loads((W/'front_corridor_midpoint_physical_r1/PROTOCOL.json').read_text())['plan'];records=[]
for c in plan['commands']:
 for task in c['tasks']:
  ep=W/'front_corridor_midpoint_physical_r1'/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}";fp={} if c['wait'] else json.loads((ep/'frontal_bypass.json').read_text())['plan']
  def scripts(pr,ct,ad,prefix):
   rows=pr(c['wait'])+[f'audit_{prefix}_v1_stage_contacts.py',f'audit_{prefix}_v1_stage_pressure.py']
   if not c['wait']:rows+=ct(fp)+ad
   return list(dict.fromkeys(rows+[f'audit_{prefix}_v1_stage_release.py']))
  old=scripts(old_primary,old_controls,old_additional,'joint_transport_reserve_r1');new=scripts(primary,controls,ADDITIONAL,'joint_transport_reserve_r2')
  expected=[mapping.get(n[:-3],n[:-3])+'.py' for n in old];assert new==expected
  for a,b in zip(old,new):
   assert b in REPORTS and (W/b).exists();on,ok=old_reports[a];nn,nk=REPORTS[b];assert ok==nk
  records.append(dict(episode=ep.name,wait=c['wait'],scripts=new,count=len(new),same_checks_as_parent=True))
assert len(records)==10 and sum(r['count'] for r in records)==224
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,actual_imports=imports,top_level_cli_ast_checks=static,inventory=records,source_sha256={str(p):sha(p) for p in [Path(__file__),D/'AUDIT_FAMILY_V2_PREPARATION.json',*[Path(r['path']) for r in prep['adapters']+prep['shared_unchanged_adapters']],W/'joint_transport_parent_coordinate_v1.py']},full_audit_family_ready=False,simulation_started=False,training_ready=False)
with (D/'AUDIT_FAMILY_V2_IMPORT_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,imports=len(imports),static_cli=len(static),conditions=10,audits=224)))
