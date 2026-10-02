"""Audit and render one complete fresh episode; never grant training approval."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
from simfoundry.data.schema import load_episode
from closed_peak_trial_data_audit import audit_waist_pilot_episode
from simfoundry.data.query_phases import episode_query_phases
p=Path(sys.argv[1]);quality=json.loads((p/'quality.json').read_text());raw=p/'raw.npz';episode=load_episode(raw);provenance=json.loads((p.parent/'provenance.json').read_text());sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
assert len(episode.q)==quality['frames']
try:report=audit_waist_pilot_episode(raw,episode,provenance);audit=dict(passed=True,report=report)
except ValueError as e:audit=dict(passed=False,error=str(e))
audit.update(raw_sha256=sha(raw),provenance_sha256=sha(p.parent/'provenance.json'),contract_sha256=sha(p.parent/'waist_pilot_contract.json'),first_upper_state_max_abs_rad=float(np.max(abs(episode.q[0,12:]))),first_upper_action_max_abs_rad=float(np.max(abs(episode.action[0,12:]))),assist_frames=episode.collect_meta['assist_frames'],scope='Actual fresh single-episode source and original numeric/pose audit. Full swap+wait coverage, actual image review and global split/converter admission still separate.',training_ready=False)
(p/'FRESH_SOURCE_AUDIT.json').write_text(json.dumps(audit,indent=2))
try:phase=episode_query_phases(episode.task_id,episode.q,episode.action,json.loads((p/'expert_control.json').read_text()))
except ValueError as e:phase=dict(error=str(e),scope='Phase labels unavailable; never admit a failed trajectory by cropping.')
phase.update(raw_sha256=sha(raw),training_ready=False);(p/'EARLY_QUERY_PHASES.json').write_text(json.dumps(phase,indent=2))
# Score pose independently even when the strict source/data gate rejects a task.
original_pose=audit.get('report',{}).get('pose')
if episode.task_id!='wait_no_package':
 from simfoundry.data.search_reward import terminal_search_scores
 with np.load(p/'trace.npz') as tr,np.load(p/'parcel_orientation.npz') as ori:
  _,poses=terminal_search_scores([quality],[0 if episode.task_id=='push_box_to_bin' else 1],{k:tr[k][:,None] for k in tr.files},{k:ori[k][:,None] for k in ori.files})
 original_pose=poses[0]
frames=np.linspace(0,len(episode.q)-1,8,dtype=int).tolist();viewers=sorted((p.parent/('viewer_'+p.name)).glob('pre_*.jpg'));assert len(viewers)>=4
selected=[viewers[i] for i in np.linspace(0,len(viewers)-1,4,dtype=int)];canvas=Image.new('RGB',(1280,750));draw=ImageDraw.Draw(canvas)
for i,t in enumerate(frames):canvas.paste(Image.fromarray(episode.rgb[t].transpose(1,2,0)).resize((320,240)),((i%4)*320,(i//4)*265));draw.text(((i%4)*320,(i//4)*265+241),str(t))
for i,v in enumerate(selected):canvas.paste(Image.open(v).resize((320,180)),(i*320,540));draw.text((i*320,722),'viewer '+v.stem)
canvas.save(p/'REVIEW_EVEN.jpg');review=dict(episode=p.name,quality=quality,pose=original_pose,raw_sha256=sha(raw),review_sheet_sha256=sha(p/'REVIEW_EVEN.jpg'),sampled_rgb_frames=frames,sampled_viewer_frames=[int(x.stem.split('_')[-1]) for x in selected],actual_sampled_visual_review='pending',training_ready=False)
(p/'EARLY_REVIEW.json').write_text(json.dumps(review,indent=2));print(json.dumps(dict(episode=p.name,audit_passed=audit['passed'],quality_passed=quality['passed'],first_q=audit['first_upper_state_max_abs_rad'],first_action=audit['first_upper_action_max_abs_rad'],progress_m=quality['metrics'].get('target_final_progress_m'),phase_counts=phase.get('counts'),training_ready=False),indent=2))
