"""Independent recorded geometry and force timeline after the actual bag handover.
No future rollout, new controller, or causal success claim.
"""
from pathlib import Path
import json,datetime,hashlib,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_inactive_clearance';R=W/'front_inactive_clearance_physical_r1';E=R/'case_840023/layout_840023_nudge_mailer_to_bin';sys.path[:0]=[str(W),str(ROOT)]
from audit_front_recontact_center_events import RecoveryEventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());hand=RecoveryEventAudit(ROOT,S).hand
with np.load(E/'raw.npz') as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
fr={r['step']:r for r in read(E/'frontal_bypass.json')['rows']};co={r['step']:r for r in read(E/'coordination.json')};packets={r['after_action_step']:r for r in read(E/'solved_contact_forces.json')['rows']};events=read(E/'front_recontact_center.json')['rows'];handover=next(r for r in events if r['kind']=='handover');start=handover['step'];end=next(r['step'] for r in fr.values() if r.get('route_stop_reason'))
rows=[]
for t in range(start,end+1):
 f=fr[t];c=co[t];T=hand.fk(q[t],'right');lowest=hand.minz(q[t],'right');nominal=hand.minz(u[t],'right');rot=float((hand.vertices['right']@T[:3,:3].T)[:,2].min());assert abs(lowest-T[2,3]-rot)<1e-12
 np.testing.assert_allclose(c['upper_q'],q[t],rtol=0,atol=1e-6)
 load=sum(abs(float(v['force_world_N'][2])) for v in packets[t-1]['parcel_contacts'] if any('left_wrist_roll' in s for s in v['shapes']) and any('/mailer/' in s for s in v['shapes']));assert abs(load-f['contact_load']['observed_vertical_load_n'])<1e-8
 anchor=np.array(c['inactive_anchor']);palm=np.array(c['palm_positions']['right']);assert anchor.shape==palm.shape==(3,)
 rows.append(dict(step=t,mode=f['mode'],recontacts=f['recontacts'],measured_lowest_z_mm=lowest*1000,command_pose_lowest_z_mm=nominal*1000,wrist_origin_z_mm=float(T[2,3]*1000),rotation_support_z_mm=rot*1000,inactive_palm_z_mm=float(palm[2]*1000),anchor_z_mm=float(anchor[2]*1000),palm_tracking_z_mm=float((palm[2]-anchor[2])*1000),observed_load_n=load,filtered_load_n=f['contact_load']['filtered_vertical_load_n'],controller=c.get('controller_kind')))
firsts={}
for threshold in [841.,840.,835.,830.]:
 firsts[str(threshold)]=next((r for r in rows if r['measured_lowest_z_mm']<threshold-0.0002),None)
initial=rows[0];minimum=min(rows,key=lambda r:r['measured_lowest_z_mm']);cross=firsts['840.0'];assert cross
changes=dict(total_lowest_change_mm=cross['measured_lowest_z_mm']-initial['measured_lowest_z_mm'],wrist_origin_change_mm=cross['wrist_origin_z_mm']-initial['wrist_origin_z_mm'],rotation_support_change_mm=cross['rotation_support_z_mm']-initial['rotation_support_z_mm'],palm_tracking_change_mm=cross['palm_tracking_z_mm']-initial['palm_tracking_z_mm'],anchor_z_change_mm=cross['anchor_z_mm']-initial['anchor_z_mm'])
assert abs(changes['total_lowest_change_mm']-changes['wrist_origin_change_mm']-changes['rotation_support_change_mm'])<1e-9
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,actual_handover_step=start,first_original_corridor_stop_step=end,first_below_mm=firsts,at_handover=initial,minimum=minimum,first_840mm_crossing_decomposition=changes,anchor_z_range_mm=[min(r['anchor_z_mm'] for r in rows),max(r['anchor_z_mm'] for r in rows)],frames=len(rows),rows=rows,interpretation='Measured lowest-point floor is distinct from a palm-position anchor. Timing distinguishes loaded transport from later unloaded-entry rejection; command-pose geometry is not an actual predicted response. Preserve original floors and retain failed trial.',source_sha256={str(p):sha(p) for p in [Path(__file__),W/'audit_front_recontact_center_events.py',E/'raw.npz',E/'coordination.json',E/'frontal_bypass.json',E/'solved_contact_forces.json',E/'front_recontact_center.json',ROOT/'assets/robots/g1_hand_support_vertices.json']},training_ready=False)
with (R/'INACTIVE_CLEARANCE_LOSS_TIMING.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:out[k] for k in ['frames','actual_handover_step','first_below_mm','minimum','first_840mm_crossing_decomposition','anchor_z_range_mm']}))
