"""Execute real pre-AppLauncher CLI and actual snapshot writer, no physics."""
from pathlib import Path
import sys,types,json,hashlib,tempfile,ast,contextlib,io
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_joint_edge_retry';sys.path[:0]=[str(stage),str(repo)]
source=(stage/'collect_paired_sorting.py').read_text();prefix=source.split('app = AppLauncher(args, enable_cameras=True).app')[0];base=list(json.loads((w/'y_path_nearhalf_groups_r1/PROTOCOL.json').read_text())['settings']);plan=json.loads((w/'fresh_trial_contracts_v2_r1/fresh_lateral_00.json').read_text())['layouts'][1]
with tempfile.TemporaryDirectory(prefix='region_prelaunch_') as td:
 td=Path(td);layout=td/'layout.json';layout.write_text(json.dumps(plan));cli=base+['--out-dir',str(td/'NOT_LAUNCHED'),'--diagnostic-layout-json',str(layout),'--layout-start',str(plan['layout_id'])]
 def parse(arguments):
  name='region_prelaunch_check';m=types.ModuleType(name);m.__file__=str(stage/'collect_paired_sorting.py');sys.modules[name]=m;old=sys.argv;sys.argv=['collector',*arguments]
  try:
   with contextlib.redirect_stderr(io.StringIO()):exec(compile(prefix,m.__file__,'exec'),m.__dict__)
   return m
  finally:sys.argv=old;sys.modules.pop(name,None)
 off=parse(cli);on=parse(cli+['--region-top-approach','--region-tracking-residual','--front-cop-slip-following','--front-cop-phase-anchor','--front-cop-route-axis','--region-causal-response','--region-causal-xy-response','--region-separate-measured-bounds','--rear-cop-centering','--rear-core-slice-feedback','--front-cop-drive-step-m','.002','--front-cop-edge-speed','--rear-coupled-progress','--rear-joint-xy-progress','--rear-joint-edge-command','--rear-joint-edge-analytic-retry']);assert not off.args.front_cop_slip_following and on.args.front_cop_slip_following and not off.args.region_top_approach and on.args.region_top_approach and on.ROOT==repo and on.waist_admission is None
 assert not off.args.front_cop_phase_anchor and on.args.front_cop_phase_anchor
 assert not off.args.front_cop_route_axis and on.args.front_cop_route_axis
 assert not off.args.region_causal_response and on.args.region_causal_response
 assert not off.args.region_causal_xy_response and on.args.region_causal_xy_response
 negative=[]
 assert not off.args.region_separate_measured_bounds and on.args.region_separate_measured_bounds
 assert not off.args.rear_cop_centering and on.args.rear_cop_centering
 complete=cli+['--region-top-approach','--region-tracking-residual','--front-cop-slip-following','--front-cop-phase-anchor','--front-cop-route-axis','--region-causal-response','--region-causal-xy-response','--region-separate-measured-bounds','--rear-cop-centering','--rear-core-slice-feedback','--front-cop-drive-step-m','.002','--front-cop-edge-speed','--rear-coupled-progress','--rear-joint-xy-progress','--rear-joint-edge-command','--rear-joint-edge-analytic-retry']
 assert not off.args.rear_core_slice_feedback and on.args.rear_core_slice_feedback
 assert off.args.front_cop_drive_step_m==.001 and on.args.front_cop_drive_step_m==.002
 assert not off.args.front_cop_edge_speed and on.args.front_cop_edge_speed
 assert not off.args.rear_coupled_progress and on.args.rear_coupled_progress
 assert not off.args.rear_joint_xy_progress and on.args.rear_joint_xy_progress
 for drop in ['--rear-joint-edge-command','--rear-joint-xy-progress','--rear-coupled-progress','--rear-core-slice-feedback','--waist-coordinated-expert','--bounded-coupled-ik','--expert-top-contact-normal-hold']:
  try:parse([x for x in complete if x!=drop])
  except SystemExit as e:assert e.code!=0;negative.append('coupled_missing_'+drop)
  else:raise AssertionError('Coupled dependency accepted')
 for extra in [['--expert-top-contact-bout-yaw-hold'],['--idle'],['--policy-port','1234']]:
  try:parse(complete+extra)
  except SystemExit as e:assert e.code!=0;negative.append('coupled_conflict_'+extra[0])
  else:raise AssertionError('Coupled conflict accepted')

 for drop in ['--front-cop-route-axis','--front-cop-phase-anchor','--front-cop-slip-following']:
  try:parse([x for x in complete if x!=drop])
  except SystemExit as e:assert e.code!=0;negative.append('edge_missing_'+drop)
  else:raise AssertionError('Edge missing dependency accepted')
 for nominal in ['.001','.003']:
  try:parse(complete+['--front-cop-drive-step-m',nominal])
  except SystemExit as e:assert e.code!=0;negative.append('edge_wrong_nominal_'+nominal)
  else:raise AssertionError('Edge other nominal accepted')
 for value in ['nan','inf','-inf','0','.0009','.0031']:
  try:parse(complete+['--front-cop-drive-step-m',value])
  except SystemExit as e:assert e.code!=0;negative.append('invalid_drive_'+value)
  else:raise AssertionError('Invalid front drive accepted')
 for invalid in [cli+['--front-cop-drive-step-m','.002','--front-cop-edge-speed','--rear-coupled-progress','--rear-joint-xy-progress','--rear-joint-edge-command','--rear-joint-edge-analytic-retry'],[x for x in complete if x!='--front-cop-route-axis']]:
  try:parse(invalid)
  except SystemExit as e:assert e.code!=0;negative.append('drive_missing_route_axis')
  else:raise AssertionError('Changed drive without route axis accepted')
 for drop in ['--rear-cop-centering','--region-separate-measured-bounds','--region-causal-xy-response','--trace-solved-contact-forces','--expert-top-hold-established-x']:
  try:parse([x for x in complete if x!=drop])
  except SystemExit as e:assert e.code!=0;negative.append('rear_cop_missing_'+drop)
  else:raise AssertionError('Rear COP missing dependency accepted')
 for extra in [['--expert-frontal-top-cross-admittance'],['--expert-frontal-top-hold-push-x'],['--expert-frontal-top-drag-step-m','.002']]:
  try:parse(complete+extra)
  except SystemExit as e:assert e.code!=0;negative.append('rear_cop_conflict_'+extra[0])
  else:raise AssertionError('Rear COP conflicting configuration accepted')
 try:parse(cli+['--region-causal-xy-response'])
 except SystemExit as e:assert e.code!=0;negative.append('xy_missing_causal_response')
 else:raise AssertionError('XY without causal accepted')
 for bad in [cli+['--region-causal-response'],[x for x in cli if x!='--trace-solved-contact-forces']+['--region-top-approach','--region-tracking-residual','--region-causal-response']]:
  try:parse(bad)
  except SystemExit as e:assert e.code!=0;negative.append('causal_missing_prerequisite')
  else:raise AssertionError('Causal missing prerequisite accepted')
 for extra in [['--front-cop-route-axis'],['--front-cop-slip-following','--front-cop-route-axis']]:
  try:parse(cli+extra)
  except SystemExit as e:assert e.code!=0;negative.append('axis_missing_prerequisite')
  else:raise AssertionError('Route-axis missing prerequisite accepted')
 try:parse(cli+['--front-cop-phase-anchor'])
 except SystemExit as e:assert e.code!=0;negative.append('phase_anchor_missing_cop')
 else:raise AssertionError('Phase anchor without COP accepted')
 for args in [cli+['--region-top-approach'],cli+['--region-tracking-residual']]:
  try:parse(args)
  except SystemExit as e:assert e.code!=0;negative.append('missing_partner_flag')
  else:raise AssertionError('Missing partner flag accepted')
 for label,args in [('pilot_role',cli+['--region-top-approach','--region-tracking-residual','--role','pilot']),('no_bounded',[x for x in cli if x!='--bounded-coupled-ik']+['--region-top-approach','--region-tracking-residual']),('no_projection',[x for x in cli if x!='--expert-top-projected-support']+['--region-top-approach','--region-tracking-residual']),('competing_center',cli+['--region-top-approach','--region-tracking-residual','--expert-top-contact-center-calibration']),('policy',cli+['--region-top-approach','--region-tracking-residual','--policy-port','1234']),('corner',cli+['--region-top-approach','--region-tracking-residual','--expert-frontal-top-visible-corner'])]:
  try:parse(args)
  except SystemExit as e:assert e.code!=0;negative.append(label)
  else:raise AssertionError('Accepted invalid configuration: '+label)
 for drop in ['--expert-front-top-route','--trace-solved-contact-forces','--expert-top-contact-normal-hold','--expert-top-projected-support']:
  try:parse([x for x in cli if x!=drop]+['--front-cop-slip-following'])
  except SystemExit as e:assert e.code!=0;negative.append('front_cop_missing_'+drop)
  else:raise AssertionError('COP missing prerequisite accepted: '+drop)
 for addition in [['--expert-front-object-relative-lead'],['--expert-top-contact-center-calibration'],['--expert-frontal-top-drag-step-m','.002']]:
  try:parse(cli+['--front-cop-slip-following',*addition])
  except SystemExit as e:assert e.code!=0;negative.append('front_cop_conflict_'+addition[0])
  else:raise AssertionError('COP conflict accepted')
 assert not off.args.rear_joint_edge_command and on.args.rear_joint_edge_command
 assert not off.args.rear_joint_edge_analytic_retry and on.args.rear_joint_edge_analytic_retry
 old=parse([x for x in complete if x!='--rear-joint-edge-analytic-retry']);assert old.args.rear_joint_edge_command and not old.args.rear_joint_edge_analytic_retry
 for extra in [['--waist-limit-rad','.9'],['--waist-limit-rad','1.1'],['--waist-limit-rad','nan'],['--waist-limit-rad','inf'],['--motion-protocol','waist_locked_v1'],['--role','pilot'],['--waist-probe']]:
  try:parse(complete+extra)
  except SystemExit as e:assert e.code!=0;negative.append('joint_edge_invalid_'+str(extra))
  else:raise AssertionError('Invalid joint edge configuration accepted')
 # Execute exact main AST from paths assignment through provenance writer.
 tree=ast.parse(source);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');start=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='paths' for t in n.targets));end=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='spec' for t in n.targets));snapshot=td/'snapshot';snapshot.mkdir();on.__dict__['root']=snapshot
 exec(compile(ast.Module(body=main.body[start:end],type_ignores=[]),str(stage/'collect_paired_sorting.py'),'exec'),on.__dict__)
 provenance=json.loads((snapshot/'provenance.json').read_text());assert provenance['args']['role']=='diagnostic' and provenance['args']['region_top_approach'] is True
 for relative,digest in provenance['source_sha256'].items():assert hashlib.sha256((snapshot/'source_snapshot'/relative).read_bytes()).hexdigest()==digest==hashlib.sha256((repo/relative).read_bytes()).hexdigest()
 expected=['contact_patch_approach.py','articulated_hand_geometry.py','region_top_contact.py','region_approach_lifecycle.py','collect_paired_sorting.py','front_cop_route.py','contact_slip_following.py','causal_unloaded_response.py','causal_response_parameters.json','rear_cop_centering.py','rear_cop_route.py','front_edge_speed.py','rear_coupled_progress.py','rear_joint_xy_progress.py','joint_edge_command.py','joint_edge_adapter.py']
 assert provenance['args']['rear_core_slice_feedback'] is True and provenance['args']['rear_cop_centering'] is True and len(provenance['source_sha256'])==60 and provenance['args']['rear_joint_xy_progress'] is True and provenance['args']['rear_coupled_progress'] is True
 for name in expected:assert str((stage/name).relative_to(repo)) in provenance['source_sha256']
 assert provenance['args']['rear_joint_edge_analytic_retry'] is True
 report=dict(checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),default_off_and_enabled_cli=True,negative_cli_rejected=negative,actual_snapshot_writer_files=len(provenance['source_sha256']),source_sha256={name:hashlib.sha256((stage/name).read_bytes()).hexdigest() for name in expected},scope='Real installed AppLauncher argument parser and complete collector prelaunch validation executed; actual source snapshot/provenance AST wrote and byte-checked temporary archives. No AppLauncher construction, physics, robot commands, training or pilot admission. Fixtures deleted.',training_ready=False)
(stage/'PRELAUNCH_AND_SOURCE_CHECK.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
