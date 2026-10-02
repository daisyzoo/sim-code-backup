"""Fixed recorded inputs, independent phase/FK/KKT checks; no counterfactual physics.
All original rear-selected physical trajectories are traversed. Sparse solver
requests include entry, both sides of the old boundary, and time quartiles.
"""
from pathlib import Path
import sys,json,hashlib,datetime,os,copy
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];STAGE=W/'staged_rear_corridor_recovery_guarded'
sys.path[:0]=[str(W),str(STAGE),str(ROOT)]
from rear_corridor_latched_phase_v2 import initial_state,propose_phase
from rear_corridor_latched_solver import solve
from rear_corridor_joint_recovery_reserve_candidate import solve as old_solve
from rear_corridor_latched_stationarity import verify
from clearance_runtime import ClearanceGuard
from audit_rear_corridor_command_records import RecoveryVerifier
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
dest=W/'REAR_CORRIDOR_LATCHED_CANDIDATE_V3_CHECK.json';assert not dest.exists()
guard=ClearanceGuard(ROOT,STAGE);verifier=RecoveryVerifier(ROOT,STAGE)
paths=[Path(__file__),W/'rear_corridor_latched_phase_v2.py',W/'rear_corridor_latched_solver.py',W/'rear_corridor_latched_stationarity.py',W/'rear_corridor_joint_recovery_reserve_candidate.py',W/'audit_rear_corridor_command_records.py',W/'audit_self_clearance_task_optimality.py',W/'audit_unloaded_wrist_prior_live.py',W/'support_vertex_stationarity.py',STAGE/'clearance_runtime.py',STAGE/'articulated_hand_geometry.py',STAGE/'self_clearance.py',STAGE/'elbow_torso_hulls.json',ROOT/'simfoundry/robots/g1_assets.py',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']
frozen={str(p):sha(p) for p in paths};sources={};episodes=[];negative=[];synthetic=[]
def save(status,**kw):
 tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=episodes,negative_checks=negative,synthetic_boundary_checks=synthetic,source_sha256=sources,frozen_sha256=frozen,training_ready=False,simulation_started=False,**kw),indent=2));tmp.replace(dest)
try:
 save('running');sizes={'box':[.14,.09,.045],'mailer':[.15,.145,.04]}
 # Measured geometry boundaries are synthetic unit cases, never logged as physics.
 base=dict(side='right',row=dict(step=1,mode='top_push',rear_cop_centering={'override':True}),coordinate=dict(step=1,active_side='right'),target_xyz=[.49,0.,.82],obstacle_xyz=[.32,0.,.82],target_rotation=np.eye(3),obstacle_rotation=np.eye(3),target_size=[.15,.1,.04],obstacle_size=[.15,.1,.04])
 state=initial_state()
 for t,x,active in [(1,.48999,True),(2,.49001,True),(3,.49199,True),(4,.49201,False),(5,.32+.15/2+.15/2+.020,False),(6,.48999,True)]:
  a=copy.deepcopy(base);a['target_xyz'][0]=x;a['row']['step']=a['coordinate']['step']=t
  event=propose_phase(state=state,step=t,**a);assert event['after']['active']==active;state=event['after'];synthetic.append(dict(step=t,target_x=x,active=active))
 for label,change in [('duplicate_step',dict(step=6)),('boolean_step',dict(step=True)),('orphan_active_state',dict(state=dict(active=True,last_step=6,entry_step=None))),('nonfinite_geometry',dict(target_xyz=[float('nan'),0.,.82])),('invalid_rotation',dict(target_rotation=np.zeros((3,3))))]:
  a=copy.deepcopy(base);a['row']['step']=a['coordinate']['step']=7;kwargs=dict(state=state,step=7,**a);kwargs.update(change)
  try:propose_phase(**kwargs)
  except ValueError:negative.append(label)
  else:raise AssertionError(label)
 for ep in sorted((W/'rear_corridor_physical_r1').glob('case_*/layout_*')):
  if not (ep/'raw.npz').exists() or not (ep/'rear_corridor_recovery.json').exists():continue
  rr=json.loads((ep/'rear_corridor_recovery.json').read_text());records=rr['rows']
  if not records:continue
  fr=json.loads((ep/'frontal_bypass.json').read_text());fs={r['step']:r for r in fr['rows']};cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())}
  key='box' if 'push_box' in ep.name else 'mailer';other='mailer' if key=='box' else 'box';side='right' if key=='box' else 'left'
  with np.load(ep/'trace.npz') as z:pos={k:z[k].copy() for k in sizes}
  with np.load(ep/'parcel_orientation.npz') as z:rot={k:Rotation.from_quat(z[k]).as_matrix() for k in sizes}
  with np.load(ep/'raw.npz') as z:actions=z['action'].copy()
  assert len(actions)==1200
  for n in ('frontal_bypass.json','coordination.json','raw.npz','trace.npz','parcel_orientation.npz','rear_corridor_recovery.json'):sources[str(ep/n)]=sha(ep/n)
  state=initial_state();eligible=[];phase_rows=[];lookup={r['step']:r for r in records}
  for record in records:
   t=record['step'];r=record.get('parent_row',fs[t]);c=record.get('parent_coordinate',cs[t]);geom=dict(target_xyz=pos[key][t],obstacle_xyz=pos[other][t],target_rotation=rot[key][t],obstacle_rotation=rot[other][t],target_size=sizes[key],obstacle_size=sizes[other]);before=copy.deepcopy(state)
   event=propose_phase(state=state,step=t,side=side,row=r,coordinate=c,**geom);assert state==before
   # Independent radius, original guard and chronological transition reconstruction.
   rad=np.sum(abs(rot[key][t])*np.array(sizes[key])[None,:],axis=1)/2;orr=np.sum(abs(rot[other][t])*np.array(sizes[other])[None,:],axis=1)/2
   deficit=float(pos[other][t,0]+orr[0]+rad[0]+.020-pos[key][t,0]);pending=bool((-1 if side=='right' else 1)*(pos[key][t,1]-pos[other][t,1])<=rad[1]+orr[1]+.020)
   ok=bool(r['mode']=='top_push' and not any((r.get('route_stop_reason'),r.get('release_reason'),c.get('region_joint_override'),c.get('terminal_joint_hold'))) and r.get('rear_cop_centering',{}).get('override'))
   active=(pending and deficit>-.002) if state['active'] else (ok and pending and deficit>0)
   expected=dict(active=bool(active),last_step=t,entry_step=(state['entry_step'] if state['active'] else t) if active else None)
   assert event['before']==state and event['after']==expected and event['eligible']==ok and event['request_recovery']==bool(active and ok)
   assert abs(event['original_deficit_m']-deficit)<1e-12
   phase_rows.append(dict(step=t,reason=event['reason'],active=bool(active),request=bool(active and ok),original_deficit_mm=deficit*1000))
   if active and ok:eligible.append(t)
   state=event['after']
  sample=set(eligible[i] for i in np.linspace(0,len(eligible)-1,5,dtype=int)) if eligible else set()
  for sign in (True,False):
   ts=[r['step'] for r in phase_rows if r['request'] and (r['original_deficit_mm']>0)==sign]
   if ts:sample.update([ts[0],ts[-1]])
  item=dict(episode=str(ep.relative_to(W)),phase_rows=phase_rows,phase_requests=len(eligible),held_beyond_old_boundary=sum(r['request'] and r['original_deficit_mm']<=0 for r in phase_rows),solver_rows=[]);episodes.append(item);save('running')
  for t in sorted(sample):
   record=lookup[t];r=record.get('parent_row',fs[t]);c=record.get('parent_coordinate',cs[t]);geometry=dict(target_xyz=pos[key][t],obstacle_xyz=pos[other][t],target_rotation=rot[key][t],obstacle_rotation=rot[other][t],target_size=sizes[key],obstacle_size=sizes[other],core_size=fr['plan']['rear_cop_centering']['actual_core_size_xyz']);args=dict(enabled=True,guard=guard,row=r,coordinate=c,current=np.asarray(c['upper_q']),previous=actions[t-1,12:23],parent_command=np.asarray(record['parent_command']),**geometry)
   # Off matches the unchanged solver exactly on the same causal inputs.
   old,old_trace=old_solve(**args);plain,plain_trace=solve(**args,recovery_active=False)
   assert (old is None)==(plain is None)
   if old is not None:assert np.array_equal(old,plain)
   for k,v in old_trace.items():assert plain_trace[k]==v,k
   cmd,result=solve(**args,recovery_active=True);check=dict(step=t,result=result,default_off_identical=True)
   if cmd is not None and result['applied']:
    T0=verifier.hand.fk(args['current'],side);T=verifier.hand.fk(cmd,side);offset=np.asarray(r['control_offset_local']);delta=T[:3,3]+T[:3,:3]@offset-T0[:3,3]-T0[:3,:3]@offset
    assert abs(delta[1])<=1e-7 and .0001-1e-7<=delta[0]<=result['requested_x_m']+1e-7
    assert min(verifier.elbows.gap(cmd))>=.005-2e-7
    assert np.all(cmd>=verifier.lower-2e-7) and np.all(cmd<=verifier.upper+2e-7) and np.all(abs(cmd-args['current'])<=verifier.steps+2e-7) and max(abs(cmd-args['previous']))<=.0550002
    cert=verify(verifier,row=r,coordinate=c,current=args['current'],previous=args['previous'],command=cmd,kind='loaded_recovery',geometry=geometry,recovery_active=True);assert cert['passed'],cert
    check.update(independent_delta_xyz_m=delta.tolist(),certificate=cert)
   else:assert cmd is None and result['requires_recontact']
   item['solver_rows'].append(check);save('running');print(ep.name,t,result['reason'],flush=True)
 for p,h in {**sources,**frozen}.items():assert sha(p)==h,p
 save('complete',passed=True,phase_rows=sum(len(e['phase_rows']) for e in episodes),solver_requests=sum(len(e['solver_rows']) for e in episodes),remaining='Collector wiring, independent full native phase/command and original audit adaptation, then new complete physical comparison. Recorded-input outcomes do not predict physical success.')
except BaseException as e:save('check_failed',passed=False,error=repr(e));raise
