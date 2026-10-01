"""Measured depth relocation by original rear_push route; no alternate trajectory or admission."""
from pathlib import Path
import json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[]
for run in ['joint_edge_groups_r1','joint_edge_retry_groups_r1']:
 for cid,task,key in [(840001,'push_box_to_bin','box'),(840004,'nudge_mailer_to_bin','mailer')]:
  ep=w/run/f'case_{cid}'/f'layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());fs={r['step']:r for r in fr['rows']};regions=json.loads((ep/'region_approach.json').read_text())['rows'];handover=next(r['step'] for r in regions if r['solver'] and r['solver'].get('handover'));first_push=next(t for t,r in fs.items() if r['mode']=='top_push')
  with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
  thresholds=[]
  for mm in [2,10,30,50,80]:
   ix=np.flatnonzero(xyz[:,0]-xyz[0,0]>mm/1000)
   if len(ix):t=int(ix[0]);thresholds.append(dict(x_change_mm=mm,first_step=t,mode=fs[t]['mode'],target_xyz=xyz[t].tolist(),actual_rear_goal_x=fs[t].get('rear_goal_x')))
  packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];t=thresholds[0]['first_step'];packet=next(r for r in packets if r['after_action_step']==t-1);contacts=[dict(shapes=c['shapes'],force_norm_N=float(np.linalg.norm(c['force_world_N']))) for c in packet['parcel_contacts'] if any(('/parcel_box/' if key=='box' else '/mailer/') in s for s in c['shapes'])]
  rows.append(dict(run=run,episode=ep.name,initial_xyz=xyz[0].tolist(),handover_step=handover,first_top_push_step=first_push,xyz_at_handover=xyz[handover].tolist(),pre_top_push_depth_change_mm=float((xyz[first_push,0]-xyz[0,0])*1000),pre_top_push_signed_progress_mm=float((xyz[first_push,1]-xyz[0,1])*(-1 if key=='box' else 1)*1000),plan_rear_goal_x=fr['plan']['rear_goal_x'],planned_object_routes=fr['plan']['front_route_candidates'],thresholds=thresholds,first_depth_motion_contacts=contacts,source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','frontal_bypass.json','region_approach.json','solved_contact_forces.json']}))
out=dict(rows=rows,checker_sha256=sha(Path(__file__)),scope=__doc__,conclusion='Large early positiveX relocation occurs during the explicit rear_push phase, not an accidental side effect of final joint retry. Rear route clears object envelopes but does not certify later arm reach/contact/visibility. Retain original non-target and tabletop constraints when evaluating alternatives.',training_ready=False)
(w/'REAR_ROUTE_DEPTH_COST.json').write_text(json.dumps(out,indent=2));print([{k:r[k] for k in ['run','episode','first_top_push_step','pre_top_push_depth_change_mm','pre_top_push_signed_progress_mm']} for r in rows])
