"""Separate front-route time allocation, edge contact and tilt recoveries."""
from pathlib import Path
import sys,json,hashlib,collections,ast
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
from simfoundry.data.top_contact_load_geometry import loaded_forward_margin
reports=[]
for run in ['region_causal_xy_groups_r2','region_measured_bounds_groups_r1']:
 for cid,task in [(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());rows=fr['rows'];key='box' if 'push_box' in task else 'mailer';side='right' if key=='box' else 'left';direction=-1 if key=='box' else 1;actor='parcel_box' if key=='box' else 'mailer';size=np.array(fr['plan']['top_recontact']['contact_size_xyz']);config=ep.parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py';prov=json.loads((ep.parent/'provenance.json').read_text());assert sha(config)==prov['source_sha256']['simfoundry/scene_bridge/isaac_cfg.py'];node=next(n for n in ast.walk(ast.parse(config.read_text())) if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='core_scale' for v in n.targets));assert ast.unparse(node.value.test)=="obj.semantic == 'mailer'";core=size*np.array(ast.literal_eval(node.value.orelse if key=='box' else node.value.body))
  with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].astype(float)
  packets={p['after_action_step']:p for p in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};events=[];changes=[];previous=None;loaded=None
  for row in rows:
   t=row['step']
   if previous and row['route_stage']!=previous['route_stage']:changes.append(dict(step=t,stage=row['route_stage'],measured_gap_mm=row['measured_front_gap_m']*1000,signed_y_mm=direction*xyz[t,1]*1000))
   if row['mode']=='top_push':
    c=loaded_forward_margin(packets.get(t-1),side,actor,xyz[t],quat[t],size,direction)
    if c['valid'] and c['normal_load_n']>=.3:loaded=dict(step=t,normal_n=c['normal_load_n'],core_margin_mm=((core[:2]/2-abs(np.array(c['weighted_contact_local'])[:2]))*1000).tolist())
   if previous and previous['mode'] in ['top_push','top_press'] and row['mode']=='top_lift':
    events.append(dict(step=t,reason=row['last_recontact_reason'],stage=row['route_stage'],observed_tilt_rad=row['observed_parcel_tilt_rad'],last_loaded_cop=loaded));loaded=None
   previous=row
  first=next(r['step'] for r in rows if r['route_stage']=='lateral_y');q=json.loads((ep/'quality.json').read_text());target_y=max(.2,direction*xyz[0,1]+.15)
  report=dict(archived_collision_config_sha256=sha(config),run=run,episode=ep.name,first_lateral_step=first,frames_remaining_at_first_lateral=len(xyz)-first,remaining_y_distance_at_first_lateral_mm=(target_y-direction*xyz[first,1])*1000,final_signed_y_mm=direction*xyz[-1,1]*1000,original_required_signed_y_mm=target_y*1000,mode_counts=dict(collections.Counter(r['mode'] for r in rows)),stage_counts=dict(collections.Counter(r['route_stage'] for r in rows)),stage_changes=changes,recoveries=events,recovery_counts=dict(collections.Counter(e['reason'] for e in events)),original_quality=q,source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json','quality.json']})
  sp=ep/'CONTACT_SURFACE_MOTION_AUDIT.json'
  if sp.exists():report['surface_motion_summary']=json.loads(sp.read_text())['summary'];report['surface_audit_sha256']=sha(sp)
  reports.append(report)
out=dict(rows=reports,checker_sha256=sha(Path(__file__)),training_ready=False,scope='Descriptive complete trajectories. First lateral time and distance expose clearance cost; no assertion that extending duration would solve task. COP is prior last-substep weighted normal contact, not interval impulse. Front tilt and front bag clearance are distinct from rear-X intervention. No changed time budget, thresholds, friction, or data admission.')
r=w/'region_measured_bounds_groups_r1';(r/'FRONT_ROUTE_CAUSE_COMPARISON.json').write_text(json.dumps(out,indent=2))
for row in reports:print({k:row[k] for k in ['run','episode','first_lateral_step','frames_remaining_at_first_lateral','remaining_y_distance_at_first_lateral_mm','final_signed_y_mm','recovery_counts']})
