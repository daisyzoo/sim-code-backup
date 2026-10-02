"""Guarded unload feasibility at the first causal measured-stall request.
No state commit or physics; a passing nominal lift is not measured unloading.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_recovery_tracking';sys.path[:0]=[str(W),str(S),str(ROOT)]
from rear_corridor_measured_stall_unload_candidate import solve_lift
from clearance_runtime import ClearanceGuard
from audit_rear_recovery_tracking_records import RecoveryVerifier
from rear_corridor_latched_stationarity import verify
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ep=Path(sys.argv[1]).resolve();dest=ep/'MEASURED_STALL_UNLOAD_PROBE.json';assert not dest.exists();screen=json.loads((ep/'MEASURED_REAR_RECOVERY_STALL_SCREEN_V2.json').read_text());trigger=screen['first_trigger'];assert trigger is not None
for p,h in screen['source_sha256'].items():assert sha(p)==h,p
rs={r['step']:r for r in json.loads((ep/'rear_corridor_recovery.json').read_text())['rows']};t=trigger['step'];r=rs[t];row=r['parent_row'];c=r['parent_coordinate']
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
request=dict(applied=False,requires_recontact=True,reason='measured_recovery_stall',measured_progress_witness=trigger)
guard=ClearanceGuard(ROOT,S);ind=RecoveryVerifier(ROOT,S);args=dict(guard=guard,row=row,coordinate=c,current=q[t],previous=u[t-1],parent_command=r['parent_command'],recovery_result=request);cmd,result=solve_lift(**args);proof=None
if cmd is not None:
 assert result['applied'] and guard.command(cmd,q[t],u[t-1])['accepted'];side=c['active_side'];offset=np.asarray(row['control_offset_local']);T=ind.hand.fk(cmd,side);T0=ind.hand.fk(q[t],side);delta=T[:3,3]+T[:3,:3]@offset-(T0[:3,3]+T0[:3,:3]@offset);v=np.asarray(ind.vertices[side]);height_gain=float((v@T[:3,:3].T+T[:3,3])[:,2].min()-(v@T0[:3,:3].T+T0[:3,3])[:,2].min())
 assert max(abs(delta[:2]))<=1e-7 and .0005-1e-7<=delta[2]<=.003+1e-7 and height_gain>=.0005-1e-7
 assert np.all(cmd>=ind.lower-2e-7) and np.all(cmd<=ind.upper+2e-7) and np.all(abs(cmd-q[t])<=ind.steps+2e-7) and max(abs(cmd-u[t-1]))<=.0550002 and min(ind.elbows.gap(cmd))>=.005-2e-7
 cert=verify(ind,row=row,coordinate=c,current=q[t],previous=u[t-1],command=cmd,kind='unload',geometry=r['geometry'],recovery_active=True);assert cert['passed'],cert
 proof=dict(nominal_delta_xyz_mm=(delta*1000).tolist(),all_vertex_lowest_height_gain_mm=height_gain*1000,stationarity=cert)
else:assert result['requires_stop']
negative=[]
for label,mutation in [('missing_witness',lambda x:x.pop('measured_progress_witness')),('future_step',lambda x:x['measured_progress_witness'].update(step=t+1)),('not_stalled',lambda x:x['measured_progress_witness'].update(stalled=False)),('wrong_window',lambda x:x['measured_progress_witness'].update(previous_actual_recovery_steps=[t-29,t])),('fabricated_failure_reason',lambda x:x.update(reason='anything'))]:
 bad=copy.deepcopy(request);mutation(bad);kw=dict(args,recovery_result=bad)
 try:solve_lift(**kw)
 except ValueError:negative.append(label)
 else:raise AssertionError(label)
sources=dict(screen['source_sha256']);sources[str(ep/'MEASURED_REAR_RECOVERY_STALL_SCREEN_V2.json')]=sha(ep/'MEASURED_REAR_RECOVERY_STALL_SCREEN_V2.json')
for p,h in sources.items():assert sha(p)==h,p
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,status='complete',passed=True,actual_source_episode=str(ep),step=t,trigger=trigger,verified_unload_available=cmd is not None,result=result,independent_proof=proof,negative_checks=negative,source_sha256=sources,code_sha256={str(p):sha(p) for p in [Path(__file__),W/'rear_corridor_measured_stall_unload_candidate.py',W/'rear_corridor_latched_stationarity.py',W/'audit_rear_recovery_tracking_records.py',S/'clearance_runtime.py']},simulation_started=False,training_ready=False,remaining='A separate actual history-state observer, commit/lift/handover integration and independent native proof are needed before any new paired physical experiment; no production changes.')
with dest.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(episode=ep.name,step=t,verified_unload_available=cmd is not None,independent_proof=proof,negative_checks=negative),indent=2))
