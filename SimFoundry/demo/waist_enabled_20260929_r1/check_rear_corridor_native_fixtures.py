"""Full-length FILE FORMAT fixtures for the native recovery boundary verifier.
SYNTHETIC, NO PHYSICS: sparse controlled branches embed real measured request
inputs and recorded solver outputs. Other rows are deliberately minimal stubs;
these fixtures cannot pass source binding or original full-control audits and
must never be used for task success, counterfactual trajectories or training.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,copy,hashlib,datetime,tempfile
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_corridor_recovery_guarded';sys.path[:0]=[str(S),str(W),str(ROOT)]
from audit_rear_corridor_native_commands_v2 import verify_files
from rear_corridor_collector_adapter import commit
from rear_cop_route import RearCopRouteState
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();dest=W/'REAR_CORRIDOR_NATIVE_FIXTURE_CHECK.json';assert not dest.exists();fixture=Path(tempfile.mkdtemp(prefix='rear_native_SYNTHETIC_NO_PHYSICS_'));guard=ClearanceGuard(ROOT,S);full=json.loads((W/'REAR_CORRIDOR_JOINT_RECOVERY_FULL_CHECK.json').read_text());unloads=json.loads((W/'REAR_CORRIDOR_UNLOAD_CHECK.json').read_text());lookup={(r['episode'],r['step']):r['result'] for r in unloads['rows']};history=json.loads((W/'REAR_TRANSPORT_LIFECYCLE_CHECK.json').read_text());cases=[];negative=[];sources={}
def dump(p,obj):p.write_text(json.dumps(obj))
def expect_reject(ep,label):
 try:verify_files(ep,ROOT,S)
 except (AssertionError,ValueError,KeyError):negative.append(label)
 else:raise AssertionError('corruption accepted '+label)
try:
 for kind,key in [('loaded_recovery','box'),('loaded_recovery','mailer'),('unload','box')]:
  old=next(ep for ep in full['episodes'] if ('push_box' in ep['episode'])==(key=='box') and any(r['result']['applied']==(kind=='loaded_recovery') for r in ep['rows']));sample=next(r for r in old['rows'] if r['result']['applied']==(kind=='loaded_recovery'));t=sample['step'];src=W/old['episode'];fr=json.loads((src/'frontal_bypass.json').read_text());row=copy.deepcopy(next(r for r in fr['rows'] if r['step']==t));coord=copy.deepcopy(next(c for c in json.loads((src/'coordination.json').read_text()) if c['step']==t));selected=sample['result'] if kind=='loaded_recovery' else lookup[(old['episode'],t)];command=np.array(next(a['command'] for a in selected['attempts'] if a['accepted']));other='mailer' if key=='box' else 'box';side=coord['active_side'];sizes={'box':[.14,.09,.045],'mailer':[.15,.145,.04]}
  with np.load(src/'raw.npz') as z:prev=z['action'][t-1,12:23].copy();parent_command=z['action'][t,12:23].copy()
  with np.load(src/'trace.npz') as z:positions={k:z[k][t].copy() for k in sizes}
  with np.load(src/'parcel_orientation.npz') as z:quats={k:z[k][t].copy() for k in sizes}
  geometry=dict(target_xyz=positions[key].tolist(),obstacle_xyz=positions[other].tolist(),target_rotation=Rotation.from_quat(quats[key]).as_matrix().tolist(),obstacle_rotation=Rotation.from_quat(quats[other]).as_matrix().tolist(),target_size=sizes[key],obstacle_size=sizes[other],core_size=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz']);record=dict(step=t,kind=kind,recovery=sample['result'],parent_row=copy.deepcopy(row),parent_coordinate=copy.deepcopy(coord),parent_command=parent_command.tolist(),proposed_command=command.tolist(),geometry=geometry)
  if kind=='unload':record['unload']=selected
  state=RearCopRouteState(rear=SimpleNamespace(plan=fr['plan']),side=side,size=tuple(sizes[key]),hold_established_x=True);state.mode=state.top_mode=row['mode'];state.command=tuple(row['target_xyz']);state.last_waypoint_xy=state.command[:2];state.push_x_anchor=row['push_x_anchor_m'];state.recontacts=row['recontacts'];state.last_recontact_reason=row['last_recontact_reason'];state.load.bias_m=row['contact_load']['stored_z_bias_m'];state.load.filtered_n=row['contact_load']['filtered_vertical_load_n']
  updated=commit(state=state,guard=guard,row=row,coordinate=coord,current=coord['upper_q'],previous=prev,command=command,record=record)
  final_coord=dict(coord,rear_corridor_override=dict(kind=kind,step=t,record_file='rear_corridor_recovery.json'))
  before_pressure=dict(step=t,mode='top_push',top_mode='top_push',bias_m=row['contact_load']['stored_z_bias_m'],filtered_n=row['contact_load']['filtered_vertical_load_n'],pressure_update_count=1);record['parent_pressure_final_state']=before_pressure;after_pressure=dict(before_pressure,mode=updated['mode'],top_mode=updated['mode'],bias_m=state.load.bias_m)
  q=np.zeros((1200,23));u=np.zeros((1200,23));q[t,12:23]=coord['upper_q'];u[t-1,12:23]=prev;u[t,12:23]=command
  fs=[dict(step=j,mode='top_lift') for j in range(1,1200)];cs=[dict(step=j) for j in range(1,1200)];fs[t-1]=updated;cs[t-1]=final_coord
  rr=[dict(step=j,kind='unchanged',recovery=dict(applied=False,reason='original_mode_guard'),parent_command=u[j,12:23].tolist()) for j in range(1,1200)];rr[t-1]=record
  evs=[dict(step=j,kind='unchanged',context=dict(parent_mode='top_lift')) for j in range(1,1200)];hands=[]
  if kind=='unload':
   h=next(r for r in history['rows'] if r['case']=='actual_measured_handover' and 'push_box' in r['episode']);hp=W/h['episode']/'recontact_pose.json';sources[str(hp)]=sha(hp);event=copy.deepcopy(next(r for r in json.loads(hp.read_text())['rows'] if r['step']==h['step']));event['step']=t+1;event['context'].update(step=t+1,recontacts=state.recontacts);event['rear_transport_handover_witness']=h['measured_witness'];evs[t]=event;hands=[dict(step=t+1,kind='measured_directional_handover',recontacts=state.recontacts)]
  ep=fixture/(kind+'_'+key);ep.mkdir();dump(ep/'FIXTURE_ONLY.json',dict(synthetic=True,physics=False,training_ready=False,scope=__doc__,borrowed_request=str(src),request_step=t))
  np.savez(ep/'raw.npz',q=q,action=u,task_id='push_box_to_bin' if key=='box' else 'nudge_mailer_to_bin');np.savez(ep/'trace.npz',**{k:np.repeat(v[None,:],1200,axis=0) for k,v in positions.items()});np.savez(ep/'parcel_orientation.npz',**{k:np.repeat(v[None,:],1200,axis=0) for k,v in quats.items()});dump(ep/'frontal_bypass.json',dict(plan=fr['plan'],rows=fs));dump(ep/'coordination.json',cs);dump(ep/'expert_control.json',[dict(step=t,mode=updated['mode'],target_xyz=updated['target_xyz'])]);dump(ep/'recontact_pose.json',dict(rows=evs));dump(ep/'peak_load_updates.json',dict(final_control_states=[after_pressure]));dump(ep/'rear_corridor_recovery.json',dict(rows=rr,handovers=hands,executed_action_count=1200,pending_recontact=False,training_ready=False))
  result=verify_files(ep,ROOT,S);assert result['passed'] and result['overrides']==1;cases.append(dict(kind=kind,key=key,source_episode=old['episode'],source_step=t,fixture=str(ep),frames=1200,verified_overrides=1,measured_handover_field_checks=len(hands),physics_verified=False))
  for n in ['raw.npz','frontal_bypass.json','coordination.json','trace.npz','parcel_orientation.npz']:sources[str(src/n)]=sha(src/n)
  orig=(ep/'rear_corridor_recovery.json').read_bytes();bad=json.loads(orig);bad['pending_recontact']=True;dump(ep/'rear_corridor_recovery.json',bad);expect_reject(ep,kind+'_'+key+'_pending_end');(ep/'rear_corridor_recovery.json').write_bytes(orig)
  bad=json.loads(orig);bad['rows'].pop();dump(ep/'rear_corridor_recovery.json',bad);expect_reject(ep,kind+'_'+key+'_missing_row');(ep/'rear_corridor_recovery.json').write_bytes(orig)
  original=(ep/'raw.npz').read_bytes();wrong=u.copy();wrong[t,12]+=.001;np.savez(ep/'raw.npz',q=q,action=wrong,task_id='push_box_to_bin' if key=='box' else 'nudge_mailer_to_bin');expect_reject(ep,kind+'_'+key+'_wrong_action');(ep/'raw.npz').write_bytes(original)
  np.savez(ep/'raw.npz',q=q[:-1],action=u[:-1],task_id='push_box_to_bin' if key=='box' else 'nudge_mailer_to_bin');expect_reject(ep,kind+'_'+key+'_short');(ep/'raw.npz').write_bytes(original)
  if hands:
   original=(ep/'recontact_pose.json').read_bytes();bad=json.loads(original);bad['rows'][t]['context']['observed_load_n']=1.;dump(ep/'recontact_pose.json',bad);expect_reject(ep,'loaded_handover');(ep/'recontact_pose.json').write_bytes(original)
  assert verify_files(ep,ROOT,S)['passed']
 # Full wait file boundary and refusal of motion in an empty-table wait.
 ep=fixture/'wait';ep.mkdir();q=np.zeros((70,23));u=q.copy();np.savez(ep/'raw.npz',q=q,action=u,task_id='wait_no_package');dump(ep/'rear_corridor_recovery.json',dict(rows=[],handovers=[],executed_action_count=70,pending_recontact=False,training_ready=False));assert verify_files(ep,ROOT,S)['passed'];cases.append(dict(kind='wait',frames=70,physics_verified=False));u[10,14]=.001;np.savez(ep/'raw.npz',q=q,action=u,task_id='wait_no_package');expect_reject(ep,'moving_wait')
 for p in [Path(__file__),W/'audit_rear_corridor_native_commands_v2.py',W/'audit_rear_corridor_command_records.py',W/'rear_corridor_stationarity.py',W/'support_vertex_stationarity.py',W/'REAR_CORRIDOR_JOINT_RECOVERY_FULL_CHECK.json',W/'REAR_CORRIDOR_UNLOAD_CHECK.json',W/'REAR_TRANSPORT_LIFECYCLE_CHECK.json',S/'rear_corridor_collector_adapter.py',S/'rear_corridor_recovery_state.py']:sources[str(p)]=sha(p)
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,fixture_root=str(fixture),cases=cases,negative_checks=negative,source_sha256=sources,physics_verified=False,training_ready=False)
except BaseException as e:
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=False,error=repr(e),scope=__doc__,fixture_root=str(fixture),cases=cases,negative_checks=negative,training_ready=False);dest.write_text(json.dumps(out,indent=2));raise
else:dest.write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','scope']},indent=2))
