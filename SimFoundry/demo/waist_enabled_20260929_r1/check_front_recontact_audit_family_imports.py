"""Syntax/import/inventory checks for candidate audit family, not readiness.
External loaded-height capture reader still needs versioned recovery adaptation.
"""
from pathlib import Path
import ast,datetime,hashlib,importlib,json,sys
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_center';sys.path[:0]=[str(W),str(ROOT)]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((S/'AUDIT_FAMILY_PREPARATION.json').read_text());imports=[];static=[]
for r in prep['adapters']:
 p=Path(r['path']);assert sha(p)==r['sha256'];tree=ast.parse(p.read_text());back=p.read_text()
 for e in reversed(r['edits']):assert back.count(e['new'])==1;back=back.replace(e['new'],e['old'],1)
 original=Path(r['parent']).read_text();assert sha(r['parent'])==r['parent_sha256']
 for a,b in prep['global_replacements']:original=original.replace(a,b)
 assert back==original
 # Older audit CLIs execute at module level; inspect their complete AST only.
 executable=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.ClassDef))]
 is_cli=any('sys.argv[' in ast.unparse(n) and not (isinstance(n,ast.If) and '__name__' in ast.unparse(n.test)) for n in executable)
 if is_cli:static.append(p.name);continue
 m=importlib.import_module(p.stem);assert Path(m.__file__).resolve()==p;imports.append(p.name)
from front_recontact_v1_stage_run_contract import primary,controls,ADDITIONAL,REPORTS
plan=json.loads((W/'front_corridor_midpoint_physical_r1/PROTOCOL.json').read_text())['plan'];all_rows=[]
for c in plan['commands']:
 for task in c['tasks']:
  ep=W/'front_corridor_midpoint_physical_r1'/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}"
  scripts=primary(c['wait'])+['audit_front_recontact_v1_stage_contacts.py','audit_front_recontact_v1_stage_pressure.py']
  if not c['wait']:scripts+=controls(json.loads((ep/'frontal_bypass.json').read_text())['plan'])+ADDITIONAL
  scripts+=['audit_front_recontact_v1_stage_release.py'];scripts=list(dict.fromkeys(scripts))
  assert all(n in REPORTS and (W/n).is_file() for n in scripts)
  all_rows.append(dict(episode=ep.name,wait=c['wait'],scripts=scripts,count=len(scripts)))
assert len(all_rows)==10 and sum(r['count'] for r in all_rows)==214
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,actual_imports=imports,top_level_cli_ast_checks=static,inventory=all_rows,source_sha256={str(p):sha(p) for p in [Path(__file__),S/'AUDIT_FAMILY_PREPARATION.json',*[Path(r['path']) for r in prep['adapters']]]},known_remaining_gap='front_loaded_z_priority_episode_inputs.EpisodeInputs.arguments uses only first capture; recovery center and initial-fallback selection must use independently verified recovery history before physical launch.',full_audit_family_ready=False,simulation_started=False,training_ready=False)
with (S/'AUDIT_FAMILY_IMPORT_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,imports=len(imports),static_cli=len(static),conditions=10,audits=214,ready=False)))
