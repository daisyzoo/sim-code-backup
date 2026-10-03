"""Check actual contact-basis orientation before blaming rotated friction axes.
The radial1-normalized capacity below is an L1 geometry diagnostic only, not a
prediction of opposing friction force, saturation, or contact persistence.
"""
from pathlib import Path
import datetime,hashlib,json
import numpy as np
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};results=[]
for run in ['front_initial_physical_r1','front_corridor_midpoint_physical_r1']:
 ep=W/run/'case_840023/layout_840023_push_box_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());modes={r['step']:r['mode'] for r in fr['rows']};pk=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];values={'hand':[],'table':[]}
 for packet in pk:
  t=packet['after_action_step']
  if modes.get(t)!='top_push':continue
  for c in packet['parcel_contacts']:
   if not any('/parcel_box/' in label for label in c['shapes']):continue
   kind='hand' if any('right_wrist_roll' in label for label in c['shapes']) else 'table' if any('/table/' in label or '/table_edge_wear/' in label for label in c['shapes']) else None
   f=np.asarray(c['force_torque_contact'][:3]);frame=np.asarray(c['contact_frame'])
   if kind is None or f[0]<=.05:continue
   np.testing.assert_allclose(f@frame,c['force_world_N'],atol=2e-5,rtol=0);np.testing.assert_allclose(frame@frame.T,np.eye(3),atol=2e-6,rtol=0)
   direction=np.array([0.,-1.,0.]);direction-=float(direction@frame[0])*frame[0];direction/=np.linalg.norm(direction);components=frame[1:]@direction;den=float(abs(components).sum());mu=np.asarray(c['friction'][:2]);assert np.allclose(mu,mu[0],rtol=0,atol=1e-8)
   values[kind].append(dict(step=t,normal_n=float(f[0]),world_y_radial_l1_factor=1/den,tangent_l1_ratio=float(np.sum(abs(f[1:])/mu)/f[0]),normal_deviation_from_vertical_rad=float(np.arccos(np.clip(abs(frame[0,2]),0,1)))))
 stats={}
 for kind,rows in values.items():
  stats[kind]={'contacts':len(rows)}
  for key in ['world_y_radial_l1_factor','tangent_l1_ratio','normal_deviation_from_vertical_rad']:
   v=np.array([r[key] for r in rows]);stats[kind][key]=dict(min=float(v.min()),median=float(np.median(v)),max=float(v.max()))
 cfg=json.loads((ep.parent/'runtime_configuration.json').read_text())
 def cone_values(x):
  if isinstance(x,dict):return [v for k,v in x.items() if k=='cone']+sum([cone_values(v) for v in x.values()],[])
  if isinstance(x,list):return sum([cone_values(v) for v in x],[])
  return []
 cones=cone_values(cfg);assert cones==['pyramidal'];results.append(dict(run=run,recorded_cone_settings=cones,contact_frame_statistics=stats))
 for p in [ep/'frontal_bypass.json',ep/'solved_contact_forces.json',ep.parent/'runtime_configuration.json',ep/'CONTACT_SURFACE_MOTION_AUDIT.json']:sources[str(p)]=sha(p)
sources[str(Path(__file__))]=sha(__file__)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,results=results,source_sha256=sources,physics_changed=False,training_ready=False)
with (W/'front_corridor_midpoint_physical_r1/REAR_CONTACT_FRAME_ORIENTATION_DIAGNOSTIC.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(results,indent=2))
