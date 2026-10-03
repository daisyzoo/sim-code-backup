"""Independent parent COP and material-cap audit, full native/source binding."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from audit_front_loaded_reference_cop_math import reconstruct
from audit_front_loaded_material_cap import MaterialCapAudit
from audit_unloaded_wrist_prior_live import HandModel
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
if __name__=='__main__':
 p=Path(sys.argv[1]).resolve()
 from front_loaded_stage_source_binding import verify_observation_binding
 from front_loaded_stage_audit_context import verified_front_events
 source_binding=verify_observation_binding(p);front_events=verified_front_events(p);cap_result=None
 log=json.loads((p/'frontal_bypass.json').read_text());args=json.loads((p.parent/'provenance.json').read_text())['args'];enabled=args.get('front_cop_route_axis',False) and args.get('front_cop_phase_anchor',False) and args.get('front_cop_slip_following',False) and log['plan'].get('front_route_selected',False);records=[];errors=[]
 if enabled:
  config=log['plan'].get('front_diagonal_entry',{})
  assert bool(config.get('enabled',False))==bool(args.get('front_diagonal_entry',False))
  if config.get('enabled',False):
   assert config['minimum_vertical_load_n']==.3 and config['planning_clearance_m']==args['expert_front_clearance_m'] and config['corner_reserve_m']==.003 and config['table_margin_m']==.005 and config['actual_direction_edge_ray'] and config['original_guard_priority'] and config['original_axis_fallback']
  c=log['plan']['front_cop_slip_following'];assert c['enabled'] and c['route_axis_only'] and c['reset_anchor_on_route_change'] and c['feedback_projection']=='orthogonal_to_current_goal_direction' and type(c['drive_step_m']) in (int,float) and .001<=c['drive_step_m']<=.003 and c['drive_step_m']==args.get('front_cop_drive_step_m',.001) and c['feedback_gain']==.05 and c['max_step_m']==.003 and c['max_reference_lead_m']==.030
  edge=c.get('edge_speed',{})
  assert bool(edge.get('enabled',False))==bool(args.get('front_cop_edge_speed',False))
  if edge.get('enabled',False):
   import ast
   provenance=json.loads((p.parent/'provenance.json').read_text())
   cfg=p.parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py'
   assert hashlib.sha256(cfg.read_bytes()).hexdigest()==provenance['source_sha256']['simfoundry/scene_bridge/isaac_cfg.py']
   node=next(n for n in ast.walk(ast.parse(cfg.read_text())) if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='core_scale' for v in n.targets))
   is_box='push_box' in p.name;scale=ast.literal_eval(node.value.orelse if is_box else node.value.body)
   expected=np.array([.14,.09,.045] if is_box else [.15,.145,.04])*np.array(scale)
   assert np.max(abs(expected-np.asarray(edge['actual_core_size_xyz'])))<1e-7
  with np.load(p/'trace.npz') as z:tr={k:z[k] for k in z.files}
  with np.load(p/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
  packets={x['after_action_step']:x for x in json.loads((p/'solved_contact_forces.json').read_text())['rows']}
  with np.load(p/'raw.npz') as z:q=z['q'][:,12:23].astype(float)
  key='box' if 'push_box' in p.name else 'mailer'
  hand=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json')
  cap_audit=MaterialCapAudit(log['rows'],log['plan'],tr[key],ori[key],packets,key,q,hand,front_events,enabled=args['front_loaded_reference_cap'])
  records,errors=reconstruct(log['rows'],log['plan'],tr,ori,packets,key,material_cap_audit=cap_audit);cap_result=cap_audit.finish()
 else:
  assert all('loaded_reference_cap' not in r for r in log['rows'])
  errors=[[r['step'],'unexpected_COP_trace'] for r in log['rows'] if r.get('cop_slip_following') is not None]
 sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();report=dict(material_cap=cap_result,source_binding=source_binding,dependent_auditors_sha256={str(W/n):hashlib.sha256((W/n).read_bytes()).hexdigest() for n in ['audit_front_loaded_reference_cop_math.py','audit_front_loaded_material_cap.py','front_initial_center_reference_ledger.py','audit_unloaded_wrist_prior_live.py']},passed=not errors,enabled=enabled,errors=errors,records=records,loaded_steps_checked=len(records),source_sha256={f:sha(p/f) for f in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json']},auditor_sha256=sha(__file__),scope='Independent previous-force COP, object pose, front clearance state/goal, phase reset and local anchor, source-bound nominal drive and optional independent raw-COP/core-edge1..nominal governor/correction, independent epigraph LP for diagonal path selection, near-corner goal, actual direction core-edge ray, coupled XY command or unchanged parent axis fallback. Existing control/reference/quality audits required separately. No dynamics or success inference.',training_ready=False);(p/'FRONT_LOADED_STAGE_COP_AUDIT.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k not in {'records','source_sha256'}});sys.exit(0 if report['passed'] else 1)
