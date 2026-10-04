"""Freeze matched ten-condition diagnostic plan, not a launch/admission decision."""
from pathlib import Path
import copy,datetime,hashlib,json,sys
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_normal_nondegradation_v3';P=W/'front_normal_physical_preparation_r3';P.mkdir(exist_ok=False);R=W/'front_normal_physical_r1';PARENT=W/'front_effective_height_physical_r1';sys.path[:0]=[str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
from front_normal_stage_source_binding_v3 import verify_preparation
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
parent=read(PARENT/'PROTOCOL.json');plan=copy.deepcopy(parent['plan']);checks=[]
plan.update(scope=__doc__,candidate_only_new_flag='--front-normal-nondegradation',direct_parent_numeric_visual_sha256=sha(PARENT/'NUMERIC_VISUAL_SUMMARY.json'),parent_result_pending=not (PARENT/'RESULT.json').exists(),created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='prepared_not_launched',collector=str(S/'collect_paired_sorting.py'),collector_sha256=sha(S/'collect_paired_sorting.py'),parent_run=str(PARENT),parent_protocol=str(PARENT/'PROTOCOL.json'),parent_protocol_sha256=sha(PARENT/'PROTOCOL.json'),simulation_started=False,training_ready=False)
for item,old in zip(plan['commands'],parent['plan']['commands']):
 args=item['args'];assert '--front-normal-nondegradation' not in args;args[args.index('--out-dir')+1]=str(R/f"case_{item['layout_id']}");args.append('--front-normal-nondegradation')
 before,_=parser_namespace(Path(parent['plan']['collector']),old['args'],full=True);after,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True)
 expected=dict(before);expected['out_dir']=after['out_dir'];expected['front_normal_nondegradation']=True;assert after==expected
 assert after['steps']==1200 and after['wait_steps']==70 and after['role']=='diagnostic' and after['motion_protocol']=='waist_yaw_enabled_v1' and '--push-assist' not in args and after['waist_limit_rad']==1.
 assert all(after[k] is True for k in ['joint_transport_clearance','joint_transport_effective_quarter_height','front_loaded_z_quarter','front_cop_route_axis','peak_load_bias_guard'])
 checks.append(dict(layout_id=item['layout_id'],tasks=item['tasks'],only_changes=['out_dir','front_normal_nondegradation'],parent_settings_preserved=True))
assert plan['groups']==parent['plan']['groups'] and len(checks)==6 and sum(len(x['tasks']) for x in checks)==10
used,bound=verify_preparation();assert len(used)==101
assert "'push_assist': False, 'assist_frames': 0" in (S/'collect_paired_sorting.py').read_text()
assert '--push-assist' not in (S/'collect_paired_sorting.py').read_text()
(P/'PLAN.json').write_text(json.dumps(plan,indent=2))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,parser_comparisons=checks,conditions=10,push_conditions=8,wait_conditions=2,active_collector_sources=101,source_sha256={**bound,**{str(S/n):h for n,h in used.items()},**{str(p):sha(p) for p in [Path(__file__),PARENT/'PROTOCOL.json',P/'PLAN.json']}},simulation_started=False,training_ready=False,physical_launch_ready=False,remaining=['Complete current full geometry fixture and pressure file entry check.','Check complete original224 audit dispatch and freeze every new helper.','Verify original parent collection+10actual image reviews complete, GPU unused, original >30GiB and per-case storage budget; launch in a new output directory only.'])
(P/'PLAN_CHECK.json').write_text(json.dumps(report,indent=2));print(dict(passed=True,conditions=10,push=8,wait=2,only_new_flag='front_normal_nondegradation',simulation_started=False))
