"""Screen current-contact window on all8 uncapped parent push observations.
Only exact prefix up to first changed advice is shared with a future candidate.
All later states remain observations of the old policy, never candidate rollouts.
Controls with no actual first-front capture remain explicitly inapplicable.
"""
from pathlib import Path
import json,datetime,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;R=W/'front_initial_physical_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};reports=[]
protocol=json.loads((R/'PROTOCOL.json').read_text());sources[str(R/'PROTOCOL.json')]=sha(R/'PROTOCOL.json')
for item in protocol['plan']['commands']:
 if item['wait']:continue
 for task in item['tasks']:
  ep=R/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}"
  def read(n):sources[str(ep/n)]=sha(ep/n);return json.loads((ep/n).read_text())
  fr=read('frontal_bypass.json');front=read('front_initial_center.json');quality=read('quality.json');assert quality['frames']==1200
  events=[r for r in front['rows'] if r['kind']=='handover'];assert len(events)<=1
  if not events:
   reports.append(dict(episode=ep.name,original_quality_passed=quality['passed'],selected=front['selected'],actual_capture=False,eligible_rows=0,first_intervention=None,training_ready=False));continue
  capture=events[0]['step'];key='box' if task=='push_box_to_bin' else 'mailer';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer'
  with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
  with np.load(ep/'trace.npz') as z:xyz=z[key].copy()
  packets={r['after_action_step']:r for r in read('solved_contact_forces.json')['rows']};by_step={r['step']:r for r in fr['rows']};records=[]
  for row in fr['rows']:
   t=row['step']
   if t<capture or row['mode']!='top_push' or row.get('route_stop_reason') or row.get('release_reason'):continue
   weights=[];positions=[]
   for c in packets[t-1]['parcel_contacts']:
    slots=[i for i,label in enumerate(c['shapes']) if '/'+actor+'/' in label]
    if len(slots)!=1 or not any(side+'_wrist' in label for label in c['shapes']):continue
    force=np.asarray(c['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(force@rot[t,:,2])
    if load>.05:weights.append(load);positions.append(c['position_world'])
   if sum(weights)<.3:continue
   cop=np.average(positions,axis=0,weights=weights);assert np.max(abs(rot[t].T@(cop-xyz[t])-row['cop_slip_following']['measured_cop_local']))<=2e-6
   previous=np.asarray(by_step[t-1]['target_xyz'][:2]);parent=np.asarray(row['target_xyz'][:2]);reference=np.asarray(row['observed_support_xyz'][:2]);assert np.max(abs(parent-previous))<=.003+1e-10
   lower=np.maximum.reduce([previous-.003,reference-.030,cop[:2]-.010]);upper=np.minimum.reduce([previous+.003,reference+.030,cop[:2]+.010]);feasible=bool(np.all(lower<=upper));command=np.clip(parent,lower,upper) if feasible else None;changed=not feasible or bool(np.max(abs(command-parent))>1e-12);drive=np.asarray(row['cop_slip_following']['drive_direction_xy'])
   records.append(dict(step=t,feasible=feasible,changed=changed,actual_parent_xy=parent.tolist(),actual_previous_xy=previous.tolist(),current_cop_world=cop.tolist(),parent_contact_lead_xy_mm=((parent-cop[:2])*1000).tolist(),candidate_xy=None if command is None else command.tolist(),parent_drive_mm=float((parent-previous)@drive)*1000,candidate_drive_mm=None if command is None else float((command-previous)@drive)*1000))
  first=next((r for r in records if r['changed']),None)
  exits=[dict(step=r['step'],reason=r.get('last_recontact_reason')) for r in fr['rows'] if r.get('recontacts',0)>by_step.get(r['step']-1,{}).get('recontacts',0)]
  reports.append(dict(episode=ep.name,original_quality_passed=quality['passed'],selected=front['selected'],actual_capture=True,capture_step=capture,eligible_rows=len(records),changed_rows_on_old_observations=sum(r['changed'] for r in records),infeasible_rows_on_old_observations=sum(not r['feasible'] for r in records),first_intervention=first,old_recontact_exits=exits,records=records,training_ready=False))
  for name in ['trace.npz','parcel_orientation.npz']:sources[str(ep/name)]=sha(ep/name)
assert len(reports)==8;sources[str(Path(__file__))]=sha(__file__);out=W/'FRONT_CONTACT_WINDOW_PARENT_FULL8_PROBE.json';assert not out.exists();out.write_text(json.dumps(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,conditions=8,episodes=reports,source_sha256=sources,controller_implemented=False,physical_success_proven=False,training_ready=False),indent=2));print(json.dumps([{k:v for k,v in r.items() if k not in ['records','old_recontact_exits']} for r in reports],indent=2))
