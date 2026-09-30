"""Generate complete development-group sampled frames; no approval is automatic."""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parent/'development32_r1'
d=json.loads((root/'RESULT.json').read_text());groups={}
for r in d['rows']:groups.setdefault(r['geometry_group'],[]).append(r)
out=root/'visual_groups';out.mkdir(exist_ok=True);manifest=[]
previous={r['group']:r for r in json.loads((out/'MANIFEST.json').read_text())} if (out/'MANIFEST.json').exists() else {}
for group,rows in groups.items():
 if len(rows)!=2:continue
 if group in previous:
  manifest.append(previous[group]);continue
 canvas=Image.new('RGB',(1344,780));draw=ImageDraw.Draw(canvas);entries=[]
 for rid,r in enumerate(rows):
  for tid,p in enumerate(r['reports']):
   i=2*rid+tid;ep=root/f"case_{r['layout_id']}"/f"layout_{r['layout_id']}_{p['task']}";sha=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest();assert sha==p['raw_sha256']
   with np.load(ep/'raw.npz') as z:
    ts=[0,30,60,90,120,len(z['q'])-1]
    for j,t in enumerate(ts):canvas.paste(Image.fromarray(z['rgb'][t].transpose(1,2,0)).resize((224,168)),(j*224,i*195+20))
   draw.text((0,i*195),f"{r['layout_id']} {p['task']} numerical={p['quality']['passed']} pose={p['pose']['search_success']}",fill='white')
   for j,t in enumerate(ts):draw.text((j*224,i*195+184),str(t),fill='white')
   entries.append(dict(episode=str(ep),raw_sha256=sha,frames=ts))
 path=out/f'{group}.jpg';canvas.save(path,quality=83)
 manifest.append(dict(group=group,sheet=str(path),episodes=entries,actual_review='pending'))
(out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2));print([r['group'] for r in manifest])
