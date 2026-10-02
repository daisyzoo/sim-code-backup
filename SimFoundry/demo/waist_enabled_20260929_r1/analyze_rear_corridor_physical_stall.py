"""Descriptive realized-vs-nominal recovery motion from a complete physical run.
Independent URDF FK uses the same pre-action frozen point for all three poses.
Does not replace native audits or prove a unique friction/contact cause.
"""
from pathlib import Path
import sys,json,hashlib,datetime,collections
import numpy as np
from audit_unloaded_wrist_prior_live import HandModel
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
ep=Path(sys.argv[1]).resolve();dest=ep/'REAR_RECOVERY_STALL_FINDINGS.json';assert not dest.exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
fr=json.loads((ep/'frontal_bypass.json').read_text());fs={r['step']:r for r in fr['rows']};rr=json.loads((ep/'rear_corridor_recovery.json').read_text());changed=[r for r in rr['rows'] if r['kind']=='loaded_recovery'];assert changed
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float);task=str(z['task_id'])
assert len(q)==1200
side='right' if task=='push_box_to_bin' else 'left';key='box' if side=='right' else 'mailer';actor='parcel_box' if key=='box' else 'mailer';other='mailer' if key=='box' else 'box';direction=-1 if side=='right' else 1
with np.load(ep/'trace.npz') as z:positions={k:z[k].astype(float) for k in ['box','mailer']}
clear=json.loads((ep/'self_clearance.json').read_text());assert clear['failure'] is None;post={r['step']:r for r in clear['rows'] if r['phase']=='post'};packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
model=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json');records=[]
for r in changed:
 t=r['step'];f=fs[t];offset=np.asarray(f['control_offset_local']);qafter=np.asarray(post[t]['upper_q']);assert np.array_equal(u[t],r['emitted_command'])
 if t+1<len(q):assert np.max(abs(qafter-q[t+1]))<1e-6
 def point(x):
  T=model.fk(x,side);return T[:3,3]+T[:3,:3]@offset
 before=point(q[t]);nominal=point(u[t]);realized=point(qafter);assert np.max(abs(before-f['observed_support_xyz']))<2e-6
 assert np.max(abs(nominal-r['commit']['new']['command']))<2e-6
 packet=packets[t];object_after=np.asarray(packet['post_action_pose'][key]);object_before=positions[key][t]
 contacts=[c for c in packet['parcel_contacts'] if any(side+'_wrist_roll' in s for s in c['shapes']) and any('/'+actor+'/' in s for s in c['shapes'])]
 object_contacts=[c for c in packet['parcel_contacts'] if any('/parcel_box/' in s for s in c['shapes']) and any('/mailer/' in s for s in c['shapes'])]
 nominal_delta=nominal-before;actual_delta=realized-before;parent_y=r['parent_row']['target_xyz'][1];committed_y=r['commit']['new']['command'][1]
 records.append(dict(step=t,deficit_mm=r['recovery']['rear_deficit_m']*1000,requested_x_mm=r['recovery']['requested_x_m']*1000,nominal_delta_xyz_mm=(nominal_delta*1000).tolist(),realized_frozen_point_delta_xyz_mm=(actual_delta*1000).tolist(),object_delta_xyz_mm=((object_after-object_before)*1000).tolist(),forward_lead_removed_mm=direction*(parent_y-committed_y)*1000,filtered_vertical_load_n=f['contact_load']['filtered_vertical_load_n'],last_tick_wrist_force_norm_sum_n=sum(float(np.linalg.norm(c['force_world_N'])) for c in contacts),last_tick_object_object_force_norm_sum_n=sum(float(np.linalg.norm(c['force_world_N'])) for c in object_contacts),max_joint_tracking_error_rad=float(abs(u[t]-qafter).max())))
def stats(x):
 x=np.asarray(x,float);return dict(min=float(x.min()),p10=float(np.quantile(x,.1)),median=float(np.median(x)),p90=float(np.quantile(x,.9)),max=float(x.max()),mean=float(x.mean()),sum=float(x.sum()))
summary=dict(first_step=records[0]['step'],last_step=records[-1]['step'],changed_steps=len(records),unload_steps=sum(r['kind']=='unload' for r in rr['rows']),deficit_mm=stats([r['deficit_mm'] for r in records]),deficit_below_0p1mm_steps=sum(r['deficit_mm']<.1 for r in records),deficit_below_1mm_steps=sum(r['deficit_mm']<1 for r in records),nominal_x_mm=stats([r['nominal_delta_xyz_mm'][0] for r in records]),realized_point_x_mm=stats([r['realized_frozen_point_delta_xyz_mm'][0] for r in records]),object_x_mm=stats([r['object_delta_xyz_mm'][0] for r in records]),forward_lead_removed_mm=stats([r['forward_lead_removed_mm'] for r in records]),filtered_load_n=stats([r['filtered_vertical_load_n'] for r in records]),last_tick_force_norm_sum_n=stats([r['last_tick_wrist_force_norm_sum_n'] for r in records]),object_object_nonzero_final_tick_steps=sum(r['last_tick_object_object_force_norm_sum_n']>1e-8 for r in records),non_target_max_xy_mm=float(np.linalg.norm(positions[other][:,:2]-positions[other][0,:2],axis=1).max()*1000))
inputs=['raw.npz','trace.npz','frontal_bypass.json','rear_corridor_recovery.json','self_clearance.json','solved_contact_forces.json','quality.json'];report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=str(ep),summary=summary,records=records,source_sha256={n:sha(ep/n) for n in inputs},analyzer_sha256=sha(Path(__file__)),independent_fk_sha256=sha(W/'audit_unloaded_wrist_prior_live.py'),limitations=['Sum of FK point changes uses a separately frozen local point on each step; not a single material point trajectory.','Last-tick contact summaries do not replace all24-substep contact audits.','These are observed associations, not proof that friction alone or the controller alone caused stagnation.'],training_ready=False)
dest.write_text(json.dumps(report,indent=2));print(json.dumps(summary,indent=2))
