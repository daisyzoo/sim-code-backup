"""Independently diagnose compact rejected-plan records and auditor coverage.
Preserves original logs, absent reports and failure statuses. No gate relaxation.
"""
from pathlib import Path
import sys,json,numpy as np,hashlib,datetime
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from audit_recontact_interior_events import EventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
a=EventAudit(W.parents[1],W/'staged_joint_edge_clearance_intersection');ep=W/'joint_edge_intersection_physical_r1/case_840015/layout_840015_push_box_to_bin';events=json.loads((ep/'recontact_pose.json').read_text())['rows'];rows=[]
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
for event in events:
 planning=event.get('planning');pref=planning.get('interior_preference',{}) if planning else {};deep=pref.get('preferred_plan',{})
 if deep!={'accepted':False,'reason':'current_scene_rejected'}:continue
 t=event['step'];ctx=event['context'];assert np.max(abs(q[t]-ctx['current']))<1e-7 and ctx['step']==t and event['kind']=='unchanged'
 geometry,_=a.geometry(q[t],ctx['scene']);assert geometry['accepted'] is False
 low=a.lo.copy();high=a.hi.copy();low[0]=-1;high[0]=1;violation=np.maximum(low-q[t],q[t]-high);indices=np.flatnonzero(violation>2e-7)
 rows.append(dict(step=t,event_kind=event['kind'],compact_preferred_rejection=deep,observed_geometry=geometry,measured_bounds_violations=[dict(upper_index=int(i),q_rad=float(q[t,i]),action_rad=float(u[t,i]),lower_rad=float(low[i]),upper_rad=float(high[i]),excess_rad=float(violation[i])) for i in indices],action_max_bound_excess_rad=float(max(0,np.max(low-u[t]),np.max(u[t]-high)))))
assert [r['step'] for r in rows]==[948,1117]
files=[ep/'raw.npz',ep/'recontact_pose.json',ep/'audit_joint_edge_stage_pose_live.py.log',W/'audit_recontact_interior_events.py',W/'audit_recontact_pose_events.py',W/'staged_joint_edge_clearance_intersection/recontact_plan_deeper.py']
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256={str(p):sha(p) for p in files},analyzer_sha256=sha(__file__),full_audit_passed=False,training_ready=False,next_step='Handle compact current_scene_rejected explicitly in a separate auditor version using independently rejected actual geometry and exact parent/fallback consistency. Preserve no plan execution and all other checks; do not invent missing fields or mark original audit passed.')
with (ep.parent.parent/'SWAP_BOX_REJECTED_SCENE_FINDINGS.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(rows,indent=2))
