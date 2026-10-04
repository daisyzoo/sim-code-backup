"""Find earliest original eligible measured entry in each selected recovery window."""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_headroom';D=W/'front_box_recenter_draft_r1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from audit_front_box_recenter_events import RecoveryEventAudit
from front_initial_center_plan import checked_scene
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prior=read(D/'RECENTER_WINDOW_PROBE.json');ep=W/'front_corridor_midpoint_physical_r1/case_840020/layout_840020_push_box_to_bin';rows=read(ep/'frontal_bypass.json')['rows'];guard=ClearanceGuard(ROOT,S);audit=RecoveryEventAudit(ROOT,S)
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
with np.load(ep/'trace.npz') as z:target=z['box'].copy();other=z['mailer'].copy()
with np.load(ep/'parcel_orientation.npz') as z:tq=z['box'].copy();oq=z['mailer'].copy()
packets={r['after_action_step']:r for r in read(ep/'solved_contact_forces.json')['rows']};probes=[];windows=[]
for old in prior['probes']:
 counter=old['counter'];template=old['planning']['scene'];checks=[];selected=None
 for r in rows:
  if r['recontacts']!=counter or r['mode'] not in ('top_cross','top_descend') or r.get('route_stop_reason') or r.get('release_reason'):continue
  t=r['step'];load=sum(abs(float(v['force_world_N'][2])) for v in packets[t-1]['parcel_contacts'] if any('right_wrist_roll' in s for s in v['shapes']) and any('/parcel_box/' in s for s in v['shapes']));assert abs(load-r['contact_load']['observed_vertical_load_n'])<1e-10
  if load!=0 or not 0<=r['contact_load']['filtered_vertical_load_n']<=.05:continue
  scene=RecontactScene(guard,'right',target[t],tq[t],template['core_size'],other[t],oq[t],template['other_size']);g=checked_scene(scene,q[t]);ind,_=audit.geometry(q[t],scene.record());audit.compare_geometry(g,ind);ok=g['accepted'] and g['inactive_lowest_z_m']>=.841;checks.append(dict(step=t,original_geometry_passed=g['accepted'],inactive_lowest_z_mm=g['inactive_lowest_z_m']*1000,entry_eligible=ok))
  if ok and selected is None:selected=dict(counter=counter,step=t,planning=dict(scene=scene.record()),actual_context=dict(current=q[t].tolist(),previous_q=q[t-1].tolist(),previous_command=u[t-1].tolist(),actual_recontact_counter=counter))
 probes.append(selected if selected else old);windows.append(dict(counter=counter,earliest_eligible_step=None if selected is None else selected['step'],checks=checks))
files=[Path(__file__),D/'RECENTER_WINDOW_PROBE.json',*[ep/n for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json']]]
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,probes=probes,windows=windows,source_sha256={str(p):sha(p) for p in files},new_physics=False,training_ready=False)
with (D/'RECENTER_HEADROOM_CONTEXTS.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps([dict(counter=r['counter'],earliest=r['earliest_eligible_step'],candidate_frames=len(r['checks'])) for r in windows]))
