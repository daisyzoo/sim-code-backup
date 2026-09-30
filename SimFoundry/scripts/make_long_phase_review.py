#!/usr/bin/env python3
"""Extract focused phase evidence; creating pages does not mark them reviewed."""
import argparse,json,hashlib,base64,io
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('--layout-id',type=int);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);rows=[];frames=[0,159,319,479,510,540,570,600,639]
for case in json.loads((a.root/'PROTOCOL.json').read_text())['cases']:
 if a.layout_id is not None and case['layout_id']!=a.layout_id:continue
 ep=a.root/f"case_{case['layout_id']}/layout_{case['layout_id']}_{case['task']}";raw=ep/'raw.npz'
 if not (ep/'quality.json').exists():continue
 control=json.loads((Path(case['source']).parent/'control.json').read_text());obj='box' if case['task']=='push_box_to_bin' else 'mailer'
 page=Image.new('RGB',(960,800),'white');draw=ImageDraw.Draw(page);draw.text((5,3),f"{case['layout_id']} {case['task']} frozen replay / source phase labels",fill='black')
 with np.load(raw) as z,np.load(ep/'trace.npz') as trace:
  assert len(z['rgb'])==640
  for n,t in enumerate(frames):
   x=(n%3)*320;y=23+(n//3)*259;xy=trace[obj][t];draw.text((x,y),f"t{t} {control[t]['mode']} x{xy[0]:.3f} y{xy[1]:.3f}",fill='black');page.paste(Image.fromarray(z['rgb'][t].transpose(1,2,0)).resize((320,240)),(x,y+18))
 name=f"layout_{case['layout_id']}";page.save(a.out/(name+'.jpg'),quality=70);b=io.BytesIO();page.save(b,format='JPEG',quality=35);s=base64.b64encode(b.getvalue()).decode();(a.out/(name+'.b64')).write_text(s)
 rows.append(dict(case=case,raw=str(raw.resolve()),raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),frames=frames,page=name+'.jpg',reviewed=False));print(name,len(s),flush=True)
(a.out/'inventory.json').write_text(json.dumps(dict(rows=rows,scope='9 selected pre-action frames per episode; source phase labels, not live controller phase. Requires actual display and review.',training_ready=False),indent=2))
