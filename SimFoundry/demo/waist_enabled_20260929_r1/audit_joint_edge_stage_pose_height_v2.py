"""Independent original height audit outside declared unloaded joint paths.
Declared paths use independent measured/nominal/predicted geometry and actual
commands; their old Cartesian target is metadata, not an executed height.
Does not import the controller. Existing load/tilt, contact, geometry, quality,
RGB and exact loaded-command audits remain separately required. Not admission.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def verify_rows(rows,controls,plan,enabled,verified_events=None):
 verified_events={} if verified_events is None else verified_events
 selected=bool(plan.get('region_approach',{}).get('enabled') and not plan.get('front_route_selected') and not plan.get('initial_top_selected'))
 cfg=plan.get('rear_short_recovery');assert bool(cfg)==bool(enabled and selected)
 if cfg:
  for key,val in dict(enabled=True,initial_travel_z=.91,recontact_travel_z=.86,release_min_z=.91,original_guard_priority=True,selected_rear_region_only=True,loaded_control_unchanged=True).items():assert type(cfg[key]) is type(val) and cfg[key]==val,key
 assert [r['step'] for r in rows]==list(range(1,len(rows)+1))
 count=0;start=None;checked=0;recoveries=[];last_mode=None
 for row in rows:
  t=row['step'];control=controls[t];target=np.asarray(row['target_xyz'],float);tip=np.asarray(row['observed_support_xyz'],float);assert target.shape==tip.shape==(3,) and np.isfinite(target).all() and np.isfinite(tip).all()
  assert np.max(abs(target-np.asarray(control['target_xyz'])))<=2e-6,(t,'expert mapping')
  if not selected:continue
  if 'travel_height_m' not in row:
   assert row['mode'] in ['rear_lift','rear_cross','rear_press','rear_push'],(t,'missing top trace')
   continue
  n=row['recontacts'];assert type(n) is int and n in [count,count+1],(t,'counter')
  if start is None or n>count:start=tip.copy()
  if n>count:
   assert row['last_recontact_reason'] in ['lost_contact','incipient_tilt_independent']
   assert row['mode'] in ['top_lift','top_cross'],(t,'restart bypass')
   recoveries.append(dict(step=t,reason=row['last_recontact_reason']))
  height=.86 if enabled and n else .91
  assert abs(row['travel_height_m']-height)<=1e-9,(t,'height',row['travel_height_m'],height)
  mode=row['mode']
  if mode=='top_lift':assert np.max(abs(target-np.r_[start[:2],max(height,start[2])]))<=2e-6,(t,'lift target')
  if t in verified_events:
   event=verified_events[t];assert event['kind'] in ('command','handover')
   assert mode==('top_press' if event['kind']=='handover' else 'top_cross')
   assert row['recontact_pose_phase']==('measured_handover' if event['kind']=='handover' else 'tracking')
  if mode=='top_cross' and t not in verified_events:
   assert abs(target[2]-height)<=2e-6,(t,'cross height')
   if last_mode!='top_cross':assert tip[2]>=height-.02-2e-6,(t,'cross entry measured height')
  if mode=='top_release':assert target[2]>=.91-2e-6,(t,'release lowered')
  if mode not in ['top_press','top_push']:assert row['contact_load']['applied_z_bias_m']==0,(t,'unloaded force bias')
  checked+=1;count=n;last_mode=mode
 return dict(selected=selected,enabled=bool(enabled and selected),frames=len(rows),height_rows=checked,recontact_events=recoveries)

def audit(ep):
 ep=Path(ep).resolve();prov=json.loads((ep.parent/'provenance.json').read_text());args=prov['args'];assert args['rear_short_recovery'] is True
 assert args['role']=='diagnostic' and not args['policy_port'] and not args['idle']
 for name in ['region_top_approach','rear_cop_centering','rear_joint_edge_analytic_retry','self_clearance_task_ik','expert_frontal_top_guarded_descent','expert_frontal_top_continuous_drag']:assert args[name] is True
 assert args['expert_frontal_top_recovery_clearance_m']==0. and args['expert_top_tilt_recontact_rad']==.03
 for name,h in prov['source_sha256'].items():assert sha(ep.parent/'source_snapshot'/name)==h
 assert any(n.endswith('/collect_paired_sorting.py') for n in prov['source_sha256']) and any(n.endswith('/region_top_contact.py') for n in prov['source_sha256'])
 fr=json.loads((ep/'frontal_bypass.json').read_text());control={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};from audit_joint_edge_stage_pose_live_v2 import inspect as inspect_pose
 pose=inspect_pose(ep);assert pose==json.loads((ep/'JOINT_EDGE_STAGE_POSE_LIVE_V2_AUDIT.json').read_text())
 events={r['step']:{k:v for k,v in r.items() if k!='step'} for r in json.loads((ep/'recontact_pose.json').read_text())['rows'] if r['kind'] in ('command','handover')}
 assert set(events)=={r['step'] for r in pose['records']}
 result=verify_rows(fr['rows'],control,fr['plan'],True,events)
 result['declared_joint_path_frames']=len(events)
 result['pose_audit_sha256']=sha(ep/'JOINT_EDGE_STAGE_POSE_LIVE_V2_AUDIT.json')
 return dict(passed=True,errors=[],**result,source_sha256={name:sha(ep/name) for name in ['raw.npz','frontal_bypass.json','expert_control.json']},provenance_sha256=sha(ep.parent/'provenance.json'),auditor_sha256=sha(__file__),training_ready=False,scope=__doc__)
if __name__=='__main__':
 ep=Path(sys.argv[1]);out=ep/'JOINT_EDGE_STAGE_POSE_HEIGHT_V2_AUDIT.json'
 if out.exists():raise RuntimeError('Refuse to overwrite existing audit; use a new fixture/episode')
 result=audit(ep);out.write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k not in ['source_sha256','recontact_events','scope']})
