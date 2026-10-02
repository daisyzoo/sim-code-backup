"""Complete declared audit inventory and result recording for pose diagnostics."""
from pathlib import Path
import ast,json,hashlib,subprocess,sys
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
_original=ast.parse((W/'watch_self_clearance_original_controls.py').read_text())
REPORTS=ast.literal_eval(next(n.value for n in ast.walk(_original) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='report_specs' for t in n.targets)))
REPLACEMENTS={'audit_contact_normal_live.py':'audit_terminal_margin_stage_normal_live.py','audit_terminal_hold_inputs.py':'audit_terminal_margin_stage_terminal_inputs.py','audit_initial_near_half_live.py':'audit_terminal_margin_stage_initial_near_half.py'}
for name in REPLACEMENTS:REPORTS.pop(name)
REPORTS.update({
 'audit_terminal_margin_stage_normal_live.py':('TERMINAL_MARGIN_STAGE_NORMAL_LIVE_V2_AUDIT.json',('passed',)),
 'audit_terminal_margin_stage_terminal_inputs.py':('TERMINAL_MARGIN_STAGE_TERMINAL_INPUT_V2_AUDIT.json',('summary','passed')),
 'audit_terminal_margin_stage_initial_near_half.py':('TERMINAL_MARGIN_STAGE_INITIAL_NEAR_HALF_V2_AUDIT.json',('passed',)),
 'audit_terminal_margin_stage_pose_live.py':('TERMINAL_MARGIN_STAGE_POSE_LIVE_V2_AUDIT.json',('passed',)),
 'audit_terminal_margin_stage_self_clearance.py':('TERMINAL_MARGIN_STAGE_SELF_CLEARANCE_V2_AUDIT.json',('episode_clearance_passed',)),
 'audit_terminal_margin_stage_micro_clearance.py':('TERMINAL_MARGIN_STAGE_MICRO_CLEARANCE_AUDIT.json',('passed',)),
 'audit_front_diagonal_entry_live.py':('FRONT_DIAGONAL_ENTRY_LIVE_AUDIT.json',('passed',)),
 'audit_normal_wait.py':('WAIT_STABILITY_AUDIT.json',('passed',)),
 'audit_terminal_margin_stage_region_continuity.py':('TERMINAL_MARGIN_STAGE_REGION_CONTINUITY_V2_AUDIT.json',('passed',)),
 'audit_terminal_margin_stage_region_bounds.py':('TERMINAL_MARGIN_STAGE_REGION_BOUNDS_V2_AUDIT.json',('passed',)),
 'audit_terminal_margin_stage_rear_xy.py':('TERMINAL_MARGIN_STAGE_REAR_XY_V2_AUDIT.json',('passed',)),
 'audit_terminal_margin_stage_pose_height.py':('TERMINAL_MARGIN_STAGE_POSE_HEIGHT_V2_AUDIT.json',('passed',)),
 'audit_terminal_margin_stage_pose_loaded_execution.py':('TERMINAL_MARGIN_STAGE_POSE_LOADED_EXECUTION_V2_AUDIT.json',('passed',)),
 'audit_terminal_margin_stage_task_optimality.py':('TERMINAL_MARGIN_STAGE_TASK_OPTIMALITY_V2_AUDIT.json',('passed',)),
})
ADDITIONAL=['audit_terminal_margin_stage_region_continuity.py','audit_terminal_margin_stage_region_bounds.py','audit_terminal_margin_stage_rear_xy.py','audit_terminal_margin_stage_pose_height.py','audit_front_diagonal_entry_live.py','audit_terminal_margin_stage_pose_loaded_execution.py','audit_terminal_margin_stage_task_optimality.py']
REPORTS['audit_terminal_margin_stage_contacts.py']=('TERMINAL_MARGIN_STAGE_CONTACT_AUDIT.json',('passed',))
REPORTS['audit_terminal_margin_stage_pressure.py']=('TERMINAL_MARGIN_STAGE_PRESSURE_V2_AUDIT.json',('passed',))
def primary(wait):
 return (['audit_terminal_margin_stage_self_clearance.py','audit_normal_wait.py'] if wait else ['audit_terminal_margin_stage_pose_live.py','audit_terminal_margin_stage_self_clearance.py','audit_terminal_margin_stage_micro_clearance.py','audit_front_diagonal_entry_live.py'])
def controls(plan):
 names=['audit_terminal_margin_stage_normal_live.py','audit_terminal_hold_live.py','audit_terminal_margin_stage_terminal_inputs.py','audit_contact_stability_control.py','audit_contact_bout_yaw_live.py','audit_bounded_top_lead_live.py','audit_clearance_feedback_live.py','audit_initial_top_recovery_live.py','audit_terminal_margin_stage_initial_near_half.py']
 if plan.get('initial_top_selected'):names+=['audit_y_path_clearance_live.py']
 if plan.get('front_route_selected'):names+=['audit_front_recovery_height_live.py','audit_recovery_and_anchor.py']
 if plan.get('contact_center_calibration',{}).get('enabled'):names+=['audit_contact_center_live.py','audit_projected_support_live.py']
 return names

def run_audit(ep,script):
 ep=Path(ep);log=ep/(script+'.log');p=subprocess.run([sys.executable,str(W/script),str(ep)],capture_output=True,text=True);log.write_text(p.stdout+'\n'+p.stderr)
 name,keys=REPORTS[script];path=ep/name;passed=False;digest=None
 if path.exists():
  digest=sha(path)
  try:
   value=json.loads(path.read_text())
   for key in keys:value=value[key]
   passed=value is True
  except (KeyError,TypeError,json.JSONDecodeError):pass
 return dict(episode=ep.name,script=script,process_returncode=p.returncode,returncode=p.returncode if p.returncode else (0 if passed else 1),report_passed=passed,report=name,report_sha256=digest,raw_sha256=sha(ep/'raw.npz') if (ep/'raw.npz').exists() else None,auditor_sha256=sha(W/script),log_sha256=sha(log))

REPORTS['audit_terminal_margin_stage_release.py']=('TERMINAL_MARGIN_STAGE_RELEASE_AUDIT.json',('passed',))
