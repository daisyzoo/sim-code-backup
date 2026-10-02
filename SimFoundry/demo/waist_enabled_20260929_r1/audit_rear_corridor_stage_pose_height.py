from pathlib import Path
import sys,json,hashlib
from rear_corridor_height_reconstruction import verify_rows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def audit(ep):
 ep=Path(ep).resolve();prov=json.loads((ep.parent/'provenance.json').read_text());args=prov['args'];assert args['rear_short_recovery'] is True
 assert args['role']=='diagnostic' and not args['policy_port'] and not args['idle']
 for name in ['region_top_approach','rear_cop_centering','rear_joint_edge_analytic_retry','self_clearance_task_ik','expert_frontal_top_guarded_descent','expert_frontal_top_continuous_drag']:assert args[name] is True
 assert args['expert_frontal_top_recovery_clearance_m']==0. and args['expert_top_tilt_recontact_rad']==.03
 for name,h in prov['source_sha256'].items():assert sha(ep.parent/'source_snapshot'/name)==h
 assert any(n.endswith('/collect_paired_sorting.py') for n in prov['source_sha256']) and any(n.endswith('/region_top_contact.py') for n in prov['source_sha256'])
 fr=json.loads((ep/'frontal_bypass.json').read_text());control={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};from audit_rear_corridor_stage_pose_live import inspect as inspect_pose
 pose=inspect_pose(ep);assert pose==json.loads((ep/'REAR_CORRIDOR_STAGE_POSE_LIVE_AUDIT.json').read_text())
 events={r['step']:{k:v for k,v in r.items() if k!='step'} for r in json.loads((ep/'recontact_pose.json').read_text())['rows'] if r['kind'] in ('command','handover')}
 assert set(events)=={r['step'] for r in pose['records']}
 from rear_corridor_audit_inputs import verify_inputs
 w=Path(__file__).resolve().parent;recovery=verify_inputs(ep,w.parents[1],w/'staged_rear_corridor_recovery_guarded')
 result=verify_rows(fr['rows'],control,fr['plan'],True,events,recovery.overrides);recovery.assert_unchanged()
 result['declared_joint_path_frames']=len(events)
 result['pose_audit_sha256']=sha(ep/'REAR_CORRIDOR_STAGE_POSE_LIVE_AUDIT.json')
 return dict(passed=True,errors=[],**result,source_sha256={name:sha(ep/name) for name in ['raw.npz','frontal_bypass.json','expert_control.json']},provenance_sha256=sha(ep.parent/'provenance.json'),auditor_sha256=sha(__file__),training_ready=False,scope=__doc__)
if __name__=='__main__':
 ep=Path(sys.argv[1]);out=ep/'REAR_CORRIDOR_STAGE_POSE_HEIGHT_AUDIT.json'
 if out.exists():raise RuntimeError('Refuse to overwrite existing audit; use a new fixture/episode')
 result=audit(ep);out.write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k not in ['source_sha256','recontact_events','scope']})
