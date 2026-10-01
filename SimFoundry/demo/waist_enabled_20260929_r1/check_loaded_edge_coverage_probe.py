"""Real-record and independent-FK checks for the unwired nominal-edge proposal.
No returned command enters the simulator. Disabled/transition/load/precedence
checks and impossible geometry verify no unsafe fallback is proposed.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_recontact_pose';sys.path[:0]=[str(w),str(stage),str(repo)]
from loaded_edge_coverage_probe import propose
from clearance_runtime import ClearanceGuard
from articulated_hand_geometry import skew
from audit_unloaded_wrist_prior_live import HandModel
from audit_unloaded_wrist_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=repo/'assets/robots/g1_hand_support_vertices.json';hand=HandModel(urdf,vertices);elbows=IndependentElbows(stage/'elbow_torso_hulls.json',urdf)
diag=json.loads((w/'LOADED_RELATIVE_CONTACT_MOTION.json').read_text());records=[];negatives=[];sources={}
for item in diag['rows']:
 if item['run']!='recontact_pose_groups_r1':continue
 cid=840001 if 'push_box' in item['episode'] else 840004;side='right' if cid==840001 else 'left';key='box' if side=='right' else 'mailer';actor='parcel_box' if side=='right' else 'mailer';direction=-1 if side=='right' else 1
 ep=w/item['run']/f'case_{cid}'/item['episode'];fr=json.loads((ep/'frontal_bypass.json').read_text());fs={r['step']:r for r in fr['rows']};cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};core=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'];assert fr['plan']['rear_joint_xy_progress']['enabled']
 with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float);us=z['action'][:,12:23].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rots=Rotation.from_quat(z[key]).as_matrix()
 packets={p['after_action_step']:p for p in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
 def load(t):
  total=0.
  for c in packets[t-1]['parcel_contacts']:
   slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
   if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
   f=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);force=-float(f@rots[t,:,2])
   if force>.05:total+=force
  return total
 chosen=[r for r in item['records'] if r['near_x_edge'] and r['inward_x_nominal_mm']<-.0001]
 for r in chosen:
  t=r['step'];f=fs[t];c=cs[t];inp=c['task_inputs'];q=qs[t];prev=us[t-1];offset=np.array(f['control_offset_local']);R=rots[t];cop=np.array(r['cop_local_mm'])/1000
  def point(x):T,_,_=guard.model.fk(side,x);return T[:3,3]+T[:3,:3]@offset
  def jac(x):T,jl,jw=guard.model.fk(side,x);return jl-skew(T[:3,:3]@offset)@jw
  ctx=dict(enabled=True,selected=True,mode=f['mode'],previous_mode=fs[t-1]['mode'],recontacts=f['recontacts'],previous_recontacts=fs[t-1]['recontacts'],load_n=load(t),previous_load_n=load(t-1),parent_guard=bool(f.get('route_stop_reason') or f.get('release_reason')),terminal_hold=bool(c.get('terminal_joint_hold')),region_override=bool(c.get('region_joint_override')),unloaded_override=c.get('controller_kind')=='verified_unloaded_recontact_joint_path',current=q,previous_command=prev,parent_command=us[t],jacobian=inp['jacobian'],error=inp['error'],damping=inp['damping'],lower=inp['lower'],upper=inp['upper'],step_limits=inp['step_limits'],object_rotation=R,cop_local=cop,core_size=core,direction=direction,point_fn=point,point_jacobian_fn=jac,geometry=guard.geometry)
  out=propose(**ctx);check=None
  if out['override']:
   x=np.array(out['command']);assert np.array_equal(x,x.astype(np.float32).astype(float));lo=np.maximum.reduce([inp['lower'],q-np.array(inp['step_limits']),prev-.055]);hi=np.minimum.reduce([inp['upper'],q+np.array(inp['step_limits']),prev+.055]);assert np.min(x-lo)>=-2e-7 and np.min(hi-x)>=-2e-7
   def ip(q):T=hand.fk(q,side);return T[:3,3]+T[:3,:3]@offset
   motion=ip(x)-ip(q);axes=[k for k in [0,1] if core[k]/2-abs(cop[k])<=.01];signed=[float(-np.sign(cop[k])*R[:,k]@motion) for k in axes]+[float(direction*motion[1])];gaps=elbows.gap(x);assert min(signed)>=-1e-7 and min(gaps)>=.005-2e-7;check={'independent_direction_m':signed,'independent_elbow_gaps_m':gaps.tolist()}
   if not negatives:
    for label,change in [('disabled',{'enabled':False}),('other_route',{'selected':False}),('nonpush',{'mode':'top_lift'}),('first_push',{'previous_mode':'top_press'}),('new_bout',{'previous_recontacts':ctx['recontacts']+1}),('no_current_load',{'load_n':0.}),('no_previous_load',{'previous_load_n':0.}),('original_guard',{'parent_guard':True}),('terminal',{'terminal_hold':True}),('region',{'region_override':True}),('unloaded_path',{'unloaded_override':True})]:
     xx=propose(**dict(ctx,**change));assert not xx['eligible'] and not xx['override'] and 'command' not in xx;negatives.append(label)
    class Impossible:
     def constraints(self,x):return np.array([-1.,-1.])
     def jacobian(self,x):return np.zeros((2,11))
    xx=propose(**dict(ctx,geometry=Impossible()));assert xx['eligible'] and not xx['accepted'] and not xx['override'] and xx['command'] is None;negatives.append('impossible_geometry_no_parent_fallback')
  else:assert (not out['eligible'] and 'command' not in out) or (out['accepted'] and out['reason']=='parent_already_valid') or (out['command'] is None and not out['accepted'])
  records.append({'episode':item['episode'],'step':t,'eligible':out['eligible'],'accepted':out['accepted'],'override':out['override'],'reason':out['reason'],'independent':check,'proposal':out});print(item['episode'],t,out['reason'],flush=True)
 for name in ['raw.npz','frontal_bypass.json','coordination.json','parcel_orientation.npz','solved_contact_forces.json']:sources[str(ep/name)]=sha(ep/name)
assert len(records)==39 and len(negatives)==12
for p in [Path(__file__),w/'loaded_edge_coverage_probe.py',w/'LOADED_RELATIVE_CONTACT_MOTION.json',urdf,vertices,stage/'elbow_torso_hulls.json',stage/'clearance_runtime.py',stage/'articulated_hand_geometry.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py']:sources[str(p)]=sha(p)
out={'passed':True,'scope':__doc__,'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'records':records,'negative_checks':negatives,'original_problem_states':len(records),'eligible':sum(r['eligible'] for r in records),'repaired_nominal_commands':sum(r['override'] for r in records),'unverified_commands':sum(r['eligible'] and not r['accepted'] for r in records),'source_sha256':sources,'physical_validation':False,'training_ready':False};(w/'LOADED_EDGE_COVERAGE_PROBE_CHECK.json').write_text(json.dumps(out,indent=2));print('SUMMARY',{k:out[k] for k in ['passed','original_problem_states','eligible','repaired_nominal_commands','unverified_commands']},flush=True)
