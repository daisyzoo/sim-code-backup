"""Original action/residual audit plus independent region press/push XY audit."""
from pathlib import Path
import sys,json,subprocess,hashlib
import numpy as np
w=Path(__file__).resolve().parent;p=Path(sys.argv[1]).resolve();subprocess.run([sys.executable,str(w/'audit_joint_edge_stage_region_causal_v2.py'),str(p)],check=True,stdout=subprocess.DEVNULL)
log=json.loads((p/'frontal_bypass.json').read_text());plan=log['plan'];rows={r['step']:r for r in log['rows']};region_path=p/'region_approach.json';records=[];errors=[]
from box_inward_step_contract import declared_step
drag_step=declared_step(plan)
if region_path.exists():
 config=plan['region_approach'];assert config['predicted_minimum_gap_linear_m']==.0042 and config['press_push_xy_initialization']=='previous_command_when_selected_region'
 region=json.loads(region_path.read_text())['rows'];first=next((r['step'] for r in region if r['solver'] and r['solver'].get('handover')),None)
 if first is not None:
  for t,row in rows.items():
   prev=rows.get(t-1)
   if t<=first or row['mode']!='top_push' or not prev or prev['mode']!='top_press':continue
   direction=plan['direction'];base=np.asarray(prev['target_xyz'],float);tip=np.asarray(row['observed_support_xyz'],float);surface=np.asarray(row['parcel_top_xyz'],float);goalx=row['push_x_anchor_m'];assert goalx is not None
   expected=np.array([base[0]+np.clip(goalx-base[0],-.002,.002),base[1]+np.clip(direction*min(.34,direction*base[1]+drag_step)-base[1],-drag_step,drag_step),tip[2]+np.clip(surface[2]+.002+row['contact_load']['applied_z_bias_m']-tip[2],-.001,.001)])
   actual=np.asarray(row['target_xyz']);error=float(np.max(abs(expected-actual)))
   if error>2e-6:errors.append([t,'press_push_waypoint_continuity',error])
   records.append(dict(step=t,previous_command_xyz=base.tolist(),actual_command_xyz=actual.tolist(),reconstruction_error_m=error,observed_load_n=row['contact_load']['observed_vertical_load_n']))
a=json.loads((p/'JOINT_EDGE_STAGE_REGION_CAUSAL_AUDIT.json').read_text());assert a['passed']
report=dict(passed=not errors,errors=errors,region_selected=region_path.exists(),transitions_checked=len(records),records=records,raw_sha256=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest(),causal_audit_sha256=hashlib.sha256((p/'JOINT_EDGE_STAGE_REGION_CAUSAL_AUDIT.json').read_bytes()).hexdigest(),auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Recorded region-only first-push command independently reconstructed from prior press command, unchanged X2mm and declared rear Y increment and original measured-tip Z initialization. Original raw action, causal residual and forecast audit required. Does not certify sustained contact or task/visual success.',training_ready=False)
(p/'JOINT_EDGE_STAGE_REGION_CONTINUITY_V2_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2));sys.exit(0 if report['passed'] else 1)
