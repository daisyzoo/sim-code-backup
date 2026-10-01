"""Summarize recorded clearance stalls and recontacts; never admit data."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw
run=Path(sys.argv[1]).resolve(); out=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for ep in sorted(run.glob('case_*/layout_*')):
 if not (ep/'quality.json').exists():continue
 rows=json.loads((ep/'frontal_bypass.json').read_text())['rows'];q=json.loads((ep/'quality.json').read_text())
 tail=rows[-300:]; feedback=[r for r in rows if r.get('clearance_feedback')]
 target=np.array([r['observed_target'] for r in tail]); changes=[]; last=0
 for r in rows:
  count=r.get('recontacts',last)
  if count>last: changes.append(dict(step=r['step'],count=count,reason=r.get('last_recontact_reason'),tilt_rad=r.get('observed_parcel_tilt_rad'),target=r['observed_target']))
  last=count
 stages=collections.Counter(r['clearance_feedback'].get('stage','rejected') for r in feedback)
 ft=[r for r in tail if r.get('clearance_feedback',{} ) and r['clearance_feedback'].get('eligible')]
 row=dict(episode=ep.name,raw_sha256=sha(ep/'raw.npz'),quality=q,phases=dict(collections.Counter(r['mode'] for r in rows)),feedback_stages=dict(stages),tail_max_xy_drift_m=float(np.linalg.norm(target[:,:2]-target[0,:2],axis=1).max()),recontacts=changes,last=rows[-1],training_ready=False)
 if ft:
  row['tail_feedback_frames']=len(ft)
  for name,values in [('xgap',[r['clearance_feedback']['axis_gaps_m'][0] for r in ft]),('object_x_error',[abs(r['clearance_feedback']['object_goal_xy'][0]-r['observed_target'][0]) for r in ft])]:row['tail_'+name+'_minmax_m']=[min(values),max(values)]
 # Events selected from measured recontact changes and tail, not from outcome.
 frames=sorted(set([0]+[x['step'] for x in changes]+[rows[-1]['step']]))
 if len(frames)>8:frames=[frames[i] for i in np.linspace(0,len(frames)-1,8,dtype=int)]
 with np.load(ep/'raw.npz') as z:
  canvas=Image.new('RGB',(1280,265*((len(frames)+3)//4)));d=ImageDraw.Draw(canvas)
  rgb_data=z['rgb']
  for i,t in enumerate(frames):
   canvas.paste(Image.fromarray(rgb_data[t].transpose(1,2,0)).resize((320,240)),(i%4*320,i//4*265));d.text((i%4*320,i//4*265+242),f'frame {t}')
  canvas.save(ep/'FEEDBACK_EVENT_REVIEW.jpg')
 row['event_review']=dict(sampled_rgb_frames=frames,image_sha256=sha(ep/'FEEDBACK_EVENT_REVIEW.jpg'),actual_visual_review='pending')
 out.append(row)
result=dict(rows=out,scope='Recorded stage/trajectory evidence, not causal identification. Event sheets pending actual view. Original quality gates unchanged.',training_ready=False)
(run/'FEEDBACK_FAILURE_DIAGNOSIS.json').write_text(json.dumps(result,indent=2))
for x in out:print(json.dumps({k:x[k] for k in ['episode','phases','feedback_stages','tail_max_xy_drift_m']}))
