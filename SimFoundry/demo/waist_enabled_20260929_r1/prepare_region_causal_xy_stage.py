"""Isolated XY-only objective wiring; no run launch or data admission."""
from pathlib import Path
import json,hashlib,ast
w=Path(__file__).resolve().parent;parent=w/'staged_region_causal_response';stage=w/'staged_region_causal_xy_response';stage.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();manifest=json.loads((parent/'MANIFEST.json').read_text())
for name,h in manifest['source_sha256'].items():assert sha(parent/name)==h;(stage/name).write_bytes((parent/name).read_bytes())
(stage/'contact_patch_approach.py').write_bytes((w/'staged_causal_xy_objective_probe/contact_patch_approach.py').read_bytes())
def change(file,pairs):
 p=stage/file;s=p.read_text()
 for old,new in pairs:assert s.count(old)==1,(file,old);s=s.replace(old,new)
 ast.parse(s);p.write_text(s)
change('region_approach_lifecycle.py',[
 ('    preferred_core_scale: object=None','    preferred_core_scale: object=None\n    response_centered_xy_objective: bool=False'),
 ('preferred_core_scale=self.preferred_core_scale,command_change_damping=True)','preferred_core_scale=self.preferred_core_scale,command_change_damping=True,response_centered_xy_objective=self.response_centered_xy_objective)'),
 ("command_change_damping=True,scope='Current/past", "command_change_damping=True,response_centered_xy_objective=self.response_centered_xy_objective,scope='Current/past")])
change('collect_paired_sorting.py',[
 ("if args.region_causal_response and not (", "if args.region_causal_xy_response and not args.region_causal_response:\n    parser.error('XY causal objective requires region causal response')\nif args.region_causal_response and not ("),
 ("parser.add_argument('--region-causal-response',action='store_true',help='Diagnostic rear-region causal lag/bias, actual core interior and previous-command damping; default off.')", "parser.add_argument('--region-causal-response',action='store_true',help='Diagnostic rear-region causal lag/bias, actual core interior and previous-command damping; default off.')\nparser.add_argument('--region-causal-xy-response',action='store_true',help='Diagnostic XY-only measured-space objective; requires region-causal-response, default off.')"),
 ('region_extra=dict(causal_decay=decay,preferred_core_scale=core_scale)','region_extra=dict(causal_decay=decay,preferred_core_scale=core_scale,response_centered_xy_objective=args.region_causal_xy_response)'),
 ('core_inset_m=.01,command_change_damping=True,planner_waist_reserve_rad=', 'core_inset_m=.01,command_change_damping=True,response_centered_xy_objective=args.region_causal_xy_response,planner_waist_reserve_rad=')])
(stage/'PREPARATION.json').write_text(json.dumps(dict(status='written_syntax_checked_not_runtime_validated',physical_started=False,source_sha256={name:sha(stage/name) for name in manifest['source_sha256']},parent_manifest_sha256=sha(parent/'MANIFEST.json'),screen_sha256=sha(w/'causal_xy_objective_screen_r1/RESULT.json'),counterfactual_sha256=sha(w/'region_causal_response_groups_r1/case_840001/layout_840001_push_box_to_bin/XY_OBJECTIVE_COUNTERFACTUAL.json'),training_ready=False),indent=2));print(stage)
