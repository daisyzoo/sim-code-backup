"""Compare full front-bag loaded bouts; independently reconstruct COP from forces.
Descriptive diagnosis only. No new expert, gates, or data admission.
"""
from pathlib import Path
import json,hashlib,datetime,ast
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());sources={};versions=[]
for name in ['front_corridor_lateral_physical_r1','front_loaded_z_quarter_physical_r2']:
 ep=W/name/'case_840023/layout_840023_nudge_mailer_to_bin';fr=read(ep/'frontal_bypass.json');rows=fr['rows'];indexed={r['step']:r for r in rows};packets={r['after_action_step']:r for r in read(ep/'solved_contact_forces.json')['rows']};plan=fr['plan'];core=np.array(plan['front_cop_slip_following']['edge_speed']['actual_core_size_xyz'])
 prov=read(ep.parent/'provenance.json');cfg=ep.parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py';assert sha(cfg)==prov['source_sha256']['simfoundry/scene_bridge/isaac_cfg.py'];node=next(n for n in ast.walk(ast.parse(cfg.read_text())) if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='core_scale' for v in n.targets));expected=np.array([.15,.145,.04])*np.array(ast.literal_eval(node.value.body));assert np.max(abs(core-expected))<1e-7
 with np.load(ep/'trace.npz') as z:xyz=z['mailer'].copy()
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['mailer']).as_matrix()
 loaded=[];by_step={}
 for row in rows:
  t=row['step'];assert np.max(abs(np.array(row['observed_target'])-xyz[t]))<2e-6
  if row['mode']!='top_push':continue
  packet=packets[t-1];assert np.max(abs(np.array(packet['post_action_pose']['mailer'])-xyz[t]))<2e-6
  points=[];weights=[]
  for c in packet['parcel_contacts']:
   slots=[i for i,label in enumerate(c['shapes']) if '/mailer/' in label]
   if len(slots)!=1 or not any('left_wrist' in label for label in c['shapes']):continue
   force=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(force@rot[t,:,2])
   if load>.05:points.append(c['position_world']);weights.append(load)
  f=row['cop_slip_following'];detail=dict(step=t,normal_load_n=sum(weights),has_valid_cop=bool(weights and sum(weights)>=.3))
  if detail['has_valid_cop']:
   local=rot[t].T@(np.average(points,axis=0,weights=weights)-xyz[t]);assert f['override'] is True and np.max(abs(local-np.array(f['measured_cop_local'])))<2e-6
   direction=np.array(f['drive_direction_xy']);assert abs(np.linalg.norm(direction)-1)<1e-6
   ray=rot[t].T@np.r_[direction,0.];half=core[:2]/2
   distances=[((half[j] if ray[j]>0 else -half[j])-local[j])/ray[j] for j in range(2) if abs(ray[j])>1e-10]
   distance=max(0.,min(distances)) if distances and np.all(abs(local[:2])<=half) else 0.
   edge=f['edge_speed'];assert abs(distance-edge['forward_core_distance_m'])<2e-6
   assert abs(edge['drive_step_m']-(.001+(edge['nominal_step_m']-.001)*np.clip(distance/.010,0,1)))<2e-6
   detail.update(cop_local_mm=(local*1000).tolist(),forward_core_distance_mm=distance*1000,minimum_axis_margin_mm=float(np.min(half-abs(local[:2]))*1000),drive_step_mm=edge['drive_step_m']*1000,command_lead_xy_mm=(np.array(f['command_reference_lead_xy'])*1000).tolist())
  else:assert not f['override']
  by_step[t]=detail;loaded.append(detail)
 bouts=[];start=None
 for j,row in enumerate(rows):
  if row['mode']=='top_push' and start is None:start=row['step']
  if start is not None and (row['mode']!='top_push' or j==len(rows)-1):
   end=row['step']-1 if row['mode']!='top_push' else row['step'];b=[by_step[t] for t in range(start,end+1)];valid=[x for x in b if x['has_valid_cop']];a=indexed[start];z=indexed[end]
   support_delta=np.array(z['observed_physical_support_xyz'])-np.array(a['observed_physical_support_xyz']);object_delta=xyz[end]-xyz[start];relative=support_delta-object_delta
   reason='unfinished_last_bout' if row['mode']=='top_push' else 'normal_release' if row['mode']=='top_release' else row.get('last_recontact_reason') if row.get('recontacts',0)>z.get('recontacts',0) else row.get('route_stop_reason','guard')
   bouts.append(dict(start=start,end=end,frames=end-start+1,exit_step=row['step'] if row['mode']!='top_push' else None,exit_reason=reason,first_valid_cop=valid[0] if valid else None,last_valid_cop=valid[-1] if valid else None,loaded_near_edge_1mm_frames=sum(x.get('forward_core_distance_mm',float('inf'))<=1 for x in b),support_delta_mm=(support_delta*1000).tolist(),object_delta_mm=(object_delta*1000).tolist(),support_relative_object_delta_mm=(relative*1000).tolist(),last_support_vs_top_z_mm=float((np.array(z['observed_physical_support_xyz'])[2]-np.array(z['parcel_top_xyz'])[2])*1000),last_stored_z_bias_mm=z['contact_load']['stored_z_bias_m']*1000))
   start=None
 versions.append(dict(run=name,quality_passed=read(ep/'quality.json')['passed'],progress_mm=read(ep/'quality.json')['metrics']['target_final_progress_m']*1000,core_size_mm=(core*1000).tolist(),loaded_frames=len(loaded),independent_loaded_cop_frames=sum(x['has_valid_cop'] for x in loaded),bouts=bouts,loaded_records=loaded))
 for p in [ep/'frontal_bypass.json',ep/'solved_contact_forces.json',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'quality.json',ep.parent/'provenance.json',cfg]:sources[str(p)]=sha(p)
sources[str(Path(__file__))]=sha(Path(__file__))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,versions=versions,source_sha256=sources,training_ready=False,interpretation='Contact loss is preceded by tangential COP approaching actual core edges and hand/object relative slip; compare all bouts before attributing to Z. Current edge governor retains minimum outward advance even at edge. This is descriptive evidence, not proof a new controller will succeed.')
out=W/'front_loaded_z_quarter_physical_r2/FRONT_BAG_CONTACT_LOSS_DIAGNOSIS_V2.json'
serialized=json.dumps(report,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else (_ for _ in ()).throw(TypeError(type(v).__name__)))
with out.open('x') as f:f.write(serialized)
print(json.dumps([dict(run=v['run'],frames=v['loaded_frames'],cop_frames=v['independent_loaded_cop_frames'],bouts=[{k:b[k] for k in ['start','end','exit_reason','loaded_near_edge_1mm_frames','support_relative_object_delta_mm','last_support_vs_top_z_mm']} for b in v['bouts']]) for v in versions],default=lambda v:v.item()))
