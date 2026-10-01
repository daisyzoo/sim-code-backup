"""Bound emitted rear-edge commands to next actual solved-contact observations.
Nominal FK reference direction is NOT a prediction of object-relative COP motion.
Final-substep samples and branch associations do not establish causal effects.
"""
from pathlib import Path
import json,hashlib,datetime,collections
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();episodes=[]
for run in ['recontact_interior_groups_r1','recontact_interior_load3_groups_r1']:
 for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';target='box' if 'push_box' in task else 'mailer';actor='parcel_box' if target=='box' else 'mailer';side='right' if target=='box' else 'left'
  fr=json.loads((ep/'frontal_bypass.json').read_text());core=np.array(fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz']);rows={x['step']:x for x in fr['rows']};co=json.loads((ep/'coordination.json').read_text());co=co if isinstance(co,list) else co['rows'];co={x['step']:x for x in co}
  with np.load(ep/'raw.npz') as z:actions=z['action'].copy()
  with np.load(ep/'trace.npz') as z:xyz=z[target].copy()
  with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[target]).as_matrix()
  packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];observations={}
  for pkt in packets:
   t=pkt['after_action_step']+1
   if t>=len(xyz):continue
   assert np.max(abs(np.array(pkt['post_action_pose'][target])-xyz[t]))<1e-6
   points=[];weights=[]
   for c in pkt['parcel_contacts']:
    slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
    if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
    force=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(force@rot[t,:,2])
    if load>.05:points.append(c['position_world']);weights.append(load)
   obs={'normal_load_n':sum(weights)}
   if sum(weights)>=.3:
    local=rot[t].T@(np.average(points,axis=0,weights=weights)-xyz[t]);obs.update(cop_local_mm=(local*1000).tolist(),xy_margin_mm=((core[:2]/2-abs(local[:2]))*1000).tolist())
   observations[t]=obs
  recorded=[]
  for t,row in rows.items():
   if row['mode']!='top_push' or t not in co or t not in observations or t+1 not in observations:continue
   edge=co[t].get('joint_edge_refinement',{});assert edge
   emitted=np.array(edge['final_upper_command']);assert np.max(abs(emitted-actions[t,12:23]))<1e-7
   if not edge['override']:assert np.array_equal(emitted,np.array(edge['parent_final_upper_command']))
   before,after=observations[t],observations[t+1];item=dict(step=t,reason=edge['reason'],override=edge['override'],input_selected=edge['input_selected'],before=before,after=after,nominal_edge_inward_mm=(np.array(edge.get('nominal_edge_inward_m',edge.get('parent_nominal_edge_inward_m',[])))*1000).tolist(),next_recorded_mode=rows.get(t+1,{}).get('mode'),lost_contact_transition_within5=any(rows.get(j,{}).get('mode')!='top_push' and rows.get(j,{}).get('last_recontact_reason')=='lost_contact' for j in range(t+1,min(t+6,len(xyz)))))
   if 'cop_local_mm' in before and 'cop_local_mm' in after:item['actual_min_margin_change_mm']=min(after['xy_margin_mm'])-min(before['xy_margin_mm'])
   recorded.append(item)
  summaries=[]
  for reason in sorted({x['reason'] for x in recorded}):
   subset=[x for x in recorded if x['reason']==reason];loaded=[x for x in subset if 'cop_local_mm' in x['before']];both=[x for x in loaded if 'actual_min_margin_change_mm' in x];vals=[x['actual_min_margin_change_mm'] for x in both]
   summaries.append(dict(reason=reason,emitted_commands=len(subset),initially_loaded=len(loaded),next_load_below_point3=sum(x['after']['normal_load_n']<.3 for x in loaded),both_loaded=len(both),next_min_margin_decreased_over_point1mm=sum(v<-.1 for v in vals),median_actual_min_margin_change_mm=float(np.median(vals)) if vals else None,nominal_outward_over_point1mm=sum(bool(x['nominal_edge_inward_mm']) and min(x['nominal_edge_inward_mm'])<-.1 for x in subset),commands_with_lost_contact_transition_within5=sum(x['lost_contact_transition_within5'] for x in subset)))
  episodes.append(dict(run=run,episode=ep.name,summaries=summaries,records=recorded,source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json','solved_contact_forces.json']}));print(run,ep.name,json.dumps(summaries),flush=True)
(w/'REAR_EDGE_EXECUTION_OUTCOMES.json').write_text(json.dumps(dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),episodes=episodes,script_sha256=sha(Path(__file__)),training_ready=False),indent=2))
