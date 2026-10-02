"""Synthetic full-file chronology with two consecutive real loaded requests.
Only these two requests receive real solver/commit calls; other controls are sparse
mode stubs. Not physical rollout evidence, not data eligible for training.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib,datetime,tempfile,copy,os
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_recovery_tracking';sys.path[:0]=[str(S),str(W),str(ROOT)]
from audit_rear_recovery_tracking_native import verify_files
from rear_recovery_tracking_adapter import propose,commit,commit_phase
from rear_corridor_latched_phase_v2 import initial_state
from rear_cop_route import RearCopRouteState
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S);base=W/'rear_latched_physical_r1';fixture=Path(tempfile.mkdtemp(prefix='rear_tracking_pair_SYNTHETIC_NO_PHYSICS_'));dest=W/'REAR_RECOVERY_TRACKING_NATIVE_PAIR_FIXTURE_CHECK.json';assert not dest.exists();cases=[];negative=[];sources={};frozen={str(p):sha(p) for p in [Path(__file__),W/'audit_rear_recovery_tracking_native.py',W/'audit_rear_recovery_tracking_observation.py',W/'audit_rear_recovery_tracking_records.py',W/'rear_recovery_tracking_stationarity.py',W/'audit_rear_corridor_latched_phase.py',W/'rear_corridor_latched_stationarity.py',W/'support_vertex_stationarity.py',*[S/n for n in json.loads((S/'PREPARATION.json').read_text())['stage_sha256']]]}
def dump(p,d):p.write_text(json.dumps(d))
def save(status,**kw):
 p=dest.with_suffix('.tmp');p.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,fixture_root=str(fixture),cases=cases,negative_checks=negative,source_sha256=sources,frozen_sha256=frozen,physics=False,training_ready=False,**kw),indent=2));p.replace(dest)
try:
 save('running')
 for rel,key in [('case_840004/layout_840004_nudge_mailer_to_bin','mailer'),('case_840015/layout_840015_push_box_to_bin','box')]:
  src=base/rel;fr=json.loads((src/'frontal_bypass.json').read_text());original=json.loads((src/'rear_corridor_recovery.json').read_text())['rows'];rs={r['step']:r for r in original};t=next(r['step'] for r in original if r['kind']=='loaded_recovery');assert rs[t+1]['kind']=='loaded_recovery';side='left' if key=='mailer' else 'right';other='box' if key=='mailer' else 'mailer';sizes={'box':[.14,.09,.045],'mailer':[.15,.145,.04]}
  with np.load(src/'raw.npz') as z:q=z['q'].astype(float);u=z['action'].astype(float)
  with np.load(src/'trace.npz') as z:pos={k:z[k].copy() for k in sizes}
  with np.load(src/'parcel_orientation.npz') as z:quats={k:z[k].copy() for k in sizes}
  rots={k:Rotation.from_quat(v).as_matrix() for k,v in quats.items()}
  fs=[dict(step=j,mode='top_lift') for j in range(1,1200)];cs=[dict(step=j) for j in range(1,1200)];records=[];ex=[];pressure=[];phase=initial_state()
  for j in range(1,1200):
   chosen=j in [t,t+1];r=copy.deepcopy(rs[j]['parent_row']) if chosen else fs[j-1];c=copy.deepcopy(rs[j]['parent_coordinate']) if chosen else cs[j-1]
   g=dict(target_xyz=pos[key][j],obstacle_xyz=pos[other][j],target_rotation=rots[key][j],obstacle_rotation=rots[other][j],target_size=sizes[key],obstacle_size=sizes[other],core_size=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'])
   parent=np.asarray(rs[j]['parent_command']) if chosen else u[j,12:23]
   cmd,record=propose(enabled=True,step=j,selected=True,parent_command=parent,phase_state=phase,side=side,guard=guard,row=r,coordinate=c,current=q[j,12:23],previous=u[j-1,12:23],tracking_feedback=True,previous_recovery_record=records[-1] if records else None,**g)
   assert cmd is not None
   if chosen:
    assert record['kind']=='loaded_recovery';u[j,12:23]=cmd
    if j==t:assert np.array_equal(cmd,rs[t]['emitted_command']),'The prior actually emitted command must match the source at the second measured frame'
    else:assert record['recovery']['tracking_feedback']['accepted'] is True
    state=RearCopRouteState(rear=SimpleNamespace(plan=fr['plan']),side=side,size=tuple(sizes[key]),hold_established_x=True);state.top_mode=state.mode=r['mode'];state.command=tuple(r['target_xyz']);state.last_waypoint_xy=state.command[:2];state.push_x_anchor=r['push_x_anchor_m'];state.recontacts=r['recontacts'];state.load.bias_m=r['contact_load']['stored_z_bias_m'];state.load.filtered_n=r['contact_load']['filtered_vertical_load_n']
    updated=commit(state=state,guard=guard,row=r,coordinate=c,current=q[j,12:23],previous=u[j-1,12:23],command=cmd,record=record);fs[j-1]=updated;cs[j-1]=dict(c,rear_corridor_override=dict(kind=record['kind'],step=j,record_file='rear_corridor_recovery.json'))
    before=dict(step=j,mode=r['mode'],top_mode=r['mode'],bias_m=r['contact_load']['stored_z_bias_m'],filtered_n=r['contact_load']['filtered_vertical_load_n'],pressure_update_count=j);record['parent_pressure_final_state']=before;pressure.append(dict(before));ex.append(dict(step=j,mode=updated['mode'],target_xyz=updated['target_xyz']))
    phase=commit_phase(phase_state=phase,record=record,guard=guard,current=q[j,12:23],previous=u[j-1,12:23],command=cmd)
   else:assert record['kind']=='unchanged';phase=record['phase']['after'];record['phase_committed']=copy.deepcopy(phase)
   records.append(record)
  ep=fixture/key;ep.mkdir();dump(ep/'FIXTURE_ONLY.json',dict(synthetic=True,physics=False,scope=__doc__,training_ready=False));np.savez(ep/'raw.npz',q=q,action=u,task_id='push_box_to_bin' if key=='box' else 'nudge_mailer_to_bin');np.savez(ep/'trace.npz',**pos);np.savez(ep/'parcel_orientation.npz',**quats);dump(ep/'frontal_bypass.json',dict(plan=fr['plan'],rows=fs));dump(ep/'coordination.json',cs);dump(ep/'expert_control.json',ex);dump(ep/'peak_load_updates.json',dict(final_control_states=pressure));dump(ep/'recontact_pose.json',dict(rows=[]));log=dict(rows=records,handovers=[],executed_action_count=1200,pending_recontact=False,training_ready=False);dump(ep/'rear_corridor_recovery.json',log)
  proof=verify_files(ep,ROOT,S);assert proof['passed'] and proof['overrides']==2 and len(proof['phase_records'])==1199
  originalbytes=(ep/'rear_corridor_recovery.json').read_bytes()
  changes=[('incorrect_bias',lambda d:d['rows'][t]['recovery']['tracking_feedback']['correction_xyz_m'].__setitem__(0,0.)),('future_previous_step',lambda d:d['rows'][t]['recovery']['tracking_feedback'].update(previous_step=t+1)),('uncommitted_previous',lambda d:d['rows'][t-1]['commit']['final_guard'].update(accepted=False)),('missing_previous_row',lambda d:d['rows'].pop(t-1)),('disabled_feedback_claim',lambda d:d['rows'][t]['recovery']['tracking_feedback'].update(accepted=False))]
  for label,mutate in changes:
   bad=json.loads(originalbytes);mutate(bad);dump(ep/'rear_corridor_recovery.json',bad)
   try:verify_files(ep,ROOT,S)
   except (AssertionError,ValueError,KeyError):negative.append(key+'_'+label)
   else:raise AssertionError('Corruption accepted '+label)
   (ep/'rear_corridor_recovery.json').write_bytes(originalbytes)
  cases.append(dict(key=key,fixture=str(ep),source_episode=str(src),source_steps=[t,t+1],verified_overrides=2,tracking_overrides=1,phase_records=1199,physics=False))
  for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','rear_corridor_recovery.json']:sources[str(src/n)]=sha(src/n)
  save('running');print(key,'verified causal pair',flush=True)
 for p,h in {**sources,**frozen}.items():assert sha(p)==h,p
 save('complete',passed=True)
except BaseException as e:save('check_failed',passed=False,error=repr(e));raise
