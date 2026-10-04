"""Explicit-defaultoff independent collector stage; no physical launch."""
from pathlib import Path
import ast,copy,datetime,hashlib,json,shutil
W=Path(__file__).resolve().parent;P=W/'staged_front_effective_height_v1';S=W/'staged_front_normal_nondegradation_v2';D=W/'front_normal_preparation_r2';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert not S.exists() and not D.exists();D.mkdir();shutil.copytree(P,S,copy_function=shutil.copy2,ignore=shutil.ignore_patterns('__pycache__'))
parents={str(p):sha(p) for p in P.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
for p,h in parents.items():
 a=Path(p);b=S/a.relative_to(P);assert sha(b)==h and a.stat().st_ino!=b.stat().st_ino
helpers=['front_normal_nondegradation_runtime_candidate_v1.py','front_normal_nondegradation_solver_candidate_v1.py','audit_front_exact_normal_planning_v1.py','independent_cross_track_assets_v1.py','audit_unloaded_wrist_prior_live.py']
for name in helpers:
 src=W/name;dst=S/name
 if dst.exists():assert sha(dst)==sha(src),name
 else:shutil.copy2(src,dst)
flag='front_normal_nondegradation';cli='--front-normal-nondegradation';p=S/'collect_paired_sorting.py';s=p.read_text()
anchor="parser.add_argument('--joint-transport-effective-quarter-height'";pos=s.index(anchor);s=s[:pos]+"parser.add_argument('--front-normal-nondegradation',action='store_true',help='Diagnostic exact-normal planning with nominal/predicted XY directions and original forecast nondegradation; verified measured-position hold requests original recovery. Default off.')\n"+s[pos:]
anchor='if args.joint_transport_effective_quarter_height and not (';pos=s.index(anchor);s=s[:pos]+"if args.front_normal_nondegradation and not (args.role=='diagnostic' and args.joint_transport_clearance and args.joint_transport_effective_quarter_height and args.front_loaded_z_quarter and args.self_clearance_task_ik and args.front_cop_route_axis and not args.policy_port and not args.idle and not args.waist_probe and not args.waist_pilot_contract):\n    parser.error('Cross-track refinement requires original diagnostic quarter-height, captured front route and final clearance pipeline')\n"+s[pos:]
anchor='    joint_transport_log = []\n';assert s.count(anchor)==1;s=s.replace(anchor,anchor+"    if args.front_normal_nondegradation:\n        from front_normal_nondegradation_runtime_candidate_v1 import FrontNormalNondegradation\n        normal_planning_controller=FrontNormalNondegradation(clearance_guard,ROOT,STAGE,enabled=True)\n        normal_planning_log=[]\n")
anchor='        if clearance_guard is not None:\n            final_clearance =';assert s.count(anchor)==1
block='''        if args.front_normal_nondegradation:
            normal_command,normal_record=normal_planning_controller.refine(step=step,selected=transport_selected,side=side,row=transport_row,coordinate=coordination_log[-1] if coordination_log and coordination_log[-1]['step']==step else None,scene=transport_scene,current=transport_current,previous_q=transport_previous_q,previous_command=previous[12:23],parent_command=action[12:23],decay=transport_decay)
            normal_planning_log.append(normal_record)
            if coordination_log and coordination_log[-1]['step']==step:
                coordination_log[-1]['front_normal_nondegradation']=normal_record
            if normal_command is None:
                clearance_failure=dict(step=step,phase='front_normal_planning',reason='normal_planning_no_verified_command',record=normal_record)
                break
            action[12:23]=normal_command
            if normal_record['applied']:
                coordination_log[-1]['normal_planning_unexecuted_parent_waist_target_rad']=coordination_log[-1]['waist_target_rad']
                coordination_log[-1]['waist_target_rad']=float(normal_command[0])
'''
s=s.replace(anchor,block+anchor)
anchor='        previous = action.copy()\n';assert s.count(anchor)==1
recovery_block="""        if args.front_normal_nondegradation and normal_record.get('requires_recovery'):
            from front_normal_nondegradation_runtime_candidate_v1 import commit_original_recovery
            commit_original_recovery(normal_record,frontal_state,final_clearance)
"""
s=s.replace(anchor,recovery_block+anchor)
anchor='    if args.front_loaded_z_quarter:\n        episode.collect_meta';pos=s.index(anchor);s=s[:pos]+"    if args.front_normal_nondegradation:\n        episode.collect_meta['front_normal_nondegradation']=dict(version='front_normal_nondegradation_v1',planning_policy='exact_normal_parent_to_zero_and_original_forecast_nondegradation_v1',measured_hold_then_original_recovery=True,mode='top_push',route_stage='lateral_y',stationarity_max=1e-6,rounding_tolerance_m=2e-7,failed_refinement_stops_before_emission=True,training_ready=False)\n        episode.collect_meta['front_normal_planning_applied_frames']=sum(r['applied'] for r in normal_planning_log)\n"+s[pos:]
anchor="        (folder/'joint_transport_clearance.json').write_text";start=s.index(anchor);end=s.index('\n',start)+1;s=s[:end]+"    if args.front_normal_nondegradation:\n        (folder/'front_normal_nondegradation.json').write_text(json.dumps(dict(rows=normal_planning_log,training_ready=False),indent=2))\n"+s[end:]
anchor='    for path in paths:\n';assert s.count(anchor)==1;s=s.replace(anchor,"    if args.front_normal_nondegradation:\n        paths.extend([STAGE/name for name in "+repr(helpers)+"])\n"+anchor);p.write_text(s)
class Strip(ast.NodeTransformer):
 def visit_If(self,n):
  if 'args.'+flag in ast.unparse(n.test):return None
  return self.generic_visit(n)
 def visit_Expr(self,n):
  if isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='parser.add_argument' and n.value.args and isinstance(n.value.args[0],ast.Constant) and n.value.args[0].value==cli:return None
  return self.generic_visit(n)
assert ast.dump(Strip().visit(copy.deepcopy(ast.parse(s))),include_attributes=False)==ast.dump(ast.parse((P/'collect_paired_sorting.py').read_text()),include_attributes=False)
for p,h in parents.items():assert sha(p)==h,p
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent_stage=str(P),stage=str(S),helpers=helpers,parent_sources_sha256=parents,stage_sources_sha256={str(p):sha(p) for p in S.rglob('*') if p.is_file() and '__pycache__' not in p.parts},defaultoff_exact_parent_ast=True,independent_inodes=True,collector_cli=cli,physical_launch_allowed=False,training_ready=False,remaining=['Actual six-command parser and invalid prerequisites','Actual32loaded candidates and2unloaded recovery requests independently reviewed','Native command assignment/waist/final guard/history and rejection before emission','Full defaultoff/enabled source and original audit-consumer integration','Original storage/complete-condition physical protocol; no launch before those checks'])
with (D/'STAGE_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(stage=str(S),parent_files=len(parents),helpers=len(helpers),defaultoff_exact_parent_ast=True,physics_started=False)))
