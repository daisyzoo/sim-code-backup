"""Separate configured expert withdrawal from unchanged formal upright gate.
Uses only actual trajectories. Post-withdrawal observations are under the actual
withdrawal action and cannot predict continuation with a different threshold.
No parameter change, replay admission, controller modification or physics launch.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;r=w/'box_inward_groups_r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();episodes=[];sources=[Path(__file__),w.parents[1]/'simfoundry/data/search_reward.py',w.parents[1]/'simfoundry/data/top_contact_bypass.py',w/'audit_contact_stability_control.py']
for run in ['rear_slow_drag_groups_r1','box_center_groups_r1','box_entry_lift_groups_r1','box_inward_groups_r1']:
 ep=w/run/'case_840001/layout_840001_push_box_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());rows=fr['rows'];plan=fr['plan'];threshold=plan['contact_stability_candidate']['tilt_recontact_rad'];assert threshold==.03 and plan['contact_stability_candidate']['original_pose_max_tilt_rad']==.20
 with np.load(ep/'parcel_orientation.npz') as z:tilt=np.arccos(np.clip(Rotation.from_quat(z['box']).as_matrix()[:,2,2],-1,1))
 with np.load(ep/'trace.npz') as z:y=-z['box'][:,1].astype(float)
 events=[];previous=None
 for row in rows:
  t=row['step']
  if previous and previous['mode'] in ('top_push','top_press') and row['mode'] not in ('top_push','top_press') and row.get('last_recontact_reason')=='incipient_tilt_independent':
   assert tilt[t]>.03
   events.append(dict(step=t,tilt_at_withdrawal_rad=float(tilt[t]),prior_tilt_rad=float(tilt[t-1]),prior_mode=previous['mode'],prior_normal_load_n=previous['contact_load']['observed_vertical_load_n'],max_next10_tilt_under_actual_withdrawal_rad=float(max(tilt[t:min(t+10,len(tilt))])),signed_y_at_withdrawal_mm=float(y[t]*1000),below_hypothetical_threshold={str(v):bool(tilt[t]<=v) for v in [.04,.05,.06,.08]}))
  previous=row
 episodes.append(dict(run=run,configured_withdrawal_rad=threshold,formal_upright_gate_rad=.20,max_observed_tilt_rad=float(max(tilt)),events=events,number_below_hypothetical_threshold={str(v):sum(e['below_hypothetical_threshold'][str(v)] for e in events) for v in [.04,.05,.06,.08]},not_counterfactual_success=True))
 sources.extend(ep/n for n in ['frontal_bypass.json','trace.npz','parcel_orientation.npz','quality.json'])
# Explicitly identify versioned audit work required before any parameter experiment.
blocking=[]
for n in ['audit_box_inward_pose_height.py','audit_micro_clearance_live.py','audit_micro_clearance_return.py']:
 s=(w/n).read_text();lines=[dict(line=i,text=line.strip()) for i,line in enumerate(s.splitlines(),1) if '.03' in line and ('tilt' in line or 'tilted' in line)];blocking.append(dict(file=n,lines=lines));sources.append(w/n)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=episodes,hardcoded_internal_threshold_auditors=blocking,next_candidate_not_selected_or_launched=True,formal_quality_gate_must_remain_rad=.20,source_sha256={str(p):sha(p) for p in sources},training_ready=False)
(r/'TILT_WITHDRAWAL_DIAGNOSTIC.json').write_text(json.dumps(out,indent=2));print(json.dumps([{k:v for k,v in e.items() if k!='events'} for e in episodes],indent=2))
