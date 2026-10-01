"""Replay all completed original8 push streams through a new, unwired adapter.
State trajectories stay original. Proposals are counterfactual single-step only.
Validate disabled identity, real gates, independent final geometry and stale
packet/state rejection. Explicit solver rejections are retained, never success.
"""
from pathlib import Path
import sys,json,hashlib,copy,datetime,collections
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_loaded_edge_coverage';sys.path[:0]=[str(stage),str(w),str(repo)]
from loaded_edge_coverage_adapter import refine_record
from clearance_runtime import ClearanceGuard
from audit_unloaded_wrist_prior_live import HandModel
from audit_unloaded_wrist_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=repo/'assets/robots/g1_hand_support_vertices.json';hand=HandModel(urdf,vertices);elbows=IndependentElbows(stage/'elbow_torso_hulls.json',urdf);run=w/'recontact_pose_groups_r1';episodes=sorted(p.parent for p in run.glob('case_*/layout_*/quality.json') if 'wait' not in str(p));assert len(episodes)==8
results=[];negative_checks=[];sources={}
for ep in episodes:
 fr=json.loads((ep/'frontal_bypass.json').read_text());rows=fr['rows'];cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};packets={p['after_action_step']:p for p in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};selected=bool(fr['plan'].get('rear_joint_xy_progress',{}).get('enabled'));key='box' if 'push_box' in ep.name else 'mailer';side='right' if key=='box' else 'left';direction=-1 if side=='right' else 1
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].copy()
 with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:R=Rotation.from_quat(z[key]).as_matrix()
 core=fr['plan'].get('region_causal_response',{}).get('actual_core',{}).get('collision_core_size_xyz');last=None;outrows=[]
 for row in rows:
  t=row['step'];ctx=dict(enabled=True,selected=selected,row=row,previous_row=last,coordinate=cs[t],current=q[t],previous=u[t-1],parent_command=u[t],packet=packets.get(t-1),object_xyz=xyz[t],object_rotation=R[t],core_size=core,model=guard.model,geometry=guard.geometry,side=side)
  disabled,dt=refine_record(**dict(ctx,enabled=False));assert dt is None and np.array_equal(disabled,u[t]);command,tr=refine_record(**ctx)
  if tr['override']:
   x=np.array(command,dtype=float);offset=np.array(row['control_offset_local']);T=hand.fk(q[t],side);Tn=hand.fk(x,side);movement=Tn[:3,3]+Tn[:3,:3]@offset-T[:3,3]-T[:3,:3]@offset;cop=np.array(tr['context']['current_cop_local']);axes=tr['threatened_axes'];edges=[float(-np.sign(cop[k])*R[t,:,k]@movement) for k in axes]+[float(direction*movement[1])];assert min(edges)>=-1e-7 and min(elbows.gap(x))>=.005-2e-7
   assert np.min(x-np.array(tr['bound_low']))>=-2e-7 and np.min(np.array(tr['bound_high'])-x)>=-2e-7
   if not negative_checks:
    mutations=[];bad=copy.deepcopy(ctx['packet']);bad['after_action_step']+=1;mutations.append(('future_packet',{'packet':bad}));bad=copy.deepcopy(ctx['packet']);bad['post_action_pose'][key][0]+=.01;mutations.append(('wrong_packet_pose',{'packet':bad}));bad=q[t].copy();bad[0]+=.01;mutations.append(('wrong_current_q',{'current':bad}));bad=u[t-1].copy();bad[0]+=.01;mutations.append(('wrong_previous_command',{'previous':bad}));bad=copy.deepcopy(last);bad['step']-=1;mutations.append(('stale_previous_row',{'previous_row':bad}));bad=copy.deepcopy(row);bad['control_offset_local'][0]+=.01;mutations.append(('wrong_reference',{'row':bad}))
    for label,change in mutations:
     try:refine_record(**dict(ctx,**change))
     except (ValueError,AssertionError):negative_checks.append(label)
     else:raise AssertionError('accepted '+label)
  elif tr['accepted']:assert command is not None and np.array_equal(command,u[t])
  else:assert command is None and tr['eligible'] and tr['command'] is None
  outrows.append({'step':t,'eligible':tr['eligible'],'accepted':tr['accepted'],'override':tr['override'],'reason':tr['reason'],'trace':tr if tr['override'] or not tr['accepted'] else None});last=row
 results.append({'episode':ep.name,'frames':len(outrows),'disabled_identity_frames':len(outrows),'eligible_frames':sum(r['eligible'] for r in outrows),'overrides':sum(r['override'] for r in outrows),'rejections':[r for r in outrows if not r['accepted']],'records':outrows});print(ep.name,'frames',len(outrows),'eligible',results[-1]['eligible_frames'],'overrides',results[-1]['overrides'],'rejected',len(results[-1]['rejections']),flush=True)
 for name in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json','solved_contact_forces.json']:sources[str(ep/name)]=sha(ep/name)
 for p in [Path(__file__),stage/'loaded_edge_coverage_adapter.py',stage/'loaded_edge_coverage_current_contact.py',stage/'articulated_hand_geometry.py',stage/'clearance_runtime.py',stage/'elbow_torso_hulls.json',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py',urdf,vertices]:sources[str(p)]=sha(p)
 (stage/'ADAPTER_CHECK_PARTIAL.json').write_text(json.dumps({'completed_episodes':len(results),'scope':__doc__,'rows':results,'negative_checks':negative_checks,'source_sha256':sources,'training_ready':False},indent=2))
assert sum(r['frames'] for r in results)==9592 and len(negative_checks)==6
out={'adapter_checks_passed':True,'all_counterfactual_commands_verified':not any(r['rejections'] for r in results),'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':__doc__,'episodes':8,'frames':9592,'overrides':sum(r['overrides'] for r in results),'rejections':sum(len(r['rejections']) for r in results),'rows':results,'negative_checks':negative_checks,'source_sha256':sources,'controller_connected':False,'physical_validation':False,'training_ready':False};(stage/'ADAPTER_CHECK.json').write_text(json.dumps(out,indent=2));print('SUMMARY',{k:out[k] for k in ['adapter_checks_passed','all_counterfactual_commands_verified','frames','overrides','rejections']})
