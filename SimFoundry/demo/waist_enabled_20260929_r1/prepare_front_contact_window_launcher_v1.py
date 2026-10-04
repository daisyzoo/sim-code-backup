"""Derive matched window launcher/closure; prepare only, never start physics."""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;P=W/'front_contact_window_physical_preparation_r1';D=W/'front_contact_window_preparation_r2';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();mapping=read(P/'REVIEW_AND_WATCHER_PREPARATION.json')['replacements'];mapping=[('staged_front_loaded_z_quarter_v1','staged_front_contact_window_v2'),('front_loaded_z_quarter_preparation_r1','front_contact_window_preparation_r2'),*mapping]
def remap(t):
 for a,b in mapping:t=t.replace(a,b)
 return t
old=W/'run_front_loaded_z_quarter_trial2_physical_r2.py';new=W/'run_front_contact_window_trial1_physical_r2.py';text=remap(old.read_text());edits=[]
def edit(a,b):
 global text
 assert text.count(a)==1,(a[:100],text.count(a));text=text.replace(a,b);edits.append(dict(old=a,new=b))
edit("PREVIOUS=W/'front_corridor_lateral_physical_r1'","PREVIOUS=W/'front_loaded_z_quarter_physical_r2'")
edit(text.splitlines()[0], '"""Matched8push2wait window experiment: original224 audits plus10 window audits.')
checks=['COLLECTOR_WIRING_CHECK.json','NATIVE_LOADED_BOUT_CHECK_V4.json','CHANGED_JOINT_CHAIN_CHECK_V1.json','INDEPENDENT_LOADED_RECORD_AUDIT_V2.json','SOURCE_BINDING_CHECK_V3.json','NATIVE_LIFECYCLE_CHECK_V3.json','FULL_PARENT_LOSS_LIFECYCLE_CHECK_V2.json','OBSERVATION_STREAM_CHECK_V1.json','AUDIT_FAMILY_IMPORT_INVENTORY_CHECK_V2.json','NATIVE_WAIT_ENABLED_CHECK_V2.json','NATIVE_WAIT_DISABLED_CHECK_V2.json','NATIVE_FRONT_DEFAULTOFF_CHECK_V1.json','NATIVE_FRONT_ENABLED_CHECK_V1.json']
edit(next(l for l in text.splitlines() if l.startswith('CHECKS=')),'CHECKS='+repr(checks))
start=text.index('def configuration():');end=text.index('\ndef parent_readiness():',start);previous=text[start:end]
new_config='''def configuration():
 plan=read(P/'PLAN.json');assert plan['status']=='prepared_not_launched' and not plan['simulation_started'] and not plan['training_ready']
 assert plan['collector']==str(S/'collect_paired_sorting.py') and sha(plan['collector'])==plan['collector_sha256']
 assert plan['parent_run']==str(PREVIOUS) and sha(plan['parent_protocol'])==plan['parent_protocol_sha256']
 parent=read(PREVIOUS/'PROTOCOL.json');old=parent['plan'];assert plan['groups']==old['groups'] and len(plan['commands'])==6 and sum(len(c['tasks']) for c in plan['commands'])==10
 from prepare_closed_peak_trial import parser_namespace
 from simfoundry.data.waist_pilot_protocol import semantic_settings
 sources=dict(parent['frozen_files_sha256']);bound(sources);used,prep_sources=verify_preparation();assert len(used)==98;sources.update(prep_sources)
 for item,original in zip(plan['commands'],old['commands']):
  args=item['args'];expected=list(original['args']);expected[expected.index('--out-dir')+1]=args[args.index('--out-dir')+1];expected.append('--front-contact-window');assert item==dict(original,args=expected)
  assert args.count('--joint-transport-clearance')==1 and '--inactive-transport-clearance' not in args and '--push-assist' not in args
  parsed,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True)
  prelaunch=dict(parsed);assert prelaunch.pop('front_contact_window') is True;assert prelaunch.pop('front_loaded_z_quarter') is True;assert prelaunch.pop('front_corridor_lateral_replan') is True;assert prelaunch.pop('joint_transport_clearance') is True and prelaunch.pop('inactive_transport_clearance') is False and prelaunch.pop('front_box_recenter') is True
  settings=semantic_settings(prelaunch)
  for key in ['front_recontact_center_landing','front_corridor_midpoint_replan','front_loaded_z_priority','front_initial_center_landing','terminal_release_margin','edge_clearance_intersection']:assert settings.pop(key) is True
  assert settings==read(W/'staged_closed_peak_trial/TRIAL_PROFILE.json')['prelaunch_settings']
  assert parsed['steps']==1200 and parsed['wait_steps']==70 and parsed['role']=='diagnostic' and parsed['motion_protocol']=='waist_yaw_enabled_v1'
  if not item['wait']:
   path=Path(args[args.index('--diagnostic-layout-json')+1]);assert sha(path)==item['layout_sha256'];sources[str(path)]=sha(path)
 for name in CHECKS:
  path=D/name;r=read(path);assert r['passed'] is True,name;bound(r['source_sha256']);sources.update(r['source_sha256']);sources[str(path)]=sha(path)
 path=D/'AUDIT_FAMILY_PREPARATION.json';r=read(path);bound(r['source_sha256']);sources.update(r['source_sha256']);sources[str(path)]=sha(path)
 for row in r['adapters']+[r['source_binding']]:
  assert sha(row['parent'])==row['parent_sha256'] and sha(row['path'])==row['sha256'];sources[row['parent']]=row['parent_sha256'];sources[row['path']]=row['sha256']
 inventory=read(D/'AUDIT_FAMILY_IMPORT_INVENTORY_CHECK_V2.json')['inventory'];assert len(inventory)==10 and sum(x['original_count'] for x in inventory)==224 and sum(x['new_count'] for x in inventory)==234
 for row in inventory:
  assert row['scripts'].count('audit_front_contact_window_stream_v1.py')==1
  for name in row['scripts']:sources[str(W/name)]=sha(W/name)
 from watch_front_contact_window_trial1_numeric_reviews_r2 import check
 numeric=check();assert numeric['passed'];sources.update(numeric['source_sha256'])
 dest=P/'CONFIGURATION_CHECK.json'
 paths=list(read(dest)['source_sha256']) if dest.exists() else [Path(__file__),*[Path(r['path']) for r in read(P/'REVIEW_AND_WATCHER_PREPARATION.json')['files']],W/'close_front_contact_window_trial1_physical_v1.py',P/'LAUNCHER_DERIVATION.json',*[S/n for n in used]]
 for path in [*paths,Path(__file__),P/'PLAN.json',P/'REVIEW_AND_WATCHER_PREPARATION.json',PREVIOUS/'PROTOCOL.json']:sources[str(path)]=sha(path)
 result=dict(passed=True,conditions=10,original_audits=224,additional_window_audits=10,expected_audits=234,direct_parent=str(PREVIOUS),source_sha256=sources,simulation_started=False,training_ready=False)
 if dest.exists():assert read(dest)==result
 else:
  with dest.open('x') as f:json.dump(result,f,indent=2)
 return plan,result
'''
edit(previous,new_config)
edit("str(W/'watch_front_corridor_lateral_trial1_physical_audits_r1.py')","str(W/'watch_front_loaded_z_quarter_trial2_physical_audits_r2.py')")
edit("rear=W/'front_box_trailing_physical_r2'","rear=W/'rear_early_edge_physical_r1'")
restored=text
for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
for a,b in reversed(mapping):restored=restored.replace(b,a)
assert restored==old.read_text();ast.parse(text)
with new.open('x') as f:f.write(text)
old_close=W/'close_front_loaded_z_quarter_trial2_physical_v1.py';new_close=W/'close_front_contact_window_trial1_physical_v1.py';ct=remap(old_close.read_text());ce=[]
for a,b in [('front_corridor_lateral_physical_r1','front_loaded_z_quarter_physical_r2'),('len(all_rows)==224','len(all_rows)==234'),("comparison_role='quarter_z_against_lateral_parent'","comparison_role='contact_window_against_quarter_parent'")]:
 assert a in ct,a;ct=ct.replace(a,b);ce.append([a,b])
restored=ct
for a,b in reversed(ce):restored=restored.replace(b,a)
for a,b in reversed(mapping):restored=restored.replace(b,a)
assert restored==old_close.read_text();ast.parse(ct)
with new_close.open('x') as f:f.write(ct)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,launcher_parent=str(old),launcher_parent_sha256=sha(old),launcher=str(new),launcher_sha256=sha(new),closure_parent=str(old_close),closure_parent_sha256=sha(old_close),closure=str(new_close),closure_sha256=sha(new_close),replacements=mapping,launcher_edits=edits,closure_edits=ce,inverse_checked=True,source_sha256={str(p):sha(p) for p in [Path(__file__),P/'PLAN.json',P/'REVIEW_AND_WATCHER_PREPARATION.json']},physical_started=False,configuration_pending=True,training_ready=False)
with (P/'LAUNCHER_DERIVATION.json').open('x') as f:json.dump(out,f,indent=2)
print('LAUNCHER_AND_CLOSURE_PREPARED_NOT_EXECUTED')
