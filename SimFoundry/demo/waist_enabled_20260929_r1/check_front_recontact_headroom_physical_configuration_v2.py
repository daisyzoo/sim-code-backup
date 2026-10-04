"""Bind complete matched condition schedule and native checks before real collection.
Prior native/affine fixtures prove wiring only, not new physical success.
"""
from pathlib import Path
import ast,datetime,hashlib,importlib,json,sys
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'front_recontact_headroom_preparation_r1';S=W/'staged_front_recontact_headroom';R=W/'front_corridor_midpoint_physical_r1';sys.path[:0]=[str(W),str(ROOT)]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
from front_recontact_headroom_v3_stage_run_contract import primary,controls,ADDITIONAL,REPORTS
plan=json.loads((P/'PLAN.json').read_text());old=json.loads((R/'PROTOCOL.json').read_text())['plan'];assert plan['groups']==old['groups']
from prepare_closed_peak_trial import parser_namespace
from simfoundry.data.waist_pilot_protocol import semantic_settings
inventory=[];sources={};names=set()
for item,original in zip(plan['commands'],old['commands']):
 args=list(item['args']);expected=list(original['args']);expected[expected.index('--out-dir')+1]=args[args.index('--out-dir')+1];expected+=['--front-recontact-center-landing'];assert item==dict(original,args=expected)
 resolved,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True);settings=semantic_settings(resolved)
 for key in ['front_recontact_center_landing','front_corridor_midpoint_replan','front_loaded_z_priority','front_initial_center_landing','terminal_release_margin','edge_clearance_intersection']:assert settings.pop(key) is True
 assert settings==json.loads((W/'staged_closed_peak_trial/TRIAL_PROFILE.json').read_text())['prelaunch_settings']
 for task in item['tasks']:
  ep=R/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}";scripts=primary(item['wait'])+['audit_front_recontact_headroom_v1_stage_contacts.py','audit_front_recontact_headroom_v1_stage_pressure.py']
  if not item['wait']:
   p=ep/'frontal_bypass.json';sources[str(p)]=sha(p);scripts+=controls(json.loads(p.read_text())['plan'])+ADDITIONAL
  scripts+=['audit_front_recontact_headroom_v1_stage_release.py'];scripts=list(dict.fromkeys(scripts));assert all(n in REPORTS and (W/n).is_file() for n in scripts);names.update(scripts)
  # Compare families to the actual204 parent invocations, allowing only version
  # names and exactly one additional independent recovery-stream entry.
  previous=json.loads((ep/'AUDIT_EXECUTION.json').read_text())['distinct_applicable_audits'];sources[str(ep/'AUDIT_EXECUTION.json')]=sha(ep/'AUDIT_EXECUTION.json')
  def key(n):
   import re
   if n=='audit_front_recontact_headroom_stream.py':return 'new_recontact_stream'
   for prefix in ['audit_front_recontact_headroom_v1_','audit_front_recontact_headroom_v2_','audit_front_recontact_headroom_v3_','audit_front_corridor_midpoint_v2_','audit_front_corridor_midpoint_']:n=n.replace(prefix,'audit_')
   return n
  assert set(map(key,scripts))-{'new_recontact_stream'}==set(map(key,previous)),(ep.name,previous,scripts)
  assert len(scripts)==len(previous)+1
  inventory.append(dict(episode=ep.name,scripts=scripts,count=len(scripts)))
assert len(inventory)==10 and sum(r['count'] for r in inventory)==214
imported=[];static=[]
for name in sorted(names):
 p=W/name;tree=ast.parse(p.read_text());sources[str(p)]=sha(p)
 executable=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.ClassDef))]
 is_cli=any(('sys.argv[' in ast.unparse(n) or '.parse_args(' in ast.unparse(n)) and not (isinstance(n,ast.If) and '__name__' in ast.unparse(n.test)) for n in executable)
 if is_cli:static.append(name)
 else:m=importlib.import_module(p.stem);assert Path(m.__file__).resolve()==p;imported.append(name)
from watch_front_recontact_headroom_numeric_reviews_r1 import check
numeric=check();assert numeric['passed'];sources.update(numeric['source_sha256'])
prep=json.loads((P/'PHYSICAL_PREPARATION.json').read_text())
for row in prep['files']:
 p=Path(row['path']);assert sha(p)==row['sha256'];sources[str(p)]=sha(p);ast.parse(p.read_text())
 assert 'rear_waypoint' not in p.read_text(),p
for name in ['NATIVE_WAIT_CHECK.json','NATIVE_JOINT_BRANCH_CHECK.json']:
 d=json.loads((S/name).read_text());assert d['passed'];sources[str(S/name)]=sha(S/name)
 for p,h in d['source_sha256'].items():assert sha(p)==h,p
for p in [Path(__file__),P/'PLAN.json',P/'PHYSICAL_PREPARATION.json',P/'AUDIT_DEPENDENCIES.json',W/'front_recontact_headroom_v3_stage_run_contract.py']:sources[str(p)]=sha(p)
for p,h in json.loads((P/'AUDIT_DEPENDENCIES.json').read_text())['source_sha256'].items():assert sha(p)==h,p
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,configuration_count=6,condition_count=10,expected_audits=214,original_204_preserved=True,inventory=inventory,actual_imports=imported,cli_ast_only=static,numeric_routing=numeric,source_sha256=sources,ready_for_physical_preflight=True,simulation_started=False,training_ready=False)
with (P/'CONFIGURATION_SOURCE_AUDIT_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,conditions=10,audits=214,imports=len(imported),cli_ast=len(static),simulation_started=False)))
