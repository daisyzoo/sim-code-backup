"""Prepare isolated default-off entry lift candidate; never freeze/launch physics."""
from pathlib import Path
import json,hashlib,ast,datetime
w=Path(__file__).resolve().parent;parent=w/'staged_box_center_preference';stage=w/'staged_box_entry_lift';assert not stage.exists();stage.mkdir();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p in [*parent.glob('*.py'),parent/'causal_response_parameters.json',parent/'elbow_torso_hulls.json']:(stage/p.name).write_bytes(p.read_bytes())
for name in ['box_recovery_entry_lift.py','box_entry_lift_recontact_guarded.py']:(stage/name).write_bytes((w/name).read_bytes())
p=stage/'collect_paired_sorting.py';s=p.read_text()
s=s.replace("parser.add_argument('--rear-box-center-preference'", "parser.add_argument('--rear-box-entry-lift',action='store_true',help='Default-off rear-box unloaded lift before original center recontact; shared240 recovery ticks.')\nparser.add_argument('--rear-box-center-preference'",1)
s=s.replace('args = parser.parse_args()','args = parser.parse_args()\nif args.rear_box_entry_lift and not (args.rear_box_center_preference and args.role==\'diagnostic\'):\n    parser.error(\'Box entry lift requires complete box-center diagnostic\')',1)
line="        recontact_lifecycle=RecontactLifecycle(enabled=True,prefer_interior=args.recontact_interior_preference,**recontact_extra)"
assert s.count(line)==1;s=s.replace(line,"        if args.rear_box_entry_lift and side=='right':\n            from box_entry_lift_recontact_guarded import RecontactLifecycle\n            recontact_extra['entry_lift']=True\n"+line)
line="                            frontal_plan['unloaded_recontact_pose']['box_center_preference']=dict(enabled=True,center_weight_per_m2=400.,parent='same_observation_minimum_motion',side='right',original_fallback=True,original_constraints_unchanged=True)"
assert s.count(line)==1;s=s.replace(line,line+"\n                        if args.rear_box_entry_lift and side=='right':\n                            frontal_plan['unloaded_recontact_pose']['entry_lift']=dict(enabled=True,side='right',original_entry_height_m=.84,nominal_lift_height_m=.845,measured_ready_frames=3,maximum_lift_ticks=40,combined_maximum_ticks=240,measured_unloaded_required=True,phase_boundary_guards=True,training_ready=False)")
line="    if args.rear_box_center_preference:\n        episode.collect_meta['rear_box_center_preference']=True";assert s.count(line)==1;s=s.replace(line,line+"\n    if args.rear_box_entry_lift:\n        episode.collect_meta['rear_box_entry_lift']=True")
line="    if args.rear_box_center_preference:\n        paths.append(STAGE/'box_center_preference_plan.py')";assert s.count(line)==1;s=s.replace(line,line+"\n    if args.rear_box_entry_lift:\n        paths.extend([STAGE/'box_recovery_entry_lift.py',STAGE/'box_entry_lift_recontact_guarded.py'])")
ast.parse(s);p.write_text(s)
manifest=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent=str(parent),new_stage=str(stage),changed_existing_files={'collect_paired_sorting.py':dict(parent_sha256=sha(parent/p.name),new_sha256=sha(p))},new_helpers={n:sha(stage/n) for n in ['box_recovery_entry_lift.py','box_entry_lift_recontact_guarded.py']},scope=__doc__,training_ready=False);(stage/'CHANGE_MANIFEST.json').write_text(json.dumps(manifest,indent=2));print('prepared_not_frozen_not_launched',stage)
