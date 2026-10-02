"""SYNTHETIC sparse native fixture of entry then recovery beyond old20mm boundary.
Borrowed actual states at214/217 are fixed inputs, not a physically consistent
trajectory after the new action. The complete original audit cannot admit it.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib,copy,tempfile,datetime
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_corridor_latched';sys.path[:0]=[str(S),str(W),str(ROOT)]
from audit_rear_corridor_latched_native import verify_files
from rear_corridor_latched_adapter import propose,commit,commit_phase
from rear_corridor_latched_phase_v2 import initial_state
from rear_cop_route import RearCopRouteState
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S);ep=Path(tempfile.mkdtemp(prefix='latched_held_SYNTHETIC_NO_PHYSICS_'));dest=W/'REAR_LATCHED_HELD_NATIVE_CHECK.json';assert not dest.exists();src=W/'rear_corridor_physical_r1/case_840015/layout_840015_push_box_to_bin'
fr=json.loads((src/'frontal_bypass.json').read_text());oldfs={r['step']:r for r in fr['rows']};oldcs={r['step']:r for r in json.loads((src/'coordination.json').read_text())};oldrr={r['step']:r for r in json.loads((src/'rear_corridor_recovery.json').read_text())['rows']}
with np.load(src/'raw.npz') as z:q=z['q'].astype(float);old_u=z['action'].astype(float)
u=old_u.copy()
with np.load(src/'trace.npz') as z:pos={k:z[k].copy() for k in ['box','mailer']}
with np.load(src/'parcel_orientation.npz') as z:quats={k:z[k].copy() for k in ['box','mailer']}
rot={k:Rotation.from_quat(v).as_matrix() for k,v in quats.items()};sizes={'box':[.14,.09,.045],'mailer':[.15,.145,.04]};fs=[];cs=[];rr=[];experts=[];pressure=[];phase=initial_state();steps=[214,217];negative=[]
for t in range(1,1200):
 r=copy.deepcopy(oldrr[t].get('parent_row',oldfs[t])) if t in steps else dict(step=t,mode='top_lift')
 c=copy.deepcopy(oldrr[t].get('parent_coordinate',oldcs[t])) if t in steps else dict(step=t)
 geom=dict(target_xyz=pos['box'][t],obstacle_xyz=pos['mailer'][t],target_rotation=rot['box'][t],obstacle_rotation=rot['mailer'][t],target_size=sizes['box'],obstacle_size=sizes['mailer'],core_size=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'])
 cmd,record=propose(enabled=True,step=t,selected=True,parent_command=np.asarray(oldrr[t]['parent_command']) if t in steps else u[t,12:23],phase_state=phase,side='right',guard=guard,row=r,coordinate=c,current=q[t,12:23],previous=u[t-1,12:23],**geom);assert cmd is not None
 if t in steps:
  assert record['kind']=='loaded_recovery';assert (record['phase']['original_deficit_m']>0)==(t==214)
  state=RearCopRouteState(rear=SimpleNamespace(plan=fr['plan']),side='right',size=tuple(sizes['box']),hold_established_x=True);state.mode=state.top_mode=r['mode'];state.command=tuple(r['target_xyz']);state.last_waypoint_xy=state.command[:2];state.push_x_anchor=r['push_x_anchor_m'];state.recontacts=r['recontacts'];state.last_recontact_reason=r['last_recontact_reason'];state.load.bias_m=r['contact_load']['stored_z_bias_m'];state.load.filtered_n=r['contact_load']['filtered_vertical_load_n']
  final=commit(state=state,guard=guard,row=r,coordinate=c,current=q[t,12:23],previous=u[t-1,12:23],command=cmd,record=record);u[t,12:23]=cmd
  before=dict(step=t,mode='top_push',top_mode='top_push',bias_m=r['contact_load']['stored_z_bias_m'],filtered_n=r['contact_load']['filtered_vertical_load_n'],pressure_update_count=1);record['parent_pressure_final_state']=before;pressure.append(dict(before));experts.append(dict(step=t,mode=final['mode'],target_xyz=final['target_xyz']));r=final;c=dict(c,rear_corridor_override=dict(kind='loaded_recovery',step=t,record_file='rear_corridor_recovery.json'))
  phase=commit_phase(phase_state=phase,record=record,guard=guard,current=q[t,12:23],previous=u[t-1,12:23],command=cmd)
 else:
  assert record['kind']=='unchanged';phase=record['phase']['after'];record['phase_committed']=copy.deepcopy(phase)
 fs.append(r);cs.append(c);rr.append(record)
def dump(name,value):(ep/name).write_text(json.dumps(value))
np.savez(ep/'raw.npz',q=q,action=u,task_id='push_box_to_bin');np.savez(ep/'trace.npz',**pos);np.savez(ep/'parcel_orientation.npz',**quats)
dump('FIXTURE_ONLY.json',dict(synthetic=True,physics=False,scope=__doc__,training_ready=False));dump('frontal_bypass.json',dict(plan=fr['plan'],rows=fs));dump('coordination.json',cs);dump('expert_control.json',experts);dump('peak_load_updates.json',dict(final_control_states=pressure));dump('recontact_pose.json',dict(rows=[]));log=dict(rows=rr,handovers=[],executed_action_count=1200,pending_recontact=False,training_ready=False);dump('rear_corridor_recovery.json',log)
proof=verify_files(ep,ROOT,S);assert proof['passed'] and proof['overrides']==2 and len(proof['phase_records'])==1199
for label,mutate in [('fake_clearance_exit',lambda d:d['rows'][216]['phase'].update(reason='measured_exit_reserve')),('erase_entry',lambda d:d['rows'][216]['phase']['before'].update(active=False,entry_step=None)),('unlatched_solver',lambda d:d['rows'][216]['recovery'].update(recovery_active=False)),('wrong_new_objective',lambda d:d['rows'][216]['recovery'].__setitem__('requested_x_m',.001))]:
 bad=copy.deepcopy(log);mutate(bad);dump('rear_corridor_recovery.json',bad)
 try:verify_files(ep,ROOT,S)
 except (AssertionError,ValueError,KeyError):negative.append(label)
 else:raise AssertionError(label)
dump('rear_corridor_recovery.json',log)
report=dict(passed=True,status='complete',created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,fixture=str(ep),frames=1200,phase_rows=1199,overrides=steps,held_deficit_m=rr[216]['phase']['original_deficit_m'],negative_checks=negative,source_sha256={n:sha(src/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json','rear_corridor_recovery.json']},auditor_sha256={n:sha(W/n) for n in ['audit_rear_corridor_latched_phase.py','audit_rear_corridor_latched_records.py','audit_rear_corridor_latched_native.py','rear_corridor_latched_stationarity.py']},checker_sha256=sha(__file__),training_ready=False,physics=False);dest.write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','auditor_sha256','scope']},indent=2))
