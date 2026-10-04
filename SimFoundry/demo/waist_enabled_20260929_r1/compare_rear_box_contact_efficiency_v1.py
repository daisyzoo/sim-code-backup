"""Actual rearbox repeat comparison: full24 load occupancy and lasttick contact wrenches.
Moments are about recorded pose origin, not inferred COM; no integrated impulse,
causal tipping model, counterfactual state, gate override or training admission.
"""
from pathlib import Path
import collections,datetime,hashlib,json
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();versions=[];sources={str(Path(__file__)):sha(Path(__file__))}
def median(records,key):
 vals=[r[key] for r in records if r.get(key) is not None];return None if not vals else np.median(vals,axis=0).tolist()
for run in ['front_loaded_z_quarter_physical_r2','front_effective_height_physical_r1']:
 ep=W/run/'case_840023/layout_840023_push_box_to_bin';observed=read(ep/'OBSERVED24_CONTACT_BOUT_DIAGNOSTIC.json')
 for p,h in observed['source_sha256'].items():assert sha(Path(p))==h,p
 fr=read(ep/'frontal_bypass.json');rowmap={r['step']:r for r in fr['rows']};packets={p['after_action_step']:p for p in read(ep/'solved_contact_forces.json')['rows']};transport=read(ep/'joint_transport_clearance.json')['rows'];assert not any(r['applied'] or r['selected'] for r in transport)
 with np.load(ep/'trace.npz') as z:xyz=z['box'].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['box']).as_matrix()
 samples={}
 for row in observed['rows']:
  t=row['step'];packet=packets[t-1];assert packet['solver_force_buffer_unchanged'];np.testing.assert_allclose(packet['post_action_pose']['box'],xyz[t],rtol=0,atol=1e-6)
  groups={k:dict(force=np.zeros(3),moment=np.zeros(3),contacts=0) for k in ['active_hand','table','other']};normal_load=0.;cop=np.zeros(3)
  for c in packet['parcel_contacts']:
   slots=[i for i,name in enumerate(c['shapes']) if '/parcel_box/' in name]
   if not slots:continue
   assert len(slots)==1;sign=1 if slots[0]==1 else -1;frame=np.array(c['contact_frame']);local=np.array(c['force_torque_contact']);raw_force=np.array(c['force_world_N']);np.testing.assert_allclose(local[:3]@frame,raw_force,rtol=0,atol=1e-5);force=raw_force*sign;offset=np.array(c['position_world'])-xyz[t];moment=np.cross(offset,force)+(local[3:]@frame)*sign
   kind='active_hand' if any('right_wrist' in n for n in c['shapes']) else 'table' if any('/table/' in n or '/table_edge_wear/' in n for n in c['shapes']) else 'other';g=groups[kind];g['force']+=force;g['moment']+=moment;g['contacts']+=1
   if kind=='active_hand':
    load=-float(force@rot[t,:,2])
    if load>.05:normal_load+=load;cop+=load*(rot[t].T@offset)
  hand=groups['active_hand'];samples[t]=dict(step=t,normal_load_n=normal_load,cop_local_mm=None if normal_load<.3 else (cop/normal_load*1000).tolist(),hand_force_local_n=(rot[t].T@hand['force']).tolist(),hand_moment_local_nm=(rot[t].T@hand['moment']).tolist(),table_force_world_n=groups['table']['force'].tolist(),other_contacts=groups['other']['contacts'])
 bouts=[]
 for b in observed['bouts']:
  begin,end=b['start'],b['end'];z=rowmap[end];after=rowmap.get(end+1)
  if after is None:reason='unfinished_episode'
  elif after['mode']=='top_release':reason='normal_release'
  elif after.get('recontacts',0)>z.get('recontacts',0):reason=after.get('last_recontact_reason') or 'unspecified_recontact'
  else:reason=after.get('route_stop_reason') or 'non_recontact_transition'
  recs=[samples[t] for t in range(begin,end+1)];loaded=[x for x in recs if x['cop_local_mm'] is not None];first=[x for x in recs[:8] if x['cop_local_mm'] is not None];last=[x for x in recs[-8:] if x['cop_local_mm'] is not None]
  item=dict(b,legacy_reason=b['exit_reason'],exit_reason=reason,loaded_tick_fraction=b['previous24_loaded_tick_count']/b['previous24_tick_count'],signed_progress_per_push_frame_mm=b['target_signed_y_progress_mm']/b['push_frames'],last_tick_loaded_samples=len(loaded),median_cop_local_mm=median(loaded,'cop_local_mm'),first8_median_cop_local_mm=median(first,'cop_local_mm'),last8_median_cop_local_mm=median(last,'cop_local_mm'),median_hand_force_local_n=median(loaded,'hand_force_local_n'),median_hand_moment_local_nm=median(loaded,'hand_moment_local_nm'),first8_median_hand_moment_local_nm=median(first,'hand_moment_local_nm'),last8_median_hand_moment_local_nm=median(last,'hand_moment_local_nm'),last8_observations=recs[-8:]);bouts.append(item)
 total_ticks=sum(b['previous24_tick_count'] for b in bouts);loaded_ticks=sum(b['previous24_loaded_tick_count'] for b in bouts);progress=sum(b['target_signed_y_progress_mm'] for b in bouts)
 versions.append(dict(run=run,quality_passed=observed['collector_quality_passed'],final_progress_mm=observed['progress_mm'],non_target_max_xy_mm=observed['non_target_max_xy_mm'],push_frames=observed['top_push_frames'],loaded_tick_fraction=loaded_ticks/total_ticks,mean24_load_n=sum(b['previous24_mean_load_n']['mean']*b['push_frames'] for b in bouts)/observed['top_push_frames'],signed_progress_within_push_intervals_mm=progress,signed_progress_per_push_frame_mm=progress/observed['top_push_frames'],corrected_exit_counts=dict(collections.Counter(b['exit_reason'] for b in bouts)),bouts=bouts,new_transport_selected=0,new_transport_applied=0))
 for n in ['OBSERVED24_CONTACT_BOUT_DIAGNOSTIC.json','frontal_bypass.json','solved_contact_forces.json','trace.npz','parcel_orientation.npz','joint_transport_clearance.json','quality.json']:sources[str(ep/n)]=sha(ep/n)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,versions=versions,source_sha256=sources,original_reports_preserved=True,controller_changed=False,training_ready=False,interpretation='Separate contact occupancy, push efficiency and actual mode transitions. Similar mean normal load alone does not establish equal contact quality. Lasttick wrenches are descriptive; causes and any changed strategy require further physical validation.')
with (W/'front_effective_height_physical_r1/REAR_BOX_CONTACT_EFFICIENCY_AND_WRENCH_V1.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps([{k:v for k,v in r.items() if k!='bouts'} for r in versions]))
