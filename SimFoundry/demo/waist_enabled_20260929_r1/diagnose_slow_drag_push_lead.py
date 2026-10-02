"""Observed rear-box pre-exit command error and last-substep contact force.
Virtual task-point tracking error is NOT physical slip or a causal force model.
"""
from pathlib import Path
import json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;r=w/'rear_slow_drag_groups_r1';ep=r/'case_840001/layout_840001_push_box_to_bin';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
fr={x['step']:x for x in json.loads((ep/'frontal_bypass.json').read_text())['rows']};source=r/'CONTACT_WRENCH_DIAGNOSTIC.json';wr=next(x for x in json.loads(source.read_text())['episodes'] if x['run']==r.name and x['episode']==ep.name);rows=[]
for b in wr['bouts']:
 if not b['last_loaded']:continue
 loaded=b['last_loaded'];t=loaded['step'];f=fr[t];force=np.array(loaded['groups']['active_hand']['force_world_n']);error=-1000*(f['target_xyz'][1]-f['observed_support_xyz'][1])
 rows.append(dict(start=b['start'],end=b['end'],last_loaded_step=t,exit_reason=b['exit_reason'],push_frames=b['end']-b['start']+1,virtual_task_point_y_error_mm=error,horizontal_hand_force_n=float(np.linalg.norm(force[:2])),downward_hand_force_n=float(-force[2])))
tilt=[x for x in rows if x['exit_reason']=='incipient_tilt_independent']
summary={key:dict(min=float(min(x[key] for x in tilt)),median=float(np.median([x[key] for x in tilt])),max=float(max(x[key] for x in tilt))) for key in ['push_frames','virtual_task_point_y_error_mm','horizontal_hand_force_n','downward_hand_force_n']}
report=dict(scope=__doc__,rows=rows,tilt_summary=summary,declared_drag_step_m=.0015,source_sha256={str(p):sha(p) for p in [Path(__file__),source,ep/'frontal_bypass.json',ep/'solved_contact_forces.json']},hypothesis='Test reduced forward reference increment as a separate physical ablation while retaining5N, all layouts, budgets, controller geometry and quality gates. This report alone cannot predict lower tipping or net task gain.',training_ready=False)
(r/'PUSH_LEAD_DIAGNOSTIC.json').write_text(json.dumps(report,indent=2));print(json.dumps(summary,indent=2))
