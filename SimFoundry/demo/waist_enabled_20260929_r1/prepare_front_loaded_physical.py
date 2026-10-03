"""Prepare complete matched8push2wait material-cap diagnostic, never auto-admit.
All diagnostic groups and eventual shared-policy validation remain required.
Start only after the current parent is fully closed with no unresolved control
errors, all new evidence is bound, original disk budget passes and GPU is free.
"""
from pathlib import Path
import ast,datetime,hashlib,json
W=Path(__file__).resolve().parent;S=W/'staged_front_loaded_reference';P=W/'front_loaded_physical_preparation_r1';assert not P.exists();P.mkdir();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
parent=W/'front_initial_physical_preparation_r1/PLAN.json';old=json.loads(parent.read_text());commands=[]
for row in old['commands']:
 args=list(row['args']);args[args.index('--out-dir')+1]=str(P/f"case_{row['layout_id']}");args.append('--front-loaded-reference-cap');commands.append(dict(row,args=args))
plan=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='prepared_not_launched',collector=str(S/'collect_paired_sorting.py'),collector_sha256=sha(S/'collect_paired_sorting.py'),groups=old['groups'],commands=commands,parent_plan=str(parent),parent_plan_sha256=sha(parent),parent_run=str(W/'front_initial_physical_r1'),scope=__doc__,simulation_started=False,training_ready=False)
(P/'PLAN.json').write_text(json.dumps(plan,indent=2))
source=(W/'run_front_initial_physical.py').read_text();body=source[source.index('def main(out,check_only=False):'):]
body=body.replace('watch_front_initial_physical_audits.py','watch_front_loaded_physical_audits.py').replace("default=str(W/'front_initial_physical_r1')","default=str(W/'front_loaded_physical_r1')")
body=body.replace("PREVIOUS/'COLLECTION_EXECUTION.json',W/", "PREVIOUS/'COLLECTION_EXECUTION.json',PREVIOUS/'RESULT_WITH_REGION_SUPPLEMENT.json',W/")
header='''"""Complete matched material-cap physics after full parent closure; no admission."""
from pathlib import Path
import os,sys,json,hashlib,datetime,subprocess,argparse
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'front_loaded_physical_preparation_r1';BASE=W/'fresh_closed_peak_trials_r1';PREVIOUS=W/'front_initial_physical_r1';S=W/'staged_front_loaded_reference'
sys.path.insert(0,str(ROOT))
from front_loaded_stage_source_binding import verify_trial_provenance
from front_loaded_stage_run_contract import primary,controls,ADDITIONAL,REPORTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
CHECKS=['staged_front_loaded_reference/CHECK.json','FRONT_INITIAL_LOADED_REFERENCE_CAP_CHECK.json','FRONT_LOADED_REFERENCE_HISTORY_V2_CHECK.json','FRONT_LOADED_REFERENCE_STAGE_CHECK.json','FRONT_LOADED_MATERIAL_AUDIT_CHECK.json','FRONT_LOADED_MATERIAL_AUDIT_V2_CHECK.json','FRONT_LOADED_AUDIT_DEPENDENCIES_CHECK.json','FRONT_LOADED_WAIT_SOURCE_FIXTURE_CHECK.json']
MANIFESTS=['FRONT_LOADED_STAGE_AUDITS_PREPARATION.json','FRONT_LOADED_STAGE_RUN_CONTRACT_PREPARATION.json','FRONT_LOADED_REFERENCE_COP_AUDIT_PREPARATION.json','FRONT_LOADED_PHYSICAL_PREPARATION.json']
def bound(mapping):
 for path,h in mapping.items():assert sha(path)==h,path

def preflight():
 plan=json.loads((P/'PLAN.json').read_text());assert plan['status']=='prepared_not_launched' and plan['simulation_started'] is False
 assert Path(plan['collector'])==S/'collect_paired_sorting.py' and sha(plan['collector'])==plan['collector_sha256']
 assert sha(plan['parent_plan'])==plan['parent_plan_sha256'];old=json.loads(Path(plan['parent_plan']).read_text())
 assert plan['groups']==old['groups'] and len(plan['commands'])==6 and sum(len(c['tasks']) for c in plan['commands'])==10
 from prepare_closed_peak_trial import parser_namespace
 from simfoundry.data.waist_pilot_protocol import semantic_settings
 for current,original in zip(plan['commands'],old['commands']):
  args=current['args'];expected=list(original['args']);expected[expected.index('--out-dir')+1]=args[args.index('--out-dir')+1];expected+=['--front-loaded-reference-cap'];assert current==dict(original,args=expected)
  for flag in ['--front-loaded-reference-cap','--front-initial-center-landing','--terminal-release-margin','--edge-clearance-intersection']:assert args.count(flag)==1
  assert not any(x in args for x in ['--terminal-directional-lead','--push-assist'])
  if not current['wait']:assert sha(args[args.index('--diagnostic-layout-json')+1])==current['layout_sha256']
  resolved,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True);settings=semantic_settings(resolved)
  for key in ['front_loaded_reference_cap','front_initial_center_landing','terminal_release_margin','edge_clearance_intersection']:assert settings.pop(key) is True
  assert settings==json.loads((W/'staged_closed_peak_trial/TRIAL_PROFILE.json').read_text())['prelaunch_settings']
 prep=json.loads((S/'PREPARATION.json').read_text());bound({str(S/k):h for k,h in prep['stage_sha256'].items()});checks={}
 for name in CHECKS:
  r=json.loads((W/name).read_text());assert r['passed'] is True
  if isinstance(r.get('source_sha256'),dict):bound(r['source_sha256'])
  if 'stage_sha256' in r:bound({str(S/k):h for k,h in r['stage_sha256'].items()})
  checks[name]=sha(W/name)
 for row in json.loads((W/MANIFESTS[0]).read_text())['adapters']:assert sha(row['parent'])==row['parent_sha256'] and sha(row['path'])==row['sha256']
 for name in MANIFESTS[1:3]:
  r=json.loads((W/name).read_text());assert sha(r['parent'])==r['parent_sha256'] and sha(r['path'])==r['sha256']
 dependent=json.loads((W/'FRONT_LOADED_AUDIT_DEPENDENCIES_CHECK.json').read_text());assert dependent['missing']==[] and dependent['conditions']==10 and dependent['expected_audit_invocations']==194
 for name in ['FRONT_LOADED_MATERIAL_AUDIT_CHECK.json','FRONT_LOADED_MATERIAL_AUDIT_V2_CHECK.json']:
  r=json.loads((W/name).read_text());assert len(r['positive'])==1 and len(r['negative'])==9
 assert json.loads((W/'FRONT_LOADED_MATERIAL_AUDIT_V2_CHECK.json').read_text())['pending']==[]
 assert json.loads((W/'FRONT_LOADED_MATERIAL_AUDIT_V2_CHECK.json').read_text())['earlier_bag_fixture_sha256']==sha(W/'FRONT_LOADED_MATERIAL_AUDIT_CHECK.json')
 assert json.loads((W/'FRONT_LOADED_WAIT_SOURCE_FIXTURE_CHECK.json').read_text())['fixture_only'] is True
 try:verify_trial_provenance(PREVIOUS/'case_840022')
 except (AssertionError,KeyError):pass
 else:raise AssertionError('Old-source parent accepted as new candidate')
 # Parent numerical failure is expected and retained. Unknown control failures
 # require diagnosis, not an automatic new launch or threshold exception.
 state=json.loads((PREVIOUS/'STATUS.json').read_text());assert state['completed_conditions']==10 and state['status']=='collection_complete_audits_visual_pending'
 parent_protocol=json.loads((PREVIOUS/'PROTOCOL.json').read_text());assert parent_protocol['plan']==old;bound(parent_protocol['frozen_files_sha256'])
 parent_result=PREVIOUS/'RESULT_WITH_REGION_SUPPLEMENT.json';assert parent_result.exists(),'parent full closure still pending'
 closed=json.loads(parent_result.read_text());assert closed['conditions']==10 and not closed['unresolved_audits'];bound(closed['source_sha256'])
 closure=json.loads((PREVIOUS/'CLOSURE_QUEUE_STATUS.json').read_text());assert closure['status']=='closed_original_and_separate_supplement_reports'
 for pid in [parent_protocol['producer_pid'],json.loads((PREVIOUS/'AUDIT_STATUS.json').read_text())['pid'],json.loads((PREVIOUS/'REGION_SUPPLEMENT_STATUS.json').read_text())['pid'],closure['pid']]:
  path=Path('/proc')/str(pid);assert not path.exists() or (path/'stat').read_text().split()[2]=='Z',('parent process active',pid)
 records=json.loads((PREVIOUS/'COLLECTION_EXECUTION.json').read_text());assert len(records)==10
 for row in records:bound(row['source_sha256'])
 from rear_corridor_storage_budget import require_storage
 storage=require_storage(ROOT,plan['commands'])
 gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,check=True);assert not gpu.stdout.strip(),gpu.stdout.strip()
 result=dict(preflight_passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(P/'PLAN.json'),checks=checks,storage=storage,runner_sha256=sha(__file__),simulation_started=False,training_ready=False)
 (P/'LAUNCH_PREFLIGHT.json').write_text(json.dumps(result,indent=2));return plan

'''
files={};s=header+body;p=W/'run_front_loaded_physical.py';assert not p.exists();ast.parse(s);p.write_text(s);files[str(p)]=sha(p)
for old_name,new_name in [('watch_front_initial_physical_audits.py','watch_front_loaded_physical_audits.py'),('review_front_initial_stage_episode.py','review_front_loaded_stage_episode.py'),('review_front_initial_incomplete_episode.py','review_front_loaded_incomplete_episode.py'),('close_front_initial_physical.py','close_front_loaded_physical.py')]:
 s=(W/old_name).read_text().replace('front_initial_stage','front_loaded_stage').replace('FRONT_INITIAL_STAGE','FRONT_LOADED_STAGE').replace('FRONT_INITIAL_REVIEW','FRONT_LOADED_REVIEW').replace('FRONT_INITIAL_INCOMPLETE','FRONT_LOADED_INCOMPLETE').replace('run_front_initial_physical.py','run_front_loaded_physical.py')
 if new_name.startswith('close_'):s=s.replace("front_initial_margin_baseline_r1/RESULT_WITH_SUPPLEMENT.json","front_initial_physical_r1/RESULT_WITH_REGION_SUPPLEMENT.json").replace("W/'front_initial_margin_baseline_r1'/ep.parent.name","W/'front_initial_physical_r1'/ep.parent.name").replace('candidate_against_matched_margin_parent','loaded_cap_against_matched_initial_center_parent')
 p=W/new_name;assert not p.exists();ast.parse(s);p.write_text(s);files[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,generator_sha256=sha(__file__),plan_sha256=sha(P/'PLAN.json'),files_sha256=files,syntax_passed=True,simulation_started=False,training_ready=False)
(W/'FRONT_LOADED_PHYSICAL_PREPARATION.json').write_text(json.dumps(report,indent=2));print('Prepared6 commands/10conditions, runner, watcher, full/short reviewers and closer; parent closure still required')
