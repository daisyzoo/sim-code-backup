"""Frozen observed-history screen of actual joint recovery code; no physics replay.
Select first/last/quartile eligible requests plus critical699/1052, from ALL11
rear histories (including three with no loaded request); do not select by success.
Independent FK and bilateral hull geometry verify all emitted float32 commands.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy,os,time
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];STAGE=W/'staged_peak_load_guard';sys.path[:0]=[str(W),str(STAGE),str(ROOT)]
from rear_corridor_joint_recovery_reserve_candidate import solve
from clearance_runtime import ClearanceGuard
from audit_self_clearance_task_optimality import IndependentElbows
from audit_unloaded_wrist_prior_live import HandModel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,STAGE);urdf=ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';verts=ROOT/'assets/robots/g1_hand_support_vertices.json';ind=IndependentElbows(STAGE/'elbow_torso_hulls.json',urdf);hand=HandModel(urdf,verts)
screen=json.loads((W/'REAR_CORRIDOR_RECOVERY_DIRECTION_SCREEN.json').read_text());dest=W/'REAR_CORRIDOR_JOINT_RECOVERY_RESERVE_CHECK.json';assert not dest.exists();sizes={'box':[.14,.09,.045],'mailer':[.15,.145,.04]};results=[];sources={};frozen={str(p):sha(p) for p in [Path(__file__),W/'rear_corridor_joint_recovery_reserve_candidate.py',W/'REAR_CORRIDOR_RECOVERY_DIRECTION_SCREEN.json',STAGE/'clearance_runtime.py',STAGE/'self_clearance.py',STAGE/'articulated_hand_geometry.py',STAGE/'elbow_torso_hulls.json',W/'audit_self_clearance_task_optimality.py',W/'audit_unloaded_wrist_prior_live.py',urdf,verts]};negative=[]
def save(status,**kwargs):
 tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=results,frozen_sha256=frozen,source_sha256=sources,negative_checks=negative,training_ready=False,**kwargs),indent=2));tmp.replace(dest)
try:
 save('running')
 for item in screen['episodes']:
  ep=W/item['episode'];fr=json.loads((ep/'frontal_bypass.json').read_text());fs={r['step']:r for r in fr['rows']};cs={c['step']:c for c in json.loads((ep/'coordination.json').read_text())};side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box'
  with np.load(ep/'trace.npz') as z:pos={k:z[k].copy() for k in sizes}
  with np.load(ep/'parcel_orientation.npz') as z:rot={k:Rotation.from_quat(z[k]).as_matrix() for k in sizes}
  with np.load(ep/'raw.npz') as z:actions=z['action'].copy()
  for n in ['trace.npz','parcel_orientation.npz','raw.npz','frontal_bypass.json','coordination.json']:sources[str(ep/n)]=sha(ep/n)
  eligible=[r['step'] for r in item['rows']];selected=sorted(set(([eligible[i] for i in np.linspace(0,len(eligible)-1,5,dtype=int)] if eligible else [])+[t for t in [699,1052] if t in eligible]));episode=dict(episode=item['episode'],all_eligible=len(eligible),selected_steps=selected,rows=[]);results.append(episode);save('running')
  for t in selected:
   for p,h in frozen.items():assert sha(p)==h
   c=cs[t];r=fs[t];q=np.array(c['upper_q']);prev=actions[t-1,12:23];parent=actions[t,12:23];core=fr['plan']['rear_cop_centering']['actual_core_size_xyz'];args=dict(enabled=True,guard=guard,row=r,coordinate=c,current=q,previous=prev,parent_command=parent,target_xyz=pos[key][t],obstacle_xyz=pos[other][t],target_rotation=rot[key][t],obstacle_rotation=rot[other][t],target_size=sizes[key],obstacle_size=sizes[other],core_size=core)
   off,off_trace=solve(**dict(args,enabled=False));assert np.array_equal(off,parent) and off_trace['reason']=='disabled'
   start=time.monotonic();x,tr=solve(**args);checked=None
   if x is not None and tr['applied']:
    gap=ind.gap(x);assert min(gap)>=.005-2e-7
    offset=np.array(r['control_offset_local']);T=hand.fk(x,side);T0=hand.fk(q,side);delta=T[:3,3]+T[:3,:3]@offset-T0[:3,3]-T0[:3,:3]@offset
    assert abs(delta[1])<=1e-7 and tr['minimum_x_m']-1e-7<=delta[0]<=tr['requested_x_m']+1e-7
    cop=rot[key][t].T@(np.array(r['rear_cop_centering']['cop_world'])-pos[key][t]);axes=[k for k in [0,1] if core[k]/2-abs(cop[k])<=.01];assert axes==tr['near_core_axes'];res=[float(-np.sign(cop[k])*rot[key][t][:,k]@delta-tr['inward_requirement_m']) for k in axes];assert not res or min(res)>=-1e-7
    assert np.all(x>=guard.lower-2e-7) and np.all(x<=guard.upper+2e-7) and np.all(abs(x-q)<=guard.limits+2e-7) and max(abs(x-prev))<=.0550002
    checked=dict(independent_delta_xyz_m=delta.tolist(),independent_elbow_gaps_m=gap.tolist(),independent_edge_residual_m=res)
   elif x is None:assert tr['requires_recontact'] and not tr['applied']
   else:assert np.array_equal(x,parent)
   episode['rows'].append(dict(step=t,result=tr,independent_verification=checked,elapsed_s=time.monotonic()-start));save('running');print(json.dumps(dict(episode=ep.name,step=t,applied=tr['applied'],reason=tr['reason'])),flush=True)
   if not negative:
    for label,mutate in [('non_push',lambda a:a['row'].update(mode='top_release')),('route_stop',lambda a:a['row'].update(route_stop_reason='guard')),('terminal_hold',lambda a:a['coordinate'].update(terminal_joint_hold=True)),('region_override',lambda a:a['coordinate'].update(region_joint_override=True)),('first_loaded',lambda a:a['row'].update(rear_cop_centering={'override':False,'reason':'preserve_first_loaded_push'}))]:
     bad=dict(args,row=copy.deepcopy(r),coordinate=copy.deepcopy(c));mutate(bad);out,trace=solve(**bad);assert np.array_equal(out,parent) and not trace['applied'];negative.append(label)
    for label,changed in [('bad_flag',dict(enabled=1)),('bad_rotation',dict(target_rotation=np.zeros((3,3)))),('causal_mismatch',dict(current=q+.001))]:
     try:solve(**dict(args,**changed))
     except ValueError:negative.append(label)
     else:raise AssertionError(('invalid input accepted',label))
 save('complete',total_requests=sum(len(r['rows']) for r in results),applied=sum(x['result']['applied'] for r in results for x in r['rows']),requires_recontact=sum(x['result'].get('requires_recontact',False) for r in results for x in r['rows']))
except Exception as e:save('check_failed',error=repr(e));raise
