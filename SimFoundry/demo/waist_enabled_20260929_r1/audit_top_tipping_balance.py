"""Contact wrench and quasi-static support balance; no assertion of dynamic causality."""
from pathlib import Path
import json,sys,hashlib,ast
import numpy as np
from scipy.spatial.transform import Rotation
run=Path(sys.argv[1]).resolve();single=(run/'raw.npz').exists()
if single:assert (run/'quality.json').exists(),'Incomplete episode'
else:assert json.loads((run/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
rows=[]
for ep in ([run] if single else sorted(run.glob('case_*/layout_*'))):
 side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';actor='parcel_box' if side=='right' else 'mailer';mass=.18 if side=='right' else .2
 tr=np.load(ep/'trace.npz');ori=np.load(ep/'parcel_orientation.npz');log=json.loads((ep/'frontal_bypass.json').read_text());modes={r['step']:r['mode'] for r in log['rows']};size=np.array([.1344,.0864,.045] if side=='right' else [.135,.1276,.04]);forces=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];rot=Rotation.from_quat(ori[key]).as_matrix();tilts=np.arccos(np.clip(rot[:,2,2],-1,1));records=[];static_z=[]
 for rr in forces:
  t=rr['after_action_step'];frame=min(t+1,len(tr[key])-1);center=tr[key][frame];R=rot[frame];net=np.zeros(3);torque=np.zeros(3);contacts=[];tablez=0.
  for c in rr['parcel_contacts']:
   shapes=c['shapes'];target_slots=[i for i,s in enumerate(shapes) if '/'+actor+'/' in s]
   if len(target_slots)!=1:continue
   sign=1 if target_slots[0]==1 else -1;f=sign*np.array(c['force_world_N'])
   if any('/table/' in s for s in shapes):tablez+=f[2]
   if not any(side+'_wrist' in s for s in shapes):continue
   net+=f;lever=np.array(c['position_world'])-center;torque+=np.cross(lever,f)+sign*(np.array(c['force_torque_contact'][3:])@np.array(c['contact_frame']))
   if np.linalg.norm(f)>.5:
    local=lever@R;contacts.append(dict(local_position_m=local.tolist(),xy_edge_margins_m=(size[:2]/2-abs(local[:2])).tolist(),force_on_target_world_N=f.tolist()))
  if t<30:static_z.append(tablez)
  if modes.get(t) not in ('top_press','top_push'):continue
  vertical_reaction=mass*9.81-net[2];h=center[2]-.75;cop=None;margin=None
  if vertical_reaction>1e-6:
   cop=np.array([center[0]+(torque[1]+h*net[0])/vertical_reaction,center[1]+(h*net[1]-torque[0])/vertical_reaction,.75]);local=(cop-center)@R;margin=(size[:2]/2-abs(local[:2])).tolist()
  records.append(dict(step=t,mode=modes[t],tilt_rad=float(tilts[frame]),net_hand_force_on_target_N=net.tolist(),net_hand_moment_about_com_Nm=torque.tolist(),quasistatic_cop_world=None if cop is None else cop.tolist(),quasistatic_cop_local_xy_margin_m=margin,near_flat=bool(tilts[frame]<.02),contacts=contacts))
 snapshot=ep.parent/'source_snapshot'
 layout_path=snapshot/'scenes/sorting_station_g1_23/twin/layout.json';spawn_path=snapshot/'simfoundry/scene_bridge/isaac_cfg.py'
 obj=next(o for o in json.loads(layout_path.read_text())['objects'] if o['name']==actor)
 assert abs(obj['mass']-mass)<1e-12
 node=next(n for n in ast.walk(ast.parse(spawn_path.read_text())) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='core_scale' for t in n.targets))
 scale=ast.literal_eval(node.value.body if key=='mailer' else node.value.orelse)
 assert np.max(abs(size-np.asarray(obj['size'])*scale))<1e-12
 actual=log['plan'].get('top_recontact',{}).get('contact_geometry')
 if actual is not None:assert np.max(abs(size-np.asarray(actual['collision_core_size_xyz'])))<1e-6
 first_tilt=next((r for r in records if r['tilt_rad']>.02),None);outside=[r for r in records if r['near_flat'] and r['quasistatic_cop_local_xy_margin_m'] is not None and min(r['quasistatic_cop_local_xy_margin_m'])<0];peak=int(np.argmax(tilts));static=np.median(static_z)
 assert abs(static-mass*9.81)<.1,'Force sign/gravity static check failed'
 result=dict(core_size_xyz=size.tolist(),core_evidence='Actual measured USD when available, otherwise frozen spawn-source AST scale times frozen layout size',frozen_spawn_sha256=hashlib.sha256(spawn_path.read_bytes()).hexdigest(),frozen_layout_sha256=hashlib.sha256(layout_path.read_bytes()).hexdigest(),source_sha256={f:hashlib.sha256((ep/f).read_bytes()).hexdigest() for f in ('raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json')},episode=ep.name,static_table_force_z_N=float(static),gravity_N=mass*9.81,max_tilt_step=peak,max_tilt_rad=float(tilts[peak]),first_top_tilt_over_002_rad=first_tilt,near_flat_cop_outside_count=len(outside),first_near_flat_cop_outside=outside[0] if outside else None,records=records);rows.append(result)
 print(ep.name,'peak tilt',peak,tilts[peak],'first tilt',None if first_tilt is None else first_tilt['step'],'nearflat outside',len(outside),'first',outside[:1])
(run/'TOP_TIPPING_BALANCE_AUDIT.json').write_text(json.dumps(dict(rows=rows,scope='Signed target force assumes contact frame points shape0 toward shape1; static table force matched gravity to check convention. Last physics tick force and next pre-action pose. Quasi-static CoP uses hand wrench+gravity and horizontal table at z0.75, ignores inertia and body damping. Interpretation limited to near-flat tilt<0.02rad; not proof of dynamics or global failure cause. Core geometry, mass from unchanged scene.',training_ready=False),indent=2))
