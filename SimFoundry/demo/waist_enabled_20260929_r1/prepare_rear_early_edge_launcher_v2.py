"""Version launcher readiness for source-contract parity, not fabricated parent success.
Fresh physical run still requires every original audit and task gate. No launch.
"""
from pathlib import Path
import json,hashlib,datetime
W=Path(__file__).resolve().parent;P=W/'rear_early_edge_physical_preparation_r1';D=W/'rear_early_edge_preparation_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
report=D/'NATIVE_UNCHANGED_PUSH_SOURCE_PARITY_V4.json';r=read(report);assert r['passed'] and r['compatibility_check_only'] and not r['all_native_executions_accepted']
assert len(r['cases'])==3 and len(r['negative_rejections'])==29 and len(r['original_execution_rejections_preserved'])==1
for p,h in r['source_sha256'].items():assert sha(p)==h,p
old=W/'run_rear_early_edge_trial1_physical_r1.py';new=W/'run_rear_early_edge_trial1_physical_r1_v2.py';s=old.read_text();edits=[]
def replace(a,b):
 global s
 assert a in s,a;s=s.replace(a,b);edits.append(dict(old=a,new=b))
replace('NATIVE_UNCHANGED_PUSH_SOURCE_CHECK_V2.json','NATIVE_UNCHANGED_PUSH_SOURCE_PARITY_V4.json')
replace('CONFIGURATION_CHECK.json','CONFIGURATION_CHECK_V2.json')
replace('LAUNCHER_DERIVATION.json','LAUNCHER_DERIVATION_V2.json')
replace('"""Fixed matched reserve trial:8push2wait with all original224audits and image review.','"""Matched early-edge diagnostic:8push2wait with original224audits and image review.\nSource-fixture compatibility retains known parent native rejection; never admission.')
marker=" joint=read(W/'rear_early_edge_candidate_v1/NATIVE_LOADED_BOUT_JOINT_REPLAY_V4.json');"
addition=""" parity=read(D/'NATIVE_UNCHANGED_PUSH_SOURCE_PARITY_V4.json')
 assert parity['compatibility_check_only'] is True and parity['all_native_executions_accepted'] is False
 assert len(parity['cases'])==3 and len(parity['negative_rejections'])==29
 assert all(x['physical_arrays_unchanged'] and x['native_execution_parity'] and x['fixture_only'] for x in parity['cases'])
 assert [(x['episode'],x['enabled'],x['native_parent_execution_passed']) for x in parity['cases']]==[('layout_840020_push_box_to_bin',True,False),('layout_840020_nudge_mailer_to_bin',True,True),('layout_840023_push_box_to_bin',False,True)]
 failures=parity['original_execution_rejections_preserved'];assert len(failures)==1 and failures[0]['episode']=='layout_840020_push_box_to_bin'
 failure=failures[0]['rejection'];assert failure['step']==667 and failure['function']=='verify_parent' and failure['proof']['reason']=='ambiguous_active_axis' and failure['proof']['passed'] is False
"""
assert s.count(marker)==1;replace(marker,addition+marker)
replace('result=dict(passed=True,conditions=10,expected_audits=224,direct_parent=str(PREVIOUS),source_sha256=sources,simulation_started=False,training_ready=False)','result=dict(passed=True,conditions=10,expected_audits=224,direct_parent=str(PREVIOUS),source_sha256=sources,source_fixture_compatibility_only=True,original_native_rejections_retained=failures,full_native_execution_certified=False,original_physical_audits_required=True,simulation_started=False,training_ready=False)')
compile(s,str(new),'exec')
with new.open('x') as f:f.write(s)
back=s
for e in reversed(edits):back=back.replace(e['new'],e['old'])
assert back==old.read_text()
qp=W/'queue_rear_early_edge_trial1_physical_v1.py';qn=W/'queue_rear_early_edge_trial1_physical_v2.py';q=qp.read_text().replace('run_rear_early_edge_trial1_physical_r1','run_rear_early_edge_trial1_physical_r1_v2').replace('CONFIGURATION_CHECK.json','CONFIGURATION_CHECK_V2.json').replace('One isolated quarter-Z trial after exact front-box producer finishes and ten actual reviews.','One early-edge diagnostic after exact quarter producer finishes and ten actual reviews.')
compile(q,str(qn),'exec')
with qn.open('x') as f:f.write(q)
result=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,launcher_parent=str(old),launcher_parent_sha256=sha(old),launcher=str(new),launcher_sha256=sha(new),edits=edits,inverse_checked=True,queue_parent=str(qp),queue_parent_sha256=sha(qp),queue=str(qn),queue_sha256=sha(qn),source_sha256={str(p):sha(p) for p in [Path(__file__),report,D/'PARENT_STATIONARITY_DIAGNOSIS_V1.json',old,new,qp,qn,P/'LAUNCHER_DERIVATION.json']},parent_native_failure_retained=True,quality_or_control_audit_gate_changed=False,configuration_checked=False,queue_prepared=False,queue_launched=False,simulation_started=False,training_ready=False)
with (P/'LAUNCHER_DERIVATION_V2.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(dict(prepared=True,launcher=new.name,queue=qn.name,original_parent_failure_retained=True)))
