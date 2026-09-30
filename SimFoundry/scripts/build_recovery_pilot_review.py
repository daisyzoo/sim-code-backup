"""Build full pilot manifest and keyframe sheets; DOES NOT approve visual review."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('--roots',nargs='+',type=Path,required=True);p.add_argument('--out-dir',type=Path,required=True);args=p.parse_args();args.out_dir.mkdir(parents=True,exist_ok=True)
rows=[];items=[]
for root in args.roots:
 status=json.loads((root/'STATUS.json').read_text());assert status['status']=='numeric_pass_visual_review_pending'
 for f in sorted(root.glob('layout_*/raw.npz')):
  quality=json.loads((f.parent/'quality.json').read_text());assert quality['passed']
  items.append(f)
for offset in range(0,len(items),4):
 group=items[offset:offset+4];sheet=Image.new('RGB',(1600,260*len(group)),'white');draw=ImageDraw.Draw(sheet)
 for row,f in enumerate(group):
  with np.load(f) as d:
   meta=json.loads(str(d['collect_meta']));q=d['q'];a=d['action'];rgb=d['rgb'];n=len(q)
   assert abs(q[0,12:]).max()<1e-4 and abs(a[0,12:]).max()<1e-4 and abs(a[:,12]).max()<1e-6
   steps=[0,10,30,70,159] if n==160 else [0,10,23,35,69]
   for col,t in enumerate(steps):
    sheet.paste(Image.fromarray(rgb[t].transpose(1,2,0)).resize((320,240)),(col*320,row*260+20));draw.text((col*320+2,row*260+2),f'{f.parent.name} t{t}',fill='black')
   rows.append({'path':str(f.resolve()),'frames':n,'task':str(d['task_id']),'raw_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'meta':meta,'quality':json.loads((f.parent/'quality.json').read_text())})
 sheet.save(args.out_dir/f'review_{offset//4}.jpg')
(args.out_dir/'numeric_manifest.json').write_text(json.dumps({'rows':rows,'visual_review':'pending','training_ready':False},indent=2));print('Prepared',len(rows),'episodes',sum(r['frames'] for r in rows),'frames')
