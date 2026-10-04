"""Recorded context -> default-off adapter -> independent certificates -> old guard.
No commands are sent to the simulator; full collector/source/audit wiring pending.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
from unittest.mock import patch
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_inactive_clearance';D=W/'inactive_transport_clearance_draft_r1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from inactive_transport_runtime import InactiveTransportRuntime
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();b=read(D/'TRANSPORT_PROBE.json');bound=read(D/'CONSTRAINT_CERTIFICATE_CHECK.json');assert bound['passed'];guard=ClearanceGuard(ROOT,S);runtime=InactiveTransportRuntime(guard,ROOT,S,enabled=True);rows=[];negative=[]
for p,h in bound['source_sha256'].items():assert sha(p)==h,p
for rr in b['records']:
 r=rr.get('record',{})
 if not r.get('applied'):continue
 ep=W/rr['run']/'case_840023/layout_840023_nudge_mailer_to_bin';t=rr['step'];c=next(x for x in read(ep/'coordination.json') if x['step']==t);f=next(x for x in read(ep/'frontal_bypass.json')['rows'] if x['step']==t);z=r['scene'];scene=RecontactScene(guard,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size']);kw=dict(step=t,selected=True,side='left',row=f,coordinate=c,scene=scene,current=r['current'],previous_q=r['previous_q'],previous_command=r['previous_command'],parent_command=r['parent_command'],decay=r['decay'])
 command,meta=runtime.refine(**kw);assert meta['applied'],meta['reason'];np.testing.assert_array_equal(command,r['command']);assert guard.command(command,np.array(r['current']),np.array(r['previous_command']))['accepted'];rows.append(dict(run=rr['run'],step=t,record=meta))
 if len(rows)==1:
  for label in ['disabled','unselected','right_task','initial_zero','joint_path','terminal_hold','route_stop','guard_saturated','missing_task','missing_normal','wrong_mode','failed_constraint_certificate','failed_path_certificate']:
   obj=InactiveTransportRuntime(guard,ROOT,S,enabled=label!='disabled');a=copy.deepcopy({k:v for k,v in kw.items() if k!='scene'});a['scene']=scene
   if label=='unselected':a['selected']=False
   elif label=='right_task':a['side']='right'
   elif label=='initial_zero':a['step']=0
   elif label=='joint_path':a['coordinate']['front_recontact_center_override']={'kind':'command'}
   elif label=='terminal_hold':a['coordinate']['terminal_joint_hold']={'held':True}
   elif label=='route_stop':a['row']['route_stop_reason']='test_stop'
   elif label=='guard_saturated':a['row']['hand_guard_saturated']=True
   elif label=='missing_task':a['coordinate']['task_inputs']=None
   elif label=='missing_normal':a['coordinate']['contact_normal_tracking']=None
   elif label=='wrong_mode':a['row']['mode']='wait'
   if label=='failed_constraint_certificate':
    with patch('inactive_transport_runtime.verify',return_value=dict(passed=False)):out,rec=obj.refine(**a)
   elif label=='failed_path_certificate':
    with patch('inactive_transport_runtime.certify',return_value=dict(passed=False)):out,rec=obj.refine(**a)
   else:out,rec=obj.refine(**a)
   assert not rec['applied'];np.testing.assert_array_equal(out,a['parent_command']);negative.append(dict(case=label,reason=rec['reason'],parent_exactly_retained=True))
  for label in ['wrong_step','wrong_previous','wrong_current','wrong_scene_side']:
   a=copy.deepcopy({k:v for k,v in kw.items() if k!='scene'});a['scene']=scene
   if label=='wrong_step':a['coordinate']['step']+=1
   elif label=='wrong_previous':a['previous_command'][8]+=.001
   elif label=='wrong_current':a['current'][8]+=.001
   else:a['scene']=RecontactScene(guard,'right',z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size'])
   try:runtime.refine(**a)
   except ValueError:negative.append(dict(case=label,rejected=True))
   else:raise AssertionError('Invalid runtime context accepted '+label)
assert len(rows)==6 and len(negative)==17
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=rows,negative_cases=negative,source_sha256={str(p):sha(p) for p in [Path(__file__),D/'TRANSPORT_PROBE.json',D/'CONSTRAINT_CERTIFICATE_CHECK.json',*D.glob('*.py')]},collector_wired=False,physics_started=False,training_ready=False)
with (D/'RUNTIME_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,contexts=len(rows),negative=len(negative))))
