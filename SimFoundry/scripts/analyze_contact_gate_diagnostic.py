"""Compare all cases of the frozen layout30 contact-gate diagnostic."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'demo/paired_data_coverage_20260924_r1'
rows=[];sheet=Image.new('RGB',(1600,4*260),'white');draw=ImageDraw.Draw(sheet)
for variant in ('baseline','settled'):
 root=ROOT/f'demo/contact_gate_{variant}_20260924_r1'
 for p in sorted(root.glob('layout_*')):
  quality=json.loads((p/'quality.json').read_text());controls=json.loads((p/'expert_control.json').read_text())
  side='right' if p.name.endswith('push_box_to_bin') else 'left'
  tr=np.load(p/'trace.npz');ts=[r['step'] for r in controls if r['mode']=='sweep'];t=ts[0] if ts else None
  row={'variant':variant,'episode':p.name,'passed':quality['passed'],'reasons':quality['reasons'],'metrics':quality['metrics'],'first_sweep_step':t,'first_sweep_palm_xyz':None if t is None else tr[f'palm_{side}'][t].tolist()}
  with np.load(p/'raw.npz') as d:
   row['first_upper_state_max_rad']=float(abs(d['q'][0,12:]).max());row['first_upper_action_max_rad']=float(abs(d['action'][0,12:]).max())
   for col,step in enumerate([0,30,60,90,159]):
    sheet.paste(Image.fromarray(d['rgb'][step].transpose(1,2,0)).resize((320,240)),(col*320,len(rows)*260+20))
    draw.text((col*320+2,len(rows)*260+2),f'{variant} {side} t{step}',fill='black')
  rows.append(row)
assert len(rows)==4,'All four cases required'
(out/'contact_comparison.json').write_text(json.dumps(rows,indent=2));sheet.save(out/'contact_comparison.jpg')
print(json.dumps(rows,indent=2))
