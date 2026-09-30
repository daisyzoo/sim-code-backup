"""Review complete unforced/forced paired push feasibility, never release data."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'demo/push_recovery_feasibility_20260928_r1'
rows=[];sheet=Image.new('RGB',(1600,8*260),'white');draw=ImageDraw.Draw(sheet)
for force in (0,40):
 root=out/f'force{force}';status=json.loads((root/'STATUS.json').read_text())
 paths=sorted(root.glob('layout_*/raw.npz'))
 assert len(paths)==4, 'Complete four cases per variant required'
 for path in paths:
  p=path.parent;d=np.load(path);b=np.load(out/'force0'/p.name/'raw.npz');q=d['q'];a=d['action'];delta=q[:,13:]-b['q'][:,13:]
  tr=np.load(p/'trace.npz');bt=np.load(out/'force0'/p.name/'trace.npz');side='right' if 'push_box' in p.name else 'left'
  row={'force_N':force,'episode':p.name,'quality':json.loads((p/'quality.json').read_text()),'state_perturbation_max_rad':float(abs(delta).max()),'last10_q_control_difference_rad':float(abs(delta[-10:]).max()),'active_palm_control_difference_max_m':float(np.linalg.norm(tr['palm_'+side]-bt['palm_'+side],axis=1).max()),'raw_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
  for col,t in enumerate([0,10,30,70,159]):
   sheet.paste(Image.fromarray(d['rgb'][t].transpose(1,2,0)).resize((320,240)),(col*320,len(rows)*260+20));draw.text((col*320+2,len(rows)*260+2),f'{force}N {p.name} t{t}',fill='black')
  rows.append(row)
sheet.save(out/'review.jpg');(out/'analysis.json').write_text(json.dumps({'rows':rows,'training_ready':False},indent=2))
for r in rows:print(r['force_N'],r['episode'],r['quality']['passed'],r['state_perturbation_max_rad'],r['last10_q_control_difference_rad'],r['quality']['metrics']['target_final_progress_m'])
