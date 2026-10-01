"""Completed new front bag: observed route-change recovery budget and yaw.
Records time actually spent; saved frames are not predicted by removing events.
Original episode length, goal and quality gates remain unchanged.
"""
from pathlib import Path
import json,hashlib,collections,numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;ep=w/'front_diagonal_entry_groups_r1/case_840001/layout_840001_nudge_mailer_to_bin';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();fr=json.loads((ep/'frontal_bypass.json').read_text());rows=fr['rows'];q=json.loads((ep/'quality.json').read_text());assert q['frames']==1200
with np.load(ep/'trace.npz') as z:pos=z['mailer'].copy()
with np.load(ep/'parcel_orientation.npz') as z:yaw=Rotation.from_quat(z['mailer']).as_euler('xyz')[:,2];yaw=np.unwrap(yaw)
events=[];previous_count=0
for i,r in enumerate(rows):
 count=r.get('recontacts',0)
 if count>previous_count:
  assert count==previous_count+1
  nxt=next((v['step'] for v in rows[i+1:] if v['mode']=='top_push'),None);end=nxt if nxt is not None else 1200
  events.append(dict(step=r['step'],reason=r['last_recontact_reason'],route_stage=r.get('route_stage'),next_push_step=nxt,recovery_frames=end-r['step'],observed_y_m=float(pos[r['step'],1]),yaw_deg=float(np.rad2deg(yaw[r['step']]))))
 previous_count=count
firstpush=next(r['step'] for r in rows if r['mode']=='top_push');firstchange=next(r['step'] for r in rows if r.get('direction_change_recontact',{}).get('restarted'));firstsegment=dict(first_push_step=firstpush,first_direction_change_step=firstchange,object_delta_mm=((pos[firstchange]-pos[firstpush])*1000).tolist(),yaw_change_deg=float(np.rad2deg(yaw[firstchange]-yaw[firstpush])))
byreason={k:dict(events=sum(e['reason']==k for e in events),recovery_frames=sum(e['recovery_frames'] for e in events if e['reason']==k)) for k in {e['reason'] for e in events}}
out=dict(scope=__doc__,episode=ep.name,quality_passed=q['passed'],quality_reasons=q['reasons'],progress_mm=q['metrics']['target_final_progress_m']*1000,final_y_mm=float(pos[-1,1]*1000),goal_y_mm=200.,remaining_final_y_mm=float((.2-pos[-1,1])*1000),first_entry=firstsegment,modes=dict(collections.Counter(r['mode'] for r in rows)),guard_lifts=sum(r['mode']=='front_guard_lift' for r in rows),recontacts=events,by_reason=byreason,recovery_frames_total=sum(e['recovery_frames'] for e in events),first_push_yaw_deg=float(np.rad2deg(yaw[firstpush])),final_yaw_deg=float(np.rad2deg(yaw[-1])),source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','quality.json','DIRECTION_RECONTACT_LIVE_AUDIT.json','FRONT_DIAGONAL_ENTRY_LIVE_AUDIT.json']},checker_sha256=sha(__file__),training_ready=False)
(w/'DIAGONAL_RECONTACT_BUDGET.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','recontacts','scope']}))
