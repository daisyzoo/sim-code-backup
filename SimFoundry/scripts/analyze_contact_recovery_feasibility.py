"""Audit preregistered contact-phase physical perturbations without data promotion."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'demo/contact_recovery_feasibility_20260928_r1';rows=[];sheet=Image.new('RGB',(1600,6*260),'white');draw=ImageDraw.Draw(sheet)
for v in ['control','negative_x60','z60']:
 root=out/v;paths=sorted(root.glob('layout_*/raw.npz'));assert len(paths)==2
 for raw in paths:
  p=raw.parent;d=np.load(raw);base=np.load(out/'control'/p.name/'raw.npz');task=str(d['task_id']);side='right' if task=='push_box_to_bin' else 'left';target='box' if side=='right' else 'mailer';quality=json.loads((p/'quality.json').read_text())
  assert len(d['q'])==160 and abs(d['q'][0,12:]).max()<1e-4 and abs(d['action'][0,12:]).max()<1e-4 and np.all(d['action'][:,12]==0)
  qdelta=d['q'][:,13:23]-base['q'][:,13:23]
  with np.load(p/'trace.npz') as tr,np.load(out/'control'/p.name/'trace.npz') as bt:
   delta=tr['palm_'+side]-bt['palm_'+side];initial=max(float(abs(tr[k][0]-bt[k][0]).max()) for k in ['box','mailer']);assert initial<.001
   palmdev=np.linalg.norm(delta,axis=1)
  force_checked=False
  if v!='control':
   force=json.loads((p/'external_force.json').read_text());assert len(force)==160
   for t,row in enumerate(force):
    f=60*np.sin(np.pi*(t-70+1)/7) if 70<=t<=75 else 0.;expected=[-f,0,0] if v=='negative_x60' else [0,0,f]
    assert row['step']==t and row['bodies']==[side+'_hand'] and np.allclose(row['force_per_body_world_N'],expected,atol=1e-6)
   force_checked=True
  contacts=json.loads((p/'episode_contacts.json').read_text())['rows'];targetpath='/parcel_box/' if target=='box' else '/mailer/';active=[]
  for t,c in enumerate(contacts):
   if any(any(targetpath in s for s in pair['shapes']) and any(f'/{side}_wrist_roll_rubber_hand/' in s for s in pair['shapes']) for pair in c['target_pairs']):active.append(t)
  row={'variant':v,'task':task,'quality':quality,'active_palm_delta_max_m':float(palmdev.max()),'active_palm_delta_during70_90_max_m':float(palmdev[70:91].max()),'arm_q_delta_max_rad':float(abs(qdelta).max()),'last10_arm_q_delta_max_rad':float(abs(qdelta[-10:]).max()),'initial_object_maxdiff_m':initial,'force_trace_checked':force_checked,'useful_scale_5mm_reached':bool(palmdev[70:91].max()>=.005),'active_hand_candidate_frames':active,'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest()}
  for col,t in enumerate([0,70,75,90,159]):
   sheet.paste(Image.fromarray(d['rgb'][t].transpose(1,2,0)).resize((320,240)),(col*320,len(rows)*260+20));draw.text((col*320+2,len(rows)*260+2),f'{v} {task} t{t}',fill='black')
  rows.append(row);print(v,task,'pass',quality['passed'],'palm delta',row['active_palm_delta_during70_90_max_m'],'progress',quality['metrics']['target_final_progress_m'],'last qdiff',row['last10_arm_q_delta_max_rad'])
(out/'ANALYSIS.json').write_text(json.dumps({'rows':rows,'training_ready':False,'visual_review':'pending','limits':'A physical feasibility/coverage check only; no model learning or closed-loop improvement proven. Candidate contacts are not force measurements. Failed numeric cases retained.'},indent=2));sheet.save(out/'review.jpg')
