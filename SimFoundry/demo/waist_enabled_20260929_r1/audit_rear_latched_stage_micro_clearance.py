"""Source-bound independent direction recontact with declared micro-return exception.
Whole original guards, geometry, COP-waypoint, quality and image audits remain
separate. This report alone is never admission or a dynamics certificate.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from audit_micro_clearance_return import verify_stream
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit(ep):
 ep=Path(ep).resolve();prov=json.loads((ep.parent/'provenance.json').read_text());args=prov['args']
 from rear_corridor_latched_source_binding import verify_observation_binding
 verify_observation_binding(ep)
 assert args['front_micro_repair_retention'] is True and args['front_diagonal_entry'] is True and args['front_direction_recontact'] is True and args['self_clearance_task_ik'] is True
 assert args['role']=='diagnostic' and not args['policy_port'] and not args['idle'] and args['expert_top_tilt_recontact_rad']==.03
 for n,h in prov['source_sha256'].items():assert sha(ep.parent/'source_snapshot'/n)==h
 fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan'];selected=bool(plan.get('front_route_selected'));events=[]
 if selected:
  cfg=plan['front_micro_repair_retention'];assert cfg['enabled'] is True and cfg['maximum_excursion_m']==.005 and cfg['minimum_core_margin_m']==.01 and cfg['minimum_normal_load_n']==.3
  assert cfg['initial_turn_keeps_recontact'] is True and cfg['whole_repair_excursion'] is True and cfg['original_guard_priority'] is True
  for name in ['front_top_route_micro.py','front_cop_route_micro.py','micro_clearance_return.py']:
   assert len([n for n in prov['source_sha256'] if n.endswith('/'+name)])==1
  with np.load(ep/'trace.npz') as z:tr={k:z[k].astype(float) for k in z.files}
  with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k].astype(float) for k in z.files}
  packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
  key='box' if 'push_box' in ep.name else 'mailer';events=verify_stream(fr['rows'],plan,tr,ori,packets,key,True)
 else:
  assert 'front_micro_repair_retention' not in plan and all('direction_change_recontact' not in r for r in fr['rows'])
 files=['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json']
 return dict(passed=True,selected=selected,frames=len(fr['rows']),events=events,retained_returns=sum(x['retained'] for x in events),recontacts=sum(x['restarted'] for x in events),source_sha256={n:sha(ep/n) for n in files},provenance_sha256=sha(ep.parent/'provenance.json'),auditor_sha256=sha(__file__),independent_verifier_sha256=sha(Path(__file__).with_name('audit_micro_clearance_return.py')),training_ready=False,scope=__doc__)
if __name__=='__main__':
 ep=Path(sys.argv[1]);out=audit(ep);(ep/'REAR_LATCHED_STAGE_MICRO_CLEARANCE_AUDIT.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ['events','source_sha256','scope']})
