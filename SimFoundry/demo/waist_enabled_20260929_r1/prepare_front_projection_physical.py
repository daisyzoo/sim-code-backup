"""Prepare full matched8push2wait projection diagnostic, no automatic launch.
Source/parameter checks may run before parent closes. Physical preflight still
requires full parent closure, explicit expected-short-failure diagnosis, original
space gates and idle GPU. No failed group admission or success substitution.
"""
from pathlib import Path
import ast,datetime,hashlib,json
W=Path(__file__).resolve().parent;S=W/'staged_front_loaded_projection';P=W/'front_projection_physical_preparation_r1';assert not P.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();P.mkdir()
parent=W/'front_loaded_physical_preparation_r1/PLAN.json';old=json.loads(parent.read_text());commands=[]
for row in old['commands']:
 args=list(row['args']);args[args.index('--out-dir')+1]=str(P/f"case_{row['layout_id']}");args.append('--front-loaded-material-projection');commands.append(dict(row,args=args))
plan=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='prepared_not_launched',collector=str(S/'collect_paired_sorting.py'),collector_sha256=sha(S/'collect_paired_sorting.py'),groups=old['groups'],commands=commands,parent_plan=str(parent),parent_plan_sha256=sha(parent),parent_run=str(W/'front_loaded_physical_r1'),scope=__doc__,simulation_started=False,training_ready=False)
(P/'PLAN.json').write_text(json.dumps(plan,indent=2));files={};changes={}
replacements=[('front_loaded_stage','front_projection_stage'),('FRONT_LOADED_STAGE','FRONT_PROJECTION_STAGE'),('FRONT_LOADED_REVIEW','FRONT_PROJECTION_REVIEW'),('FRONT_LOADED_INCOMPLETE','FRONT_PROJECTION_INCOMPLETE'),('run_front_loaded_physical.py','run_front_projection_physical.py')]
for before,after in [('watch_front_loaded_physical_audits.py','watch_front_projection_physical_audits.py'),('review_front_loaded_stage_episode.py','review_front_projection_stage_episode.py'),('review_front_loaded_incomplete_episode.py','review_front_projection_incomplete_episode.py'),('close_front_loaded_physical.py','close_front_projection_physical.py')]:
 s=(W/before).read_text()
 for a,b in replacements:s=s.replace(a,b)
 if after.startswith('close_'):
  s=s.replace('front_initial_physical_r1/RESULT_WITH_REGION_SUPPLEMENT.json','front_loaded_physical_r1/RESULT.json').replace("W/'front_initial_physical_r1'/ep.parent.name","W/'front_loaded_physical_r1'/ep.parent.name").replace('loaded_cap_against_matched_initial_center_parent','material_projection_against_matched_old_cap_parent')
 dest=W/after;assert not dest.exists();ast.parse(s);dest.write_text(s);files[str(dest)]=sha(dest);changes[str(dest)]=dict(parent=str(W/before),parent_sha256=sha(W/before))
body=(W/'run_front_loaded_physical.py').read_text().split('def main(out,check_only=False):',1)[1]
body='def main(out,check_only=False):'+body
body=body.replace('watch_front_loaded_physical_audits.py','watch_front_projection_physical_audits.py').replace("W/'front_loaded_physical_r1'","W/'front_projection_physical_r1'").replace("PREVIOUS/'RESULT_WITH_REGION_SUPPLEMENT.json'","PREVIOUS/'RESULT.json'")
header='''"""Full matched projection diagnostic with unchanged quality gates."""
from pathlib import Path
import os,sys,json,hashlib,datetime,subprocess,argparse
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'front_projection_physical_preparation_r1';BASE=W/'fresh_closed_peak_trials_r1';PREVIOUS=W/'front_loaded_physical_r1';S=W/'staged_front_loaded_projection'
sys.path.insert(0,str(ROOT))
from front_projection_stage_source_binding import verify_trial_provenance
from front_projection_stage_run_contract import primary,controls,ADDITIONAL,REPORTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
CHECKS=['staged_front_loaded_projection/CHECK.json','FRONT_LOADED_MATERIAL_PROJECTION_CHECK.json','FRONT_LOADED_PROJECTION_STAGE_CHECK.json','FRONT_LOADED_PROJECTION_AUDIT_CHECK.json','FRONT_PROJECTION_AUDIT_DEPENDENCIES_CHECK.json','FRONT_PROJECTION_WAIT_SOURCE_FIXTURE_CHECK.json']
MANIFESTS=['FRONT_PROJECTION_STAGE_AUDITS_PREPARATION.json','FRONT_LOADED_PROJECTION_AUDIT_PREPARATION.json','FRONT_PROJECTION_PHYSICAL_PREPARATION.json']
def bound(mapping):
 for path,h in mapping.items():assert sha(path)==h,path

def configuration():
 plan=json.loads((P/'PLAN.json').read_text());assert plan['status']=='prepared_not_launched' and plan['simulation_started'] is False
 assert Path(plan['collector'])==S/'collect_paired_sorting.py' and sha(plan['collector'])==plan['collector_sha256']
 assert sha(plan['parent_plan'])==plan['parent_plan_sha256'];old=json.loads(Path(plan['parent_plan']).read_text())
 assert plan['groups']==old['groups'] and len(plan['commands'])==6 and sum(len(c['tasks']) for c in plan['commands'])==10
 from prepare_closed_peak_trial import parser_namespace
 from simfoundry.data.waist_pilot_protocol import semantic_settings
 for current,original in zip(plan['commands'],old['commands']):
  args=current['args'];expected=list(original['args']);expected[expected.index('--out-dir')+1]=args[args.index('--out-dir')+1];expected+=['--front-loaded-material-projection'];assert current==dict(original,args=expected)
  for flag in ['--front-loaded-material-projection','--front-loaded-reference-cap','--front-initial-center-landing','--terminal-release-margin','--edge-clearance-intersection']:assert args.count(flag)==1
  assert not any(x in args for x in ['--terminal-directional-lead','--push-assist'])
  if not current['wait']:assert sha(args[args.index('--diagnostic-layout-json')+1])==current['layout_sha256']
  resolved,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True);settings=semantic_settings(resolved)
  for key in ['front_loaded_material_projection','front_loaded_reference_cap','front_initial_center_landing','terminal_release_margin','edge_clearance_intersection']:assert settings.pop(key) is True
  assert settings==json.loads((W/'staged_closed_peak_trial/TRIAL_PROFILE.json').read_text())['prelaunch_settings']
 prep=json.loads((S/'PREPARATION.json').read_text());bound({str(S/k):h for k,h in prep['stage_sha256'].items()})
 for name in CHECKS:
  r=json.loads((W/name).read_text());assert r['passed'] is True
  if isinstance(r.get('source_sha256'),dict):bound(r['source_sha256'])
  if 'stage_sha256' in r:bound({str(S/k):h for k,h in r['stage_sha256'].items()})
 for row in json.loads((W/MANIFESTS[0]).read_text())['adapters']:assert sha(row['parent'])==row['parent_sha256'] and sha(row['path'])==row['sha256']
 bound(json.loads((W/MANIFESTS[1]).read_text())['source_sha256'])
 bound(json.loads((W/MANIFESTS[2]).read_text())['files_sha256'])
 dependent=json.loads((W/'FRONT_PROJECTION_AUDIT_DEPENDENCIES_CHECK.json').read_text());assert dependent['missing']==[] and dependent['conditions']==10 and dependent['expected_audit_invocations']==194
 assert json.loads((W/'FRONT_PROJECTION_WAIT_SOURCE_FIXTURE_CHECK.json').read_text())['fixture_only'] is True
 try:verify_trial_provenance(PREVIOUS/'case_840022')
 except (AssertionError,KeyError):pass
 else:raise AssertionError('Old-source parent accepted as new candidate')
 return plan

def preflight():
 plan=configuration();old=json.loads(Path(plan['parent_plan']).read_text())
 state=json.loads((PREVIOUS/'STATUS.json').read_text());assert state['completed_conditions']==10 and state['status']=='collection_complete_audits_visual_pending'
 parent_protocol=json.loads((PREVIOUS/'PROTOCOL.json').read_text());assert parent_protocol['plan']==old;bound(parent_protocol['frozen_files_sha256'])
 parent_result=PREVIOUS/'RESULT.json';assert parent_result.exists(),'parent complete original closure still pending'
 closed=json.loads(parent_result.read_text());assert closed['conditions']==10 and closed['audit_invocations']==194;bound(closed['source_sha256'])
 assert closed['status']=='diagnostic_complete_failures_retained' and closed['training_ready'] is False
 # Only the two already diagnosed short cap stops are expected. Every full
 # control/wait episode must pass all original audits, not only task scores.
 failures=closed['failed_audit_invocations'];shorts={'layout_840023_nudge_mailer_to_bin':191,'layout_840020_push_box_to_bin':212}
 assert len(failures)==36 and {x['episode'] for x in failures}==set(shorts)
 for row in closed['rows']:
  if row['episode'] in shorts:assert row['incomplete_episode'] and row['frames']==shorts[row['episode']] and not row['original_task_and_pose_passed']
  else:assert row['control_audits_passed'] and not row['failed_audits'] and not row['incomplete_episode']
 for f in failures:
  assert f['incomplete_episode'] and f['returncode']!=0
  ep=next(PREVIOUS.glob('case_*/'+f['episode']));log=ep/(f['script']+'.log');assert sha(log)==f['log_sha256'];text=log.read_text()
  assert 'front_loaded_stage_source_binding.py' in text and "assert frames==args['wait_steps' if task=='wait_no_package' else 'steps']" in text and text.rstrip().endswith('AssertionError')
  failure=json.loads((ep/'self_clearance.json').read_text())['failure'];assert failure['reason']=='empty_original_slew_lead_material_intersection' and failure['step']==shorts[ep.name]
 for name in ['FRONT_LOADED_TWO_EARLY_STOP_FINDINGS.json','FRONT_LOADED_STOP_STATE_EVIDENCE_CORRECTION.json']:
  diagnosis=json.loads((W/name).read_text())
  if 'source_sha256' in diagnosis:bound(diagnosis['source_sha256'])
 closure=json.loads((PREVIOUS/'CLOSURE_QUEUE_STATUS.json').read_text());assert closure['status']=='closed_original_failures_retained'
 for pid in [parent_protocol['producer_pid'],json.loads((PREVIOUS/'AUDIT_STATUS.json').read_text())['pid'],closure['pid']]:
  path=Path('/proc')/str(pid);assert not path.exists() or (path/'stat').read_text().split()[2]=='Z',('parent process active',pid)
 records=json.loads((PREVIOUS/'COLLECTION_EXECUTION.json').read_text());assert len(records)==10
 for row in records:bound(row['source_sha256'])
 # Stop context implementation is a separate diagnostic prerequisite. It must
 # be explicitly checked before this prepared runner may launch.
 stop_check=W/'FRONT_PROJECTION_STOP_CONTEXT_CHECK.json';assert stop_check.exists(),'independent stop context checks still pending'
 stop=json.loads(stop_check.read_text());assert stop['passed'];bound(stop['source_sha256'])
 from rear_corridor_storage_budget import require_storage
 storage=require_storage(ROOT,plan['commands'])
 gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,check=True);assert not gpu.stdout.strip(),gpu.stdout.strip()
 result=dict(preflight_passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(P/'PLAN.json'),checks={n:sha(W/n) for n in CHECKS},stop_context_check_sha256=sha(stop_check),storage=storage,runner_sha256=sha(__file__),simulation_started=False,training_ready=False)
 (P/'LAUNCH_PREFLIGHT.json').write_text(json.dumps(result,indent=2));return plan

'''
# Freeze the extra diagnostic report alongside every W Python source at launch.
body=body.replace("*[W/n for n in CHECKS+MANIFESTS]","W/'FRONT_PROJECTION_STOP_CONTEXT_CHECK.json',W/'FRONT_LOADED_STOP_STATE_EVIDENCE_CORRECTION.json',W/'FRONT_LOADED_TWO_EARLY_STOP_FINDINGS.json',*[W/n for n in CHECKS+MANIFESTS]")
s=header+body;p=W/'run_front_projection_physical.py';assert not p.exists();ast.parse(s);p.write_text(s);files[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,generator_sha256=sha(__file__),plan_sha256=sha(P/'PLAN.json'),files_sha256=files,adapters=changes,global_replacements=replacements,syntax_passed=True,stop_context_checks_pending=True,simulation_started=False,training_ready=False)
(W/'FRONT_PROJECTION_PHYSICAL_PREPARATION.json').write_text(json.dumps(report,indent=2));print('Prepared6 commands/10conditions, full runner/reviewers/closer; parent closure and stop-context verification required')
