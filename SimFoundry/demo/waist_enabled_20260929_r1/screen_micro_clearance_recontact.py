"""Screen recorded small front-clearance repairs for possible contact retention.
Only a prior lateral->front repair followed by front->lateral return is considered.
Initial major route turn, contact loss, guards, and edge contacts remain excluded.
No controller is modified and observed recovery durations are not saved-time forecasts.
"""
from pathlib import Path
import json,hashlib,numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();results=[]
for run in ['front_direction_recontact_groups_r1','front_diagonal_entry_groups_r1']:
 for cid,task in [(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}'
  if not (ep/'quality.json').exists():continue
  quality=json.loads((ep/'quality.json').read_text());assert quality['frames']==1200
  fr=json.loads((ep/'frontal_bypass.json').read_text());rows=fr['rows'];key='box' if 'push_box' in task else 'mailer';actor='parcel_box' if key=='box' else 'mailer';side='right' if key=='box' else 'left';core=np.array(fr['plan']['front_cop_slip_following']['edge_speed']['actual_core_size_xyz']);packets={p['after_action_step']:p for p in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
  with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
  repair_start=None;events=[];previous_stage='front_x'
  for i,row in enumerate(rows):
   t=row['step'];stage=row.get('route_stage');e=row.get('direction_change_recontact');changed=stage!=previous_stage
   if changed and previous_stage=='lateral_y' and stage=='front_x':repair_start=t
   if e and e['restarted']:
    packet=packets[t-1];assert np.max(abs(np.array(packet['post_action_pose'][key])-xyz[t]))<1e-6;points=[];weights=[]
    for c in packet['parcel_contacts']:
     slots=[j for j,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
     if len(slots)!=1 or not any(side+'_wrist_roll' in s for s in c['shapes']):continue
     f=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(f@rot[t,:,2])
     if load>.05:points.append(c['position_world']);weights.append(load)
    margin=None;coplocal=None
    if sum(weights)>=.3:
     cop=np.average(points,axis=0,weights=weights);coplocal=rot[t].T@(cop-xyz[t]);margin=float(min(core[:2]/2-abs(coplocal[:2])))
    distance=None if repair_start is None else float(np.linalg.norm(xyz[t,:2]-xyz[repair_start,:2]))
    # Endpoint distance alone can hide a long excursion. Also require all prior
    # observed repair points within5mm of its start, including approach/recontact.
    maxexcursion=None if repair_start is None else float(np.max(np.linalg.norm(xyz[repair_start:t+1,:2]-xyz[repair_start,:2],axis=1)))
    returning=bool(previous_stage=='front_x' and stage=='lateral_y' and repair_start is not None)
    eligible=bool(returning and maxexcursion<=.005 and margin is not None and margin>=.01 and not e['terminal_precedence'] and not e['tilt_precedence'])
    nxt=next((v['step'] for v in rows[i+1:] if v['mode']=='top_push'),None)
    events.append(dict(step=t,previous_stage=previous_stage,current_stage=stage,repair_start_step=repair_start,repair_endpoint_distance_mm=None if distance is None else distance*1000,repair_max_excursion_mm=None if maxexcursion is None else maxexcursion*1000,current_cop_core_margin_mm=None if margin is None else margin*1000,current_cop_local_mm=None if coplocal is None else (coplocal*1000).tolist(),previous_normal_load_n=float(sum(weights)),screen_eligible=eligible,observed_recovery_frames=(nxt if nxt is not None else 1200)-t))
   if changed and stage=='lateral_y':repair_start=None
   previous_stage=stage
  selected=[e for e in events if e['screen_eligible']];result=dict(episode=str(ep),events=events,screen_selected=len(selected),selected_steps=[e['step'] for e in selected],observed_recovery_frames_of_selected=sum(e['observed_recovery_frames'] for e in selected),source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json','quality.json']});results.append(result);print(ep.parent.parent.name,ep.name,result['selected_steps'],'observed recovery',result['observed_recovery_frames_of_selected'],flush=True)
out=dict(scope=__doc__,episodes=results,maximum_observed_repair_excursion_m=.005,minimum_measured_cop_core_edge_margin_m=.01,initial_turn_excluded=True,collector_wired=False,physical_validation=False,training_ready=False,checker_sha256=sha(__file__))
(w/'MICRO_CLEARANCE_RECONTACT_SCREEN.json').write_text(json.dumps(out,indent=2))
