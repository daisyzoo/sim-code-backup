"""Measured command lead/contact slip during top pushes, no causal proof."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
p=Path(sys.argv[1]).resolve();key='box' if 'push_box' in p.name else 'mailer'
with np.load(p/'trace.npz') as z:position=z[key].copy()
front=json.loads((p/'frontal_bypass.json').read_text())['rows'];contact={r['controller_step']:r for r in json.loads((p/'LOADED_CONTACT_OFFSETS.json').read_text())['records']};records=[]
for r in front:
 if r['mode']!='top_push':continue
 t=r['step'];command=np.asarray(r['target_xyz']);actual=np.asarray(r['observed_support_xyz']);c=contact.get(t)
 records.append(dict(step=t,route_stage=r.get('route_stage','lateral_y'),command_minus_object_xy_m=(command[:2]-position[t,:2]).tolist(),reference_minus_object_xy_m=(actual[:2]-position[t,:2]).tolist(),command_minus_reference_xy_m=(command[:2]-actual[:2]).tolist(),target_next_frame_xy_step_m=(position[min(t+1,len(position)-1),:2]-position[t,:2]).tolist(),contact_minus_object_xy_m=None if c is None else c['contact_minus_target_xy_m'],hand_force_world_n=None if c is None else c['force_on_target_world_n']))
summary={}
for phase in sorted({r['route_stage'] for r in records}):
 rows=[r for r in records if r['route_stage']==phase];loaded=[r for r in rows if r['contact_minus_object_xy_m'] is not None]
 summary[phase]=dict(frames=len(rows),loaded_frames=len(loaded),max_command_axis_lead_m=float(np.max(np.abs([r['command_minus_object_xy_m'] for r in rows]))),median_command_minus_reference_xy_m=np.median([r['command_minus_reference_xy_m'] for r in rows],axis=0).tolist(),median_target_step_xy_m=np.median([r['target_next_frame_xy_step_m'] for r in rows],axis=0).tolist(),max_contact_axis_offset_m=float(np.max(np.abs([r['contact_minus_object_xy_m'] for r in loaded]))) if loaded else None)
sha=lambda f:hashlib.sha256((p/f).read_bytes()).hexdigest()
out=dict(summary=summary,records=records,source_sha256={f:sha(f) for f in ('raw.npz','trace.npz','frontal_bypass.json','LOADED_CONTACT_OFFSETS.json')},scope='Pre-action measured object/reference/current command; contact centroid uses previous solved-force packet aligned to current pose, next object step separately labeled. Association of cumulative command lead, contact migration and recovery, not proof of root cause. No alternative force prediction or executed bounded-lead intervention.',training_ready=False)
(p/'CONTACT_LEAD_DRIFT.json').write_text(json.dumps(out,indent=2));print(p.name,json.dumps(summary,indent=2))
