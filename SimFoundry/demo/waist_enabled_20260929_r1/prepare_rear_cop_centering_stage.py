"""Prepare default-off rear-only collector; do not install or launch physics."""
from pathlib import Path
import ast,hashlib,json
w=Path(__file__).resolve().parent
parent=w/'staged_region_causal_xy_diagnostics';probe=w/'staged_rear_cop_centering_probe';dst=w/'staged_rear_cop_centering'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((parent/'MANIFEST.json').read_text())
for name,h in manifest['source_sha256'].items():assert sha(parent/name)==h
for filename in ['CHECK.json','LIFECYCLE_CHECK.json']:
 check=json.loads((probe/filename).read_text());assert check['passed']
 if filename=='CHECK.json':assert check['candidate_sha256']==sha(probe/'rear_cop_centering.py')
 else:
  for p,h in check['source_sha256'].items():assert sha(Path(p))==h
dst.mkdir(exist_ok=False)
for name in manifest['source_sha256']:(dst/name).write_bytes((parent/name).read_bytes())
for name in ['rear_cop_centering.py','rear_cop_route.py']:(dst/name).write_bytes((probe/name).read_bytes())
p=dst/'collect_paired_sorting.py';s=p.read_text()
def replace(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old))
 s=s.replace(old,new)
replace("parser.add_argument('--region-causal-xy-response',", "parser.add_argument('--rear-cop-centering', action='store_true', help='Diagnostic rear-region loaded X-only measured COP centering; default off.')\nparser.add_argument('--region-causal-xy-response',")
replace('args = parser.parse_args()', '''args = parser.parse_args()
if args.rear_cop_centering and not (args.region_causal_xy_response and args.trace_solved_contact_forces and args.expert_frontal_top_drag_step_m==.003 and args.expert_top_hold_established_x and not args.expert_frontal_top_cross_admittance and not args.expert_frontal_top_hold_push_x):
    parser.error('Rear COP requires causal XY region, traced original3mm continuous drag and established X hold without competing transverse controllers')''')
replace('                    region_approach = RegionApproachLifecycle(**region_extra)', '''                    if args.rear_cop_centering:
                        from rear_cop_route import RearCopRouteState
                        top_cls = RearCopRouteState
                        top_extra.update(rear_cop_enabled=True, rear_cop_core_size=tuple(actual_core['collision_core_size_xyz']))
                        frontal_plan['rear_cop_centering']=dict(enabled=True,actual_core_size_xyz=list(actual_core['collision_core_size_xyz']),core_inset_m=.01,feedback_gain=.05,max_x_step_m=.002,max_reference_x_lead_m=.030,preserve_first_loaded_push=True,measured_contact_packet='previous_solved_substep',parent_yz_unchanged=True,original_guard_priority=True)
                    region_approach = RegionApproachLifecycle(**region_extra)''')
replace('                center_measurement = None', '''                if args.rear_cop_centering and region_approach is not None:
                    from simfoundry.data.top_contact_load_geometry import loaded_forward_margin
                    point_kwargs['slip_contact']=loaded_forward_margin(solved_contact_forces[-1] if solved_contact_forces else None,side,target_actor,parcel_xyz(env,target_actor),target_quat,frontal_state.size,-1 if side=='right' else 1)
                center_measurement = None''')
old="'contact_slip_following.py','causal_unloaded_response.py','causal_response_parameters.json']])"
replace(old,"'contact_slip_following.py','causal_unloaded_response.py','causal_response_parameters.json','rear_cop_centering.py','rear_cop_route.py']])")
p.write_text(s)
for path in dst.glob('*.py'):ast.parse(path.read_text())
source_names=[*manifest['source_sha256'],'rear_cop_centering.py','rear_cop_route.py']
report=dict(parent_manifest_sha256=sha(parent/'MANIFEST.json'),source_sha256={n:sha(dst/n) for n in source_names},probe_checks_sha256={n:sha(probe/n) for n in ['CHECK.json','LIFECYCLE_CHECK.json']},collector_wired_in_source=True,cli_checked=False,actual_wiring_checked=False,physical_started=False,training_ready=False,scope='Default-off rear-only X correction after original state update. Frozen parent8helpers unchanged,2new helpers,collector parser/selection/measurement/archive edits only. Release-margin probe not included. Requires real CLI, source, collector wiring and independent actual-command audit checks before any launch.')
(dst/'PREPARATION.json').write_text(json.dumps(report,indent=2));print(dst)
