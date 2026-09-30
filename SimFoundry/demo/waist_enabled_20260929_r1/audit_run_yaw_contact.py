"""Read-only yaw/phase/contact-direction evidence for physical off-center push."""
from pathlib import Path
import json,sys
import numpy as np
from scipy.spatial.transform import Rotation
run=Path(sys.argv[1]);status=json.loads((run/'STATUS.json').read_text());assert status['stage']=='numeric_complete_actual_visual_review_pending'
rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';actor='parcel_box' if side=='right' else 'mailer';direction=-1 if side=='right' else 1
 tr=np.load(ep/'trace.npz');ori=np.load(ep/'parcel_orientation.npz');yaw=np.unwrap(Rotation.from_quat(ori[key]).as_euler('xyz')[:,2]);log=json.loads((ep/'frontal_bypass.json').read_text())['rows'];phases={v['step']:v['mode'] for v in log};firsttip=next((v['step'] for v in log if v['mode'].startswith('tip_')),None);samples={}
 for rr in json.loads((ep/'solved_contact_forces.json').read_text())['rows']:
  t=rr['after_action_step'];phase=phases.get(t,'unknown');group='rear' if phase.startswith('rear_') else 'tip'
  for c in rr['parcel_contacts']:
   shapes=' '.join(c['shapes']);force=np.array(c['force_world_N']);magnitude=float(np.linalg.norm(force))
   if side+'_wrist' not in shapes or actor+'/geometry' not in shapes or magnitude<=.5:continue
   normal=np.abs(np.array(c['contact_frame'])[0]);samples.setdefault(group,[]).append([magnitude,*normal])
 alignment={}
 for phase,values in samples.items():
  a=np.array(values);alignment[phase]=dict(samples=len(a),force_weighted_abs_normal_xyz=np.average(a[:,1:],axis=0,weights=a[:,0]).tolist())
 rows.append(dict(episode=ep.name,initial_yaw_deg=float(np.rad2deg(yaw[0])),yaw_at_first_tip_deg=None if firsttip is None else float(np.rad2deg(yaw[firsttip])),final_yaw_deg=float(np.rad2deg(yaw[-1])),signed_yaw_change_toward_sorting_deg=float(direction*np.rad2deg(yaw[-1]-yaw[0])),first_tip_step=firsttip,target_at_first_tip=None if firsttip is None else tr[key][firsttip].tolist(),target_final=tr[key][-1].tolist(),contact_normal_alignment=alignment))
report=dict(rows=rows,scope='Recorded object yaw and last-tick active-hand/target contacts>0.5N; weighted absolute normal components indicate contact orientation, not net force/impulse or guaranteed motion direction. No training admission.',training_ready=False)
(run/'YAW_CONTACT_MECHANISM.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
