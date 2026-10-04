"""Independent inactive-arm preparation arithmetic and geometry.
No candidate/runtime/optimizer imports. Preparation verification is not an
optimizer optimality certificate or a complete physical-episode admission.
"""
import copy
import numpy as np
from scipy.spatial.transform import Rotation
from audit_front_initial_center_planning_v2 import SelectionAudit
from audit_front_recontact_center_events import RecoveryEventAudit
from audit_unloaded_wrist_prior_live import near

class InactivePreparationAudit(SelectionAudit):
 def verify_preparation(self,event,*,step,current,previous_q,previous_command,final_command,scene,decay,counter,preparation_ticks,total_ticks):
  assert event['kind']=='command' and event['phase']=='inactive_clearance_preparation'
  assert type(counter) is int and counter>0 and type(step) is int and step>0
  assert type(preparation_ticks) is int and type(total_ticks) is int and 1<=preparation_ticks==total_ticks<=240
  assert event['preparation_ticks']==preparation_ticks and event['ticks']==total_ticks and event['measured_ready_count']==0
  assert not event.get('planning') and not any(k.startswith('captured_') for k in event)
  c=event['context'];p=event['proposal']
  assert c['step']==step and c['recontacts']==counter and c['scene']==scene and c['selected'] is True and c['guard_stop'] is False
  assert scene['side']=='left' and c['parent_mode'] in ('top_cross','top_descend') and c['observed_load_n']==0. and 0<=c['filtered_load_n']<=.05
  q,qp,prev,u,a=[np.asarray(x,float) for x in [current,previous_q,previous_command,final_command,decay]]
  for x in [q,qp,prev,u,a]:assert x.shape==(11,) and np.isfinite(x).all()
  assert np.all(a>=0) and np.all(a<=.95)
  for k,v in [('current',q),('previous_q',qp),('previous_command',prev),('decay',a)]:near(c[k],v,1e-7);near(p[k],v,1e-7)
  near(event['command'],u,0);near(p['command'],u,0)
  assert p['applied'] is True and p['reason']=='unissued_verified_local_proposal' and p['optimizer_status']==0 and type(p['iterations']) is int and 0<p['iterations']<=120
  measured,detail=self.geometry(q,scene);assert measured['accepted'] and measured['inactive_lowest_z_m']<.841;self.compare_geometry(p['measured'],measured)
  near(c['observed_hand_pose'],detail['pose'],1e-4);near(c['observed_inactive_hand_pose'],detail['inactive'],1e-4)
  bias=q-prev-a*(qp-prev);hold=(q-a*q-bias)/(1-a);pred=(1-a)*u+a*q+bias
  near(p['causal_bias'],bias,1e-12);near(p['predicted_q'],pred,1e-12);near(u[:6],hold[:6].astype(np.float32),0)
  assert np.max(abs(pred[:6]-q[:6]))<1e-7;near(p['predicted_active_hold_error'],np.max(abs(pred[:6]-q[:6])),1e-12)
  assert np.all(u>=self.lo-2e-7) and np.all(u<=self.hi+2e-7) and np.all(abs(u-q)<=self.limits+2e-7) and np.max(abs(u-prev))<=.0550002
  check=p['original_command_check'];assert check['accepted'] is True and check['first'] is False
  assert check['checks']==dict(joint_bounds=True,measured_step=True,previous_slew=True,nominal_margin=True,first_zero=True)
  near(check['command'],u,0);near(check['current'],q,1e-7);near(check['previous'],prev,0);near(check['gaps_m'],self.elbows.gap(u),2e-9)
  samples=0
  for name,x in [('nominal',u),('predicted',pred)]:
   geometry,_=self.geometry(x,scene);assert geometry['accepted'] and geometry['inactive_lowest_z_m']>=.8415-2e-7;self.compare_geometry(p[name],geometry)
   count=max(1,int(np.ceil(np.max(abs(x-q)/(self.limits*.25)))));expected=[q+(x-q)*j/count for j in range(count+1)];stored=p['sampled_paths'][name]
   assert stored['accepted'] is True and len(stored['states'])==len(stored['checks'])==len(expected)
   for z,zz,check in zip(expected,stored['states'],stored['checks']):
    near(zz,z,1e-12);geo,_=self.geometry(z,scene);assert geo['accepted'];self.compare_geometry(check,geo);samples+=1
  for native,original in [('candidate_command','command'),('command_check','original_command_check'),('nominal_scene','nominal'),('predicted_scene','predicted')]:
   if native in p:assert p[native]==p[original]
  return dict(passed=True,step=step,independent_sampled_geometry=samples,shared_ticks=total_ticks)

 def verify_committed_sequence(self,events,repo,stage):
  # This entry verifies a complete committed segment supplied by the caller.
  # It cannot prove missing episode frames, raw provenance or prior counters.
  assert events and events[0].get('phase')=='inactive_clearance_preparation'
  old=RecoveryEventAudit(repo,stage);prep_count=0;tracking=False;start_scene=events[0]['context']['scene'];counter=events[0]['context']['recontacts'];last=None;rows=[]
  for i,e in enumerate(events):
   c=e['context'];sc=c['scene'];assert c['recontacts']==counter and e['ticks']==i+1<=240
   if last:
    assert c['step']==last['context']['step']+1;near(c['previous_q'],last['context']['current'],1e-7);near(c['previous_command'],last['command'],0)
   for actor in ['target','other']:
    assert np.linalg.norm(np.array(sc[actor+'_xyz'])-start_scene[actor+'_xyz'])<=.002
    assert (Rotation.from_quat(sc[actor+'_quat'])*Rotation.from_quat(start_scene[actor+'_quat']).inv()).magnitude()<=.02
   assert sc['core_size']==start_scene['core_size'] and sc['other_size']==start_scene['other_size']
   args={k:c[k] for k in ['step','current','previous_q','previous_command','scene','decay']};args['final_command']=e['command']
   if e.get('phase')=='inactive_clearance_preparation':
    assert not tracking;prep_count+=1;rows.append(self.verify_preparation(e,**args,counter=counter,preparation_ticks=prep_count,total_ticks=i+1))
   else:
    assert e['kind'] in ('command','handover')
    if not tracking:
     geo,_=self.geometry(c['current'],sc);assert geo['accepted'] and geo['inactive_lowest_z_m']>=.841
     assert e['measured_clearance_transition'] is True and e['preparation_ticks']==prep_count
     self.verify_selection(e['planning'],current=c['current'],previous_q=c['previous_q'],previous_command=c['previous_command'],decay=c['decay'],scene=sc,step=c['step']);tracking=True
    # Adapt only the count view for the unchanged recovery-only audit;
    # the true combined count was independently enforced above, with max240.
    view=copy.deepcopy(e);view['ticks']-=prep_count
    result=old.verify(view,**args,selected=c['selected'],parent_mode=c['parent_mode'],recontacts=counter,guard_stop=c['guard_stop'],observed_load_n=c['observed_load_n'],filtered_load_n=c['filtered_load_n'])
    for key in ['nominal_scene','predicted_scene']:assert e['proposal'][key]['inactive_lowest_z_m']>=.8405
    rows.append(result)
    if e['kind']=='handover':assert i==len(events)-1 and not old.active
   last=e
  assert tracking and events[-1]['kind']=='handover' and not old.active
  return dict(passed=True,preparation_ticks=prep_count,combined_ticks=len(events),rows=rows,scope='Complete supplied committed segment only; caller must bind the full real episode and raw observations.',training_ready=False)
