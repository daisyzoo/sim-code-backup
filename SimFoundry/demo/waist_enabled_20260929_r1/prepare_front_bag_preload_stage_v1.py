"""Isolate finite front-bag preload wiring; no physics or admission permission."""
from pathlib import Path
import ast,copy,datetime,hashlib,json,shutil
W=Path(__file__).resolve().parent
P=W/'staged_front_effective_height_v1';S=W/'staged_front_bag_preload_hold_v1';D=W/'front_bag_preload_stage_preparation_r1'
assert not S.exists() and not D.exists()
D.mkdir();shutil.copytree(P,S,copy_function=shutil.copy2,ignore=shutil.ignore_patterns('__pycache__'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
parents={str(p):sha(p) for p in P.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
for p,h in parents.items():
 a=Path(p);b=S/a.relative_to(P);assert sha(b)==h and a.stat().st_ino!=b.stat().st_ino
helper='front_bag_preload_waypoint_candidate_v1.py';shutil.copy2(W/helper,S/helper)
f=S/'collect_paired_sorting.py';s=f.read_text()
def replace(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old))
 s=s.replace(old,new)
replace('args = parser.parse_args()\n', '''parser.add_argument('--front-bag-preload-hold', action='store_true', help='Diagnostic finite measured-XY preload for the front left-hand bag only; default off.')
args = parser.parse_args()
if args.front_bag_preload_hold:
    if not (args.role=='diagnostic' and args.front_initial_center_landing and args.front_recontact_center_landing and args.peak_load_bias_guard and args.front_loaded_z_quarter and args.joint_transport_clearance and args.joint_transport_effective_quarter_height and args.front_cop_route_axis and args.self_clearance_task_ik and not args.policy_port and not args.idle and not args.waist_probe and not args.waist_pilot_contract):
        parser.error('Front bag preload requires original effective-quarter diagnostic expert profile, not policy or training collection')
''')
replace('    front_loaded_z_priority_controller = None\n', '''    front_loaded_z_priority_controller = None
    if args.front_bag_preload_hold:
        from front_bag_preload_waypoint_candidate_v1 import FrontBagPreload
        preload_controller = FrontBagPreload(enabled=True)
        preload_waypoint_log = []
        preload_stop = None
''')
replace('    for step in range(horizon):\n', '''    for step in range(horizon):
        if args.front_bag_preload_hold:
            preload_proposal = None
''')
replace("                active_control_offset = waypoint.get('control_offset_local')\n", '''                if args.front_bag_preload_hold:
                    preload_proposal = preload_controller.propose(
                        step=step, selected=bool(frontal_plan.get('front_route_selected')), side=side,
                        row=dict(step=step, **waypoint),
                        previous_waypoint_xy=waypoint.get('cop_slip_following', {}).get('previous_command_xy'),
                        core_size=frontal_plan.get('front_cop_slip_following', {}).get('edge_speed', {}).get('actual_core_size_xyz'),
                        desired_n=frontal_state.load.desired_n, min_bias_m=frontal_state.load.min_bias_m)
                    if preload_proposal['record']['requires_stop']:
                        preload_stop = preload_proposal
                        clearance_failure = dict(step=step, phase='front_bag_preload', reason=preload_proposal['record']['reason'], record=preload_proposal)
                        break
                    waypoint = dict(waypoint, target_xyz=preload_proposal['record']['output_target_xyz'], front_bag_preload_proposal=preload_proposal)
                active_control_offset = waypoint.get('control_offset_local')
''')
replace('        previous = action.copy()\n', '''        if args.front_bag_preload_hold:
            if clearance_guard is None:
                raise ValueError('Preload admission requires original final joint guard')
            if preload_proposal is not None:
                preload_committed_state = preload_controller.commit_after_final_guard(
                    preload_proposal, final_guard=final_clearance,
                    actual_command=action[12:23]+default[12:23], expert_state=frontal_state)
                preload_waypoint_log.append(dict(step=step, proposal=preload_proposal,
                    state_after=preload_committed_state, actual_command=(action[12:23]+default[12:23]).tolist()))
            else:
                preload_waypoint_log.append(dict(step=step, proposal=None,
                    reason='no_frontal_waypoint_first_frame_or_wait',
                    state_after=dict(preload_controller.state), actual_command=(action[12:23]+default[12:23]).tolist()))
        previous = action.copy()
''')
replace("    if args.front_corridor_midpoint_replan:\n        episode.collect_meta", '''    if args.front_bag_preload_hold:
        episode.collect_meta['front_bag_preload_hold'] = dict(
            version='front_bag_preload_hold_v1', enabled=True,
            selected='front_route_left_hand_bag_only', maximum_hold_frames=24,
            observed_and_filtered_load_ready_n=4., consecutive_ready_frames=3,
            desired_pressure_n=5., original_minimum_pressure_bias_m=-.006,
            original_z_preserved=True, waypoint_slew_m=.003,
            stationary_hand_or_force_guarantee=False, training_ready=False,
            applied_hold_frames=sum(r['proposal'] is not None and r['proposal']['record']['kind']=='hold' for r in preload_waypoint_log))
    if args.front_corridor_midpoint_replan:
        episode.collect_meta''')
replace("    (folder / 'quality.json').write_text(json.dumps(report, indent=2))\n", '''    if args.front_bag_preload_hold:
        if len(preload_waypoint_log)!=len(qs):
            raise ValueError('Preload admitted log must cover every executed action')
        (folder/'front_bag_preload_hold.json').write_text(json.dumps(dict(
            rows=preload_waypoint_log, pending_unexecuted_proposal=preload_controller.pending,
            stop=preload_stop, executed_action_count=len(qs), training_ready=False,
            scope='Changed Cartesian goal enters original complete joint solve; final guard precedes state commit. Physical force not certified.'), indent=2))
    (folder / 'quality.json').write_text(json.dumps(report, indent=2))
''')
replace('    for path in paths:\n', '''    if args.front_bag_preload_hold:
        paths.append(STAGE/'front_bag_preload_waypoint_candidate_v1.py')
    for path in paths:
''')
compile(s,str(f),'exec');f.write_text(s)
class Strip(ast.NodeTransformer):
 def visit_If(self,n):
  if 'args.front_bag_preload_hold' in ast.unparse(n.test):return None
  return self.generic_visit(n)
 def visit_Expr(self,n):
  if isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='parser.add_argument' and n.value.args and isinstance(n.value.args[0],ast.Constant) and n.value.args[0].value=='--front-bag-preload-hold':return None
  return self.generic_visit(n)
assert ast.dump(Strip().visit(copy.deepcopy(ast.parse(s))),include_attributes=False)==ast.dump(ast.parse((P/f.name).read_text()),include_attributes=False)
for p,h in parents.items():assert sha(p)==h
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,parent_stage=str(P),stage=str(S),defaultoff_exact_parent_ast=True,independent_inodes=True,helper_byte_exact=sha(S/helper)==sha(W/helper),parent_source_sha256=parents,stage_source_sha256={str(p):sha(p) for p in S.rglob('*') if p.is_file() and '__pycache__' not in p.parts},physical_launch_allowed=False,training_ready=False,remaining=['Actual parser positive/negative protocol checks','Native collector target/commit/stop/save/archive execution tests including wait and default-off','Independent sequential preload state and actual task binding audit','Original complete consumers and full condition physical plan'])
(D/'STAGE_PREPARATION.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k] for k in ['passed','stage','defaultoff_exact_parent_ast','helper_byte_exact','physical_launch_allowed']}))
