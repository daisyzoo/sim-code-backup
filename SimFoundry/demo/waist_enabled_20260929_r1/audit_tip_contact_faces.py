"""Classify last-tick contact normals in object frame; not all physics substeps."""
from pathlib import Path
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text()
exec(compile(source.split('results=[];rng')[0],'<validated_cached_fk_setup>','exec'))
rows=[]
for ep in (root/'frontal_tip_extended_smoke_r1/case_62000').glob('layout_*'):
 side='right' if 'push_box' in ep.name else 'left';target='box' if side=='right' else 'mailer';actor='parcel_box' if side=='right' else 'mailer';z=np.load(ep/'raw.npz');ori=np.load(ep/'parcel_orientation.npz');forces=json.loads((ep/'solved_contact_forces.json').read_text());modes={r['step']:r['mode'] for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};contacts=[]
 for rr in forces['rows']:
  t=rr['after_action_step']
  if not modes.get(t,'').startswith('tip_'):continue
  for c in rr['parcel_contacts']:
   sh=' '.join(c['shapes']);f=np.array(c['force_world_N'])
   if actor+'/geometry' not in sh or side+'_wrist' not in sh or np.linalg.norm(f)<.5:continue
   frame=min(t+1,len(z['q'])-1);q=dict(zip(names,z['q'][frame,12:23]));m=np.eye(4);m[:3,3]=[.08,0,.793]
   for name,orig,axis in chains[side]:
    m=m@orig
    if axis is not None:r=np.eye(4);r[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@r
   local=(np.array(c['position_world'])-m[:3,3])@m[:3,:3];normal=np.array(c['contact_frame'])[0]@Rotation.from_quat(ori[target][frame]).as_matrix();face='XYZ'[int(np.argmax(abs(normal)))]
   contacts.append(dict(step=t,phase=modes[t],object_normal_axis=face,world_force_norm=float(np.linalg.norm(f)),hand_local_contact=local.tolist(),object_local_normal=normal.tolist()))
 totals={ax:sum(c['world_force_norm'] for c in contacts if c['object_normal_axis']==ax) for ax in 'XYZ'}
 rows.append(dict(episode=ep.name,force_magnitude_sum_by_object_normal_axis=totals,contacts=contacts));print(ep.name,totals,'first',contacts[:4])
(root/'TIP_CONTACT_FACE_AUDIT.json').write_text(json.dumps(dict(rows=rows,scope='Contact normal row0 and next pre-action pose approximating recorded post-action orientation; last physics tick only. Dominant local normal axis classifies face, near edges may be ambiguous. Sum of force magnitudes across records is not net impulse.',training_ready=False),indent=2))
