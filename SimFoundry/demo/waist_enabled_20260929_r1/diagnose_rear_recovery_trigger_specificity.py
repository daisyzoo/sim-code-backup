"""Screen the entry rule on all 48 baseline pushes, without changing any policy.
Uses actual historical observations; subsequent progress is descriptive only,
not available to a controller at the trigger. Original failures stay failures.
A successful baseline with a trigger is evidence of unnecessary intervention
on that history, not proof that every future parent action will be safe.
"""
from pathlib import Path
import json,hashlib,datetime,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;B=W/'fresh_closed_peak_trials_r1';dest=W/'REAR_RECOVERY_TRIGGER_SPECIFICITY.json';assert not dest.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rows=[];sources={}
for ep in sorted(B.glob('case_*/layout_*')):
 if 'wait_no_package' in ep.name or not (ep/'quality.json').exists():continue
 quality=json.loads((ep/'quality.json').read_text());fr=json.loads((ep/'frontal_bypass.json').read_text());selected=bool(fr['plan'].get('rear_joint_xy_progress',{}).get('enabled'))
 row=dict(episode=ep.name,frames=quality['frames'],original_quality_passed=quality['passed'],original_reasons=quality['reasons'],rear_selected=selected,first_trigger=None,trigger_count=0)
 for name in ['quality.json','frontal_bypass.json']:sources[str(ep/name)]=sha(ep/name)
 if selected:
  side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';direction=-1 if side=='right' else 1;sizes={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])}
  with np.load(ep/'trace.npz') as z:pos={k:z[k].astype(float) for k in sizes}
  with np.load(ep/'parcel_orientation.npz') as z:rad={k:abs(Rotation.from_quat(z[k]).as_matrix())@sizes[k]/2 for k in sizes}
  coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};n=len(pos[key]);assert n==row['frames'];triggers=[]
  for f in fr['rows']:
   t=f['step']
   if t>=n:continue
   c=coords[t];pending=direction*(pos[key][t,1]-pos[other][t,1])<=rad[key][t,1]+rad[other][t,1]+.020
   gap=pos[key][t,0]-pos[other][t,0]-rad[key][t,0]-rad[other][t,0]
   eligible=f['mode']=='top_push' and not f.get('route_stop_reason') and not f.get('release_reason') and not c.get('region_joint_override') and not c.get('terminal_joint_hold') and f.get('rear_cop_centering',{}).get('override')
   if eligible and pending and gap<.020:
    end=min(n-1,t+30);start=max(0,t-30)
    triggers.append(dict(step=t,x_aabb_clearance_mm=float(gap*1000),entry_deficit_mm=float((.020-gap)*1000),past30_signed_y_mm=float(direction*(pos[key][t,1]-pos[key][start,1])*1000),future_up_to30_actual_signed_y_mm=float(direction*(pos[key][end,1]-pos[key][t,1])*1000),future_frames=end-t,contact_bout=f['recontacts'],mode=f['mode'],observed_load_n=f.get('contact_load',{}).get('observed_vertical_load_n')))
  row.update(trigger_count=len(triggers),first_trigger=triggers[0] if triggers else None,target_final_progress_mm=quality['metrics']['target_final_progress_m']*1000,non_target_original_quality_max_xy_mm=quality['metrics'][other+'_max_xy_m']*1000,all_trigger_steps=[x['step'] for x in triggers])
  for name in ['trace.npz','parcel_orientation.npz','coordination.json']:sources[str(ep/name)]=sha(ep/name)
 rows.append(row)
assert len(rows)==48
summary=dict(conditions=48,original_quality_passes=sum(r['original_quality_passed'] for r in rows),rear_selected=sum(r['rear_selected'] for r in rows),rear_with_trigger=sum(r['trigger_count']>0 for r in rows),original_success_with_trigger=sum(r['original_quality_passed'] and r['trigger_count']>0 for r in rows),original_failure_with_trigger=sum(not r['original_quality_passed'] and r['trigger_count']>0 for r in rows))
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,summary=summary,rows=rows,source_sha256=sources,analyzer_sha256=sha(__file__),training_ready=False,physics=False,limitations=['Historical specificity screen does not prove a new trigger or controller.','No true object collision distance is inferred from axis-aligned X clearance.','No quality margin, goal layout, original failure or group admission changed.'])
with dest.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(summary,indent=2));print(json.dumps([r for r in rows if r['rear_selected']],indent=2))
