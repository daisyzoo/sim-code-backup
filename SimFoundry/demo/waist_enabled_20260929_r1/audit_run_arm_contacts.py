"""Last-tick solved forces involving recorded shoulder/elbow/wrist shapes."""
from pathlib import Path
import json,sys
import numpy as np
run=Path(sys.argv[1]).resolve();protocol=json.loads((run/'PROTOCOL.json').read_text());assert '--trace-arm-contact-forces' in protocol['settings'];assert json.loads((run/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
tokens=('left_shoulder','right_shoulder','left_elbow','right_elbow','left_wrist','right_wrist');rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 force=json.loads((ep/'solved_contact_forces.json').read_text());modes={r['step']:r['mode'] for r in json.loads((ep/'expert_control.json').read_text())};pairs={}
 for packet in force['rows']:
  assert packet['solver_force_buffer_unchanged'];assert 'arm_contacts' in packet
  for c in packet['arm_contacts']:
   assert any(t in n for n in c['shapes'] for t in tokens)
   key=tuple(c['shapes']);p=pairs.setdefault(key,dict(shapes=c['shapes'],max_force_N=0.,loaded_samples=0,modes=set(),first_loaded_step=None,nonhand_arm=any(any(t in n for t in tokens) and '_wrist_roll_rubber_hand' not in n for n in c['shapes'])))
   f=float(np.linalg.norm(c['force_world_N']));p['max_force_N']=max(p['max_force_N'],f)
   if f>.5:
    p['loaded_samples']+=1;p['modes'].add(modes.get(packet['after_action_step'],'zero'))
    if p['first_loaded_step'] is None:p['first_loaded_step']=packet['after_action_step']
 for p in pairs.values():p['modes']=sorted(p['modes'])
 rows.append(dict(episode=ep.name,pairs=list(pairs.values())));print(ep.name,[p for p in pairs.values() if p['loaded_samples']])
(run/'ARM_CONTACT_AUDIT.json').write_text(json.dumps(dict(rows=rows,scope='All recorded shoulder/elbow/wrist labeled contacts at last physics tick, threshold0.5N only for reporting. Does not certify all physics substeps, unlabeled shapes, geometry clearance without contact, or dataset admission. Simulation solver-force buffer unchanged assertions enforced.',training_ready=False),indent=2))
