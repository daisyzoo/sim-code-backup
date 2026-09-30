"""Generate sampled evidence, never mark visual review completed automatically."""
import json,sys,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
root=Path(sys.argv[1]);cases=sorted(p for p in root.glob('case_*') if p.is_dir())
if not cases:raise ValueError('No complete case directories')
all_rows=[]
for case in cases:
 j=json.loads((case/'POSE_AND_MOTION_REVIEW.json').read_text())
 for row in j['rows']:
  ep=case/row['episode'];s=json.loads((ep/'frontal_bypass.json').read_text());side='left' if 'mailer_to' in ep.name else 'right';target='mailer' if side=='left' else 'box'
  with np.load(ep/'raw.npz') as z,np.load(ep/'trace.npz') as tr:
   row['frontal_last']=s['rows'][-1] if s['rows'] else None;row['target_final']=tr[target][-1].tolist();row['palm_final']=tr['palm_'+side][-1].tolist()
   row['rear_x_motion_m']=float(tr[target][-1,0]-tr[target][0,0]);row['raw_sha256']=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest()
   control=json.loads((ep/'expert_control.json').read_text());row['phase_counts']={v:sum(x['mode']==v for x in control) for v in sorted(set(x['mode'] for x in control))};row['final_expert_mode']=control[-1]['mode']
   canvas=Image.new('RGB',(1280,750));d=ImageDraw.Draw(canvas)
   rgb_times=[0,40,80,120,160,200,240,319] if len(z['q'])==320 else np.linspace(0,len(z['q'])-1,8,dtype=int).tolist()
   available_viewers=sorted((case/('viewer_'+ep.name)).glob('pre_*.jpg'))
   viewer_times=[80,160,240,315] if len(z['q'])==320 else [int(available_viewers[k].stem.split('_')[-1]) for k in np.linspace(0,len(available_viewers)-1,4,dtype=int)]
   row['sampled_rgb_frames']=rgb_times;row['sampled_viewer_frames']=viewer_times
   rgb_data=z['rgb']
   for i,t in enumerate(rgb_times):
    canvas.paste(Image.fromarray(rgb_data[t].transpose(1,2,0)).resize((320,240)),((i%4)*320,(i//4)*265));d.text(((i%4)*320,(i//4)*265+241),str(t))
   for i,t in enumerate(viewer_times):
    p=case/('viewer_'+ep.name)/f'pre_{t:04d}.jpg';canvas.paste(Image.open(p).resize((320,180)),(i*320,540));d.text((i*320,722),f'viewer {t}')
   canvas.save(ep/'REVIEW_EVEN.jpg')
  row['actual_sampled_visual_review']='pending';print(row['episode'],row['quality']['passed'],row['pose']['search_success'],row['rear_x_motion_m'],row['final_expert_mode'])
 all_rows.extend(j['rows'])
j={'rows':all_rows}
j['visual_review']='pending_actual_view';j['training_ready']=False;(root/'RESULT.json').write_text(json.dumps(j,indent=2))
