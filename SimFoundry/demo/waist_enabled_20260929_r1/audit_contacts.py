import json,sys
from pathlib import Path
import numpy as np
root=Path(sys.argv[1]);output=[]
for ep in sorted(root.glob('layout_*')):
 if not (ep/'solved_contact_forces.json').exists():continue
 rows=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];pairs={}
 for row in rows:
  for c in row['parcel_contacts']:
   labels=sorted(c['shapes']);name=' | '.join(labels);f=float(np.linalg.norm(c['force_world_N']))
   p=pairs.setdefault(name,dict(max_force_N=0.,first_above_1N_after_action_step=None,contact_samples=0))
   p['max_force_N']=max(p['max_force_N'],f);p['contact_samples']+=1
   if f>1 and p['first_above_1N_after_action_step'] is None:p['first_above_1N_after_action_step']=row['after_action_step']
 with np.load(ep/'trace.npz') as z:
  motion={}
  for key in ('box','mailer'):
   delta=np.linalg.norm(z[key][:,:2]-z[key][0,:2],axis=1)
   motion[key]={}
   for limit in (.002,.005,.015):
    ix=np.flatnonzero(delta>limit);motion[key][str(limit)]=int(ix[0]) if len(ix) else None
  sep=float(np.linalg.norm(z['palm_left']-z['palm_right'],axis=1).min())
 output.append(dict(episode=ep.name,quality=json.loads((ep/'quality.json').read_text()),min_palm_separation_m=sep,first_motion_pre_action_frame=motion,contacts=pairs))
result=dict(rows=output,limitations='Contact forces sampled after action at last physics tick only, not integrated impulse. Motion frame is pre-action state. No robot-robot contacts included. No training release.',training_ready=False)
(root/'CONTACT_AUDIT.json').write_text(json.dumps(result,indent=2))
for row in output:
 print(row['episode'],row['quality']['reasons'],row['first_motion_pre_action_frame'])
 for name,d in row['contacts'].items():
  if '/table/' not in name:print(name.split(' | ')[-1],d)
