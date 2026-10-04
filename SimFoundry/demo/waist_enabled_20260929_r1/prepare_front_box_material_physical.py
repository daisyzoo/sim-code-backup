"""Prepare full matched eight-push/two-wait finite-preload diagnostic; no launch.
Only new default-off finite-preload flag changes against the closed2mm midpoint
parent. Preserve all original controls, source gates, cases and denominators.
"""
from pathlib import Path
import ast,copy,datetime,hashlib,json,re
W=Path(__file__).resolve().parent;S=W/'staged_front_box_material_preload';P=W/'front_box_material_physical_preparation_r1';R=W/'front_box_material_physical_r1';PREVIOUS=W/'front_corridor_midpoint_physical_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
P.mkdir(exist_ok=False);parent=json.loads((PREVIOUS/'PROTOCOL.json').read_text());plan=copy.deepcopy(parent['plan'])
for item in plan['commands']:
 a=item['args'];a[a.index('--out-dir')+1]=str(R/f"case_{item['layout_id']}");assert '--front-box-material-preload' not in a;a.append('--front-box-material-preload')
plan.update(status='prepared_not_launched',collector=str(S/'collect_paired_sorting.py'),collector_sha256=sha(S/'collect_paired_sorting.py'),parent_protocol=str(PREVIOUS/'PROTOCOL.json'),parent_protocol_sha256=sha(PREVIOUS/'PROTOCOL.json'),simulation_started=False,training_ready=False,scope=__doc__)
with (P/'PLAN.json').open('x') as f:json.dump(plan,f,indent=2)
mapping=dict(json.loads((S/'AUDIT_FAMILY_PREPARATION.json').read_text())['replacements'])
mapping.update(front_corridor_midpoint_physical_preparation_r1='front_box_material_physical_preparation_r1',front_corridor_midpoint_physical_r1='front_box_material_physical_r1',run_front_corridor_midpoint_physical='run_front_box_material_physical',watch_front_corridor_midpoint_physical_audits='watch_front_box_material_physical_audits',watch_front_corridor_midpoint_numeric_reviews='watch_front_box_material_numeric_reviews',review_front_corridor_midpoint_stage_episode='review_front_box_material_v1_stage_episode',review_front_corridor_midpoint_incomplete_episode='review_front_box_material_incomplete_episode',close_front_corridor_midpoint_physical='close_front_box_material_physical',queue_front_corridor_midpoint_physical_closure='queue_front_box_material_physical_closure',FRONT_CORRIDOR_MIDPOINT_INCOMPLETE='FRONT_BOX_MATERIAL_INCOMPLETE',FRONT_CORRIDOR_MIDPOINT_REVIEW='FRONT_BOX_MATERIAL_REVIEW')
pat=re.compile('|'.join(re.escape(k) for k in sorted(mapping,key=len,reverse=True)));rename=lambda s:pat.sub(lambda m:mapping[m.group()],s);records=[]
for name in ['review_front_corridor_midpoint_stage_episode.py','review_front_corridor_midpoint_incomplete_episode.py','watch_front_corridor_midpoint_numeric_reviews.py','watch_front_corridor_midpoint_physical_audits.py','close_front_corridor_midpoint_physical.py','queue_front_corridor_midpoint_physical_closure.py']:
 p=W/name;t=W/rename(name);s=rename(p.read_text())
 if name=='close_front_corridor_midpoint_physical.py':s=s.replace('front_z_priority_physical_r1/RESULT_WITH_ROTATION_SUPPLEMENT.json','front_corridor_midpoint_physical_r1/RESULT.json').replace('midpoint_route_against_matched_loaded_z_parent','finite_preload_against_matched_midpoint2mm_parent')
 ast.parse(s)
 with t.open('x') as f:f.write(s)
 records.append(dict(parent=str(p),parent_sha256=sha(p),path=str(t),sha256=sha(t)))
# Use the existing explicitly supplemented parent closure preflight and loop.
p=W/'run_front_drive_1mm_rigid_parent_v2.py';s=p.read_text().replace('front_drive_1mm_preparation_r2','front_box_material_physical_preparation_r1').replace("S=W/'staged_front_drive_1mm'","S=W/'staged_front_box_material_preload'").replace('front_drive_1mm_v2_stage_source_binding','front_box_material_stage_source_binding').replace('front_drive_1mm_v2_stage_run_contract','front_box_material_v1_stage_run_contract').replace('watch_front_drive_1mm_physical_audits','watch_front_box_material_physical_audits').replace('watch_front_drive_1mm_numeric_reviews','watch_front_box_material_numeric_reviews').replace('front_drive_1mm_physical_r1','front_box_material_physical_r1').replace('RIGID_PARENT_V2_CONFIGURATION_CHECK','CONFIGURATION_CHECK').replace('RIGID_PARENT_V2_LAUNCH_PREFLIGHT','LAUNCH_PREFLIGHT').replace('Matched declared1mm-front-drive physical diagnostic','Matched finite material-preload physical diagnostic')
a=s.index('CHECKS=');b=s.index('_cache={}',a)
checks=['staged_front_box_material_preload/'+n for n in ['PARSER_DISPATCH_CHECK.json','SOURCE_CONTRACT_CHECK.json','NATIVE_WAIT_ENTRY_CHECK.json','AUDIT_DEPENDENCIES_CHECK.json','JOINT_CHAIN_CHECK.json']]+['front_box_material_preload_draft_r1/CONTROL_HISTORY_MIDPOINT_NEGATIVE_CHECK.json']
s=s[:a]+'CHECKS='+repr(checks)+"\nMANIFESTS=['staged_front_box_material_preload/AUDIT_FAMILY_PREPARATION.json','front_box_material_physical_preparation_r1/PHYSICAL_PREPARATION.json']\n"+s[b:]
a=s.index('def configuration():');b=s.index('def preflight():',a)
s=s[:a]+'''def configuration():
 plan=json.loads((P/'PLAN.json').read_text());assert plan['status']=='prepared_not_launched' and plan['simulation_started'] is False
 assert Path(plan['collector'])==S/'collect_paired_sorting.py' and sha(plan['collector'])==plan['collector_sha256']
 assert sha(plan['parent_protocol'])==plan['parent_protocol_sha256'];old=json.loads(Path(plan['parent_protocol']).read_text())['plan']
 assert plan['groups']==old['groups'] and len(plan['commands'])==6 and sum(len(c['tasks']) for c in plan['commands'])==10
 from prepare_closed_peak_trial import parser_namespace
 from simfoundry.data.waist_pilot_protocol import semantic_settings
 for item,original in zip(plan['commands'],old['commands']):
  args=item['args'];expected=list(original['args']);expected[expected.index('--out-dir')+1]=args[args.index('--out-dir')+1];expected.append('--front-box-material-preload');assert item==dict(original,args=expected)
  if not item['wait']:assert sha(args[args.index('--diagnostic-layout-json')+1])==item['layout_sha256']
  resolved,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True);settings=semantic_settings(resolved)
  for key in ['front_box_material_preload','front_corridor_midpoint_replan','front_loaded_z_priority','front_initial_center_landing','terminal_release_margin','edge_clearance_intersection']:assert settings.pop(key) is True
  assert settings==json.loads((W/'staged_closed_peak_trial/TRIAL_PROFILE.json').read_text())['prelaunch_settings']
 from front_box_material_stage_source_binding import verify_preparation
 expected,proofs=verify_preparation();bound(proofs);bound({str(S/n):h for n,h in expected.items()})
 for n in CHECKS:
  r=json.loads((W/n).read_text());assert r['passed'] is True;bound(r['source_sha256'])
 family=json.loads((W/MANIFESTS[0]).read_text());bound(family['source_sha256'])
 for r in family['adapters']:assert sha(r['parent'])==r['parent_sha256'] and sha(r['path'])==r['sha256']
 generated=json.loads((W/MANIFESTS[1]).read_text())
 for r in generated['files']:assert sha(r['parent'])==r['parent_sha256'] and sha(r['path'])==r['sha256']
 deps=json.loads((S/'AUDIT_DEPENDENCIES_CHECK.json').read_text());assert deps['passed'] and deps['conditions']==10 and deps['expected_audit_invocations']==204
 try:verify_trial_provenance(PREVIOUS/'case_840022')
 except (AssertionError,KeyError):pass
 else:raise AssertionError('Old-source parent admitted as new stage')
 from watch_front_box_material_numeric_reviews import check
 numeric=check();assert numeric['passed'];bound(numeric['source_sha256'])
 result=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),conditions=10,total_audits=204,plan_sha256=sha(P/'PLAN.json'),checks={n:sha(W/n) for n in CHECKS},numeric_routing=numeric,runner_sha256=sha(__file__),simulation_started=False,training_ready=False)
 (P/'CONFIGURATION_CHECK.json').write_text(json.dumps(result,indent=2));return plan

''' +s[b:]
t=W/'run_front_box_material_physical.py';ast.parse(s)
with t.open('x') as f:f.write(s)
records.append(dict(parent=str(p),parent_sha256=sha(p),path=str(t),sha256=sha(t)))
with (P/'PHYSICAL_PREPARATION.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,files=records,replacements=mapping,plan_sha256=sha(P/'PLAN.json'),generator_sha256=sha(__file__),simulation_started=False,training_ready=False),f,indent=2)
print(json.dumps(dict(files=len(records),conditions=10,simulation_started=False)))
