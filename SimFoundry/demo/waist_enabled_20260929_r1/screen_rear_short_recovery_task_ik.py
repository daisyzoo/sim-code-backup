"""One-step IK feasibility at recorded states for unwired rear short-recovery waypoints.
Uses actual recorded q/J/previous action and independently checks elbow bounds.
All changed references at fixed recorded states; original normal rows remain active in lift/cross/descend/press/push. No recursive state rollout, contact-force forecast, physical or training evidence.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_micro_clearance_return';sys.path[:0]=[str(stage),str(w),str(repo)]
from task_ik import solve
from clearance_runtime import ClearanceGuard
from audit_self_clearance_task_optimality import IndependentElbows
from articulated_hand_geometry import ArticulatedHandGeometry
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';independent=IndependentElbows(stage/'elbow_torso_hulls.json',urdf);model=ArticulatedHandGeometry(urdf,repo/'assets/robots/g1_hand_support_vertices.json');replay=w/'REAR_SHORT_RECOVERY_REPLAY.json';d=json.loads(replay.read_text());reports=[]
for episode in d['episodes']:
 ep=Path(episode['episode']);coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';osize=(.15,.145,.04) if key=='box' else (.14,.09,.045);size=(.14,.09,.045) if key=='box' else (.15,.145,.04);ix=slice(3,6) if side=='right' else slice(0,3);records=[];original={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']}
 with np.load(ep/'trace.npz') as z:xyz={k:z[k].astype(float) for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k].astype(float) for k in z.files}
 for row in episode['changed_rows']:
  baseline=original[row['step']]
  if baseline['mode']==row['mode'] and np.max(abs(np.array(baseline['target_xyz'])-np.array(row['target_xyz'])))<1e-7:continue
  t=row['step'];c=coords[t];inp=dict(c['task_inputs']);old=np.array(inp['error']);assert len(old)==9 and c['contact_normal_tracking'] is not None,'Original held normal must remain in all changed top-mode tasks';desired=np.array(row['target_xyz'],dtype=np.float32);point=np.array(c['control_point_positions'][side],dtype=np.float32);new=old.copy();new[ix]=np.clip(np.float32(.72)*(desired-point),np.float32(-.035),np.float32(.035));inp['error']=new
  command,info=solve(enabled=True,geometry=guard.geometry,**inp);entry=dict(step=t,accepted=command is not None,solver_reason=info['reason'])
  if command is not None:
   current=np.array(inp['current']);previous=np.array(inp['previous']);limits=np.array(inp['step_limits']);lo=np.maximum.reduce([inp['lower'],current-limits,previous-.055]);hi=np.minimum.reduce([inp['upper'],current+limits,previous+.055]);gaps=independent.gap(command);assert np.all(command>=lo-2e-7) and np.all(command<=hi+2e-7) and min(gaps)>=.005-2e-7
   final=guard.command(command,current,previous);assert final['accepted'];entry.update(min_gap_mm=float(min(gaps)*1000),override=info['override'],linear_task_residual_mm=float(np.linalg.norm(np.array(inp['jacobian'])@(command-current)-new)*1000),measured_joint_delta_max_rad=float(max(abs(command-current))))
   from scipy.spatial.transform import Rotation
   scene=model.scene_geometry(side,command,target_xyz=xyz[key][t],target_quat=ori[key][t],other_xyz=xyz[other][t],other_quat=ori[other][t],other_size=osize)
   handverts=scene['vertices']@scene['hand_rotation'].T+scene['hand_xyz'];target_upper=xyz[key][t,2]+abs(Rotation.from_quat(ori[key][t]).as_matrix()[2])@(np.array(size)/2);other_upper=xyz[other][t,2]+abs(Rotation.from_quat(ori[other][t]).as_matrix()[2])@(np.array(osize)/2)
   entry.update(mode=row['mode'],hand_other_gap_mm=scene['hand_other_gap_m']*1000,hand_min_z_m=float(min(handverts[:,2])),above_both_parcels_mm=float((min(handverts[:,2])-max(target_upper,other_upper))*1000))
   assert scene['hand_other_gap_m']>=.005-2e-7
   if row['mode']=='top_cross':assert entry['above_both_parcels_mm']>=10.
  records.append(entry)
 reports.append(dict(episode=str(ep),eligible_frames=len(records),accepted_frames=sum(r['accepted'] for r in records),rejected_frames=sum(not r['accepted'] for r in records),records=records,source_sha256={n:sha(ep/n) for n in ['raw.npz','coordination.json','frontal_bypass.json']}));print(ep.name,'frames',len(records),'accepted',sum(r['accepted'] for r in records),flush=True)
out=dict(scope=__doc__,episodes=reports,replay_sha256=sha(replay),source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'task_ik.py',stage/'self_clearance.py',stage/'clearance_runtime.py',w/'audit_self_clearance_task_optimality.py']},collector_wired=False,physical_validation=False,training_ready=False);(w/'REAR_SHORT_RECOVERY_TASK_IK.json').write_text(json.dumps(out,indent=2))
