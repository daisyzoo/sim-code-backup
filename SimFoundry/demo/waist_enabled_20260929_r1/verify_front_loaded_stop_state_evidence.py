"""Correct the earlier overly broad missing-stop-q statement from actual logs.
Raw lacks the attempted step; self_clearance retains its pre q/link poses.
Parcel orientation at that attempted step is still absent; no full geometry or
successful recovery is inferred from this partial-state verification.
"""
from pathlib import Path
import json,hashlib,datetime,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(W))
from audit_unloaded_wrist_prior_live import HandModel,near
model=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};records=[]
for layout,task in [(840023,'nudge_mailer_to_bin'),(840020,'push_box_to_bin')]:
 ep=W/'front_loaded_physical_r1'/f'case_{layout}'/f'layout_{layout}_{task}'
 def read(n):sources[str(ep/n)]=sha(ep/n);return json.loads((ep/n).read_text())
 clear=read('self_clearance.json');failure=clear['failure'];t=failure['step'];pre=[r for r in clear['rows'] if r['step']==t];assert len(pre)==1 and pre[0]['phase']=='pre' and pre[0]['accepted'];pre=pre[0]
 post=next(r for r in clear['rows'] if r['step']==t-1 and r['phase']=='post');near(pre['upper_q'],post['upper_q'],0.);assert pre['runtime_link_poses']==post['runtime_link_poses'];q=np.array(pre['upper_q']);assert q.shape==(11,)
 with np.load(ep/'raw.npz') as z:assert len(z['q'])==t;last=z['action'][-1,12:23].astype(float)
 final=next(r for r in clear['rows'] if r['step']==t-1 and r['phase']=='final_command');near(last,final['command'],0.)
 packets=read('solved_contact_forces.json')['rows'];p=packets[-1];assert p['after_action_step']==t-1
 errors={}
 for side in ['left','right']:
  position=model.fk(q,side)[:3,3];actual=p['post_action_pose']['palm_'+side];near(position,actual,1e-4);errors[side]=float(np.linalg.norm(position-actual))
 with np.load(ep/'parcel_orientation.npz') as z:assert len(z['box'])==len(z['mailer'])==t
 for n in ['raw.npz','parcel_orientation.npz']:sources[str(ep/n)]=sha(ep/n)
 records.append(dict(episode=ep.name,attempted_stop_step=t,stop_q_present_in_self_clearance_pre=True,stop_q_equals_previous_post=True,runtime_torso_elbow_poses_present=list(pre['runtime_link_poses']),hand_fk_vs_last_packet_position_error_m=errors,stop_parcel_quaternion_present=False,full_stop_material_geometry_independently_verified=False,training_ready=False))
for p in [Path(__file__),W/'audit_unloaded_wrist_prior_live.py',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json']:sources[str(p)]=sha(p)
out=W/'FRONT_LOADED_STOP_STATE_EVIDENCE_CORRECTION.json';assert not out.exists()
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,records=records,source_sha256=sources,correction='Previous raw/q/quat array-length statements were correct, but saying no stop q was saved anywhere was too broad. Exact attempted-step pre q and torso/elbow poses already exist in self_clearance; material orientation remains missing.',training_ready=False)
out.write_text(json.dumps(report,indent=2));print(json.dumps(records,indent=2))
