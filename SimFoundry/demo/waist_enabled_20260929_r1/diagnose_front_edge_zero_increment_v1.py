"""Check whether zero new COP drive actually removes existing forward waypoint lead.
Algebraic counterfactual at original measured histories, NOT a new controller or
new physics. Original helper rejects zero drive; no production bounds are edited.
"""
from pathlib import Path
import datetime,hashlib,json
import numpy as np
W=Path(__file__).resolve().parent;R=W/'front_effective_height_physical_r1';D=W/'front_edge_zero_increment_probe_r1';D.mkdir(exist_ok=False)
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={str(Path(__file__)):sha(__file__)};result=[]
for case in read(R/'PROTOCOL.json')['plan']['commands']:
 if case['wait']:continue
 for task in case['tasks']:
  ep=R/f"case_{case['layout_id']}"/f"layout_{case['layout_id']}_{task}";rows=read(ep/'frontal_bypass.json')['rows'];out=[];verified=0
  for row in rows:
   f=row.get('cop_slip_following',{})
   if not f.get('override'):continue
   prev=np.asarray(f['previous_command_xy']);ref=np.asarray(f['reference_xy']);feed=np.asarray(f['object_anchor_translation_xy']);drive=np.asarray(f['drive_xy']);correction=np.asarray(f['slip_correction_xy']);direction=np.asarray(f['drive_direction_xy']);cmd=np.asarray(f['command_xy']);old=prev+np.clip(np.clip(prev+feed+drive+correction,ref-.030,ref+.030)-prev,-.003,.003)
   np.testing.assert_allclose(old,cmd,rtol=0,atol=2e-12);verified+=1
   edge=f.get('edge_speed',{})
   if not edge.get('applied') or edge['forward_core_distance_m']>=.010:continue
   zero=prev+np.clip(np.clip(prev+feed+correction,ref-.030,ref+.030)-prev,-.003,.003)
   actual_old=old.copy();actual_zero=zero.copy()
   if 'route_axis_control' in f:
    route=f['route_axis_control'];axis=1-route['active_axis'];actual_old[axis]=route['emitted_xy'][axis];actual_zero[axis]=route['emitted_xy'][axis]
   np.testing.assert_allclose(actual_old,row['target_xyz'][:2],rtol=0,atol=2e-12)
   out.append(dict(step=row['step'],route_stage=row['route_stage'],forward_edge_distance_mm=1000*edge['forward_core_distance_m'],removed_drive_mm=(1000*drive).tolist(),old_forward_lead_mm=1000*float((actual_old-ref)@direction),zero_increment_forward_lead_mm=1000*float((actual_zero-ref)@direction),zero_increment_command_delta_mm=(1000*(actual_zero-prev)).tolist(),zero_increment_waypoint_xy=actual_zero.tolist(),reference_xy=ref.tolist(),old_waypoint_xy=actual_old.tolist()))
  if not verified:continue
  lead=[r['zero_increment_forward_lead_mm'] for r in out];result.append(dict(episode=ep.name,original_feedback_rows_verified=verified,edge_warning_frames=len(out),zero_increment_still_forward=sum(v>1e-6 for v in lead),zero_increment_forward_lead_min_mm=min(lead) if lead else None,zero_increment_forward_lead_median_mm=float(np.median(lead)) if lead else None,zero_increment_forward_lead_max_mm=max(lead) if lead else None,rows=out))
  for name in ['frontal_bypass.json','quality.json']:sources[str(ep/name)]=sha(ep/name)
assert len(result)==2
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,episodes=result,source_sha256=sources,conclusion='Reducing the increment does not in general hold the measured hand: previous waypoint lead and object feedforward persist. Do not label zero drive as a stationary-contact strategy.',new_physics=False,training_ready=False)
with (D/'RESULT.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps([{k:v for k,v in r.items() if k!='rows'} for r in result],indent=2))
