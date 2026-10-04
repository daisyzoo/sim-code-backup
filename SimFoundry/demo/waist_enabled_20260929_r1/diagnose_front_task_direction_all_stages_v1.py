"""Recorded two-axis command direction, all front pushing stages and both objects.
Descriptive fixed-state evidence; task-error direction is not a force/dynamics proof.
"""
from pathlib import Path
import collections,datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from audit_unloaded_wrist_prior_live import HandModel
hand=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());R=W/'front_effective_height_physical_r1';sources={str(Path(__file__)):sha(__file__)};episodes=[]
for case,task in [(840020,'push_box_to_bin'),(840023,'nudge_mailer_to_bin')]:
 ep=R/f'case_{case}'/f'layout_{case}_{task}';co={c['step']:c for c in read(ep/'coordination.json')};fr=read(ep/'frontal_bypass.json')['rows'];records=[]
 for row in fr:
  if row['mode']!='top_push':continue
  t=row['step'];c=co[t];tp=c['joint_transport_clearance'];tc=tp['collector_context'];sc=tc['scene'];side=sc['side'];start=0 if side=='left' else 3;q=np.array(c['task_inputs']['current']);normal=Rotation.from_quat(sc['target_quat']).as_matrix()[:,2];center=np.array(c['active_support_reference']['center_local']);z=c['front_loaded_z_priority']
  def point(v):
   T=hand.fk(v,side);n=T[:3,:3].T@normal;offset=center+n*(min(hand.vertices[side]@n)-center@n);return T[:3,3]+T[:3,:3]@offset
  current=point(q);np.testing.assert_allclose(current,row['observed_support_xyz'],rtol=0,atol=2e-6);request=np.array(c['task_inputs']['error'][start:start+2]);stage=row['route_stage'];commands={'before_z':z['context']['parent_command'],'after_z':z['output_command'],'final':tp['output_command']};deltas={k:((point(v)-current)*1000).tolist() for k,v in commands.items()};reversals={k:[bool(request[j]!=0 and np.sign(request[j])*delta[j]<-.0002) for j in range(2)] for k,delta in deltas.items()}
  records.append(dict(step=t,stage=stage,load_n=row['contact_load']['observed_vertical_load_n'],request_xy_mm=(request*1000).tolist(),nominal_delta_xyz_mm=deltas,reversals_xy=reversals,z_applied=z['applied'],transport_applied=tp['applied']))
 summaries=[]
 for stage in sorted({r['stage'] for r in records}):
  rs=[r for r in records if r['stage']==stage];axis=0 if stage=='front_x' else 1
  counts={k:dict(x=sum(r['reversals_xy'][k][0] for r in rs),y=sum(r['reversals_xy'][k][1] for r in rs),primary_axis=sum(r['reversals_xy'][k][axis] for r in rs)) for k in ['before_z','after_z','final']};summaries.append(dict(stage=stage,frames=len(rs),primary_axis=axis,reversal_counts=counts))
 episodes.append(dict(episode=ep.name,summaries=summaries,rows=records));print(json.dumps(dict(episode=ep.name,summaries=summaries)),flush=True)
 for name in ['coordination.json','frontal_bypass.json']:sources[str(ep/name)]=sha(ep/name)
for p in [W/'audit_unloaded_wrist_prior_live.py',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json']:sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=episodes,source_sha256=sources,training_ready=False,limitations=['Primary axis label uses front_x or lateral_y stage; actual diagonal entry still has a two-dimensional direction.','Counts alone cannot distinguish contact loss, physical traction, joint tracking or future candidate success.','Do not silently broaden the candidate constraints from X correction to all axes without feasibility and all original path/certificate checks.'])
encoded=json.dumps(report,indent=2)
with (R/'FRONT_ALL_STAGE_DIRECTION_DIAGNOSIS_V1.json').open('x') as f:f.write(encoded)
