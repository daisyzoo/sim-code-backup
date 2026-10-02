"""Actual fixed input checks, no counterfactual physical continuation.
Default-off exactly reproduces the parent. New loaded commands require
independent FK/1e-6 KKT; failed new solves request independently checked original
unload. A verified unload proposal is not actual unloading or handover.
"""
from pathlib import Path
import sys,json,hashlib,datetime,os
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_transport_retry';sys.path[:0]=[str(W),str(S),str(ROOT)]
from rear_recovery_progress_gate_candidate_v2 import solve
from rear_recovery_tracking_solver_v2 import solve as parent_solve
from rear_corridor_unload_candidate import solve_lift
from clearance_runtime import ClearanceGuard
from audit_rear_recovery_tracking_records import RecoveryVerifier
from rear_recovery_progress_gate_stationarity import verify as verify_loaded
from rear_corridor_latched_stationarity import verify as verify_unload
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();dest=W/'REAR_PROGRESS_GATE_FIRST_INTERVENTIONS_CHECK.json';assert not dest.exists();guard=ClearanceGuard(ROOT,S);ind=RecoveryVerifier(ROOT,S);rows=[];sources={};reference={'rows':[]}
for case,task in [(840004,'nudge_mailer_to_bin'),(840015,'push_box_to_bin')]:
 ep=W/'rear_transport_retry_physical_r1'/f'case_{case}'/f'layout_{case}_{task}'
 for record in json.loads((ep/'rear_corridor_recovery.json').read_text())['rows']:
  result=record.get('recovery',{});feedback=result.get('tracking_feedback',{})
  if record['kind']=='loaded_recovery' and feedback.get('accepted') and result['reference_delta_xyz_m'][0]+feedback['correction_xyz_m'][0]<.72*result['requested_x_m']-1e-7:
   reference['rows'].append(dict(episode=ep.name,step=record['step']));break
assert len(reference['rows'])==2
frozen={str(W/n):sha(W/n) for n in ['check_rear_progress_gate_first_interventions.py','rear_recovery_progress_gate_candidate_v2.py','rear_recovery_progress_gate_solver.py','rear_recovery_tracking_solver_v2.py','rear_recovery_progress_gate_stationarity.py','rear_corridor_unload_candidate.py','rear_corridor_latched_stationarity.py']}
def save(status,**kw):
 tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256=sources,frozen_sha256=frozen,physics=False,training_ready=False,**kw),indent=2));tmp.replace(dest)
try:
 save('running')
 for source in reference['rows']:
  ep=next((W/'rear_transport_retry_physical_r1').glob('case_*/'+source['episode']));p=ep/'rear_corridor_recovery.json';rr={r['step']:r for r in json.loads(p.read_text())['rows']};sources[str(p)]=sha(p);t=source['step'];r=rr[t];row=r['parent_row'];c=r['parent_coordinate'];q=np.array(c['upper_q']);previous=np.array(c['task_inputs']['previous']);kw=dict(enabled=True,guard=guard,row=row,coordinate=c,current=q,previous=previous,parent_command=r['parent_command'],recovery_active=True,tracking_feedback=True,previous_recovery_record=rr[t-1],**r['geometry'])
  baseline,detail=parent_solve(**kw);off,offdetail=solve(progress_gate=False,**kw);assert np.array_equal(baseline,off) and detail==offdetail;assert np.array_equal(baseline,r['emitted_command'])
  cmd,result=solve(progress_gate=True,**kw);gate=result['progress_gate'];assert np.array_equal(gate['parent_command'],baseline)
  side=c['active_side'];offset=np.array(row['control_offset_local']);T0=ind.hand.fk(q,side)
  def motion(x):
   T=ind.hand.fk(x,side);return T[:3,3]+T[:3,:3]@offset-T0[:3,3]-T0[:3,:3]@offset
  assert abs(motion(baseline)[2]-gate['nominal_z_ceiling_m'])<2e-9
  item=dict(episode=ep.name,step=t,default_off_identical=True,new_loaded_command=cmd is not None,gate_selection=gate['selection'])
  if cmd is not None:
   delta=motion(cmd);bias=np.array(result['tracking_feedback']['correction_xyz_m']);assert delta[0]+bias[0]>=gate['minimum_predicted_x_m']-1e-7 and delta[2]<=gate['nominal_z_ceiling_m']+1e-7 and abs(delta[1]+bias[1])<=1e-7;assert guard.command(cmd,q,previous)['accepted']
   cert=verify_loaded(ind,row=row,coordinate=c,current=q,previous=previous,command=cmd,kind='loaded_recovery',geometry=r['geometry'],recovery_active=True,tracking_bias_xyz_m=bias,nominal_z_ceiling_m=gate['nominal_z_ceiling_m']);assert cert['passed'];item.update(independent_proof=cert,reference_delta_mm=(delta*1000).tolist())
  else:
   lift,record=solve_lift(guard=guard,row=row,coordinate=c,current=q,previous=previous,parent_command=r['parent_command'],recovery_result=result);item['original_unload_available']=lift is not None
   if lift is not None:
    cert=verify_unload(ind,row=row,coordinate=c,current=q,previous=previous,command=lift,kind='unload',geometry=r['geometry'],recovery_active=True);assert cert['passed'];assert guard.command(lift,q,previous)['accepted'];item['independent_unload_proof']=cert
  for key,value in [('enabled',False),('tracking_feedback',False)]:
   neutral=dict(kw);neutral[key]=value;old_command,old_record=parent_solve(**neutral);new_command,new_record=solve(progress_gate=True,**neutral);assert (old_command is None)==(new_command is None)
   if old_command is not None:assert np.array_equal(old_command,new_command)
   assert old_record==new_record
  try:solve(progress_gate=1,**kw)
  except ValueError:pass
  else:raise AssertionError('integer flag admitted')
  item['disabled_and_no_tracking_unchanged']=True;item['integer_flag_rejected']=True
  rows.append(item);save('running');print(ep.name,t,item,flush=True)
 for p,h in {**sources,**frozen}.items():assert sha(p)==h,p
 save('complete',passed=True,remaining='Causal lifecycle/adapters/full native metadata/negative tests, original audit/source binding and full physical groups required. Not connected to collector.')
except BaseException as e:save('failed',passed=False,error=repr(e));raise
