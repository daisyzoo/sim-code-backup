"""Real failing context with isolated solver/certificate/path/guard fault injection.
No simulator. Original input stays intact, and a reversing parent cannot leak.
"""
from pathlib import Path
import copy,datetime,gzip,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';D=W/'front_cross_track_rejections_r1';D.mkdir(exist_ok=False);sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
import front_cross_track_runtime_candidate_v2 as runtime
from audit_front_cross_track_certificate_v2 import verify as old_verify
from audit_front_cross_track_certificate_v3 import verify
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ep=W/'front_effective_height_physical_r1/case_840020/layout_840020_push_box_to_bin';t=1009;c=next(x for x in read(ep/'coordination.json') if x['step']==t);row=next(x for x in read(ep/'frontal_bypass.json')['rows'] if x['step']==t);old=c['joint_transport_clearance'];tc=old['collector_context'];sc=tc['scene'];G=ClearanceGuard(ROOT,S);scene=RecontactScene(G,sc['side'],sc['target_xyz'],sc['target_quat'],sc['core_size'],sc['other_xyz'],sc['other_quat'],sc['other_size']);kw=dict(step=t,selected=True,side=sc['side'],row=row,coordinate=c,scene=scene,current=np.array(tc['current']),previous_q=tc['previous_q'],previous_command=tc['previous_command'],parent_command=old['output_command'],decay=tc['decay']);detail_path=W/'front_cross_track_full_stream_probe_r1/contexts/layout_840020_push_box_to_bin_1009.json.gz';detail=json.loads(gzip.decompress(detail_path.read_bytes()));p=detail['proposal'];u=np.array(p['command']);original_runtime_propose=runtime.propose;original_runtime_verify=runtime.verify;before=copy.deepcopy(c)
# Demonstrate the former report-only NaN weakness and reject it explicitly in V3.
invalid=copy.deepcopy(p);invalid['cross_track_nonreversal']['proposal_signed_nominal_dx_m']=float('nan');old_nan_accepted=old_verify(invalid,c['task_inputs'],c,guard=G,elbow_reserve_m=.0015,quarter_enabled=True)['passed'];assert old_nan_accepted
positive=verify(p,c['task_inputs'],c,guard=G,elbow_reserve_m=.0015,quarter_enabled=True);assert positive['passed'];tamper_results=[]
for key,value in [('proposal_signed_nominal_dx_m',float('nan')),('parent_signed_nominal_dx_m',float('inf')),('axis',False),('requested_direction',1.),('rounding_tolerance_m',.01),('threshold_m',-.01),('proposal_signed_nominal_dx_m',.1),('enabled',False)]:
 bad=copy.deepcopy(p);bad['cross_track_nonreversal'][key]=value
 try:verify(bad,c['task_inputs'],c,guard=G,elbow_reserve_m=.0015,quarter_enabled=True)
 except (ValueError,AssertionError):tamper_results.append(dict(field=key,rejected=True))
 else:raise AssertionError('Tamper accepted '+key)
class Paths:
 def __init__(self,original,fail):self.original=original;self.fail=fail
 def margins(self,*a):return np.full(6,-1.) if self.fail=='measured' else self.original.margins(*a)
 def certify(self,*a):return dict(passed=False,reason='injected_path_failure') if self.fail=='path' else dict(passed=True,scope='Previously validated stored-context path, injected for branch test')
class Guard:
 def __init__(self,fail):self.fail=fail
 def __getattr__(self,k):return getattr(G,k)
 def command(self,command,*a,**kw):
  bad=self.fail=='parent' and np.array_equal(command,old['output_command']) or self.fail=='final' and np.array_equal(command,u)
  return dict(accepted=False,reason='injected_guard_failure') if bad else G.command(command,*a,**kw)
results=[]
for failure,reason in [('solver','no_verified_nonreversing_proposal'),('certificate','independent_nonreversal_certificate_rejected'),('measured','reversing_parent_measured_geometry_invalid'),('path','nonreversing_static_path_rejected'),('parent','reversing_parent_original_guard_rejected'),('final','nonreversing_final_guard_rejected')]:
 actor=runtime.FrontCrossTrackNonreversal(Guard(failure),ROOT,S,enabled=True);actor.paths=Paths(actor.paths,failure)
 runtime.propose=lambda **unused:(None,dict(solver_success=False,solver_status=9)) if failure=='solver' else (u.copy(),copy.deepcopy(p))
 runtime.verify=lambda *a,**kw:dict(passed=False,reason='injected_certificate_failure') if failure=='certificate' else copy.deepcopy(positive)
 command,record=actor.refine(**kw);assert command is None and record['requires_stop'] and record['output_command'] is None and record['reason']==reason;assert c==before
 results.append(dict(failure=failure,reason=reason,requires_stop=True,no_command_emitted=True));print(json.dumps(results[-1]),flush=True)
runtime.propose=original_runtime_propose;runtime.verify=original_runtime_verify
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,original_v2_nan_metadata_accepted=old_nan_accepted,v3_positive_certificate_passed=positive['passed'],tamper_rejections=tamper_results,fault_injections=results,source_sha256={str(x):sha(x) for x in [Path(__file__),W/'front_cross_track_runtime_candidate_v2.py',W/'audit_front_cross_track_certificate_v2.py',W/'audit_front_cross_track_certificate_v3.py',detail_path,ep/'coordination.json',ep/'frontal_bypass.json']},installed=False,physics_started=False,training_ready=False,limitations=['Fault injection verifies component return contract only; native collector must stop before assignment/history/physics.','V3 adds finite/type checks to metadata; no quality threshold or candidate optimization changed.'])
with (D/'RESULT.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,tamper_rejections=len(tamper_results),fault_injections=len(results))),flush=True)
