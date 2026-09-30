"""Last-tick force balance and pyramidal tangential-force utilization during top push."""
from pathlib import Path
import json,sys
import numpy as np
from scipy.spatial.transform import Rotation
run=Path(sys.argv[1]).resolve();rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';actor='parcel_box' if side=='right' else 'mailer';mass=.18 if key=='box' else .2;ori=np.load(ep/'parcel_orientation.npz')[key];tilt=np.arccos(np.clip(Rotation.from_quat(ori).as_matrix()[:,2,2],-1,1));modes={r['step']:r['mode'] for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];records=[]
 for p in packets:
  t=p['after_action_step'];frame=min(t+1,len(tilt)-1)
  if modes.get(t)!='top_push' or tilt[frame]>.02:continue
  net={k:np.zeros(3) for k in ('hand','table')};util={k:[] for k in net}
  for c in p['parcel_contacts']:
   slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
   if len(slots)!=1:continue
   kind='hand' if any(side+'_wrist' in s for s in c['shapes']) else ('table' if any('/table/' in s for s in c['shapes']) else None)
   if kind is None:continue
   f=np.array(c['force_torque_contact']);mu=np.array(c['friction']);net[kind]+=(1 if slots[0]==1 else -1)*np.array(c['force_world_N'])
   if f[0]>.05 and min(mu[:2])>0:util[kind].append((float((abs(f[1])/mu[0]+abs(f[2])/mu[1])/f[0]),float(f[0])))
  if not util['hand']:continue
  record=dict(step=t,hand_force_world_N=net['hand'].tolist(),table_force_world_N=net['table'].tolist(),net_contact_plus_gravity_N=(net['hand']+net['table']-[0,0,mass*9.81]).tolist(),tangent_utilization={k:None if not util[k] else sum(a*b for a,b in util[k])/sum(b for a,b in util[k]) for k in util});records.append(record)
 summary={}
 for k in ('hand','table'):
  vals=[r['tangent_utilization'][k] for r in records if r['tangent_utilization'][k] is not None];summary[k]=dict(samples=len(vals),median=float(np.median(vals)),p90=float(np.quantile(vals,.9)),max=float(max(vals))) if vals else None
 rows.append(dict(episode=ep.name,summary=summary,records=records));print(ep.name,summary,'sample',records[len(records)//2:len(records)//2+1])
(run/'CONTACT_FRICTION_BUDGET.json').write_text(json.dumps(dict(rows=rows,scope='Recorded local force components0 normal/1,2 tangential and friction[:2]. Ratio (abs(ft1)/mu1+abs(ft2)/mu2)/fn describes translational pyramidal-cone utilization, not full rotational cone. Normal-force-weighted per packet, only near-flat object poses and top_push. Signed target force convention static-mg checked separately. Last physics tick, no substep integral or dynamic proof; residual includes inertia/damping/unrecorded terms.',training_ready=False),indent=2))
