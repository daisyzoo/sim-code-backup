"""Decompose inactive-hand height loss after the actual first bag handover.
Raw q, observed wrist pose, stored inactive anchor and original geometry are
cross-bound. Pure vertical translations below are geometric counterfactuals,
not predictions of a different controller or evidence of physical success.
"""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_headroom';sys.path[:0]=[str(W),str(ROOT)]
from audit_front_initial_center_planning_v2 import SelectionAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();R=W/'front_recontact_headroom_physical_r1';ep=R/'case_840023/layout_840023_nudge_mailer_to_bin';a=SelectionAudit(ROOT,S)
events=json.loads((ep/'front_recontact_center.json').read_text())['rows'];coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())}
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float)
handover=next(e for e in events if e['kind']=='handover');assert handover['step']==299
old=np.asarray(handover['old_inactive_anchor']);captured=np.asarray(handover['captured_inactive_anchor_world']);offset=np.array([.20,0.,.007]);records=[]
for e in events:
 if not e.get('reason','').startswith('waiting_for_') or e['step']<299:continue
 t=e['step'];c=e['context'];np.testing.assert_allclose(c['current'],q[t],atol=1e-7,rtol=0);g,_=a.geometry(q[t],c['scene']);pose=np.asarray(c['observed_inactive_hand_pose']);palm=pose[:3,3]+pose[:3,:3]@offset;anchor=np.asarray(coords[t]['inactive_anchor']);np.testing.assert_allclose(anchor,captured,atol=0,rtol=0);np.testing.assert_allclose(palm,coords[t]['palm_positions']['right'],atol=1e-7,rtol=0)
 verts=a.hand.vertices['right'];world=verts@pose[:3,:3].T+pose[:3,3];lowest=float(world[:,2].min());np.testing.assert_allclose(lowest,g['inactive_lowest_z_m'],atol=1e-6,rtol=0)
 nominal=a.hand.fk(q[t],'right');np.testing.assert_allclose(nominal,pose,atol=1e-6,rtol=0)
 shape=float(np.min((verts-offset)@pose[:3,:3].T,axis=0)[2]);assert abs(palm[2]+shape-lowest)<1e-12
 records.append(dict(step=t,counter=e['real_recontact_index'],reason=e['reason'],inactive_lowest_z_m=lowest,palm_z_m=float(palm[2]),anchor_z_m=float(anchor[2]),palm_z_tracking_error_m=float(palm[2]-anchor[2]),orientation_shape_height_from_palm_m=shape,required_pure_vertical_translation_to_entry_m=max(0.,.841-lowest),counterfactual_lowest_if_palm_exactly_at_current_anchor_z_m=float(anchor[2]+shape),counterfactual_lowest_if_palm_exactly_at_old_anchor_z_m=float(old[2]+shape),original_geometry_accepted=g['accepted']))
groups=[]
for n in sorted({v['counter'] for v in records}):
 rows=[v for v in records if v['counter']==n];eligible=[v for v in rows if v['original_geometry_accepted']]
 def span(k):return [min(v[k] for v in rows),max(v[k] for v in rows)]
 groups.append(dict(counter=n,rows=len(rows),inactive_z_range_m=span('inactive_lowest_z_m'),tracking_error_range_m=span('palm_z_tracking_error_m'),orientation_shape_range_m=span('orientation_shape_height_from_palm_m'),required_translation_range_m=span('required_pure_vertical_translation_to_entry_m'),original_geometry_accepted=len(eligible),current_anchor_exact_geometry_above_entry=sum(v['counterfactual_lowest_if_palm_exactly_at_current_anchor_z_m']>=.841 for v in rows),old_anchor_exact_geometry_above_entry=sum(v['counterfactual_lowest_if_palm_exactly_at_old_anchor_z_m']>=.841 for v in rows)))
files=[Path(__file__),ep/'raw.npz',ep/'front_recontact_center.json',ep/'coordination.json',R/'LATE_RECOVERY_WINDOW_DIAGNOSIS.json',W/'audit_front_initial_center_planning_v2.py',W/'audit_front_initial_center_events.py']
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,handover_step=299,old_anchor_xyz=old.tolist(),captured_anchor_xyz=captured.tolist(),anchor_change_m=(captured-old).tolist(),records=records,groups=groups,conclusion='Handover lowered inactive palm anchor; subsequent palm tracking error and changing hand orientation jointly reduce lowest-hand height. A fixed palm target alone does not enforce minimum hand height. Test coordinated inactive-hand clearance/anchor retention without relaxing original geometry gates.',source_sha256={str(p):sha(p) for p in files},physical_candidate_started=False,training_ready=False)
with (R/'INACTIVE_ANCHOR_HEIGHT_DIAGNOSIS.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(anchor_change_m=out['anchor_change_m'],groups=groups),indent=2))
