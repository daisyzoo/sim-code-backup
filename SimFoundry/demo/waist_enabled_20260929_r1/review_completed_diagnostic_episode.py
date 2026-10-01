"""Original pose scoring and sampled sheet for one saved diagnostic attempt.
Short episodes remain failed; rendering never changes quality or admission."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo))
from simfoundry.data.search_reward import terminal_search_scores
ep=Path(sys.argv[1]).resolve();q=json.loads((ep/'quality.json').read_text());assert q['frames']>0
with np.load(ep/'raw.npz') as z,np.load(ep/'trace.npz') as tr,np.load(ep/'parcel_orientation.npz') as ori:
 assert len(z['q'])==q['frames']
 task=0 if 'push_box' in ep.name else 1
 _,pose=terminal_search_scores([q],[task],{k:tr[k][:,None] for k in tr.files},{k:ori[k][:,None] for k in ori.files})
 rgb_times=np.linspace(0,len(z['q'])-1,8,dtype=int).tolist();viewers=sorted((ep.parent/('viewer_'+ep.name)).glob('pre_*.jpg'));viewer_times=[int(viewers[k].stem.split('_')[-1]) for k in np.linspace(0,len(viewers)-1,4,dtype=int)]
 canvas=Image.new('RGB',(1280,750));d=ImageDraw.Draw(canvas)
 rgb_data=z['rgb']
 for i,t in enumerate(rgb_times):
  canvas.paste(Image.fromarray(rgb_data[t].transpose(1,2,0)).resize((320,240)),((i%4)*320,(i//4)*265));d.text(((i%4)*320,(i//4)*265+241),str(t))
 for i,t in enumerate(viewer_times):
  canvas.paste(Image.open(ep.parent/('viewer_'+ep.name)/f'pre_{t:04d}.jpg').resize((320,180)),(i*320,540));d.text((i*320,722),f'viewer {t}')
 canvas.save(ep/'REVIEW_EVEN.jpg')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=dict(episode=ep.name,quality=q,pose=pose[0],raw_sha256=sha(ep/'raw.npz'),review_sheet_sha256=sha(ep/'REVIEW_EVEN.jpg'),sampled_rgb_frames=rgb_times,sampled_viewer_frames=viewer_times,actual_sampled_visual_review='pending',training_ready=False)
(ep/'EARLY_REVIEW.json').write_text(json.dumps(result,indent=2));print(json.dumps(dict(episode=ep.name,pose=pose[0])))
