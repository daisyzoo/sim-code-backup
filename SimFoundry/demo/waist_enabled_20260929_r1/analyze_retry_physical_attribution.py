"""Separate an enabled option from an actually executed retry intervention.
Compare full observed prefixes only; post-divergence outcomes are not a paired
counterfactual and are never credited to a branch that was not selected.
"""
from pathlib import Path
import sys,json,hashlib,datetime,collections
import numpy as np
W=Path(__file__).resolve().parent;ep=Path(sys.argv[1]).resolve();old=W/'rear_tracking_physical_r1'/ep.parent.name/ep.name;dest=ep/'REAR_RETRY_PHYSICAL_ATTRIBUTION.json';assert not dest.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={}
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
prov=read(ep.parent/'provenance.json');oldprov=read(old.parent/'provenance.json');assert prov['args']['rear_transport_feasible_retry'] is True
from simfoundry.data.waist_pilot_protocol import semantic_settings
settings=semantic_settings(prov['args']);assert settings.pop('rear_transport_feasible_retry') is True;assert settings==semantic_settings(oldprov['args'])
events=read(ep/'recontact_pose.json')['rows'];witnesses=[]
for r in events:
 for name,node in [('planning',(r.get('planning') or {}).get('rear_transport_witness')),('measured',r.get('rear_transport_handover_witness'))]:
  if node:
   retry=node['feasible_endpoint_retry'];witnesses.append(dict(step=r['step'],entry=name,accepted=node['accepted'],retry_attempted=retry['attempted'],original_attempt=retry['original_attempt'],final_solver_status=node['solver_status'],measured_ready_count=r.get('measured_ready_count')))
arrays=[]
for root in [old,ep]:
 for name in ['raw.npz','trace.npz']:sources[str(root/name)]=sha(root/name)
 with np.load(root/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 with np.load(root/'trace.npz') as z:pos={k:z[k].astype(float) for k in ['box','mailer']}
 arrays.append((q,u,pos))
n=min(len(x[0]) for x in arrays);prefix={}
for label,a,b in [('upper_q',arrays[0][0],arrays[1][0]),('upper_command',arrays[0][1],arrays[1][1]),('box_xyz',arrays[0][2]['box'],arrays[1][2]['box']),('mailer_xyz',arrays[0][2]['mailer'],arrays[1][2]['mailer'])]:
 diff=abs(a[:n]-b[:n]).max(axis=1);first={str(tol):(int(np.flatnonzero(diff>tol)[0]) if np.any(diff>tol) else None) for tol in [0.,1e-7,1e-5,1e-3]};prefix[label]=dict(first_exceeding_abs_tolerance=first,shared_prefix_max_abs=float(diff.max()))
rr=read(ep/'rear_corridor_recovery.json');quality=read(ep/'quality.json');oldquality=read(old/'quality.json')
summary=dict(frames=quality['frames'],quality_passed=quality['passed'],target_progress_mm=quality['metrics']['target_final_progress_m']*1000,original_frames=oldquality['frames'],original_target_progress_mm=oldquality['metrics']['target_final_progress_m']*1000,actual_retry_attempts=sum(r['retry_attempted'] for r in witnesses),planned_and_measured_witnesses=witnesses,actual_handovers=rr['handovers'],recovery_kind_counts=dict(collections.Counter(r['kind'] for r in rr['rows'])),unload_steps=[r['step'] for r in rr['rows'] if r['kind']=='unload'],pending_recontact_at_end=rr['pending_recontact'],shared_observed_frames=n,prefix_differences=prefix)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,summary=summary,source_sha256=sources,analyzer_sha256=sha(__file__),training_ready=False,intervention_benefit_proven=False,limitations=['Equal requested seed/settings do not ensure identical simulation trajectories.','No unique cause of floating-point/physical divergence is asserted.','Actual zero retry executions cannot demonstrate the retry branch physical benefit.'])
with dest.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(summary,indent=2))
