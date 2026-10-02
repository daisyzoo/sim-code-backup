"""First-front candidate on exactly the two matched parent groups,8push2wait.
All eight front groups remain the diagnostic coverage objective; this batch does
not replace the full12-group data protocol or independent model evaluation.
"""
from pathlib import Path
import json,hashlib,datetime,ast
W=Path(__file__).resolve().parent;S=W/'staged_front_initial_center';P=W/'front_initial_physical_preparation_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert not P.exists();P.mkdir()
parent=W/'front_initial_margin_baseline_preparation_r1/PLAN.json';old=json.loads(parent.read_text());commands=[]
for row in old['commands']:
 args=list(row['args']);args[args.index('--out-dir')+1]=str(P/f"case_{row['layout_id']}");args.append('--front-initial-center-landing');commands.append(dict(row,args=args))
plan=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='prepared_not_launched',collector=str(S/'collect_paired_sorting.py'),collector_sha256=sha(S/'collect_paired_sorting.py'),groups=old['groups'],commands=commands,parent_plan=str(parent),parent_plan_sha256=sha(parent),parent_run=str(W/'front_initial_margin_baseline_r1'),scope=__doc__,simulation_started=False,training_ready=False)
(P/'PLAN.json').write_text(json.dumps(plan,indent=2))
source=(W/'run_terminal_margin_physical.py').read_text();body=source[source.index('def main(out,check_only=False):'):]
body=body.replace('watch_terminal_margin_physical_audits.py','watch_front_initial_physical_audits.py').replace("default=str(W/'terminal_margin_physical_r1')","default=str(W/'front_initial_physical_r1')")
body=body.replace("PREVIOUS/'RESULT_WITH_SUPPLEMENT.json',PREVIOUS/'STATUS.json'","PREVIOUS/'PROTOCOL.json',PREVIOUS/'COLLECTION_EXECUTION.json',W/'terminal_margin_physical_r1/RESULT_WITH_SUPPLEMENT.json'")
body=body.replace('baseline_result_sha256=sha(BASE/\'RESULT.json\')','baseline_result_sha256=sha(BASE/\'RESULT.json\'),matched_parent_protocol_sha256=sha(PREVIOUS/\'PROTOCOL.json\'),matched_parent_collection_sha256=sha(PREVIOUS/\'COLLECTION_EXECUTION.json\'),matched_parent_audits_and_visuals_required_for_comparison=True')
body=body.replace('remaining_edge_cpu_audits_may_overlap=False','remaining_edge_cpu_audits_may_overlap=True')
header='''"""Complete first-front physics on matched reverse11/diagonal10 groups.
Baseline control/visual checks may run on CPU concurrently; comparison cannot
close until both full original evidence sets finish. No training admission.
"""
from pathlib import Path
import os,sys,json,hashlib,datetime,subprocess,argparse
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'front_initial_physical_preparation_r1';BASE=W/'fresh_closed_peak_trials_r1';PREVIOUS=W/'front_initial_margin_baseline_r1';S=W/'staged_front_initial_center'
sys.path.insert(0,str(ROOT))
from front_initial_stage_source_binding import verify_trial_provenance
from front_initial_stage_run_contract import primary,controls,ADDITIONAL,REPORTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
CHECKS=['staged_front_initial_center/CHECK.json','FRONT_INITIAL_OBSERVATION_BINDING_CHECK.json','FRONT_INITIAL_CONTROL_HISTORY_V3_CHECK.json','FRONT_INITIAL_CLEARANCE_DISPATCH_CHECK.json','FRONT_INITIAL_ACTUAL_CORE_CHECK.json','FRONT_INITIAL_ACTUAL_STAGE_CHECK.json','FRONT_INITIAL_CENTER_NATIVE_V2_CHECK.json','FRONT_INITIAL_STAGE_POSE_FILES_CHECK.json','FRONT_INITIAL_CENTER_UNFINISHED_HORIZON_CHECK.json','FRONT_INITIAL_CENTER_REFERENCE_LIFETIME_CHECK.json','FRONT_INITIAL_STAGE_INVENTORY_CHECK.json','FRONT_INITIAL_CENTER_TASK_ROWS_CHECK.json']
MANIFESTS=['FRONT_INITIAL_STAGE_AUDITS_PREPARATION.json','FRONT_INITIAL_STAGE_REMAINING_AUDITS_PREPARATION.json','FRONT_INITIAL_REVIEW_PREPARATION.json']
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
  args=current['args'];expected=list(original['args']);expected[expected.index('--out-dir')+1]=args[args.index('--out-dir')+1];expected+=['--front-initial-center-landing'];assert current==dict(original,args=expected)
  assert args.count('--front-initial-center-landing')==args.count('--terminal-release-margin')==args.count('--edge-clearance-intersection')==1
  assert not any(x in args for x in ['--terminal-directional-lead','--push-assist'])
  if not current['wait']:assert sha(args[args.index('--diagnostic-layout-json')+1])==current['layout_sha256']
  resolved,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True);settings=semantic_settings(resolved)
  for key in ['front_initial_center_landing','terminal_release_margin','edge_clearance_intersection']:assert settings.pop(key) is True
  assert settings==json.loads((W/'staged_closed_peak_trial/TRIAL_PROFILE.json').read_text())['prelaunch_settings']
 prep=json.loads((S/'PREPARATION.json').read_text());bound({str(S/k):h for k,h in prep['stage_sha256'].items()})
 checks={}
 for name in CHECKS:
  r=json.loads((W/name).read_text());assert r['passed'] is True
  if isinstance(r.get('source_sha256'),dict):bound(r['source_sha256'])
  if 'stage_sha256' in r:bound({str(S/k):h for k,h in r['stage_sha256'].items()})
  checks[name]=sha(W/name)
 actual=json.loads((W/'FRONT_INITIAL_ACTUAL_CORE_CHECK.json').read_text());assert actual['status']=='complete' and len(actual['records'])==8
 for row in actual['records']:bound(row['source_sha256']);assert row['plan']['scene']['core_size']==row['actual_core']['collision_core_size_xyz']
 for name in MANIFESTS[:2]:
  for row in json.loads((W/name).read_text())['adapters']:assert sha(row['parent'])==row['parent_sha256'] and sha(row['path'])==row['sha256']
 state=json.loads((PREVIOUS/'STATUS.json').read_text());assert state['status']=='collection_complete_audits_visual_pending' and state['completed_conditions']==10,'matched parent collection must finish before candidate'
 parent_protocol=json.loads((PREVIOUS/'PROTOCOL.json').read_text());assert parent_protocol['plan']==old;bound(parent_protocol['frozen_files_sha256'])
 pid=parent_protocol['producer_pid'];path=Path('/proc')/str(pid);assert not path.exists() or (path/'stat').read_text().split()[2]=='Z','parent producer still active'
 assert json.loads((PREVIOUS/'AUDIT_STATUS.json').read_text())['status'] in ('running','complete'),'parent audit process failed/incomplete'
 records=json.loads((PREVIOUS/'COLLECTION_EXECUTION.json').read_text());assert len(records)==10
 for row in records:bound(row['source_sha256'])
 try:verify_trial_provenance(PREVIOUS/'case_840022')
 except (AssertionError,KeyError):pass
 else:raise AssertionError('Parent data accepted as candidate source')
 from rear_corridor_storage_budget import require_storage
 storage=require_storage(ROOT,plan['commands'])
 gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,check=True);assert not gpu.stdout.strip(),gpu.stdout.strip()
 result=dict(preflight_passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(P/'PLAN.json'),checks=checks,storage=storage,runner_sha256=sha(__file__),simulation_started=False,training_ready=False)
 (P/'LAUNCH_PREFLIGHT.json').write_text(json.dumps(result,indent=2));return plan

'''
s=header+body;p=W/'run_front_initial_physical.py';assert not p.exists();ast.parse(s);p.write_text(s)
s=(W/'watch_terminal_margin_physical_audits.py').read_text().replace('terminal_margin_stage','front_initial_stage').replace("'run_terminal_margin_physical.py'","'run_front_initial_physical.py'");p=W/'watch_front_initial_physical_audits.py';assert not p.exists();ast.parse(s);p.write_text(s)
print('Prepared candidate full2-group plan and runner; no launch until matched parent complete and GPU free.')
