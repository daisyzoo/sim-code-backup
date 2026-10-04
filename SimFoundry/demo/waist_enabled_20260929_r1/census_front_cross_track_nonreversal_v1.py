"""Census every frame in the original ten-condition run; no dynamics or admission."""
from pathlib import Path
import collections,datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';D=W/'front_cross_track_full_stream_probe_r1';D.mkdir(exist_ok=False);sys.path[:0]=[str(S),str(W),str(ROOT)]
from audit_unloaded_wrist_prior_live import HandModel
hand=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json')
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();R=W/'front_effective_height_physical_r1';protocol=read(R/'PROTOCOL.json');sources={str(Path(__file__)):sha(__file__),str(R/'PROTOCOL.json'):sha(R/'PROTOCOL.json')};episodes=[];required=[]
for spec in protocol['plan']['commands']:
 for task in spec['tasks']:
  ep=R/f"case_{spec['layout_id']}"/f"layout_{spec['layout_id']}_{task}";tp=read(ep/'joint_transport_clearance.json')['rows'];co={} if spec['wait'] else {c['step']:c for c in read(ep/'coordination.json')};fr={} if spec['wait'] else {r['step']:r for r in read(ep/'frontal_bypass.json')['rows']};counts=collections.Counter();rows=[]
  with np.load(ep/'raw.npz') as z:u=z['action'][:,12:23].copy()
  assert [r['step'] for r in tp]==list(range(len(u)))
  for t,r in enumerate(tp):
   np.testing.assert_array_equal(r['output_command'],u[t])
   if not r['selected']:counts['not_captured_front']+=1;continue
   row=fr[t];c=co[t]
   if row['mode']!='top_push':counts['nonpush']+=1;continue
   if row.get('route_stage')!='lateral_y':counts['not_lateral']+=1;continue
   if any(c.get(k) is not None for k in ['front_recontact_center_override','front_initial_center_override','recontact_pose_override']) or c.get('terminal_joint_hold') or row.get('route_stop_reason') or row.get('hand_guard_saturated'):counts['original_precedence']+=1;continue
   sc=r['collector_context']['scene'];side=sc['side'];task_error=c['task_inputs']['error'][0 if side=='left' else 3];direction=float(np.sign(task_error))
   if direction==0:counts['zero_request']+=1;continue
   q=np.array(c['task_inputs']['current']);normal=Rotation.from_quat(sc['target_quat']).as_matrix()[:,2];center=np.array(c['active_support_reference']['center_local'])
   def point(v):
    T=hand.fk(v,side);n=T[:3,:3].T@normal;off=center+n*(min(hand.vertices[side]@n)-center@n);return T[:3,3]+T[:3,:3]@off
   current=point(q);np.testing.assert_allclose(current,row['observed_support_xyz'],rtol=0,atol=2e-6)
   dx=float(point(u[t])[0]-current[0]);signed=direction*dx;bad=signed < -2e-7;counts['reversed' if bad else 'already_nonreversing']+=1
   out=dict(step=t,side=side,requested_direction=direction,original_requested_dx_m=task_error,emitted_nominal_dx_m=dx,signed_emitted_nominal_dx_m=signed,needs_proposal=bool(bad),original_transport_applied=r['applied'],original_transport_reason=r['reason'],observed_load_n=row['contact_load']['observed_vertical_load_n']);rows.append(out)
   if bad:required.append(dict(episode=str(ep),**out))
  assert sum(counts.values())==len(u)
  episodes.append(dict(episode=str(ep),wait=spec['wait'],frames=len(u),counts=dict(counts),selected_lateral_push_rows=rows))
  for name in ['raw.npz','joint_transport_clearance.json']+([] if spec['wait'] else ['coordination.json','frontal_bypass.json']):sources[str(ep/name)]=sha(ep/name)
  print(json.dumps(dict(episode=ep.name,frames=len(u),counts=dict(counts))),flush=True)
for p in [W/'audit_unloaded_wrist_prior_live.py',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json']:sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=episodes,required_proposals=required,frame_count=sum(e['frames'] for e in episodes),source_sha256=sources,training_ready=False,limitations=['Recorded final command inspected with actual history fixed.','Candidate would need an explicit stop/rejection if a reversing command cannot be replaced safely; silently returning the same reversing parent would not satisfy the proposed rule.','Includes all eight pushes and both waits; only selected lateral pushing cases need the new constraint.'])
with (D/'CENSUS.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(total_frames=report['frame_count'],required_proposals=len(required))),flush=True)
