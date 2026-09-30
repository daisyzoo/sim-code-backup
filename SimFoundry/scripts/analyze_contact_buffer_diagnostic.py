"""Summarize read-only collision candidates; never call them measured forces."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'demo/contact_buffer_diagnostic_20260928_r1';rows=[]
sheet=Image.new('RGB',(1600,4*260),'white');draw=ImageDraw.Draw(sheet)
for variant,sub in [('expert','expert'),('model','model_seed0/rollouts')]:
 root=out/sub;paths=sorted(root.glob('layout_*/raw.npz'));assert len(paths)==2
 expected='numeric_pass_visual_review_pending' if variant=='expert' else 'evaluation_complete'
 assert json.loads((root/'STATUS.json').read_text())['status']==expected
 for raw in paths:
  folder=raw.parent;data=np.load(raw);task=str(data['task_id']);contacts=json.loads((folder/'episode_contacts.json').read_text())['rows'];assert len(contacts)==len(data['q'])==160
  target='box' if task=='push_box_to_bin' else 'mailer';target_path='/parcel_box/' if target=='box' else '/mailer/';side='right' if target=='box' else 'left';sign=-1 if side=='right' else 1
  active=[];wrong=[];robot=[]
  for t,c in enumerate(contacts):
   assert c['after_action_step']==t
   pairs=[p['shapes'] for p in c['target_pairs'] if any(target_path in s for s in p['shapes'])]
   if any(any(f'/{side}_wrist_roll_rubber_hand/' in s for s in pair) for pair in pairs):active.append(t)
   other='left' if side=='right' else 'right'
   if any(any(f'/{other}_wrist_roll_rubber_hand/' in s for s in pair) for pair in pairs):wrong.append(t)
   if any(any('/Robot/' in s for s in pair) for pair in pairs):robot.append(t)
  with np.load(folder/'trace.npz') as tr:
   initial=float(tr[target][0,1]);pre_palm_z=tr['palm_'+side][:,2].copy()
  post=np.array([r['post_action_pose'][target][1] for r in contacts]);increment=sign*np.diff(np.r_[initial,post]);moving=np.flatnonzero(increment>.0005)
  quality=json.loads((folder/'quality.json').read_text())
  row={'variant':variant,'task':task,'quality':quality,'active_hand_candidate_frames':active,'wrong_hand_candidate_frames':wrong,'any_robot_candidate_frames':robot,'forward_motion_gt0p5mm_frames':moving.tolist(),'forward_motion_with_sampled_hand_candidate_frames':sorted(set(active)&set(moving.tolist())),'palm_height_main30_100_median_m':float(np.median(pre_palm_z[30:101])),'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'contact_sha256':hashlib.sha256((folder/'episode_contacts.json').read_bytes()).hexdigest()}
  for col,t in enumerate([0,30,60,90,159]):
   sheet.paste(Image.fromarray(data['rgb'][t].transpose(1,2,0)).resize((320,240)),(col*320,len(rows)*260+20));draw.text((col*320+2,len(rows)*260+2),f'{variant} {task} t{t}',fill='black')
  rows.append(row);print(variant,task,'strict',quality['passed'],'progress',quality['metrics']['target_final_progress_m'],'hand candidates',len(active),'first/last',active[:1],active[-1:],'motion',len(moving),'height',row['palm_height_main30_100_median_m'])
comparison=[]
for task in ['push_box_to_bin','nudge_mailer_to_bin']:
 a=out/'expert'/f'layout_0020_{task}';b=out/'model_seed0/rollouts'/f'layout_0020_{task}'
 with np.load(a/'raw.npz') as da,np.load(b/'raw.npz') as db:
  qdiff=float(abs(da['q'][0]-db['q'][0]).max());mae=float(abs(da['rgb'][0].astype(float)-db['rgb'][0]).mean())
 with np.load(a/'trace.npz') as ta,np.load(b/'trace.npz') as tb:
  xyz=max(float(abs(ta[k][0]-tb[k][0]).max()) for k in ['box','mailer'])
 assert qdiff<1e-4 and xyz<.001
 comparison.append({'task':task,'initial_q_maxdiff_rad':qdiff,'initial_object_xyz_maxdiff_m':xyz,'initial_rgb_mae_255':mae})
sheet.save(out/'review.jpg');(out/'ANALYSIS.json').write_text(json.dumps({'rows':rows,'initial_comparison':comparison,'visual_review':'pending','training_ready':False,'limits':'Only final physics collision buffer per control step, no contact forces/impulses; presence is not proof of effective push and absence does not exclude transient substep contact. Diagnostic layout20, not reserved confirmation.'},indent=2))
