"""Read-only face-axis guard timing and comparison with independent full SAT."""
from pathlib import Path
import sys,json
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.hand_obstacle_clearance import hand_face_separation
source=(root/'audit_terminal_reach.py').read_text();exec(compile(source.split('results=[];rng')[0],'<cached_fk>','exec'))
run=Path(sys.argv[1]).resolve();full=json.loads((run/'HAND_OBSTACLE_CLEARANCE_AUDIT.json').read_text());reports=[]
for ep in sorted(run.glob('case_*/layout_*')):
 side='right' if 'push_box' in ep.name else 'left';other='mailer' if side=='right' else 'box';size=[.135,.1276,.04] if other=='mailer' else [.1344,.0864,.045];z=np.load(ep/'raw.npz');tr=np.load(ep/'trace.npz');ori=np.load(ep/'parcel_orientation.npz');log=json.loads((ep/'frontal_bypass.json').read_text())['rows'];audited=next(x for x in full['rows'] if x['episode']==ep.name);independent={x['frame']:x for x in audited['records']};samples=[];errors=[]
 for row in log:
  t=row['step'];q=dict(zip(names,z['q'][t,12:23]));m=np.eye(4);m[:3,3]=[.08,0,.793]
  for name,origin,axis in chains[side]:
   m=m@origin
   if axis is not None:a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@a
  gap=hand_face_separation(side).gap(m[:3,3],Rotation.from_matrix(m[:3,:3]).as_quat(),tr[other][t],ori[other][t],size)
  if t in independent and gap>independent[t]['max_separating_axis_gap_m']+1e-7:errors.append([t,gap,independent[t]['max_separating_axis_gap_m']])
  if row['mode'] in ['top_descend','top_press','top_push']:samples.append(dict(step=t,mode=row['mode'],conservative_gap_m=gap,guard_trigger=gap<.005))
 assert not errors,errors[:3]
 triggers=[x for x in samples if x['guard_trigger']];first_contact=min((x['after_action_step'] for x in audited['contact_events']),default=None)
 report=dict(episode=ep.name,face_gap_never_exceeds_full_sat_on_matched_frames=True,first_guard=triggers[0] if triggers else None,trigger_frames=len(triggers),first_recorded_hand_other_force_over_005n=first_contact,records=samples);reports.append(report);print(ep.name,'first guard',report['first_guard'],'first contact',first_contact,'guardframes',len(triggers),flush=True)
(run/'HAND_GUARD_SHADOW.json').write_text(json.dumps(dict(rows=reports,scope='New conservative face-axis distance replayed on historical actual poses, compared with independently implemented full-SAT at sampled matching times. Inset/lift not executed; earlier warning does not prove a safe recovery or improved task. Uses historical actual Cube sizes verified separately.',training_ready=False),indent=2))
