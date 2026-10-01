"""Diagnose recorded clearance recovery stagnation, no controller changes."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
p=Path(sys.argv[1]);log=json.loads((p/'frontal_bypass.json').read_text())['rows'];key='box' if 'push_box' in p.name else 'mailer';tail=[r for r in log if r['step']>=900];active=[r for r in tail if (r.get('clearance_feedback') or {}).get('stage')=='clearance_x'];steps=[r['step'] for r in active]
with np.load(p/'trace.npz') as tr,np.load(p/'raw.npz') as raw:
 positions=tr[key];deltas=np.linalg.norm(positions[900:,:2]-positions[900,:2],axis=1);rgb=raw['rgb'];times=[0,90,120,210,400,600,900,1199];sheet=Image.new('RGB',(1280,530));draw=ImageDraw.Draw(sheet)
 for i,t in enumerate(times):
  sheet.paste(Image.fromarray(rgb[t].transpose(1,2,0)).resize((320,240)),((i%4)*320,(i//4)*265));draw.text(((i%4)*320,(i//4)*265+242),str(t))
 sheet.save(p/'CLEARANCE_EVENT_REVIEW.jpg');final=positions[-1].tolist()
xgaps=[r['clearance_feedback']['axis_gaps_m'][0] for r in active];errors=[r['observed_target'][0]-r['clearance_feedback']['object_goal_xy'][0] for r in active]
j=dict(episode=p.name,tail_clearance_frames=len(active),tail_max_target_xy_drift_m=float(deltas.max()),tail_x_gap_minmax_m=[min(xgaps),max(xgaps)] if xgaps else None,resume_x_gap_m=.021,planned_x_gap_m=.022,tail_object_x_error_minmax_m=[min(errors),max(errors)] if errors else None,final_target=final,last=log[-1],raw_sha256=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest(),image_sha256=hashlib.sha256((p/'CLEARANCE_EVENT_REVIEW.jpg').read_bytes()).hexdigest(),sampled_rgb_frames=times,actual_visual_review='pending',scope='Measured late stagnation and threshold deficit only. No proof of a unique force/IK cause, no gate relaxation or successful counterfactual.',training_ready=False)
(p/'CLEARANCE_STAGNATION_DIAGNOSIS.json').write_text(json.dumps(j,indent=2));print({k:v for k,v in j.items() if k!='last'})
