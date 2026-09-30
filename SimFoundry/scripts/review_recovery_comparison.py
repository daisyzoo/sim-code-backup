"""Build per-seed rollout keyframes and detailed model comparison; no approval."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('--experiment',type=Path,required=True);p.add_argument('--variant',choices=('ordinary','recovery','baseline','waitonly'),required=True);p.add_argument('--seeds',type=int,nargs='+',default=[0,1,2]);args=p.parse_args()
out=args.experiment/'failure_review';out.mkdir(exist_ok=True);rows=[]
for seed in args.seeds:
 root=args.experiment/f'{args.variant}_seed{seed}'/'rollouts'
 assert json.loads((root/'STATUS.json').read_text())['status']=='evaluation_complete'
 folders=sorted(root.glob('layout_*'));assert len(folders)==7
 sheet=Image.new('RGB',(1600,7*260),'white');draw=ImageDraw.Draw(sheet)
 for row,folder in enumerate(folders):
  d=np.load(folder/'raw.npz');a=d['action'];q=d['q'];rgb=d['rgb'];quality=json.loads((folder/'quality.json').read_text())
  ts=[0,30,60,90,159] if len(a)==160 else [0,10,25,45,69]
  for col,t in enumerate(ts):
   sheet.paste(Image.fromarray(rgb[t].transpose(1,2,0)).resize((320,240)),(col*320,row*260+20));draw.text((col*320+2,row*260+2),f'{args.variant} s{seed} {folder.name} t{t}',fill='black')
  jumps=(np.flatnonzero(np.abs(np.diff(a[:,12:],axis=0)).max(1)>.08)+1).tolist()
  rows.append({'seed':seed,'path':str(folder),'quality':quality,'jump_frames':jumps,'first_action_max_rad':float(abs(a[0,12:]).max()),'raw_sha256':hashlib.sha256((folder/'raw.npz').read_bytes()).hexdigest()})
 sheet.save(out/f'{args.variant}_seed{seed}.jpg')
suffix='' if args.seeds==[0,1,2] else '_seeds'+'-'.join(map(str,args.seeds))
(out/f'{args.variant}{suffix}_detail.json').write_text(json.dumps({'rows':rows,'visual_review':'pending'},indent=2))
print(args.variant,'strict',sum(r['quality']['passed'] for r in rows),'/',len(rows))
