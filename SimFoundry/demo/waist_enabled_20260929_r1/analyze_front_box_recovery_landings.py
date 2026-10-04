"""Describe actual first-contact geometry after each recovery; no commands issued."""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ep=W/'front_corridor_midpoint_physical_r1/case_840020/layout_840020_push_box_to_bin';out=W/'front_box_recenter_draft_r1/ACTUAL_RECOVERY_LANDINGS.json'
fr=json.loads((ep/'frontal_bypass.json').read_text())['rows']
with np.load(ep/'trace.npz') as z:target=z['box'].copy()
with np.load(ep/'parcel_orientation.npz') as z:quat=z['box'].copy()
packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
rows=[]
for counter in sorted({r['recontacts'] for r in fr}):
 group=[r for r in fr if r['recontacts']==counter];loaded=[]
 for r in group:
  if r['mode'] not in ('top_press','top_push'):continue
  contacts=[v for v in packets[r['step']-1]['parcel_contacts'] if any('right_wrist_roll' in s for s in v['shapes']) and any('/parcel_box/' in s for s in v['shapes'])]
  force=sum(abs(float(v['force_world_N'][2])) for v in contacts)
  assert abs(force-r['contact_load']['observed_vertical_load_n'])<1e-10
  if force<=0:continue
  # This is the physical lowest support point recorded before this command,
  # not the force-weighted COP; preserve that distinction.
  t=r['step'];p=Rotation.from_quat(quat[t]).as_matrix().T@(np.array(r['observed_physical_support_xyz'])-target[t])
  cop=r.get('cop_slip_following',{}).get('measured_cop_local')
  loaded.append(dict(step=t,mode=r['mode'],load_n=force,physical_support_local_mm=(p*1000).tolist(),support_xy_radius_mm=float(np.linalg.norm(p[:2])*1000),cop_local_mm=None if cop is None else (np.array(cop)*1000).tolist(),tilt_rad=r['observed_parcel_tilt_rad']))
 rows.append(dict(counter=counter,loaded_frames=len(loaded),first_loaded=loaded[0] if loaded else None,last_loaded=loaded[-1] if loaded else None,maximum_support_xy_radius_mm=max([r['support_xy_radius_mm'] for r in loaded],default=None),progress_mm=float((target[group[0]['step'],1]-target[group[-1]['step'],1])*1000),exit_reason=group[0].get('last_recontact_reason')))
files=[Path(__file__),*[ep/n for n in ['frontal_bypass.json','trace.npz','parcel_orientation.npz','solved_contact_forces.json']]]
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},causal_effect_proven=False,new_physics=False,training_ready=False)
with out.open('x') as f:json.dump(result,f,indent=2)
print(json.dumps([dict(counter=r['counter'],loaded=r['loaded_frames'],first_support_radius_mm=r['first_loaded']['support_xy_radius_mm'] if r['first_loaded'] else None,progress_mm=r['progress_mm']) for r in rows]))
