"""Observed press-to-push history across all eight matched pushes.
Counterfactual thresholds are classified on OLD observations only, not a rollout
or evidence that waiting raises force. Retain successful-task controls and failures.
"""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;R=W/'front_effective_height_physical_r1';D=W/'front_press_entry_census_r1';D.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
sources={str(Path(__file__)):sha(__file__),str(R/'PROTOCOL.json'):sha(R/'PROTOCOL.json')};results=[]
def stats(xs):
 a=np.asarray(xs,float);assert np.isfinite(a).all()
 return None if not len(a) else dict(n=len(a),min=float(a.min()),median=float(np.median(a)),max=float(a.max()))
for case in read(R/'PROTOCOL.json')['plan']['commands']:
 if case['wait']:continue
 for task in case['tasks']:
  ep=R/f"case_{case['layout_id']}"/f"layout_{case['layout_id']}_{task}";f=read(ep/'frontal_bypass.json');rows=f['rows'];quality=read(ep/'quality.json');mark=read(ep/'READY_FOR_AUDIT.json')
  for name,h in mark['source_sha256'].items():assert sha(name)==h,name
  side='left' if task=='nudge_mailer_to_bin' else 'right';actor='mailer' if side=='left' else 'parcel_box';target='mailer' if side=='left' else 'box'
  packets={x['after_action_step']:x for x in read(ep/'solved_contact_forces.json')['rows']}
  with np.load(ep/'trace.npz',allow_pickle=False) as z:xyz=z[target].copy()
  assert len(xyz)==quality['frames']==1200 and len(rows)==1199
  observed=[];by_step={}
  for row in rows:
   if row['mode'] not in ('top_press','top_push'):continue
   t=row['step'];p=packets[t-1];assert p['solver_force_buffer_unchanged'];assert np.max(abs(np.array(p['post_action_pose'][target])-xyz[t]))<2e-6
   load=sum(abs(float(c['force_world_N'][2])) for c in p['parcel_contacts'] if any(side+'_wrist_roll' in label for label in c['shapes']) and any('/'+actor+'/' in label for label in c['shapes']))
   logged=row['contact_load'];assert abs(load-logged['observed_vertical_load_n'])<1e-5,(ep.name,t,load,logged['observed_vertical_load_n'])
   measured=np.asarray(row.get('observed_physical_support_xyz',row['observed_support_xyz']),float);desired=np.asarray(row['target_xyz'],float)
   rec=dict(step=t,mode=row['mode'],lasttick_vertical_n=load,filtered_n=logged['filtered_vertical_load_n'],stored_bias_mm=1000*logged['stored_z_bias_m'],support_z_error_mm=1000*float(desired[2]-measured[2]),peak_bias_guard_held=logged.get('peak_bias_guard',{}).get('held_negative_increment',False));observed.append(rec);by_step[t]=rec
  bouts=[];i=0
  while i<len(rows):
   if rows[i]['mode']!='top_push':i+=1;continue
   start=i
   while i+1<len(rows) and rows[i+1]['mode']=='top_push':i+=1
   end=i;s=rows[start]['step'];e=rows[end]['step'];entry=by_step[s];first=[by_step[t] for t in range(s,min(e+1,s+20))];prior=[];j=start-1
   while j>=0 and rows[j]['mode']=='top_press':prior.append(by_step[rows[j]['step']]);j-=1
   prior.reverse();nxt=rows[end+1] if end+1<len(rows) else None
   if nxt is None:reason='episode_end'
   elif nxt['mode']=='top_release':reason='release'
   elif nxt.get('recontacts',0)>rows[end].get('recontacts',0):reason=nxt.get('last_recontact_reason')
   else:reason=nxt.get('route_stop_reason') or 'other_mode_transition'
   counts={str(th):dict(entry_filtered_meets=entry['filtered_n']>=th,prior_press_filtered_meets=sum(r['filtered_n']>=th for r in prior),first20_push_filtered_meets=sum(r['filtered_n']>=th for r in first)) for th in [.3,1.,2.,3.,4.,5.]}
   bouts.append(dict(start=s,end=e,frames=e-s+1,exit_reason=reason,preceding_press_frames=len(prior),entry=entry,prior_press_load_n=stats([r['lasttick_vertical_n'] for r in prior]),first20_push_load_n=stats([r['lasttick_vertical_n'] for r in first]),first20_push_bias_mm=stats([r['stored_bias_mm'] for r in first]),first20_target_delta_mm=(1000*(xyz[min(e,s+19)]-xyz[s])).tolist(),old_history_thresholds=counts))
   i+=1
  result=dict(episode=ep.name,quality_passed=quality['passed'],progress_mm=1000*quality['metrics']['target_final_progress_m'],top_press_frames=sum(r['mode']=='top_press' for r in observed),top_push_frames=sum(r['mode']=='top_push' for r in observed),bouts=bouts,observations=observed);results.append(result)
  for name in ['READY_FOR_AUDIT.json','frontal_bypass.json','solved_contact_forces.json','trace.npz','quality.json']:sources[str(ep/name)]=sha(ep/name)
assert len(results)==8
summary=[]
for r in results:
 bs=r['bouts'];summary.append(dict(episode=r['episode'],quality_passed=r['quality_passed'],push_bouts=len(bs),entry_filtered_n=stats([b['entry']['filtered_n'] for b in bs]),entries_below3N=sum(b['entry']['filtered_n']<3 for b in bs),prior_press_never3N=sum(not b['old_history_thresholds']['3.0']['prior_press_filtered_meets'] for b in bs),lost_contact_bouts=sum(b['exit_reason']=='lost_contact' for b in bs),first20_peak_bias_holds=sum(o['peak_bias_guard_held'] for o in r['observations'] if any(b['start']<=o['step']<min(b['end']+1,b['start']+20) for b in bs))))
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,conditions=8,summary=summary,episodes=results,source_sha256=sources,interpretation='Use the full successful and failed control census before proposing load-first. A threshold mismatch is not proof of a future deadlock or of improvement: command changes alter future observations.',new_physics=False,training_ready=False)
with (D/'RESULT.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(summary,indent=2))
