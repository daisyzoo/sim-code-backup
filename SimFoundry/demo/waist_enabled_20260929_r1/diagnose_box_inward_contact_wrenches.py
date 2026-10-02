"""Recorded last-substep hand/table wrenches about the parcel pose origin.
Force directions and contact-frame transforms are checked from archived packets.
No integrated impulse, COM assumption, tipping prediction or causality claim.
"""
from pathlib import Path
import json,hashlib,datetime,collections
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();episodes=[]
for run in ['minimum_motion_groups_r1','rear_slow_drag_groups_r1','rear_box_rate_groups_r1','box_center_groups_r1','box_entry_lift_groups_r1','box_inward_groups_r1']:
 r=w/run;protocol=json.loads((r/'PROTOCOL.json').read_text())
 for item in protocol['commands']:
  if item['wait'] or item['layout_id']!=840001:continue
  if run in ['recontact_interior_groups_r1','recontact_interior_load3_groups_r1'] and item['layout_id'] not in [840001,840004]:continue
  for task in item['tasks']:
   if task!='push_box_to_bin':continue
   ep=r/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}"
   if not (ep/'quality.json').exists():continue
   key='box' if 'push_box' in task else 'mailer';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer'
   with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
   with np.load(ep/'parcel_orientation.npz') as z:R=Rotation.from_quat(z[key]).as_matrix()
   fr=json.loads((ep/'frontal_bypass.json').read_text());packets={p['after_action_step']:p for p in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};samples={};push=[];bouts=[]
   for row in fr['rows']:
    t=row['step'];packet=packets[t-1];assert packet['solver_force_buffer_unchanged'] and np.max(abs(np.array(packet['post_action_pose'][key])-xyz[t]))<1e-6
    groups={k:dict(force=np.zeros(3),moment=np.zeros(3),count=0) for k in ['active_hand','table','other']};normal_load=0.;weighted_cop=np.zeros(3)
    for c in packet['parcel_contacts']:
     slots=[i for i,n in enumerate(c['shapes']) if '/'+actor+'/' in n]
     if not slots:continue
     assert len(slots)==1;sign=1 if slots[0]==1 else -1;frame=np.array(c['contact_frame']);local=np.array(c['force_torque_contact']);force=np.array(c['force_world_N']);assert np.max(abs(local[:3]@frame-force))<1e-5
     force*=sign;moment=np.cross(np.array(c['position_world'])-xyz[t],force)+(local[3:]@frame)*sign
     kind='active_hand' if any(side+'_wrist' in n for n in c['shapes']) else ('table' if any('/table/' in n for n in c['shapes']) else 'other');g=groups[kind];g['force']+=force;g['moment']+=moment;g['count']+=1
     if kind=='active_hand':
      load=-float(force@R[t,:,2])
      if load>.05:normal_load+=load;weighted_cop+=load*(R[t].T@(np.array(c['position_world'])-xyz[t]))
    rec=dict(step=t,mode=row['mode'],tilt_rad=float(row.get('observed_parcel_tilt_rad',0.)),hand_normal_load_n=normal_load,groups={k:dict(force_world_n=g['force'].tolist(),moment_world_nm=g['moment'].tolist(),force_local_n=(R[t].T@g['force']).tolist(),moment_local_nm=(R[t].T@g['moment']).tolist(),contacts=g['count']) for k,g in groups.items()})
    if normal_load>=.3:rec['hand_cop_local_mm']=(weighted_cop/normal_load*1000).tolist()
    samples[t]=rec
    if row['mode']=='top_push':push.append(t)
    elif push:
     last=[samples[k] for k in push[-8:]];loaded=[x for x in last if x['hand_normal_load_n']>=.3]
     bouts.append(dict(start=push[0],end=push[-1],exit_step=t,exit_reason=row.get('last_recontact_reason'),exit_tilt_rad=rec['tilt_rad'],last8=last,last_loaded=loaded[-1] if loaded else None));push=[]
   def summarize(reason):
    b=[x for x in bouts if x['exit_reason']==reason];last=[x['last_loaded'] for x in b if x['last_loaded']]
    return dict(exits=len(b),with_loaded_last8=len(last),median_hand_normal_load_n=float(np.median([x['hand_normal_load_n'] for x in last])) if last else None,median_abs_hand_moment_local_nm=np.median([np.abs(x['groups']['active_hand']['moment_local_nm']) for x in last],axis=0).tolist() if last else None,median_cop_local_mm=np.median([x['hand_cop_local_mm'] for x in last],axis=0).tolist() if last else None,median_table_upward_force_n=float(np.median([x['groups']['table']['force_world_n'][2] for x in last])) if last else None)
   quiet=[x for x in samples.values() if x['groups']['active_hand']['contacts']==0 and x['groups']['other']['contacts']==0 and x['groups']['table']['force_world_n'][2]>0 and x['tilt_rad']<.001]
   summary=dict(tilt=summarize('incipient_tilt_independent'),lost=summarize('lost_contact'),quiet_no_hand_samples=len(quiet),quiet_table_upward_force_median_n=float(np.median([x['groups']['table']['force_world_n'][2] for x in quiet])) if quiet else None)
   episodes.append(dict(run=run,episode=ep.name,frames=len(xyz),summary=summary,bouts=bouts,source_sha256={n:sha(ep/n) for n in ['trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json','quality.json']}));print(run,ep.name,'tilt',summary['tilt']['exits'],'lost',summary['lost']['exits'],flush=True)
report=dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),episodes=episodes,source_sha256={str(Path(__file__)):sha(Path(__file__))},controller_changed=False,training_ready=False);(w/'box_inward_groups_r1/SIX_VARIANT_BOX_CONTACT_WRENCH_DIAGNOSTIC.json').write_text(json.dumps(report,indent=2))
