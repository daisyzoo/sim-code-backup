"""Descriptive whole-run contact response for all original8push2wait conditions.
No new acceptance threshold, admission, or causal claim. Requires completed actual
reviews and bound original arrays; never fabricates counterfactual trajectories.
"""
from pathlib import Path
import argparse,json,hashlib,datetime,collections
import numpy as np
from scipy.spatial.transform import Rotation
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(run):
 run=Path(run).resolve();dest=run/'PAIRED_CONTACT_RESPONSE_V1.json';assert not dest.exists();sources={}
 def read(p):
  sources[str(p)]=sha(p);return json.loads(p.read_text())
 summary=read(run/'NUMERIC_VISUAL_SUMMARY.json');assert summary['actual_reviews']==10 and len(summary['rows'])==10 and not summary['training_ready']
 for p,h in summary['source_sha256'].items():assert sha(p)==h,p
 sources.update(summary['source_sha256']);results=[]
 for row in summary['rows']:
  ep=next(run.glob('case_*/'+row['episode']));ready=read(ep/'READY_FOR_AUDIT.json');quality=read(ep/'quality.json');review=read(ep/'ACTUAL_REVIEW_BINDING.json');assert review['actual_visual_review'].startswith('completed_actual_view')
  assert ready['executed_frames']==ready['requested_frames']==quality['frames'];n=quality['frames']
  for p,h in ready['source_sha256'].items():assert sha(p)==h,p
  if row['wait']:
   results.append(dict(episode=ep.name,wait=True,frames=n,original_task_and_pose_passed=row['original_task_and_pose_passed'],metrics=row['metrics'],training_ready=False));continue
  assert n==1200
  target='box' if ep.name.endswith('push_box_to_bin') else 'mailer';side='right' if target=='box' else 'left';body='parcel_box' if target=='box' else 'mailer'
  meta=read(ep/'SUBSTEP_CONTACT_RECORDING.json');m=meta['metadata'];assert meta['recording_sha256']==sha(ep/'substep_contacts.npz') and meta['action_intervals']==n
  assert m['expected_substeps']==24 and m['control_decimation']*m['substeps_per_physics_tick']==24
  with np.load(ep/'substep_contacts.npz') as z:a={k:z[k].copy() for k in ['shape_ids','contact_offsets','action_step','substep_tick','force_torque_world']}
  labels=m['shape_labels'];object_ids=np.array([i for i,s in enumerate(labels) if '/'+body+'/' in s]);wrist_ids=np.array([i for i,s in enumerate(labels) if side+'_wrist_roll' in s]);assert len(object_ids)>0 and len(wrist_ids)>0
  pairs=a['shape_ids'];selected=np.isin(pairs,object_ids).any(1)&np.isin(pairs,wrist_ids).any(1);ids=np.repeat(np.arange(len(a['action_step'])),np.diff(a['contact_offsets']));assert len(ids)==len(pairs)==len(a['force_torque_world'])
  loads=np.bincount(ids[selected],weights=np.abs(a['force_torque_world'][selected,2].astype(float)),minlength=len(a['action_step']));interval=m['expected_substeps']+m['expected_manager_steps'];assert len(a['action_step'])==n*interval
  peak=[]
  for step in range(n):
   start=step*interval;ticks=a['substep_tick'][start:start+interval];assert np.all(a['action_step'][start:start+interval]==step)
   ix=[start+int(np.flatnonzero(ticks==k)[0]) for k in range(1,25)];peak.append(float(np.max(loads[ix])))
  fr=read(ep/'frontal_bypass.json')['rows'];by_step={r['step']:r for r in fr};assert len(fr)==len(by_step) and set(by_step).issubset(range(n))
  with np.load(ep/'parcel_orientation.npz') as z:yaw=np.unwrap(Rotation.from_quat(z[target]).as_euler('xyz')[:,2])
  assert len(yaw)==n
  yaw_deg=np.degrees(yaw-yaw[0]);priority={r['step']:r for r in read(ep/'front_loaded_z_priority.json')['rows']};assert len(priority)==n
  phase_peaks=collections.defaultdict(list);events=[];bouts=[];current=None
  for t in range(n):
   r=by_step.get(t,{});mode=r.get('mode','no_frontal_record');phase_peaks[mode].append(peak[t]);reason=r.get('route_stop_reason')
   if reason:events.append(dict(step=t,reason=reason))
   if mode=='top_push':
    if current is None:current=dict(start=t,end=t,frames=0)
    current['end']=t;current['frames']+=1
   elif current is not None:current['exit_reason']=r.get('last_recontact_reason');bouts.append(current);current=None
  if current is not None:current['exit_reason']='episode_end';bouts.append(current)
  summarize=lambda v:dict(actions=len(v),maximum_n=float(np.max(v)),median_n=float(np.median(v)),p95_n=float(np.percentile(v,95)),actions_above_existing10n_peak_bias_guard=sum(x>10 for x in v))
  out=dict(episode=ep.name,group=row['group'],wait=False,frames=n,target=target,active_side=side,original_task_and_pose_passed=row['original_task_and_pose_passed'],metrics=row['metrics'],active_wrist_assembly_target_vertical_abs_peak=summarize(peak),phase_peaks={k:summarize(v) for k,v in phase_peaks.items()},initial_relative_yaw_max_abs_deg=float(np.max(np.abs(yaw_deg))),initial_relative_yaw_final_deg=float(yaw_deg[-1]),max_one_observation_yaw_change_deg=float(np.max(np.abs(np.diff(yaw_deg)))),first_route_stop=None if not events else events[0],route_stop_frames=len(events),tilt_exit_count=sum(b['exit_reason']=='incipient_tilt_independent' for b in bouts),lost_contact_exit_count=sum(b['exit_reason']=='lost_contact' for b in bouts),priority_applied_frames=sum(bool(r['applied']) for r in priority.values()),selected_shape_labels=dict(target=[labels[i] for i in object_ids],active_wrist_assembly=[labels[i] for i in wrist_ids]),per_action=[dict(step=t,mode=by_step.get(t,{}).get('mode'),peak_vertical_abs_n=peak[t],target_yaw_relative_deg=float(yaw_deg[t]),priority_applied=bool(priority[t]['applied'])) for t in range(n)],training_ready=False)
  results.append(out)
  for name in ['substep_contacts.npz','parcel_orientation.npz']:sources[str(ep/name)]=sha(ep/name)
  print(json.dumps({k:out[k] for k in ['episode','original_task_and_pose_passed','active_wrist_assembly_target_vertical_abs_peak','initial_relative_yaw_max_abs_deg','tilt_exit_count','lost_contact_exit_count']}),flush=True)
 assert len(results)==10 and sum(not x['wait'] for x in results)==8
 sources[str(Path(__file__).resolve())]=sha(__file__)
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,conditions=10,push_conditions=8,wait_conditions=2,rows=results,source_sha256=sources,limitations=['Absolute vertical contact forces summed across target/active wrist assembly pairs are not signed net object forces; selected labels include any forearm shapes attached to that assembly.','Peak uses one occurrence of each completed solver tick1..24 per action; tick0 and repeated manager boundaries excluded.','Force and observed state are not assumed synchronous; yaw is observation change, not causal torque response.','10N is the existing peak-bias guard threshold, not a new task-quality gate.','Descriptive comparison across recorded trajectories cannot isolate a controller change causally without physical matched repeats.'],training_ready=False)
 with dest.open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(dict(report=str(dest),conditions=10,training_ready=False)),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run');main(p.parse_args().run)
