"""Complete saved-episode checks and phase statistics; never substitutes actual image review."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_closed_peak_trial_source_contract import verify_closed_peak_trial_source
from verify_closed_peak_trial_pressure_setting import verify
from simfoundry.data.search_reward import terminal_search_scores
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ep=Path(sys.argv[1]).resolve();quality=json.loads((ep/'quality.json').read_text());wait='wait_no_package' in ep.name;n=quality['frames'];assert n== (70 if wait else 1200)
out=dict(episode=ep.name,frames=n,quality_passed=quality['passed'],source_binding=verify_closed_peak_trial_source(ep),pressure_binding=verify(ep,5.),training_ready=False,actual_visual_review='pending')
protocol_path=ep.parent.parent/'PROTOCOL.json';protocol=json.loads(protocol_path.read_text())
for path,digest in protocol['frozen_files_sha256'].items():assert sha(path)==digest,path
out['protocol_sha256']=sha(protocol_path)
record=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text());out['substep_records']=record['sample_records'];out['substep_intervals']=record['action_intervals'];assert out['substep_intervals']==n
out['substep_independent_audit_present']=(ep/'CLOSED_PEAK_TRIAL_CONTACT_AUDIT.json').exists()
with np.load(ep/'raw.npz') as raw,np.load(ep/'trace.npz') as tr:
 meta=json.loads(str(raw['collect_meta']));assert raw['q'].shape==raw['action'].shape==(n,23)
 out.update(initial11_q_max_abs=float(abs(raw['q'][0,12:23]).max()),initial11_action_max_abs=float(abs(raw['action'][0,12:23]).max()),assist_frames=meta['assist_frames']);assert out['initial11_q_max_abs']==out['initial11_action_max_abs']==out['assist_frames']==0
 if wait:
  out.update(all11_action_max_abs=float(abs(raw['action'][:,12:23]).max()),waist_max_abs_rad=float(abs(raw['q'][:,12]).max()));assert out['all11_action_max_abs']==0
 else:
  key='box' if 'push_box' in ep.name else 'mailer';other='mailer' if key=='box' else 'box';direction=-1 if key=='box' else 1;sy=direction*tr[key][:,1].astype(float)
  with np.load(ep/'parcel_orientation.npz') as ori:_,pose=terminal_search_scores([quality],[0 if key=='box' else 1],{k:tr[k][:,None] for k in tr.files},{k:ori[k][:,None] for k in ori.files})
  out.update(original_task_and_pose_passed=bool(quality['passed'] and pose[0]['search_success']),pose=pose[0],progress_mm=quality['metrics']['target_final_progress_m']*1000,final10_signed_y_min_mm=float(min(sy[-10:])*1000),final10_signed_y_mean_mm=float(np.mean(sy[-10:])*1000),non_target_max_xy_mm=float(np.max(np.linalg.norm(tr[other][:,:2]-tr[other][0,:2],axis=1))*1000))
  frontal=json.loads((ep/'frontal_bypass.json').read_text());fs=frontal['rows'];bouts=[];current=None
  for i,f in enumerate(fs):
   if f['mode']=='top_push':
    if current is None:current=dict(start=f['step'],end=f['step'],frames=0)
    current['end']=f['step'];current['frames']+=1
   elif current is not None:
    current['exit_reason']=f.get('last_recontact_reason');bouts.append(current);current=None
  if current is not None:current['exit_reason']='episode_end';bouts.append(current)
  out.update(declared_drag_step_m=frontal['plan']['top_recontact']['drag_step_m'],phase_counts=dict(collections.Counter(f['mode'] for f in fs)),bouts=bouts,tilt_exit_count=sum(x['exit_reason']=='incipient_tilt_independent' for x in bouts),lost_contact_exit_count=sum(x['exit_reason']=='lost_contact' for x in bouts),maximum_observed_tilt_rad=max(f.get('observed_parcel_tilt_rad',0) for f in fs))
  out['comparison_scope']='Fresh trial numeric review; no automatic historical comparison by layout ID.'
files=['raw.npz','trace.npz','quality.json']+([] if wait else ['parcel_orientation.npz','frontal_bypass.json'])
out['source_sha256']={name:sha(ep/name) for name in files};out['inspector_sha256']=sha(__file__);(ep/'CLOSED_PEAK_TRIAL_NUMERIC_REVIEW.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['source_binding','pressure_binding','source_sha256','pose','bouts']},indent=2))
