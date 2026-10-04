"""Diagnostic archived-record composition, not a new physical stream."""
from pathlib import Path
import copy,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;D=W/'front_normal_pressure_consumer_r1';D.mkdir(exist_ok=False);sys.path.insert(0,str(W))
from audit_front_normal_pressure_finalization_v1 import verify
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
a=read(W/'front_normal_prefix_recovery_r3/RESULT.json');assert a['passed']
b=read(W/'front_normal_recovery_checks_r1/RESULT.json');records={r['step']:r['record'] for r in b['recoveries']}
ep=W/'front_effective_height_physical_r1/case_840020/layout_840020_push_box_to_bin';fr={r['step']:r for r in read(ep/'frontal_bypass.json')['rows']};cs={r['step']:r for r in read(ep/'coordination.json')}
rows=[];negative=[]
for fork in a['recovery_forks']:
 t=fork['step'];record=copy.deepcopy(records[t]);record['recovery_transition']=fork['commit'];final=fork['final_pressure_record'];q=cs[t]['joint_transport_clearance']['collector_context']['current'];action=np.asarray(q).astype(np.float32).astype(float)
 kw=dict(row=fr[t],record=record,current=q,executed_command=action,side='right');rows.append(verify(final,**kw))
 for case in ['stale_phase','nonzero_bias','changed_filter','missing_pre_state','wrong_counter','not_committed','wrong_action','nan_filter']:
  f=copy.deepcopy(final);k=copy.deepcopy(kw)
  if case=='stale_phase':f['top_mode']='top_push'
  elif case=='nonzero_bias':f['bias_m']=-.001
  elif case=='changed_filter':f['filtered_n']+=.01
  elif case=='missing_pre_state':del f['before_final_recovery']
  elif case=='wrong_counter':f['final_recovery_transition']['after']['recontacts']+=1;k['record']['recovery_transition']=f['final_recovery_transition']
  elif case=='not_committed':k['record']['recovery_committed']=False
  elif case=='wrong_action':k['executed_command'][0]+=.001
  else:f['filtered_n']=float('nan')
  try:verify(f,**k)
  except (AssertionError,KeyError):negative.append(dict(step=t,case=case,rejected=True))
  else:raise AssertionError(('tamper accepted',t,case))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,rows=rows,negative=negative,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'audit_front_normal_pressure_finalization_v1.py',W/'front_normal_prefix_recovery_r3/RESULT.json',W/'front_normal_recovery_checks_r1/RESULT.json',ep/'frontal_bypass.json',ep/'coordination.json']},full_pressure_consumer_integrated=False,physics_started=False,training_ready=False)
(D/'RESULT.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(passed=True,positive=len(rows),rejected_tampers=len(negative))))
