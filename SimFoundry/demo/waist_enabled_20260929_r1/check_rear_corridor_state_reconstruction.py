"""Unchanged-history equivalence and explicit commit-boundary reconstruction.
Committed-prefix fixtures are synthetic file/control inputs, not physical replay.
The stale-next-waypoint test verifies that old post-override history is rejected,
not that a counterfactual object/robot trajectory has been produced.
"""
from pathlib import Path
import sys,json,copy,hashlib,datetime,os
import numpy as np
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W.parents[1])]
from audit_closed_peak_trial_rear_xy import reconstruct as old_xy
from rear_corridor_xy_reconstruction import reconstruct as new_xy
from audit_closed_peak_trial_pose_height import verify_rows as old_height
from rear_corridor_height_reconstruction import verify_rows as new_height
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();dest=W/'REAR_CORRIDOR_STATE_RECONSTRUCTION_CHECK.json';assert not dest.exists();full=json.loads((W/'REAR_CORRIDOR_JOINT_RECOVERY_FULL_CHECK.json').read_text());fixtures=json.loads((W/'REAR_CORRIDOR_NATIVE_FIXTURE_CHECK.json').read_text());assert fixtures['passed'];rows=[];branches=[];negative=[];sources={};cache={}
def save(status,**extra):
 temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,unchanged_histories=rows,commit_boundaries=branches,negative_checks=negative,source_sha256=sources,training_ready=False,**extra),indent=2));temp.replace(dest)
def read_ep(name):
 if name in cache:return cache[name]
 ep=W/name;fr=json.loads((ep/'frontal_bypass.json').read_text());ex={x['step']:x for x in json.loads((ep/'expert_control.json').read_text())};region=json.loads((ep/'region_approach.json').read_text())['rows'];handover=next((x['step'] for x in region if x['solver'] and x['solver'].get('handover')),None);key='box' if 'push_box' in name else 'mailer';events={x['step']:{k:v for k,v in x.items() if k!='step'} for x in json.loads((ep/'recontact_pose.json').read_text())['rows'] if x['kind'] in ['command','handover']};packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
 with np.load(ep/'trace.npz') as z:xyz=z[key].copy()
 with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].copy()
 for n in ['frontal_bypass.json','expert_control.json','region_approach.json','recontact_pose.json','solved_contact_forces.json','trace.npz','parcel_orientation.npz']:sources[str(ep/n)]=sha(ep/n)
 out=dict(fr=fr,ex=ex,handover=handover,key=key,events=events,packets=packets,xyz=xyz,quat=quat);cache[name]=out;return out
try:
 save('running')
 for item in full['episodes']:
  d=read_ep(item['episode']);args=[d['fr']['rows'],d['fr']['plan'],d['xyz'],d['quat'],d['packets'],d['key'],d['handover']];a=old_xy(*args);b=new_xy(*args);assert a==b
  ha=old_height(d['fr']['rows'],d['ex'],d['fr']['plan'],True,d['events']);hb=new_height(d['fr']['rows'],d['ex'],d['fr']['plan'],True,d['events']);assert ha==hb
  rows.append(dict(episode=item['episode'],frames=len(d['fr']['rows']),xy_exact_equal=True,xy_passed=a['passed'],height_exact_equal=True,original_xy_errors=a['errors']));save('running');print('equivalent',item['episode'],flush=True)
 for item in fixtures['cases']:
  if item['kind']=='wait':continue
  d=read_ep(item['source_episode']);t=item['source_step'];fp=Path(item['fixture']);rr=json.loads((fp/'rear_corridor_recovery.json').read_text());record=next(r for r in rr['rows'] if r['step']==t);final=next(r for r in json.loads((fp/'frontal_bypass.json').read_text())['rows'] if r['step']==t);prefix=copy.deepcopy([r for r in d['fr']['rows'] if r['step']<=t]);assert prefix[-1]==record['parent_row'];parent=copy.deepcopy(prefix);prefix[-1]=final;ex=copy.deepcopy(d['ex']);ex[t].update(mode=final['mode'],target_xyz=final['target_xyz']);mapping={t:record}
  args=[d['fr']['plan'],d['xyz'],d['quat'],d['packets'],d['key'],d['handover']];orig=old_xy(parent,*args);new=new_xy(prefix,*args,recovery_records=mapping);assert orig==new and new['passed']
  height=new_height(prefix,ex,d['fr']['plan'],True,d['events'],recovery_records=mapping)
  # The following recorded original waypoint is deliberately stale after a new
  # reference commit. New reconstruction must not silently accept it.
  stale=copy.deepcopy(prefix)+[copy.deepcopy(next(r for r in d['fr']['rows'] if r['step']==t+1))]
  rejected=False
  try:bad=new_xy(stale,*args,recovery_records=mapping);rejected=not bad['passed']
  except (AssertionError,ValueError):rejected=True
  assert rejected;negative.append(item['kind']+'_'+item['key']+'_stale_next_reference')
  if item['kind']=='unload':
   tip=np.asarray(record['parent_row']['observed_support_xyz']);nextrow=copy.deepcopy(stale[-1]);nextrow.update(mode='top_lift',recontacts=final['recontacts'],last_recontact_reason=final['last_recontact_reason'],travel_height_m=.86,target_xyz=np.r_[tip[:2],max(.86,tip[2])].tolist());nextrow['contact_load'].update(applied_z_bias_m=0.,stored_z_bias_m=0.);ex[t+1].update(mode='top_lift',target_xyz=nextrow['target_xyz']);liftheight=new_height(prefix+[nextrow],ex,d['fr']['plan'],True,d['events'],recovery_records=mapping);assert liftheight['recontact_events'][-1]['step']==t
   corrupted=copy.deepcopy(nextrow);corrupted['recontacts']+=1
   try:new_height(prefix+[corrupted],ex,d['fr']['plan'],True,d['events'],recovery_records=mapping)
   except AssertionError:negative.append('unload_duplicate_counter_rejected')
   else:raise AssertionError('Duplicated recovery count accepted')
  branches.append(dict(episode=item['source_episode'],step=t,kind=item['kind'],key=item['key'],parent_xy_prefix_preserved=True,height_checked=True,synthetic=True,physics_verified=False));save('running')
 for p in [Path(__file__),W/'REAR_CORRIDOR_NATIVE_FIXTURE_CHECK.json',W/'REAR_CORRIDOR_JOINT_RECOVERY_FULL_CHECK.json',W/'audit_closed_peak_trial_rear_xy.py',W/'rear_corridor_xy_reconstruction.py',W/'audit_closed_peak_trial_pose_height.py',W/'rear_corridor_height_reconstruction.py']:sources[str(p)]=sha(p)
 save('complete',passed=True)
except BaseException as e:save('check_failed',error=repr(e));raise
