"""Replay all edge overrides in the first8 complete frozen groups, no admission.
All input histories remain observed baseline histories; counterfactual outputs
are not recursively applied and this is not a physical rollout.
"""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];STAGE=W/'staged_closed_peak_trial';sys.path[:0]=[str(W),str(STAGE),str(ROOT)]
from clearance_runtime import ClearanceGuard
from articulated_hand_geometry import skew
from joint_edge_clearance_intersection_candidate import repair
from audit_self_clearance_task_optimality import IndependentElbows
from audit_unloaded_wrist_prior_live import HandModel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
run=Path(sys.argv[1]).resolve();out=run/'JOINT_EDGE_CLEARANCE_INTERSECTION_CHECK.json';assert not out.exists();guard=ClearanceGuard(ROOT,STAGE);urdf=ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';ind=IndependentElbows(STAGE/'elbow_torso_hulls.json',urdf);hand=HandModel(urdf,ROOT/'assets/robots/g1_hand_support_vertices.json');records=[];sources={};changed=[]
for layout in range(840000,840016):
 for ep in sorted((run/f'case_{layout}').glob('layout_*')):
  assert (ep.parent/'STATUS.json').exists();status=json.loads((ep.parent/'STATUS.json').read_text());assert status['status'] in ['blocked_quality_or_runtime','numeric_pass_visual_review_pending']
  coords=json.loads((ep/'coordination.json').read_text());fr=json.loads((ep/'frontal_bypass.json').read_text());fs={v['step']:v for v in fr['rows']};count=0;unchanged=0;changed_steps=[]
  for c in coords:
   tr=c.get('joint_edge_refinement')
   if not tr or not tr.get('override'):continue
   count+=1;q=np.array(c['upper_q']);prev=np.array(tr['previous_upper_command']);old=np.array(tr['final_upper_command']);ctx=None
   if not guard.command(old,q,prev)['accepted']:
    t=c['step'];f=fs[t];side=c['active_side'];direction=-1 if side=='right' else 1;key='box' if side=='right' else 'mailer';quality=json.loads((ep/'quality.json').read_text())
    if t<quality['frames']:
     with np.load(ep/'parcel_orientation.npz') as z:R=Rotation.from_quat(z[key][t]).as_matrix()
    else:
     with np.load(ep/'substep_contacts.npz') as z:
      idx=int(np.flatnonzero(z['action_step']==t-1)[-1]);pose=z['body_q'][idx,0 if side=='right' else 1];assert max(abs(pose[:3]-f['observed_target']))<1e-7;R=Rotation.from_quat(pose[3:]).as_matrix()
    local=R.T@(np.array(f['rear_cop_centering']['cop_world'])-f['observed_target']);core=np.array(fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz']);axes=[k for k in [0,1] if core[k]/2-abs(local[k])<=.01];assert axes==tr['threatened_axes'];normals=np.array([-np.sign(local[k])*R[:,k] for k in axes]);off=np.array(f['control_offset_local']);inp=c['task_inputs']
    def point(x):
     T,jl,jw=guard.model.fk(side,x);v=T[:3,:3]@off;return T[:3,3]+v,jl-skew(v)@jw
    ctx=dict(jacobian=inp['jacobian'],error=inp['error'],damping=inp['damping'],normals=normals,direction=direction,inward_m=.0005 if side=='right' else 0.,point_and_jacobian=point,parent=tr['parent_final_upper_command'])
   x,trace=repair(guard=guard,current=q,previous=prev,command=old,context=ctx);assert x is not None,(ep.name,c['step'],trace)
   if trace['changed']:
    gap=ind.gap(x);assert min(gap)>=.005-2e-7
    T=hand.fk(x,side);T0=hand.fk(q,side);move=(T[:3,3]+T[:3,:3]@off)-(T0[:3,3]+T0[:3,:3]@off);v=np.r_[normals@move-ctx['inward_m'],direction*move[1]];assert min(v)>=-1e-7
    changed_steps.append(c['step']);changed.append(dict(episode=ep.name,step=c['step'],trace=trace,independent_gap_m=gap.tolist(),independent_edge_residual_m=v.tolist()))
   else:assert np.array_equal(x,old);unchanged+=1
  records.append(dict(episode=ep.name,frames=json.loads((ep/'quality.json').read_text())['frames'],edge_overrides=count,unchanged_commands=unchanged,changed_steps=changed_steps))
  for name in ['coordination.json','frontal_bypass.json','quality.json','parcel_orientation.npz']:sources[str(ep/name)]=sha(ep/name)
  print(json.dumps(records[-1]),flush=True)
# Negative paths must fail closed; no hidden command fallback.
z=np.zeros(11);bad=z.copy();bad[0]=1.1
assert repair(guard=guard,current=z,previous=z,command=bad)[0] is None
known=changed[0];ep=next(run.glob('case_*/'+known['episode']));c=next(x for x in json.loads((ep/'coordination.json').read_text()) if x['step']==known['step']);tr=c['joint_edge_refinement']
assert repair(guard=guard,current=c['upper_q'],previous=tr['previous_upper_command'],command=tr['final_upper_command'])[0] is None
try:repair(guard=guard,current=np.full(11,np.nan),previous=z,command=z)
except ValueError:pass
else:raise AssertionError('nonfinite accepted')
for p in [Path(__file__),W/'joint_edge_clearance_intersection_candidate.py',STAGE/'clearance_runtime.py',STAGE/'self_clearance.py',STAGE/'articulated_hand_geometry.py',STAGE/'elbow_torso_hulls.json',W/'audit_self_clearance_task_optimality.py',W/'audit_unloaded_wrist_prior_live.py',ep/'substep_contacts.npz',*map(Path,guard.model.source_sha256)]:sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,episodes=len(records),edge_overrides=sum(v['edge_overrides'] for v in records),unchanged_commands=sum(v['unchanged_commands'] for v in records),changed_commands=changed,negative_checks=3,source_sha256=sources,runtime_changed=False,training_ready=False)
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k not in ['records','source_sha256','changed_commands']},indent=2))
