"""Verify all previously emitted candidate commands with an independent audit.
Fixtures combine frozen measured parent inputs and actual recorded solver outputs;
post-guard commit runs the candidate adapter. No simulated state is manufactured
or admitted, and full physical phase/path/pressure audits remain required.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,copy,hashlib,datetime,os
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_corridor_recovery';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from rear_cop_route import RearCopRouteState
from rear_corridor_collector_adapter import commit
from audit_rear_corridor_command_records import RecoveryVerifier
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S);audit=RecoveryVerifier(ROOT,S)
DEST=W/'REAR_CORRIDOR_INDEPENDENT_RECORD_CHECK.json';assert not DEST.exists();rows=[];negative=[];sources={};frozen={str(p):sha(p) for p in [Path(__file__),W/'audit_rear_corridor_command_records.py',W/'REAR_CORRIDOR_JOINT_RECOVERY_FULL_CHECK.json',W/'REAR_CORRIDOR_UNLOAD_CHECK.json',W/'audit_self_clearance_task_optimality.py',W/'audit_unloaded_wrist_prior_live.py',ROOT/'simfoundry/robots/g1_assets.py',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json',*[p for p in S.iterdir() if p.is_file() and p.suffix=='.py'],S/'elbow_torso_hulls.json']}
def save(status,**extra):
 tmp=DEST.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,negative_checks=negative,source_sha256=sources,frozen_sha256=frozen,training_ready=False,**extra),indent=2));tmp.replace(DEST)
try:
 save('running');full=json.loads((W/'REAR_CORRIDOR_JOINT_RECOVERY_FULL_CHECK.json').read_text());lifts=json.loads((W/'REAR_CORRIDOR_UNLOAD_CHECK.json').read_text());lookup={(r['episode'],r['step']):r['result'] for r in lifts['rows']};sizes={'box':[.14,.09,.045],'mailer':[.15,.145,.04]}
 for epitem in full['episodes']:
  ep=W/epitem['episode'];f=json.loads((ep/'frontal_bypass.json').read_text());fs={r['step']:r for r in f['rows']};cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};key='box' if 'push_box' in ep.name else 'mailer';other='mailer' if key=='box' else 'box';side='right' if key=='box' else 'left'
  with np.load(ep/'trace.npz') as z:pos={k:z[k].copy() for k in sizes}
  with np.load(ep/'parcel_orientation.npz') as z:rot={k:Rotation.from_quat(z[k]).as_matrix() for k in sizes}
  with np.load(ep/'raw.npz') as z:actions=z['action'].copy()
  for n in ['frontal_bypass.json','coordination.json','trace.npz','parcel_orientation.npz','raw.npz']:sources[str(ep/n)]=sha(ep/n)
  for item in epitem['rows']:
   t=item['step'];parent=fs[t];coord=cs[t];result=item['result'];kind='loaded_recovery' if result['applied'] else 'unload';q=np.array(coord['upper_q']);prev=actions[t-1,12:23];chosen=result if kind=='loaded_recovery' else lookup[(epitem['episode'],t)];cmd=np.array(next(a['command'] for a in chosen['attempts'] if a['accepted']));geometry=dict(target_xyz=pos[key][t].tolist(),obstacle_xyz=pos[other][t].tolist(),target_rotation=rot[key][t].tolist(),obstacle_rotation=rot[other][t].tolist(),target_size=sizes[key],obstacle_size=sizes[other],core_size=f['plan']['rear_cop_centering']['actual_core_size_xyz'])
   record=dict(step=t,kind=kind,recovery=result,parent_row=copy.deepcopy(parent),parent_coordinate=copy.deepcopy(coord),parent_command=actions[t,12:23].tolist(),proposed_command=cmd.tolist(),geometry=geometry)
   if kind=='unload':record['unload']=chosen
   state=RearCopRouteState(rear=SimpleNamespace(plan=f['plan']),side=side,size=tuple(sizes[key]),hold_established_x=True);state.mode=state.top_mode=parent['mode'];state.command=tuple(parent['target_xyz']);state.last_waypoint_xy=state.command[:2];state.push_x_anchor=parent['push_x_anchor_m'];state.recontacts=parent['recontacts'];state.last_recontact_reason=parent['last_recontact_reason'];state.load.bias_m=parent['contact_load']['stored_z_bias_m'];state.load.filtered_n=parent['contact_load']['filtered_vertical_load_n']
   updated=commit(state=state,guard=guard,row=parent,coordinate=coord,current=q,previous=prev,command=cmd,record=record);actual_coord=dict(coord,rear_corridor_override=dict(kind=kind,step=t,record_file='rear_corridor_recovery.json'));args=dict(row=updated,coordinate=actual_coord,current=q,previous=prev,action=cmd,geometry=geometry);verified=audit.verify(record,**args);rows.append(dict(episode=epitem['episode'],**verified))
   label='negative_'+kind
   if label not in negative:
    changes=[('wrong_action',lambda r,a:a.update(action=cmd+.001)),('wrong_reference',lambda r,a:a['row']['target_xyz'].__setitem__(0,a['row']['target_xyz'][0]+.001)),('wrong_mode',lambda r,a:a['row'].update(mode='top_press')),('wrong_bias',lambda r,a:a['row']['contact_load'].update(stored_z_bias_m=.1)),('other_pose',lambda r,a:a['geometry']['obstacle_xyz'].__setitem__(0,a['geometry']['obstacle_xyz'][0]+.01)),('parent_guard',lambda r,a:r['parent_row'].update(route_stop_reason='guard')),('fake_step',lambda r,a:r.update(step=t+1)),('wrong_previous',lambda r,a:a.update(previous=prev+.001)),('claim_more_progress',lambda r,a:r['recovery'].update(rear_deficit_m=r['recovery']['rear_deficit_m']+.001)),('duplicate_accepted_solution',lambda r,a:(r['recovery'] if kind=='loaded_recovery' else r['unload'])['attempts'].append(copy.deepcopy(next(v for v in chosen['attempts'] if v['accepted']))))]
    for name,mutate in changes:
     rr=copy.deepcopy(record);aa=copy.deepcopy(args);mutate(rr,aa)
     try:audit.verify(rr,**aa)
     except (AssertionError,ValueError,KeyError):negative.append(name+'_'+kind)
     else:raise AssertionError('Corrupted evidence accepted: '+name)
    negative.append(label)
   if len(rows)%250==0:save('running');print('verified',len(rows),flush=True)
 for p,h in {**sources,**frozen}.items():assert sha(p)==h,p
 assert len(rows)==1943;save('complete',passed=True,loaded_recovery=sum(r['kind']=='loaded_recovery' for r in rows),unload=sum(r['kind']=='unload' for r in rows))
except BaseException as e:save('check_failed',error=repr(e));raise
