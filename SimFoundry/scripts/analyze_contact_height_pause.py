"""Review failed height-pause hypothesis without promoting its data."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'demo/contact_height_pause_20260928_r1';original=ROOT/'demo/contact_recovery_feasibility_20260928_r1';rows=[];sheet=Image.new('RGB',(1600,4*260),'white');draw=ImageDraw.Draw(sheet)
for v in ['control','z60']:
 paths=sorted((out/v).glob('layout_*/raw.npz'));assert len(paths)==2
 for raw in paths:
  d=np.load(raw);base=np.load(original/v/raw.parent.name/'raw.npz');control=json.loads((raw.parent/'expert_control.json').read_text());paused=[x['step'] for x in control if x['height_paused']];quality=json.loads((raw.parent/'quality.json').read_text());task=str(d['task_id']);side='right' if task=='push_box_to_bin' else 'left'
  assert abs(d['q'][0,12:]).max()<1e-4 and abs(d['action'][0,12:]).max()<1e-4 and np.all(d['action'][:,12]==0)
  if v=='z60':
   a=json.loads((raw.parent/'external_force.json').read_text());b=json.loads((original/v/raw.parent.name/'external_force.json').read_text());assert a==b
  with np.load(raw.parent/'trace.npz') as tr:
   height=tr['palm_'+side][70:81,2].tolist()
  row={'variant':v,'task':task,'quality':quality,'pause_steps':paused,'before70_q_maxdiff_vs_original_rad':float(abs(d['q'][:70,12:]-base['q'][:70,12:]).max()),'height70_80_m':height,'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest()}
  for col,t in enumerate([0,70,75,105,159]):
   sheet.paste(Image.fromarray(d['rgb'][t].transpose(1,2,0)).resize((320,240)),(col*320,len(rows)*260+20));draw.text((col*320+2,len(rows)*260+2),f'{v} pause {task} t{t}',fill='black')
  rows.append(row);print(v,task,'pass',quality['passed'],'progress',quality['metrics']['target_final_progress_m'],'pause count',len(paused),'before70qdiff',row['before70_q_maxdiff_vs_original_rad'])
(out/'ANALYSIS.json').write_text(json.dumps({'rows':rows,'training_ready':False,'visual_review':'pending','conclusion':'Do not promote this option. It changes normal approach timing and does not trigger around the intended force window, then may remain paused late. Absolute height alone is not a validated contact-recovery detector.'},indent=2));sheet.save(out/'review.jpg')
