"""Six actual unloaded recovery contexts, original centered physical-hull planner.
No lifecycle counter is rewritten and no action is executed. Inspect first
recorded unloaded top_cross observation per recovery, before corridor guard;
no selection by optimizer outcome. Independent geometry checks every returned
endpoint and sampled path. Static local solutions are not physical transfers.
"""
from pathlib import Path
import sys,datetime,hashlib,json,os
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_waypoint_reconciliation';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_initial_center_plan import plan
from audit_front_initial_center_events import EventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
D=W/'front_bag_recontact_center_draft_r2';D.mkdir(exist_ok=False);out=D/'STATIC_CONTEXT_PROBE.json';guard=ClearanceGuard(ROOT,S);ind=EventAudit(ROOT,S);rows=[];sources={str(Path(__file__)):sha(__file__)};sources.update(guard.model.source_sha256)
for p in S.glob('*.py'):sources[str(p)]=sha(p)
sources[str(W/'audit_front_initial_center_events.py')]=sha(W/'audit_front_initial_center_events.py')
def save(status,**kw):
 p=D/'STATUS.tmp';p.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed=len(rows),**kw),indent=2));p.replace(D/'STATUS.json')
try:
 for run in ['front_corridor_midpoint_physical_r1','front_drive_1mm_physical_r1']:
  ep=W/run/'case_840023/layout_840023_nudge_mailer_to_bin';binding=json.loads((ep/'FRONT_BAG_TORQUE_FINDINGS.json').read_text()) if (ep/'FRONT_BAG_TORQUE_FINDINGS.json').exists() else json.loads((W/'front_drive_1mm_physical_r1/FRONT_BAG_TORQUE_FINDINGS.json').read_text())
  for name,h in binding['source_sha256'].items():assert sha(name)==h,name
  fr=json.loads((ep/'frontal_bypass.json').read_text());assert fr['plan']['front_route_selected'];events=json.loads((ep/'front_initial_center.json').read_text())['rows'];initial=next(e['context']['scene'] for e in events if e.get('context') and e['kind']=='command');guard_step=next(r['step'] for r in fr['rows'] if r['mode']=='front_guard_lift')
  with np.load(ep/'raw.npz') as a:q=a['q'][:,12:23].astype(float);u=a['action'][:,12:23].astype(float)
  with np.load(ep/'trace.npz') as a:positions={k:a[k] for k in ['box','mailer']}
  with np.load(ep/'parcel_orientation.npz') as a:quats={k:a[k] for k in ['box','mailer']}
  for name in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','front_initial_center.json']:sources[str(ep/name)]=sha(ep/name)
  counters=sorted({r['recontacts'] for r in fr['rows'] if 0<r.get('recontacts',0) and r['step']<guard_step});assert counters==[1,2,3]
  for counter in counters:
   candidates=[r for r in fr['rows'] if r.get('recontacts',0)==counter and r['step']<guard_step and r['mode']=='top_cross' and r['contact_load']['observed_vertical_load_n']==0 and 0<=r['contact_load']['filtered_vertical_load_n']<=.05]
   assert candidates,('no unloaded cross',run,counter);r=candidates[0];t=r['step'];scene=RecontactScene(guard,'left',positions['mailer'][t],quats['mailer'][t],initial['core_size'],positions['box'][t],quats['box'][t],initial['other_size']);actual,detail=ind.geometry(q[t],scene.record());save('running',run=run,recontacts=counter,step=t)
   planned=plan(scene,q[t],step=t);checks=[]
   for attempt in planned['attempts']:
    if attempt['endpoint'] is None:continue
    x=np.asarray(attempt['endpoint']);g,d=ind.geometry(x,scene.record());axis=np.linalg.eigh(np.cov(ind.hand.vertices['left'].T))[1][:,0];align=abs(d['rotation'][:,2]@d['pose'][:3,:3]@axis);minimum=float(min(align**2-.8**2,*list(.002-abs(d['point'][:2])),g['active_above_top_m']-.006,.007-g['active_above_top_m'],g['inactive_lowest_z_m']-.84,g['elbow_gap_m']-.005));assert abs(minimum-attempt['minimum_constraint_m'])<2e-8
    ok=bool(attempt['status']==0 and minimum>=-2e-7 and g['accepted'] and np.all(x>=ind.lo-2e-7) and np.all(x<=ind.hi+2e-7));assert ok==attempt['endpoint_accepted']
    path=attempt['nominal_path'];path_checks=[] if path is None else [ind.geometry(np.asarray(v),scene.record())[0] for v in path['waypoints']]
    if path is not None:assert path['accepted']==all(c['accepted'] for c in path_checks)
    checks.append(dict(seed=attempt['seed'],endpoint_passed=ok,endpoint_geometry=g,independent_minimum=minimum,nominal_nodes=len(path_checks),independent_path_passed=bool(path_checks and all(c['accepted'] for c in path_checks)),path_geometry=path_checks))
   row=dict(run=run,episode=ep.name,step=t,recontacts=counter,mode=r['mode'],last_recontact_reason=r['last_recontact_reason'],observed_load_n=r['contact_load']['observed_vertical_load_n'],filtered_load_n=r['contact_load']['filtered_vertical_load_n'],actual_start=q[t].tolist(),previous_q=q[t-1].tolist(),previous_command=u[t-1].tolist(),initial_scene=actual,planning=planned,independent_checks=checks);rows.append(row);print(json.dumps(dict(run=run,step=t,recontacts=counter,accepted=planned['accepted'],reason=planned['reason'],endpoints=sum(x['endpoint_passed'] for x in checks),paths=sum(x['independent_path_passed'] for x in checks))),flush=True)
 assert len(rows)==6
 result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=rows,accepted_contexts=sum(r['planning']['accepted'] for r in rows),source_sha256=sources,simulation_started=False,collector_integrated=False,training_ready=False,limitations=['Planner checks selected hand/parcel and elbow geometry at sampled nodes, not a swept full-body proof.','Original affine causal transport and actual three-frame measured handover still required; no physical success claim.','Original recontacts counters are retained in input evidence; initial-only live eligibility has not been bypassed.'])
 with out.open('x') as f:json.dump(result,f,indent=2)
 save('complete',accepted_contexts=result['accepted_contexts'],report_sha256=sha(out))
except Exception as e:save('failed',error=repr(e));raise
