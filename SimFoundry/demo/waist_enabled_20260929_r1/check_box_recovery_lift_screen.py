"""Independent URDF geometry check of recorded offline lift endpoints/paths only."""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_box_center_preference';sys.path[:0]=[str(w),str(repo)]
from audit_slow_drag_plan import PlanAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();p=w/'BOX_RECOVERY_LIFT_SCREEN.json';d=json.loads(p.read_text());assert d['complete'];assert all(sha(k)==v for k,v in d['source_sha256'].items());audit=PlanAudit(repo,stage);rows=[]
for row in d['rows']:
 ep=w/row['run']/'case_840001/layout_840001_push_box_to_bin';events=json.loads((ep/'recontact_pose.json').read_text())['rows'];ev=next(e for e in events if e.get('reason')=='initial_hand_below_unloaded_planning_height' and e['context']['recontacts']==row['recontacts']);assert ev['step']==row['step'];ctx=ev['context'];q=np.array(ctx['current']);scene=ctx['scene'];lift=row['lift'];assert row['geometry_accepted'];audit.lift(lift,q,lift['height_m'],scene);audit.checked_path(row['path'],[q,np.array(lift['candidate'])],scene);z=audit.hand.minz(lift['candidate'],'right');assert z>=.84 and abs(z-row['nominal_endpoint_lowest_world_z_m'])<1e-8
 bad=copy.deepcopy(lift);bad['candidate'][0]=2.
 try:audit.lift(bad,q,lift['height_m'],scene)
 except (AssertionError,ValueError):pass
 else:raise AssertionError('invalid joint endpoint accepted')
 rows.append(dict(run=row['run'],step=row['step'],waypoints=len(row['path']['waypoints']),independent_geometry_passed=True,invalid_joint_endpoint_rejected=True))
out=dict(completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,rows=rows,source_sha256={str(f):sha(f) for f in [Path(__file__),p,w/'audit_slow_drag_plan.py',w/'audit_recontact_interior_events.py',w/'audit_recontact_pose_events.py']},physical_validation=False,training_ready=False)
(w/'BOX_RECOVERY_LIFT_INDEPENDENT_CHECK.json').write_text(json.dumps(out,indent=2));print('INDEPENDENT',len(rows),'PASS')
