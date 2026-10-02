"""SYNTHETIC full-length file-format fixtures, not physics or data admission.
Borrow real request states, solve new commands, retain sparse mode stubs elsewhere.
Independently audit phase chronology, commands and original1e-6 KKT. Original
source, scene path/contact and quality audits must reject these as real episodes.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib,datetime,tempfile,copy,os
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_corridor_latched';sys.path[:0]=[str(S),str(W),str(ROOT)]
from audit_rear_corridor_latched_native import verify_files
from rear_corridor_latched_adapter import propose,commit,commit_phase
from rear_corridor_latched_phase_v2 import initial_state
from rear_cop_route import RearCopRouteState
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S)
fixture=Path(tempfile.mkdtemp(prefix='rear_latched_SYNTHETIC_NO_PHYSICS_'));dest=W/'REAR_CORRIDOR_LATCHED_NATIVE_FIXTURE_CHECK.json';assert not dest.exists()
full=json.loads((W/'REAR_CORRIDOR_JOINT_RECOVERY_FULL_CHECK.json').read_text());history=json.loads((W/'REAR_TRANSPORT_LIFECYCLE_CHECK.json').read_text());cases=[];negative=[];sources={};frozen={str(p):sha(p) for p in [Path(__file__),W/'audit_rear_corridor_latched_native.py',W/'audit_rear_corridor_latched_phase.py',W/'audit_rear_corridor_latched_records.py',W/'rear_corridor_latched_stationarity.py',W/'support_vertex_stationarity.py',S/'PREPARATION.json',*[S/n for n in json.loads((S/'PREPARATION.json').read_text())['stage_sha256']]]}
def dump(p,obj):p.write_text(json.dumps(obj))
def save(status,**kw):
 tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,fixtures=cases,negative_checks=negative,fixture_root=str(fixture),source_sha256=sources,frozen_sha256=frozen,physics=False,training_ready=False,**kw),indent=2));tmp.replace(dest)
def reject(ep,label):
 try:verify_files(ep,ROOT,S)
 except (AssertionError,ValueError,KeyError):negative.append(label)
 else:raise AssertionError('Corruption accepted: '+label)
try:
 save('running')
 for kind,key in [('loaded_recovery','box'),('loaded_recovery','mailer'),('unload','box')]:
  old=next(ep for ep in full['episodes'] if ('push_box' in ep['episode'])==(key=='box') and any(r['result']['applied']==(kind=='loaded_recovery') for r in ep['rows']));sample=next(r for r in old['rows'] if r['result']['applied']==(kind=='loaded_recovery'));t=sample['step'];src=W/old['episode'];fr=json.loads((src/'frontal_bypass.json').read_text());row=copy.deepcopy(next(r for r in fr['rows'] if r['step']==t));coord=copy.deepcopy(next(c for c in json.loads((src/'coordination.json').read_text()) if c['step']==t));other='mailer' if key=='box' else 'box';side=coord['active_side'];sizes={'box':[.14,.09,.045],'mailer':[.15,.145,.04]}
  with np.load(src/'raw.npz') as z:prev=z['action'][t-1,12:23].copy();parent=z['action'][t,12:23].copy()
  with np.load(src/'trace.npz') as z:pos={k:z[k][t].copy() for k in sizes}
  with np.load(src/'parcel_orientation.npz') as z:quats={k:z[k][t].copy() for k in sizes}
  geometry=dict(target_xyz=pos[key],obstacle_xyz=pos[other],target_rotation=Rotation.from_quat(quats[key]).as_matrix(),obstacle_rotation=Rotation.from_quat(quats[other]).as_matrix(),target_size=sizes[key],obstacle_size=sizes[other],core_size=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'])
  q=np.zeros((1200,23));u=np.zeros((1200,23));q[t,12:23]=coord['upper_q'];u[t-1,12:23]=prev
  fs=[dict(step=j,mode='top_lift') for j in range(1,1200)];cs=[dict(step=j) for j in range(1,1200)];rr=[];phase=initial_state();hands=[];evs=[dict(step=j,kind='unchanged',context=dict(parent_mode='top_lift')) for j in range(1,1200)]
  for j in range(1,1200):
   r=row if j==t else fs[j-1];c=coord if j==t else cs[j-1];p=parent if j==t else u[j,12:23]
   cmd,record=propose(enabled=True,step=j,selected=True,parent_command=p,phase_state=phase,side=side,guard=guard,row=r,coordinate=c,current=q[j,12:23],previous=u[j-1,12:23],**geometry)
   assert cmd is not None
   if j==t:
    assert record['kind']==kind,('new branch differs',kind,record['kind']);u[t,12:23]=cmd
    st=RearCopRouteState(rear=SimpleNamespace(plan=fr['plan']),side=side,size=tuple(sizes[key]),hold_established_x=True);st.mode=st.top_mode=row['mode'];st.command=tuple(row['target_xyz']);st.last_waypoint_xy=st.command[:2];st.push_x_anchor=row['push_x_anchor_m'];st.recontacts=row['recontacts'];st.last_recontact_reason=row['last_recontact_reason'];st.load.bias_m=row['contact_load']['stored_z_bias_m'];st.load.filtered_n=row['contact_load']['filtered_vertical_load_n']
    updated=commit(state=st,guard=guard,row=row,coordinate=coord,current=coord['upper_q'],previous=prev,command=cmd,record=record);fs[t-1]=updated;cs[t-1]=dict(coord,rear_corridor_override=dict(kind=kind,step=t,record_file='rear_corridor_recovery.json'))
    before=dict(step=t,mode='top_push',top_mode='top_push',bias_m=row['contact_load']['stored_z_bias_m'],filtered_n=row['contact_load']['filtered_vertical_load_n'],pressure_update_count=1);record['parent_pressure_final_state']=before;after=dict(before,mode=updated['mode'],top_mode=updated['mode'],bias_m=st.load.bias_m)
    phase=commit_phase(phase_state=phase,record=record,guard=guard,current=coord['upper_q'],previous=prev,command=cmd)
   else:
    # Deliberately synthetic sparse rows; test FILE FORMAT, not command admissibility.
    assert record['kind']=='unchanged';phase=record['phase']['after'];record['phase_committed']=copy.deepcopy(phase)
   rr.append(record)
  if kind=='unload':
   h=next(r for r in history['rows'] if r['case']=='actual_measured_handover' and 'push_box' in r['episode']);hp=W/h['episode']/'recontact_pose.json';sources[str(hp)]=sha(hp);event=copy.deepcopy(next(r for r in json.loads(hp.read_text())['rows'] if r['step']==h['step']));event['step']=t+1;event['context'].update(step=t+1,recontacts=st.recontacts);event['rear_transport_handover_witness']=h['measured_witness'];evs[t]=event;hands=[dict(step=t+1,kind='measured_directional_handover',recontacts=st.recontacts)]
  ep=fixture/(kind+'_'+key);ep.mkdir();dump(ep/'FIXTURE_ONLY.json',dict(synthetic=True,physics=False,scope=__doc__,training_ready=False))
  np.savez(ep/'raw.npz',q=q,action=u,task_id='push_box_to_bin' if key=='box' else 'nudge_mailer_to_bin');np.savez(ep/'trace.npz',**{k:np.repeat(v[None,:],1200,axis=0) for k,v in pos.items()});np.savez(ep/'parcel_orientation.npz',**{k:np.repeat(v[None,:],1200,axis=0) for k,v in quats.items()});dump(ep/'frontal_bypass.json',dict(plan=fr['plan'],rows=fs));dump(ep/'coordination.json',cs);dump(ep/'expert_control.json',[dict(step=t,mode=updated['mode'],target_xyz=updated['target_xyz'])]);dump(ep/'recontact_pose.json',dict(rows=evs));dump(ep/'peak_load_updates.json',dict(final_control_states=[after]));log=dict(rows=rr,handovers=hands,executed_action_count=1200,pending_recontact=False,training_ready=False);dump(ep/'rear_corridor_recovery.json',log)
  proof=verify_files(ep,ROOT,S);assert proof['passed'] and proof['overrides']==1 and len(proof['phase_records'])==1199;cases.append(dict(kind=kind,key=key,fixture=str(ep),frames=1200,phase_records=1199,verified_overrides=1,handover_checks=len(hands),source_episode=str(src),source_step=t,physics=False));save('running')
  original=(ep/'rear_corridor_recovery.json').read_bytes()
  changes=[('false_entry',lambda d:d['rows'][t-1]['phase']['before'].update(active=True,entry_step=1)),('premature_exit',lambda d:d['rows'][t]['phase']['after'].update(active=False,entry_step=None)),('changed_reserve',lambda d:d['rows'][t-1]['phase'].update(exit_reserve_m=.001)),('changed_geometry',lambda d:d['rows'][t-1]['phase']['geometry']['target_xyz'].__setitem__(0,999.)),('missing_commit',lambda d:d['rows'][t-1].pop('phase_committed')),('pending_at_end',lambda d:d.update(pending_recontact=True)),('missing_row',lambda d:d['rows'].pop())]
  for label,mutate in changes:
   bad=json.loads(original);mutate(bad);dump(ep/'rear_corridor_recovery.json',bad);reject(ep,kind+'_'+key+'_'+label);(ep/'rear_corridor_recovery.json').write_bytes(original)
  for n in ('raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json'):sources[str(src/n)]=sha(src/n)
  print(kind,key,'verified1199phases',flush=True)
 wait=fixture/'wait';wait.mkdir();np.savez(wait/'raw.npz',q=np.zeros((70,23)),action=np.zeros((70,23)),task_id='wait_no_package');dump(wait/'rear_corridor_recovery.json',dict(rows=[],handovers=[],executed_action_count=70,pending_recontact=False,training_ready=False));assert verify_files(wait,ROOT,S)['passed'];cases.append(dict(kind='wait',frames=70,physics=False))
 for p,h in {**sources,**frozen}.items():assert sha(p)==h,p
 save('complete',passed=True)
except BaseException as e:save('check_failed',passed=False,error=repr(e));raise
