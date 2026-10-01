"""Decompose actual front-route time, object motion, and force-loaded bouts."""
from pathlib import Path
import json,hashlib,ast,collections
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[]
for run in ['region_measured_bounds_groups_r1','rear_cop_measured_bounds_groups_r1','rear_core_slice_groups_r1']:
 for cid,task in [(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());rows=fr['rows'];key='box' if 'push_box' in task else 'mailer';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer';direction=-1 if key=='box' else 1
  with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:R=Rotation.from_quat(z[key]).as_matrix()
  packets={p['after_action_step']:p for p in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
  cfg=ep.parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py';prov=json.loads((ep.parent/'provenance.json').read_text());assert sha(cfg)==prov['source_sha256']['simfoundry/scene_bridge/isaac_cfg.py'];node=next(n for n in ast.walk(ast.parse(cfg.read_text())) if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='core_scale' for v in n.targets));size=np.array(fr['plan']['top_recontact']['contact_size_xyz']);core=size*np.array(ast.literal_eval(node.value.orelse if key=='box' else node.value.body))
  steps=[];bouts=[];active=[]
  for row in rows:
   t=row['step'];packet=packets.get(t-1);points=[];weights=[];forces=[]
   if packet:
    assert np.max(abs(np.array(packet['post_action_pose'][key])-xyz[t]))<1e-6
    for c in packet['parcel_contacts']:
     slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
     if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
     force=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);normal=-float(force@R[t,:,2])
     if normal>.05:points.append(c['position_world']);weights.append(normal);forces.append(force)
   load=sum(weights);axis=0 if row['route_stage']=='front_x' else 1;sign=-1 if axis==0 else direction;f=row.get('cop_slip_following',{});move=xyz[t+1,:2]-xyz[t,:2] if t+1<len(xyz) else np.zeros(2)
   s=dict(step=t,stage=row['route_stage'],mode=row['mode'],object_delta_xy_mm=(move*1000).tolist(),active_object_delta_mm=float(sign*move[axis]*1000),signed_y_delta_mm=float(direction*move[1]*1000),loaded=load>=.3,normal_n=load,override=bool(f.get('override')),active_command_delta_mm=sign*f['route_axis_control']['emitted_xy'][axis]*1000 if f.get('override') else None)
   if f.get('override'):s['active_command_delta_mm']=sign*(f['route_axis_control']['emitted_xy'][axis]-f['previous_command_xy'][axis])*1000
   if weights:
    cop=R[t].T@(np.average(points,axis=0,weights=weights)-xyz[t]);force=np.sum(forces,axis=0);tangent=force+(load*R[t,:,2]);s.update(core_xy_margin_mm=((core[:2]/2-abs(cop[:2]))*1000).tolist(),tangent_to_normal_ratio=float(np.linalg.norm(tangent)/load),active_force_n=float(sign*force[axis]))
   steps.append(s)
   if row['mode']=='top_push':active.append(s)
   elif active:
    bouts.append(dict(start=active[0]['step'],end=active[-1]['step'],frames=len(active),loaded_frames=sum(x['loaded'] for x in active),stage_counts=dict(collections.Counter(x['stage'] for x in active)),net_xy_mm=np.sum([x['object_delta_xy_mm'] for x in active],axis=0).tolist(),signed_y_delta_mm=sum(x['signed_y_delta_mm'] for x in active),exit_reason=row.get('last_recontact_reason'),last_loaded=next((x for x in reversed(active) if x['loaded']),None)));active=[]
  if active:bouts.append(dict(start=active[0]['step'],end=active[-1]['step'],frames=len(active),loaded_frames=sum(x['loaded'] for x in active),episode_end=True))
  summaries=[]
  for stage in ['front_x','lateral_y']:
   rr=[x for x in steps if x['stage']==stage];loaded=[x for x in rr if x['mode']=='top_push' and x['loaded']];unloaded=[x for x in rr if x['mode']=='top_push' and not x['loaded']]
   summary=dict(stage=stage,frames=len(rr),mode_counts=dict(collections.Counter(x['mode'] for x in rr)),push_loaded_frames=len(loaded),push_unloaded_frames=len(unloaded),net_xy_mm=np.sum([x['object_delta_xy_mm'] for x in rr],axis=0).tolist(),signed_y_delta_mm=sum(x['signed_y_delta_mm'] for x in rr),loaded_active_object_median_mm=float(np.median([x['active_object_delta_mm'] for x in loaded])) if loaded else None,loaded_active_command_median_mm=float(np.median([x['active_command_delta_mm'] for x in loaded if x['active_command_delta_mm'] is not None])) if loaded else None,loaded_active_net_mm=sum(x['active_object_delta_mm'] for x in loaded),normal_load_median_n=float(np.median([x['normal_n'] for x in loaded])) if loaded else None,force_ratio_median=float(np.median([x['tangent_to_normal_ratio'] for x in loaded])) if loaded else None)
   summaries.append(summary)
  assert np.allclose(np.sum([x['net_xy_mm'] for x in summaries],axis=0),(xyz[-1,:2]-xyz[1,:2])*1000,atol=1e-8)
  report=dict(run=run,episode=ep.name,stages=summaries,bouts=bouts,source_sha256={n:sha(ep/n) for n in ['trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json']},collision_config_sha256=sha(cfg));reports.append(report);print(json.dumps({k:v for k,v in report.items() if k in ['run','episode','stages']}),flush=True)
out=dict(episodes=reports,checker_sha256=sha(Path(__file__)),training_ready=False,scope='Actual command t aligned to object t->t+1, prior solved last-substep contact t-1. Loaded bouts and stage time allocation; last-step displacement excluded. Tangential/normal ratio not a friction coefficient or saturation proof. No simulated faster-drive outcome.')
p=w/'FRONT_LOADED_EFFICIENCY_DIAGNOSIS.json';assert not p.exists();p.write_text(json.dumps(out,indent=2))
