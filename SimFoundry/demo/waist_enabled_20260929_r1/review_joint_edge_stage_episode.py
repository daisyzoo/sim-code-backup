"""Full diagnostic source and original task/pose checks plus actual-review sheets.
Does not grant data admission, replace remaining control audits or label images
as reviewed. Uses actual raw states and original quality functions unchanged.
"""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from audit_joint_edge_stage_contract import verify_joint_edge_stage_source
from simfoundry.data.schema import load_episode
from simfoundry.data.paired_sorting import audit_rollout
from simfoundry.data.search_reward import terminal_search_scores
from simfoundry.data.prompts import PAIRED_SORTING_PROMPTS
from simfoundry.data.query_phases import episode_query_phases
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ep=Path(sys.argv[1]).resolve();raw=ep/'raw.npz';dest=ep/'JOINT_EDGE_STAGE_NUMERIC_REVIEW.json';assert not dest.exists();source=verify_joint_edge_stage_source(ep);episode=load_episode(raw);args=json.loads((ep.parent/'provenance.json').read_text())['args'];saved=json.loads((ep/'quality.json').read_text());wait=episode.task_id=='wait_no_package';n=70 if wait else 1200
assert episode.q.shape==episode.action.shape==(n,23) and len(episode.rgb)==saved['frames']==n
assert episode.instruction==PAIRED_SORTING_PROMPTS[episode.task_id]
meta=episode.collect_meta;assert meta['collection_role']=='diagnostic' and meta['edge_clearance_intersection'] is True and meta['assist_frames']==0 and meta['push_assist'] is False
assert not meta.get('wait_force_n',0) and not meta.get('push_force_n',0) and meta.get('idle_diagnostic') is False
for key in ['motion_protocol','waist_limit_rad','waist_wait_tolerance_rad','environment_seed']:assert meta[key]==args[key]
assert np.max(abs(episode.q[0,12:23]))==np.max(abs(episode.action[0,12:23]))==0
with np.load(ep/'trace.npz') as z:trace={k:z[k].copy() for k in z.files}
quality=audit_rollout(episode.task_id,episode.q,episode.action,trace,motion_protocol=args['motion_protocol'],waist_limit_rad=args['waist_limit_rad'],waist_wait_tolerance_rad=args['waist_wait_tolerance_rad']);pose=None
out=dict(episode=ep.name,frames=n,source_binding=source,recomputed_quality=quality,saved_quality_passed=saved['passed'],initial11_q_max_abs=0.,initial11_action_max_abs=0.,assist_frames=0,raw_sha256=sha(raw),source_protocol_sha256=sha(ep.parent.parent/'PROTOCOL.json'),reviewer_sha256=sha(__file__),training_ready=False)
protocol=json.loads((ep.parent.parent/'PROTOCOL.json').read_text())
for path,h in protocol['frozen_files_sha256'].items():assert sha(path)==h,path
if wait:
 assert np.max(abs(episode.action[:,12:23]))==0;out.update(all11_action_max_abs=0.,waist_max_abs_rad=float(np.max(abs(episode.q[:,12]))))
else:
 key='box' if episode.task_id=='push_box_to_bin' else 'mailer';other='mailer' if key=='box' else 'box';direction=-1 if key=='box' else 1
 with np.load(ep/'parcel_orientation.npz') as z:_,poses=terminal_search_scores([quality],[0 if key=='box' else 1],{k:v[:,None] for k,v in trace.items()},{k:z[k][:,None] for k in z.files})
 pose=poses[0];fr=json.loads((ep/'frontal_bypass.json').read_text());rows=fr['rows'];bouts=[];current=None
 for row in rows:
  if row['mode']=='top_push':
   if current is None:current=dict(start=row['step'],end=row['step'],frames=0)
   current['end']=row['step'];current['frames']+=1
  elif current is not None:current['exit_reason']=row.get('last_recontact_reason');bouts.append(current);current=None
 if current is not None:current['exit_reason']='episode_end';bouts.append(current)
 out.update(pose=pose,progress_mm=quality['metrics']['target_final_progress_m']*1000,final10_signed_y_min_mm=float(np.min(direction*trace[key][-10:,1])*1000),non_target_max_xy_mm=float(np.max(np.linalg.norm(trace[other][:,:2]-trace[other][0,:2],axis=1))*1000),phase_counts=dict(collections.Counter(r['mode'] for r in rows)),tilt_exit_count=sum(x['exit_reason']=='incipient_tilt_independent' for x in bouts),lost_contact_exit_count=sum(x['exit_reason']=='lost_contact' for x in bouts),bouts=bouts)
try:phases=episode_query_phases(episode.task_id,episode.q,episode.action,json.loads((ep/'expert_control.json').read_text()))
except ValueError as e:phases=dict(error=str(e))
out['query_phase_counts']=phases.get('counts');out['query_phase_error']=phases.get('error');out['original_task_and_pose_passed']=bool(saved['passed'] and quality['passed'] and (wait or pose['search_success']))
frames=np.linspace(0,n-1,8,dtype=int).tolist();viewer=ep.parent/('viewer_'+ep.name);external=sorted(viewer.glob('pre_*.jpg'));selected=[] if wait else [external[i] for i in np.linspace(0,len(external)-1,4,dtype=int)];assert wait or len(external)>=4
canvas=Image.new('RGB',(1280,540 if wait else 750));draw=ImageDraw.Draw(canvas)
for i,t in enumerate(frames):canvas.paste(Image.fromarray(episode.rgb[t].transpose(1,2,0)).resize((320,240)),((i%4)*320,(i//4)*265));draw.text(((i%4)*320,(i//4)*265+241),str(t))
for i,p in enumerate(selected):canvas.paste(Image.open(p).resize((320,180)),(i*320,540));draw.text((i*320,722),'viewer '+p.stem)
sheet=ep/'JOINT_EDGE_REVIEW.jpg';canvas.save(sheet);out.update(review_sheet_sha256=sha(sheet),sampled_rgb_frames=frames,sampled_viewer_frames=[int(p.stem.split('_')[-1]) for p in selected],external_source_sha256={p.name:sha(p) for p in selected},actual_visual_review='pending',remaining='Full applicable control audits, actual visual review, full swap/control-group comparison. Diagnostic samples never enter training.')
dest.write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['source_binding','recomputed_quality','pose','bouts','external_source_sha256']},indent=2))
