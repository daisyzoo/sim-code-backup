"""Label COP intermediates separately from emitted mixed-axis commands."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
p=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();source=p/'FRONT_ROUTE_FEEDBACK_DIAGNOSIS.json';d=json.loads(source.read_text());rows=json.loads((p/'frontal_bypass.json').read_text())['rows'];by={r['step']:r for r in rows};checked=0
for row in rows:
 f=row.get('cop_slip_following',{});mix=f.get('route_axis_control')
 if mix is not None:
  assert np.max(abs(np.array(mix['emitted_xy'])-row['target_xyz'][:2]))<1e-12
  assert mix['active_axis']==(0 if row['route_stage']=='front_x' else 1);checked+=1
for event in d['events']:
 t=event['step'];row=by[t];prev=by[t-1];event['full_cop_delta_before_axis_selection']=event.pop('command_delta_xy',None);event['actual_command_delta_xy']=[row['target_xyz'][i]-prev['target_xyz'][i] for i in range(2)];event['route_axis_control']=row.get('cop_slip_following',{}).get('route_axis_control');event['cop_slip_correction_xy_before_axis_selection']=event.pop('slip_correction_xy',None)
for bout in d['lateral_bouts']:bout['median_unapplied_cop_correction_x_mm']=bout.pop('median_correction_x_mm')
d.update(mixed_output_records_checked=checked,source_feedback_report_sha256=sha(source),adapter_sha256=sha(__file__));d['scope']+=' In this route-axis candidate, lateral COP X correction is not emitted; actual waypoint delta and independent mixed-command auditor must be used. Intermediates explicitly labeled separately.';(p/'ROUTE_AXIS_FEEDBACK_DIAGNOSIS.json').write_text(json.dumps(d,indent=2));print(dict(checked=checked,summary=d['summary']))
