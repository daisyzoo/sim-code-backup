"""Independent direction-change eligibility from recorded prior mode and forces.
Does not import new controller or its helper. Original route/force/recovery,
final-action geometry, task quality and sampled visual audits stay separate.
"""
from pathlib import Path
import sys,json,hashlib,math
import numpy as np
from scipy.spatial.transform import Rotation

def verify_event(row,previous_stage,previous_mode,load,initial_y,observed_y,direction,quat,tilt_threshold,previous_recontacts):
 e=row['direction_change_recontact'];assert type(e['restarted']) is bool
 terminal=direction*observed_y>=max(.205,direction*initial_y+.16)
 tilt=math.acos(float(np.clip(Rotation.from_quat(quat).as_matrix()[2,2],-1,1)))
 tilted=bool(tilt_threshold and tilt>tilt_threshold);changed=previous_stage!=row['route_stage']
 expected=bool(changed and previous_mode=='top_push' and load>=.3 and not terminal and not tilted)
 assert e['previous_stage']==previous_stage and e['current_stage']==row['route_stage'] and e['previous_top_mode']==previous_mode
 assert abs(e['measured_vertical_load_n']-load)<1e-9 and e['stage_changed']==changed
 assert e['terminal_precedence']==bool(terminal) and e['tilt_precedence']==tilted and e['restarted']==expected
 if expected:
  assert row['mode'] in ['top_lift','top_cross'] and row['last_recontact_reason']=='front_route_direction_change'
  assert row['recontacts']==previous_recontacts+1 and row['contact_load']['applied_z_bias_m']==0
  assert not row['cop_slip_following']['override']
  if row['mode']=='top_lift':assert np.max(abs(np.array(row['target_xyz'][:2])-row['observed_support_xyz'][:2]))<2e-7
 return expected

def audit(ep):
 ep=Path(ep).resolve();prov=json.loads((ep.parent/'provenance.json').read_text());args=prov['args'];assert args['front_direction_recontact'] and args['self_clearance_task_ik'] and args['role']=='diagnostic' and not args['policy_port']
 sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
 for n,h in prov['source_sha256'].items():assert sha(ep.parent/'source_snapshot'/n)==h
 fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan'];selected=bool(plan.get('front_route_selected'));events=[]
 if not selected:assert not plan.get('front_direction_recontact') and all('direction_change_recontact' not in row for row in fr['rows'])
 else:
  assert plan['front_direction_recontact']['enabled'];assert args['expert_top_tilt_recontact_rad']==.03
  side='right' if ep.name.endswith('push_box_to_bin') else 'left';key='box' if side=='right' else 'mailer';actor='parcel_box' if side=='right' else 'mailer';direction=-1 if side=='right' else 1
  packets={x['after_action_step']:x for x in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
  with np.load(ep/'trace.npz') as z:xyz=z[key].copy()
  with np.load(ep/'parcel_orientation.npz') as z:quats=z[key].copy()
  previous_stage='front_x';previous_mode='top_lift';previous_recontacts=0;latched=False
  for row in fr['rows']:
   t=row['step'];packet=packets[t-1];assert np.max(abs(np.array(packet['post_action_pose'][key])-xyz[t]))<1e-6
   if row.get('route_stop_reason'):
    assert 'direction_change_recontact' not in row and row['mode']=='front_guard_lift';latched=True;continue
   assert not latched
   load=sum(abs(float(c['force_world_N'][2])) for c in packet['parcel_contacts'] if any(side+'_wrist_roll' in label for label in c['shapes']) and any('/'+actor+'/' in label for label in c['shapes']))
   expected=verify_event(row,previous_stage,previous_mode,load,plan['initial_target_xyz'][1],xyz[t,1],direction,quats[t],args['expert_top_tilt_recontact_rad'],previous_recontacts)
   if expected:events.append(dict(step=t,load_n=load,mode=row['mode'],route_stage=row['route_stage']))
   previous_stage=row['route_stage'];previous_mode=row['mode'];previous_recontacts=row['recontacts']
 files=['frontal_bypass.json','raw.npz','trace.npz','parcel_orientation.npz','solved_contact_forces.json']
 return dict(passed=True,selected=selected,events=events,frames=len(fr['rows']),source_sha256={n:sha(ep/n) for n in files},auditor_sha256=sha(__file__),training_ready=False,scope=__doc__)
if __name__=='__main__':
 ep=Path(sys.argv[1]);out=audit(ep);(ep/'DIRECTION_RECONTACT_LIVE_AUDIT.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ['source_sha256','scope']})
