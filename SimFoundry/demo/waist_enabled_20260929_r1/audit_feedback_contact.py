"""Compare measured contact location/force and object motion; no controller writes."""
from pathlib import Path
import json
import numpy as np
root=Path(__file__).resolve().parent
paths={'timed':root/'contact_x_ablation_r1/uncapped/layout_62004_nudge_mailer_to_bin','feedback':root/'object_feedback_pair_r1/feedback_62004/layout_62004_nudge_mailer_to_bin'}
result={}
for name,p in paths.items():
 rows=json.loads((p/'solved_contact_forces.json').read_text())['rows'];steps=[]
 with np.load(p/'trace.npz') as z:tr={k:z[k] for k in z.files}
 for r in rows:
  t=r['after_action_step'];contacts=[c for c in r['parcel_contacts'] if any('left_wrist_roll' in s for s in c['shapes']) and any('/mailer/' in s for s in c['shapes']) and np.linalg.norm(c['force_world_N'])>.1]
  steps.append(dict(t=t,palm=tr['palm_left'][t].tolist(),bag=tr['mailer'][t].tolist(),relative_palm=(tr['palm_left'][t]-tr['mailer'][t]).tolist(),force_norm_sum=float(sum(np.linalg.norm(c['force_world_N']) for c in contacts)),sum_abs_force_xyz=np.sum([abs(np.array(c['force_world_N'])) for c in contacts],axis=0).tolist() if contacts else [0,0,0],contact_positions=[c['position_world'] for c in contacts]))
 windows=[]
 for start,end in [(0,60),(60,90),(90,120),(120,160)]:
  rs=steps[start:end];windows.append(dict(frames=[start,end-1],active_contact_steps=sum(r['force_norm_sum']>.1 for r in rs),mean_abs_force_xyz=np.mean([r['sum_abs_force_xyz'] for r in rs],axis=0).tolist(),bag_progress_y_m=float(tr['mailer'][end-1,1]-tr['mailer'][start,1]),palm_minus_bag_final_xyz=rs[-1]['relative_palm']))
 result[name]=dict(windows=windows,steps=steps)
(root/'FEEDBACK_CONTACT_LOCATION_AUDIT.json').write_text(json.dumps(dict(variants=result,scope='Last-tick forces, unsigned component sums only; object/palm recorded pre-action, contacts post-action. No inferred exact coefficient/friction model or full substep impulse.',training_ready=False),indent=2))
for name,r in result.items():print(name,json.dumps(r['windows']))
