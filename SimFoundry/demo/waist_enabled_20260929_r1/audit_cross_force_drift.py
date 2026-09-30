"""Signed non-task X force and object/command drift during continuous top pushes."""
from pathlib import Path
import json,sys
import numpy as np
run=Path(sys.argv[1]).resolve();rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';actor='parcel_box' if side=='right' else 'mailer';tr=np.load(ep/'trace.npz');log=json.loads((ep/'frontal_bypass.json').read_text())['rows'];forces={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};segments=[]
 for row in log:
  if row['mode']!='top_push':continue
  t=row['step'];net=np.zeros(3)
  for c in forces.get(t,{}).get('parcel_contacts',[]):
   slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
   if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
   net+=(1 if slots[0]==1 else -1)*np.array(c['force_world_N'])
  if not segments or t!=segments[-1][-1]['step']+1:segments.append([])
  segments[-1].append(dict(step=t,force_on_target_world_N=net.tolist(),command_x_m=row['target_xyz'][0],object_x_m=float(tr[key][t,0]),approach_bias_x_m=row['approach_xy_bias_m'][0]))
 result=[]
 for seg in segments:
  samples=np.array([r['force_on_target_world_N'] for r in seg]);result.append(dict(first_step=seg[0]['step'],last_step=seg[-1]['step'],target_dx_m=seg[-1]['object_x_m']-seg[0]['object_x_m'],command_dx_m=seg[-1]['command_x_m']-seg[0]['command_x_m'],mean_force_world_N=samples.mean(0).tolist(),positive_fx_samples=int((samples[:,0]>.3).sum()),negative_fx_samples=int((samples[:,0]<-.3).sum()),records=seg))
 rows.append(dict(episode=ep.name,segments=result));print(ep.name,[{k:v for k,v in s.items() if k!='records'} for s in result])
(run/'CROSS_FORCE_DRIFT_AUDIT.json').write_text(json.dumps(dict(rows=rows,scope='Signed force on target (shape1 positive) with static sign convention verified separately. Mean is frame-sample average, not impulse; actual target/command X increments within continuous pushes. Positive X is rearward, whereas task displacement is worldY. Correlation is not an isolated causal result. No controller change.',training_ready=False),indent=2))
