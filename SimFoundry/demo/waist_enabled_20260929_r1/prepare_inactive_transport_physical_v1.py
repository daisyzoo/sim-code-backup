"""Prepare full matched8push2wait transport experiment; no launch.
Original214 audits plus10 transport audits, all old gates and closures retained.
New recursive post-intervention physical behavior is intentionally not presumed.
"""
from pathlib import Path
import ast,json,hashlib,datetime,re
W=Path(__file__).resolve().parent;S=W/'staged_inactive_transport_v2';P=W/'inactive_transport_physical_preparation_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert not (P/'PHYSICAL_PREPARATION.json').exists()
family=json.loads((S/'AUDIT_FAMILY_V3_PREPARATION.json').read_text());mapping=dict(family['replacements'])
oldprep=json.loads((W/'front_box_recenter_preparation_r2/PHYSICAL_PREPARATION.json').read_text());names=[Path(r['path']).name for r in oldprep['files']]
for name in names:mapping[name[:-3]]=name[:-3].replace('front_box_recenter_trial2_','inactive_transport_trial1_',1)
mapping.update(front_box_recenter_preparation_r2='inactive_transport_physical_preparation_r1',front_box_recenter_physical_r2='inactive_transport_physical_r1')
pattern=re.compile('|'.join(re.escape(k) for k in sorted(mapping,key=len,reverse=True)));records=[]
new_checks=['PARSER_CHECK.json','NATIVE_HOOK_CHECK.json','INDEPENDENT_RECORD_CHECK.json','SOURCE_BINDING_CHECK.json','NATIVE_WAIT_STREAM_CHECK.json','AUDIT_FAMILY_V3_IMPORT_CHECK.json','PARENT_COMMAND_CHECK.json','FAMILY_NATIVE_WAIT_CHECK.json','NATIVE_REAR_STREAM_CHECK.json','FRONT_PREFIX_CHECK.json']
for n in new_checks:
 d=json.loads((S/n).read_text());assert d['passed']
 for p,h in d['source_sha256'].items():assert sha(p)==h,p
for name in names:
 old=W/name;text=pattern.sub(lambda m:mapping[m.group()],old.read_text());edits=[]
 def change(a,b):
  global text
  assert text.count(a)==1,(name,a[:150],text.count(a));text=text.replace(a,b);edits.append(dict(old=a,new=b))
 if name.startswith('run_') or name.startswith('check_'):
  change("expected+=['--front-recontact-center-landing','--front-box-recenter']","expected+=['--front-recontact-center-landing','--front-box-recenter','--inactive-transport-clearance']")
  change("for key in ['front_box_recenter','front_recontact_center_landing'","for key in ['inactive_transport_clearance','front_box_recenter','front_recontact_center_landing'")
 if name.startswith('run_'):
  change("for flag in ['--front-box-recenter'","for flag in ['--inactive-transport-clearance','--front-box-recenter'")
  change("deps['expected_audits']==214","deps['expected_audits']==224")
  change('original_audits=204,new_recontact_stream_audits=10,total_audits=214','original_audits=214,new_transport_stream_audits=10,total_audits=224')
  tree=ast.parse(old.read_text());lists={t.id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) for t in n.targets if isinstance(t,ast.Name) and t.id in ['CHECKS','MANIFESTS']}
  checks=lists['CHECKS']+['staged_inactive_transport_v2/'+n for n in new_checks]+['inactive_transport_physical_preparation_r1/PLAN_CONFIGURATION_CHECK.json','inactive_transport_physical_preparation_r1/CONFIGURATION_SOURCE_AUDIT_CHECK.json']
  manifests=lists['MANIFESTS']+['staged_inactive_transport_v2/AUDIT_FAMILY_V3_PREPARATION.json','inactive_transport_physical_preparation_r1/PHYSICAL_PREPARATION.json']
  start=text.index('CHECKS=');end=text.index('_cache={}',start);change(text[start:end],'CHECKS='+repr(checks)+'\nMANIFESTS='+repr(manifests)+'\n')
  marker=" from rear_corridor_storage_budget import require_storage\n storage=require_storage(ROOT,plan['commands'])"
  extra=""" matched_transport=W/'front_box_recenter_physical_r2'
 assert sha(plan['matched_box_recenter_protocol'])==plan['matched_box_recenter_protocol_sha256']
 transport_parent=json.loads((matched_transport/'RESULT.json').read_text())
 assert transport_parent['conditions']==10 and transport_parent['audit_invocations']==214 and transport_parent['training_ready'] is False
 bound(transport_parent['source_sha256']);bound(json.loads((matched_transport/'PROTOCOL.json').read_text())['frozen_files_sha256'])
 transport_audit=json.loads((matched_transport/'AUDIT_STATUS.json').read_text());assert transport_audit['status']=='complete' and len(transport_audit['rows'])==214
 transport_visual=json.loads((matched_transport/'NUMERIC_VISUAL_SUMMARY.json').read_text());assert transport_visual['actual_reviews']==10;bound(transport_visual['source_sha256'])
 for pid in [transport_audit['pid'],json.loads((matched_transport/'PROTOCOL.json').read_text())['producer_pid']]:
  path=Path('/proc')/str(pid);assert not path.exists() or (path/'stat').read_text().split()[2]=='Z'
"""
  change(marker,extra+marker)
  marker="storage=storage,runner_sha256=sha(__file__),simulation_started=False"
  change(marker,"storage=storage,transport_parent_closure_sha256=sha(matched_transport/'RESULT.json'),runner_sha256=sha(__file__),simulation_started=False")
  marker="protocol=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),producer_pid=os.getpid()"
  extra="for p in [W/'front_box_recenter_physical_r2/RESULT.json',W/'front_box_recenter_physical_r2/PROTOCOL.json',W/'front_box_recenter_physical_r2/COLLECTION_EXECUTION.json',W/'front_box_recenter_physical_r2/NUMERIC_VISUAL_SUMMARY.json']:frozen[str(p)]=sha(p)\n "
  change(marker,extra+marker)
  change("matched_parent_audits_and_visuals_required_for_comparison=True","matched_transport_parent_protocol_sha256=sha(W/'front_box_recenter_physical_r2/PROTOCOL.json'),matched_parent_audits_and_visuals_required_for_comparison=True")
 if name.startswith('watch_') and 'physical_audits' in name:change("len(all_rows)==214","len(all_rows)==224")
 if name.startswith('close_'):
  change("parent=read(W/'front_recontact_headroom_physical_r1/RESULT.json')","parent=read(W/'front_box_recenter_physical_r2/RESULT.json')")
  change('len(all_rows)==214','len(all_rows)==224')
 if name.startswith('queue_'):
  # Parent queue waits for the exact original watcher of this new run.
  text=text.replace('==214','==224').replace('!=214','!=224')
 if name.startswith('check_'):
  change("if n=='audit_inactive_transport_front_recovery_stream_v3.py':return 'new_recontact_stream'","if n=='audit_inactive_transport_front_recovery_stream_v3.py':return 'new_recontact_stream'\n   if n=='audit_inactive_transport_stream_v2.py':return 'new_transport_stream'")
  change("-{'new_recontact_stream'}","-{'new_recontact_stream','new_transport_stream'}")
  change('len(scripts)==len(previous)+1','len(scripts)==len(previous)+2')
  change("sum(r['count'] for r in inventory)==214","sum(r['count'] for r in inventory)==224")
  change("for name in ['NATIVE_WAIT_CHECK.json','NATIVE_JOINT_BRANCH_CHECK.json']:","for name in ['FAMILY_NATIVE_WAIT_CHECK.json','PARENT_COMMAND_CHECK.json','FRONT_PREFIX_CHECK.json']:")
  change('expected_audits=214','expected_audits=224');change('audits=214','audits=224')
 ast.parse(text);dest=W/(mapping[old.stem]+'.py');assert not dest.exists(),dest
 with dest.open('x') as f:f.write(text)
 records.append(dict(parent=str(old),parent_sha256=sha(old),path=str(dest),sha256=sha(dest),edits=edits))
with (P/'PHYSICAL_PREPARATION.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,files=records,replacements=mapping,source_sha256={str(p):sha(p) for p in [Path(__file__),S/'AUDIT_FAMILY_V3_PREPARATION.json',P/'PLAN.json',P/'PLAN_CONFIGURATION_CHECK.json']},physics_started=False,training_ready=False),f,indent=2)
queue=[Path(r['path']) for r in family['adapters']]+[W/'audit_inactive_transport_stream_v2.py',W/'inactive_transport_stage_source_binding_v2.py',W/'inactive_transport_command_ledger_v2.py'];seen={}
while queue:
 p=queue.pop()
 if str(p) in seen:continue
 seen[str(p)]=sha(p)
 for n in ast.walk(ast.parse(p.read_text())):
  mods=([n.module] if isinstance(n,ast.ImportFrom) and n.module else [a.name for a in n.names] if isinstance(n,ast.Import) else [])
  for module in mods:
   q=W/(module+'.py')
   if q.is_file():queue.append(q)
  if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.endswith('.py') and '/' not in n.value:
   q=W/n.value
   if q.is_file():queue.append(q)
with (P/'AUDIT_DEPENDENCIES.json').open('x') as f:json.dump(dict(source_sha256=seen,missing=[],training_ready=False),f,indent=2)
print(json.dumps(dict(scripts=len(records),audit_dependencies=len(seen),conditions=10,audits=224,physics=False)))
