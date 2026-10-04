"""Prepare matched complete8push2wait right-box recenter trial, without launch.
Only adds the explicit right-box recenter flag to headroom settings. Requires the original
headroom run to close and all new checks/storage/GPU preflight before collection.
"""
from pathlib import Path
import ast,json,hashlib,datetime,re
W=Path(__file__).resolve().parent;S=W/'staged_front_box_recenter_v3';P=W/'front_box_recenter_preparation_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert not P.exists()
family=json.loads((S/'AUDIT_FAMILY_V2_PREPARATION.json').read_text());mapping=dict(family['replacements']);mapping['front_recontact_headroom_v3_stage_run_contract']='front_box_recenter_a2_v4_stage_run_contract'
names=['review_front_recontact_headroom_v1_stage_episode.py','review_front_recontact_headroom_incomplete_episode.py','watch_front_recontact_headroom_numeric_reviews_r1.py','watch_front_recontact_headroom_physical_audits_r1.py','close_front_recontact_headroom_physical.py','queue_front_recontact_headroom_physical_r1_closure.py','summarize_front_recontact_headroom_actual_reviews.py','run_front_recontact_headroom_physical_r1.py','check_front_recontact_headroom_physical_configuration_v3.py']
for n in names:mapping[n[:-3]]=n[:-3].replace('front_recontact_headroom_','front_box_recenter_',1)
mapping.update(front_recontact_headroom_preparation_r1='front_box_recenter_preparation_r1',front_recontact_headroom_physical_r1='front_box_recenter_physical_r1')
pattern=re.compile('|'.join(re.escape(k) for k in sorted(mapping,key=len,reverse=True)));plan=json.loads((W/'front_recontact_headroom_preparation_r1/PLAN.json').read_text());plan['created_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();plan['collector']=str(S/'collect_paired_sorting.py');plan['collector_sha256']=sha(plan['collector']);plan['scope']=__doc__;plan['box_recenter']=json.loads((S/'COLLECTOR_PREPARATION.json').read_text())['box_recenter'];plan['matched_headroom_protocol']=str(W/'front_recontact_headroom_physical_r1/PROTOCOL.json');plan['matched_headroom_protocol_sha256']=sha(plan['matched_headroom_protocol'])
for c in plan['commands']:c['args'][c['args'].index('--out-dir')+1]=str(W/'front_box_recenter_physical_r1'/f"case_{c['layout_id']}");c['args'].append('--front-recontact-right-box recenter')
P.mkdir()
with (P/'PLAN.json').open('x') as f:json.dump(plan,f,indent=2)
records=[]
for name in names:
 old=W/name;text=pattern.sub(lambda m:mapping[m.group()],old.read_text());changes=[]
 def change(a,b):
  global text
  assert a in text,(name,a[:100]);text=text.replace(a,b);changes.append(dict(old=a,new=b))
 if name.startswith('run_') or name.startswith('check_'):
  change("expected+=['--front-recontact-center-landing']","expected+=['--front-recontact-center-landing','--front-recontact-right-box recenter']")
  change("for key in ['front_recontact_center_landing','front_corridor_midpoint_replan'","for key in ['front_box_recenter','front_recontact_center_landing','front_corridor_midpoint_replan'")
 if name.startswith('run_'):
  tree=ast.parse(old.read_text());lists={t.id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) for t in n.targets if isinstance(t,ast.Name) and t.id in ['CHECKS','MANIFESTS']}
  checks=lists['CHECKS']+['staged_front_box_recenter_v3/'+x for x in ['PARSER_CHECK.json','COLLECTOR_HOOK_CHECK.json','DISPATCH_GUARD_CHECK.json','SOURCE_BINDING_CHECK.json','INDEPENDENT_STREAM_CHECK.json','UNCHANGED_STREAMS_CHECK.json','AUDIT_FAMILY_V2_IMPORT_CHECK.json','NATIVE_WAIT_CHECK.json','NATIVE_JOINT_BRANCH_CHECK.json','REFERENCE_LEDGER_CHECK.json','LOADED_INPUT_CHECK.json','NORMAL_CAPTURE_CHECK.json']]+['front_box_recenter_preparation_r1/CONFIGURATION_SOURCE_AUDIT_CHECK.json'];manifests=lists['MANIFESTS']+['staged_front_box_recenter_v3/AUDIT_FAMILY_V2_PREPARATION.json','front_box_recenter_preparation_r1/PHYSICAL_PREPARATION.json']
  start=text.index('CHECKS=');end=text.index('_cache={}',start);change(text[start:end],'CHECKS='+repr(checks)+'\nMANIFESTS='+repr(manifests)+'\n')
  change("for flag in ['--front-recontact-center-landing'","for flag in ['--front-recontact-right-box recenter','--front-recontact-center-landing'")
  marker=' from rear_corridor_storage_budget import require_storage\n storage=require_storage(ROOT,plan[\'commands\'])'
  extra=""" matched=W/'front_recontact_headroom_physical_r1'
 assert sha(plan['matched_headroom_protocol'])==plan['matched_headroom_protocol_sha256']
 closed=json.loads((matched/'RESULT.json').read_text());assert closed['conditions']==10 and closed['audit_invocations']==214 and closed['training_ready'] is False
 bound(closed['source_sha256']);bound(json.loads((matched/'PROTOCOL.json').read_text())['frozen_files_sha256'])
 oldaudit=json.loads((matched/'AUDIT_STATUS.json').read_text());assert oldaudit['status']=='complete' and len(oldaudit['rows'])==214
 oldvisual=json.loads((matched/'NUMERIC_VISUAL_SUMMARY.json').read_text());assert oldvisual['actual_reviews']==10;bound(oldvisual['source_sha256'])
 for pid in [oldaudit['pid'],json.loads((matched/'PROTOCOL.json').read_text())['producer_pid']]:
  path=Path('/proc')/str(pid);assert not path.exists() or (path/'stat').read_text().split()[2]=='Z'
"""
  change(marker,extra+marker)
 if name.startswith('close_'):
  change("parent=read(W/'front_corridor_midpoint_physical_r1/RESULT.json')","parent=read(W/'front_recontact_headroom_physical_r1/RESULT.json')")
 if name.startswith('check_'):
  change("['audit_front_recontact_v1_','audit_front_recontact_v2_','audit_front_recontact_v3_'","['audit_front_box_recenter_a2_v1_','audit_front_box_recenter_a2_v2_','audit_front_box_recenter_a2_v3_'")
 ast.parse(text);dest=W/(mapping[old.stem]+'.py');assert not dest.exists()
 with dest.open('x') as f:f.write(text)
 records.append(dict(parent=str(old),parent_sha256=sha(old),path=str(dest),sha256=sha(dest),edits=changes))
with (P/'PHYSICAL_PREPARATION.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,files=records,replacements=mapping,source_sha256={str(p):sha(p) for p in [Path(__file__),S/'AUDIT_FAMILY_V2_PREPARATION.json',P/'PLAN.json']},physics_started=False,training_ready=False),f,indent=2)
queue=[Path(r['path']) for r in family['adapters']]+[W/'audit_front_box_recenter_stream.py',W/'front_box_recenter_stage_source_binding.py'];seen={}
while queue:
 p=queue.pop()
 if str(p) in seen:continue
 seen[str(p)]=sha(p)
 for n in ast.walk(ast.parse(p.read_text())):
  modules=([n.module] if isinstance(n,ast.ImportFrom) and n.module else [a.name for a in n.names] if isinstance(n,ast.Import) else [])
  for module in modules:
   q=W/(module+'.py')
   if q.is_file():queue.append(q)
  if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.endswith('.py') and '/' not in n.value:
   q=W/n.value
   if q.is_file():queue.append(q)
with (P/'AUDIT_DEPENDENCIES.json').open('x') as f:json.dump(dict(source_sha256=seen,missing=[],training_ready=False),f,indent=2)
print(dict(prepared_scripts=len(records),audit_dependencies=len(seen),conditions=10,physics_started=False))
