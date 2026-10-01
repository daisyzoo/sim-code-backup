"""Locate last measured loaded COP before rear push exits; observational evidence only."""
from pathlib import Path
import json,hashlib,collections
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[]
for run in ['recontact_interior_groups_r1','precise_interior_groups_r1']:
 for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}'
  needed=['quality.json','frontal_bypass.json','trace.npz','parcel_orientation.npz','solved_contact_forces.json','recontact_pose.json']
  if not all((ep/n).exists() for n in needed):continue
  fr=json.loads((ep/'frontal_bypass.json').read_text());rows=fr['rows'];key='box' if 'push_box' in task else 'mailer';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer';direction=-1 if key=='box' else 1;core=np.array(fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'])
  with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
  packets={p['after_action_step']:p for p in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
  samples={};bouts=[];active=[]
  for row in rows:
   if 'contact_load' not in row:
    assert not row['mode'].startswith('top_') and not active
    continue
   t=row['step'];packet=packets.get(t-1);points=[];weights=[]
   selected=rot[t].T@(np.array(row['parcel_top_xyz'])-xyz[t])
   if packet:
    assert np.max(abs(np.array(packet['post_action_pose'][key])-xyz[t]))<1e-6
    for c in packet['parcel_contacts']:
     slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
     if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
     force=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(force@rot[t,:,2])
     if load>.05:points.append(c['position_world']);weights.append(load)
   sample=dict(step=t,mode=row['mode'],selected_surface_local_mm=(selected*1000).tolist(),selected_surface_core_margin_mm=((core[:2]/2-abs(selected[:2]))*1000).tolist(),normal_load_n=sum(weights),vertical_load_n=row['contact_load']['observed_vertical_load_n'],filtered_vertical_load_n=row['contact_load']['filtered_vertical_load_n'],z_bias_mm=row['contact_load']['applied_z_bias_m']*1000,reference_minus_top_z_mm=(row['observed_support_xyz'][2]-row['parcel_top_xyz'][2])*1000,command_signed_y_lead_mm=direction*(row['target_xyz'][1]-xyz[t,1])*1000,reference_signed_y_lead_mm=direction*(row['observed_support_xyz'][1]-xyz[t,1])*1000)
   if sum(weights)>=.3:
    local=rot[t].T@(np.average(points,axis=0,weights=weights)-xyz[t]);sample.update(cop_local_mm=(local*1000).tolist(),core_xy_edge_margin_mm=((core[:2]/2-abs(local[:2]))*1000).tolist())
   samples[t]=sample
   if row['mode']=='top_push':active.append(t)
   elif active:
    loaded=[samples[k] for k in active if 'cop_local_mm' in samples[k]]
    bouts.append(dict(start=active[0],end=active[-1],exit_step=t,exit_reason=row.get('last_recontact_reason'),exit_mode=row['mode'],push_steps=len(active),loaded_steps=len(loaded),object_signed_y_progress_mm=direction*(xyz[t,1]-xyz[active[0],1])*1000,first_loaded=loaded[0] if loaded else None,last_loaded=loaded[-1] if loaded else None,final_window=[samples[k] for k in active[-8:]]));active=[]
  lost=[b for b in bouts if b['exit_reason']=='lost_contact'];ll=[b['last_loaded'] for b in lost if b['last_loaded']]
  handover=next((r['step'] for r in rows if r.get('region_handover')),None)
  selected_samples=[x for x in samples.values() if handover is not None and x['step']>=handover]
  firsts=[b['first_loaded'] for b in bouts if b['first_loaded']]
  summary=dict(handover_step=handover,post_handover_selected_xy_range_mm=np.ptp([x['selected_surface_local_mm'][:2] for x in selected_samples],axis=0).tolist() if selected_samples else None,loaded_bouts=len(firsts),first_cop_within3mm_of_any_core_edge=sum(min(x['core_xy_edge_margin_mm'])<=3 for x in firsts),median_first_core_margins_mm=np.median([x['core_xy_edge_margin_mm'] for x in firsts],axis=0).tolist() if firsts else None,selected_surface_local_xy_range_mm=np.ptp([x['selected_surface_local_mm'][:2] for x in samples.values()],axis=0).tolist(),exit_counts=dict(collections.Counter(b['exit_reason'] for b in bouts)),lost_with_loaded_cop=len(ll),lost_last_cop_x_edge_within3mm=sum(x['core_xy_edge_margin_mm'][0]<=3 for x in ll),lost_last_cop_y_edge_within3mm=sum(x['core_xy_edge_margin_mm'][1]<=3 for x in ll),lost_last_z_bias_at_minus6mm=sum(x['z_bias_mm']<=-5.999 for x in ll),median_lost_last_load_n=float(np.median([x['normal_load_n'] for x in ll])) if ll else None,median_lost_last_cop_xy_margin_mm=np.median([x['core_xy_edge_margin_mm'] for x in ll],axis=0).tolist() if ll else None)
  quality=json.loads((ep/'quality.json').read_text());events=json.loads((ep/'recontact_pose.json').read_text())['rows'];plans=[e for e in events if e.get('planning')];captures=[e for e in events if e['kind']=='handover'];commands=[e for e in events if e['kind']=='command'];other='mailer' if key=='box' else 'box'
  summary.update(original_task_passed=quality['passed'],frames=quality['frames'],progress_mm=quality['metrics']['target_final_progress_m']*1000,non_target_max_xy_mm=quality['metrics'][other+'_max_xy_m']*1000,recovery_command_frames=len(commands),recovery_handovers=len(captures),preferred_selection_counts=dict(collections.Counter(e['planning'].get('interior_preference',{}).get('selected','original_parent') for e in plans)),push_mode_frames=sum(r['mode']=='top_push' for r in rows),handover_steps_and_ticks=[dict(step=e['step'],ticks=e['ticks'],measured_margin_mm=((core[:2]/2-abs(np.array(e['selected_surface_local_xy'])))*1000).tolist()) for e in captures])
  reports.append(dict(run=run,episode=ep.name,summary=summary,bouts=bouts,unfinished_push_steps=len(active),source_sha256={n:sha(ep/n) for n in ['quality.json','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json','recontact_pose.json']}));print(run,ep.name,summary,flush=True)
out=dict(episodes=reports,checker_sha256=sha(Path(__file__)),scope='Previous solved final-substep contact aligned to observation, force-normal COP and actual rotated collision core. Last COP near an edge supports edge-slip investigation but does not prove cause or continuous force integration. Reference is virtual, not physical hand contact extent. Read-only comparison of completed actual parent/interior episodes. It does not certify contact continuity, original audits, visual learnability or training admission.',training_ready=False)
p=w/'precise_interior_groups_r1/CONTACT_EXIT_COMPARISON.json';p.write_text(json.dumps(out,indent=2))
