"""Actual front-contact exit mechanisms, current2mm vs same complete1mm parent."""
from pathlib import Path
import ast,collections,hashlib,json
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[]
for run in ['rear_core_slice_groups_r1','front_drive_increment_groups_r1']:
 for cid,task in [(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';quality=json.loads((ep/'quality.json').read_text());assert quality['frames']==1200
  fr=json.loads((ep/'frontal_bypass.json').read_text());rows=fr['rows'];key='box' if 'push_box' in task else 'mailer';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer';direction=-1 if key=='box' else 1
  cfg=ep.parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py';prov=json.loads((ep.parent/'provenance.json').read_text());assert sha(cfg)==prov['source_sha256']['simfoundry/scene_bridge/isaac_cfg.py'];node=next(n for n in ast.walk(ast.parse(cfg.read_text())) if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='core_scale' for v in n.targets));core=np.array(fr['plan']['top_recontact']['contact_size_xyz'])*np.array(ast.literal_eval(node.value.orelse if key=='box' else node.value.body))
  with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
  packets={p['after_action_step']:p for p in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};samples={};bouts=[];active=[]
  for row in rows:
   t=row['step'];packet=packets.get(t-1);points=[];weights=[]
   if packet:
    assert np.max(abs(np.array(packet['post_action_pose'][key])-xyz[t]))<1e-6
    for c in packet['parcel_contacts']:
     slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
     if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
     force=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(force@rot[t,:,2])
     if load>.05:points.append(c['position_world']);weights.append(load)
   stage=row['route_stage'];axis=0 if stage=='front_x' else 1;sign=-1 if axis==0 else direction
   sample=dict(step=t,stage=stage,mode=row['mode'],normal_load_n=sum(weights),z_bias_mm=row.get('contact_load',{}).get('applied_z_bias_m',0)*1000)
   if sum(weights)>=.3:
    local=rot[t].T@(np.average(points,axis=0,weights=weights)-xyz[t]);ray=sign*rot[t][axis,:];half=core[:2]/2;limits=[((half[j] if ray[j]>0 else -half[j])-local[j])/ray[j] for j in range(2) if abs(ray[j])>1e-10]
    sample.update(cop_local_mm=(local*1000).tolist(),core_xy_edge_margin_mm=((half-abs(local[:2]))*1000).tolist(),forward_core_ray_distance_mm=min(limits)*1000)
   samples[t]=sample
   if row['mode']=='top_push':active.append(t)
   elif active:
    loaded=[samples[k] for k in active if 'cop_local_mm' in samples[k]];reason='terminal_release' if row['mode']=='top_release' else row.get('last_recontact_reason')
    bouts.append(dict(start=active[0],end=active[-1],exit_step=t,exit_reason=reason,exit_mode=row['mode'],stage_counts=dict(collections.Counter(samples[k]['stage'] for k in active)),push_steps=len(active),loaded_steps=len(loaded),object_signed_y_progress_mm=direction*(xyz[t,1]-xyz[active[0],1])*1000,last_loaded=loaded[-1] if loaded else None));active=[]
  lost=[b for b in bouts if b['exit_reason']=='lost_contact'];summary=dict(exit_counts=dict(collections.Counter(b['exit_reason'] for b in bouts)),lost_last_loaded_near_drive_edge=sum(bool(b['last_loaded'] is not None and b['last_loaded']['forward_core_ray_distance_mm']<=3) for b in lost),lost_with_loaded_cop=sum(b['last_loaded'] is not None for b in lost))
  report=dict(run=run,episode=ep.name,summary=summary,bouts=bouts,unfinished_push_steps=len(active),collision_config_sha256=sha(cfg),source_sha256={n:sha(ep/n) for n in ['quality.json','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json']});reports.append(report);print(run,ep.name,summary,flush=True)
out=dict(episodes=reports,checker_sha256=sha(Path(__file__)),scope='Actual prior final-substep force COP at last loaded step. Ray distance is world current drive direction to archived rotated collision-core XY edge with object held fixed; not future contact prediction. Terminal release classified separately from stale last recovery reason.',training_ready=False);p=w/'FRONT_CONTACT_EXIT_2MM_DIAGNOSIS.json';assert not p.exists();p.write_text(json.dumps(out,indent=2))
