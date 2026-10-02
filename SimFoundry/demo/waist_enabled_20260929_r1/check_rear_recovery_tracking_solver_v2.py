"""Fixed actual input screen of causal XY tracking correction, independent FK/KKT.
No resulting trajectory is synthesized, no physics or data admission.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy,os
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_corridor_latched';sys.path[:0]=[str(W),str(S),str(ROOT)]
from rear_recovery_tracking_solver_v2 import solve
from rear_corridor_latched_solver import solve as parent_solve
from rear_recovery_tracking_observation_v2 import observe
from rear_recovery_tracking_stationarity import verify
from audit_rear_corridor_latched_records_v2 import RecoveryVerifier
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S);ind=RecoveryVerifier(ROOT,S);rows=[];negative=[];sources={};dest=W/'REAR_RECOVERY_TRACKING_SOLVER_V2_CHECK.json';assert not dest.exists();paths=[Path(__file__),W/'rear_recovery_tracking_solver_v2.py',W/'rear_recovery_tracking_observation_v2.py',W/'rear_recovery_tracking_stationarity.py',W/'rear_corridor_latched_solver.py',W/'audit_rear_corridor_latched_records_v2.py',W/'support_vertex_stationarity.py',W/'audit_unloaded_wrist_prior_live.py',W/'audit_self_clearance_task_optimality.py',S/'clearance_runtime.py',S/'articulated_hand_geometry.py',S/'self_clearance.py',S/'elbow_torso_hulls.json',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf'];frozen={str(p):sha(p) for p in paths}
def save(status,**kw):
 p=dest.with_suffix('.tmp');p.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,negative_checks=negative,source_sha256=sources,frozen_sha256=frozen,simulation_started=False,training_ready=False,**kw),indent=2));p.replace(dest)
try:
 save('running')
 for relative in ['case_840004/layout_840004_nudge_mailer_to_bin','case_840015/layout_840015_push_box_to_bin']:
  ep=W/'rear_latched_physical_r1'/relative;rs={r['step']:r for r in json.loads((ep/'rear_corridor_recovery.json').read_text())['rows']};eligible=[t for t,r in rs.items() if r['kind']=='loaded_recovery' and rs.get(t-1,{}).get('kind')=='loaded_recovery'];selected=sorted(set(eligible[i] for i in np.linspace(0,len(eligible)-1,7,dtype=int)))
  with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
  for n in ['rear_corridor_recovery.json','raw.npz']:sources[str(ep/n)]=sha(ep/n)
  for t in selected:
   r=rs[t];row=r['parent_row'];c=r['parent_coordinate'];g=r['geometry'];args=dict(enabled=True,recovery_active=True,guard=guard,row=row,coordinate=c,current=q[t],previous=u[t-1],parent_command=r['parent_command'],**g)
   off,off_trace=solve(**args);parent,pt=parent_solve(**args);assert (off is None)==(parent is None) and off_trace==pt
   if off is not None:assert np.array_equal(off,parent)
   obs=observe(enabled=True,guard=guard,row=row,coordinate=c,current=q[t],previous=u[t-1],previous_record=rs[t-1]);assert obs['accepted'];side=c['active_side'];offset=np.asarray(row['control_offset_local'])
   def point(x):
    T=ind.hand.fk(x,side);return T[:3,3]+T[:3,:3]@offset
   measured=point(q[t]);prior=point(u[t-1]);bias=measured-prior;assert max(abs(bias-np.asarray(obs['observed_residual_xyz_m'])))<2e-10;bias[2]=0.
   assert np.array_equal(u[t-1],rs[t-1]['emitted_command']) and rs[t-1]['step']==t-1 and rs[t-1]['parent_row']['recontacts']==row['recontacts']
   cmd,result=solve(**args,tracking_feedback=True,previous_recovery_record=rs[t-1]);item=dict(episode=relative,step=t,tracking=obs,result=result,default_off_identical=True)
   if cmd is not None and result['applied']:
    delta=point(cmd)-measured;predicted=delta+bias;assert .0001-1e-7<=delta[0]<=.0035+1e-7 and .0001-1e-7<=predicted[0]<=result['requested_x_m']+1e-7 and abs(predicted[1])<=1e-7
    assert np.all(cmd>=ind.lower-2e-7) and np.all(cmd<=ind.upper+2e-7) and np.all(abs(cmd-q[t])<=ind.steps+2e-7) and max(abs(cmd-u[t-1]))<=.0550002
    assert min(ind.elbows.gap(cmd))>=.005-2e-7
    cert=verify(ind,row=row,coordinate=c,current=q[t],previous=u[t-1],command=cmd,kind='loaded_recovery',geometry=g,recovery_active=True,tracking_bias_xyz_m=bias);assert cert['passed'],cert
    item.update(independent_nominal_delta_xyz_m=delta.tolist(),predicted_delta_xyz_m=predicted.tolist(),certificate=cert)
   else:assert cmd is None and result['requires_recontact']
   rows.append(item);save('running');print(relative,t,result['reason'],flush=True)
   if not negative:
    for label,kw in [('disabled',dict(enabled=False)),('uncommitted',dict(previous_record=dict(rs[t-1],commit=None))),('wrong_previous',dict(previous=u[t-1]+.001)),('bad_current',dict(current=q[t]+.001)),('old_step',dict(previous_record=dict(rs[t-1],step=t-2)))]:
     base=dict(enabled=True,guard=guard,row=row,coordinate=c,current=q[t],previous=u[t-1],previous_record=rs[t-1]);base.update(kw)
     try:value=observe(**base)
     except ValueError:negative.append(label)
     else:
      if label=='uncommitted':
       # A missing actual commit must be rejected; None is not a commit.
       assert not value['accepted'],label
      else:assert not value['accepted'],label
      negative.append(label)
    for bad in [0,1,'true']:
     try:solve(**args,tracking_feedback=bad,previous_recovery_record=rs[t-1])
     except ValueError:negative.append('flag_'+repr(bad))
     else:raise AssertionError('Invalid tracking flag accepted')
 for p,h in {**sources,**frozen}.items():assert sha(p)==h,p
 save('complete',passed=True,verified_commands=sum('certificate' in r for r in rows),requests=len(rows),remaining='Broader held/history-domain/uncertainty checks; actual adapter, fallback unload/state/audit wiring; then complete paired physical comparison. This is not demonstrated task improvement.')
except BaseException as e:save('check_failed',passed=False,error=repr(e));raise
