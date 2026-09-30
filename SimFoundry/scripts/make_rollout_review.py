#!/usr/bin/env python3
"""Create review evidence only; never set reviewed/training_ready automatically."""
import argparse,json,hashlib,collections,io,base64
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--layout-ids',type=int,nargs='+');a=p.parse_args();a.out.mkdir(exist_ok=False,parents=True)
rows=[]
for path in sorted(a.root.glob('*/layout_*/raw.npz')):
 if a.layout_ids is not None and int(path.parent.name.split('_')[1]) not in a.layout_ids:continue
 q=json.loads((path.parent/'quality.json').read_text());m=json.loads((path.parent/'expert_control.json').read_text())
 rows.append({'path':str(path.parent),'passed':q['passed'],'reasons':q['reasons'],'metrics':q['metrics'],'modes':dict(collections.Counter(x['mode'] for x in m)),'raw_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
for page,start in enumerate(range(0,len(rows),6)):
 subset=rows[start:start+6];im=Image.new('RGB',(1200,len(subset)*199),'white');draw=ImageDraw.Draw(im)
 for j,row in enumerate(subset):
  r=Path(row['path']);draw.text((0,j*199),r.parent.name+' '+r.name+(' PASS' if row['passed'] else ' FAIL'),fill='black')
  with np.load(r/'raw.npz') as raw:
   for k,t in enumerate(np.linspace(0,len(raw['rgb'])-1,5,dtype=int)):im.paste(Image.fromarray(raw['rgb'][t].transpose(1,2,0)).resize((240,180)),(240*k,j*199+19))
 dest=a.out/f'page_{page}.jpg';im.save(dest,quality=45)
 b=io.BytesIO();im.save(b,format='JPEG',quality=28);s=base64.b64encode(b.getvalue()).decode();(a.out/f'page_{page}.b64').write_text(s)
 print(page,len(s),flush=True)
(a.out/'inventory.json').write_text(json.dumps(rows,indent=2));print('PASS',sum(x['passed'] for x in rows),'TOTAL',len(rows),flush=True)
