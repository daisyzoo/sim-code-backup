"""Separate parent motion from local-reference changes at first kinematic holds.
Historical references are fixed during replay; actual closed-loop controller would
recompute references/waypoints from new measured geometry, so this is not a rollout.
"""
from pathlib import Path
import json,hashlib,sys
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(repo),str(w/'staged_joint_edge_command')]
from articulated_hand_geometry import ArticulatedHandGeometry
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();out=[]
for cid,task in [(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin')]:
 ep=w/f'joint_edge_retry_groups_r1/case_{cid}/layout_{cid}_{task}';replay=w/'staged_self_clearance_exact_probe/kinematic_replay_r1';report=json.loads((replay/(ep.name+'.json')).read_text());t=next(r['step'] for r in report['records'] if r['reason']=='hold_verified_previous');side='left' if 'nudge' in task else 'right'
 with np.load(ep/'raw.npz') as z:p=z['action'][:,12:23]
 with np.load(replay/(ep.name+'_commands.npz')) as z:q=z['command']
 frames={f['step']:f for f in json.loads((ep/'frontal_bypass.json').read_text())['rows']};old_offset=np.array(frames[t-1].get('control_offset_local') or [.2,0,.007]);new_offset=np.array(frames[t].get('control_offset_local') or [.2,0,.007]);Tp,_,_=model.fk(side,p[t]);Told,_,_=model.fk(side,p[t-1]);Tq,_,_=model.fk(side,q[t-1]);point=lambda T,o:T[:3,3]+T[:3,:3]@o
 parent_motion=point(Tp,new_offset)-point(Told,new_offset);old_match=point(Told,old_offset)-point(Tq,old_offset);ref_effect=(Told[:3,:3]-Tq[:3,:3])@(new_offset-old_offset);required=point(Tp,new_offset)-point(Tq,new_offset);assert np.max(abs(required-parent_motion-old_match-ref_effect))<1e-10
 row=dict(episode=ep.name,first_hold=t,previous_mode=frames[t-1]['mode'],mode=frames[t]['mode'],old_offset=old_offset.tolist(),new_offset=new_offset.tolist(),local_offset_change_mm=float(np.linalg.norm(new_offset-old_offset)*1000),required_step_mm=(required*1000).tolist(),parent_motion_mm=(parent_motion*1000).tolist(),prior_match_residual_mm=(old_match*1000).tolist(),reference_switch_effect_mm=(ref_effect*1000).tolist(),source_sha256={str(p.relative_to(w)):sha(p) for p in [ep/'raw.npz',ep/'frontal_bypass.json',replay/(ep.name+'_commands.npz'),replay/(ep.name+'.json')]});out.append(row);print(row['episode'],t,row['previous_mode'],row['mode'],'offsetchange',row['local_offset_change_mm'],'switch mm',row['reference_switch_effect_mm'],flush=True)
(w/'SELF_CLEARANCE_REFERENCE_CHANGE_DIAGNOSIS.json').write_text(json.dumps(dict(scope=__doc__,rows=out,checker_sha256=sha(Path(__file__)),training_ready=False),indent=2))
