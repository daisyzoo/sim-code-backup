"""Execute actual pose/self-clearance/task audit branches on independently bound
recovery affine events. Only branch integration is checked, not whole physics.
Full-stream missing events/poses/commands were independently tested separately.
"""
from pathlib import Path
import ast,copy,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_headroom';D=W/'front_bag_recontact_headroom_draft_r1';sys.path[:0]=[str(W),str(ROOT)]
from audit_front_recontact_headroom_v3_stage_self_clearance import near
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
paths=dict(pose=W/'audit_front_recontact_headroom_v1_stage_pose_live.py',clearance=W/'audit_front_recontact_headroom_v3_stage_self_clearance.py',task=W/'audit_front_recontact_headroom_task_rows.py')
def branch_code(p,label):
 tree=ast.parse(p.read_text())
 if label=='pose':matches=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='t in front_events or t in recovery_events']
 else:matches=[n for n in ast.walk(tree) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and 'controller_kind' in ast.unparse(n.test) and 'verified_unloaded_front_recontact_joint_path' in ast.unparse(n.test)]
 assert len(matches)==1
 loop=ast.For(target=ast.Name(id='_once',ctx=ast.Store()),iter=ast.Tuple(elts=[ast.Constant(0)],ctx=ast.Load()),body=[copy.deepcopy(matches[0])],orelse=[])
 return compile(ast.fix_missing_locations(ast.Module(body=[loop],type_ignores=[])),str(p),'exec')
codes={k:branch_code(p,k) for k,p in paths.items()};base=json.loads((D/'PROBE_RESULT.json').read_text());bound=json.loads((S/'INDEPENDENT_STREAM_CHECK.json').read_text());assert bound['passed'] and bound['affine_events']==143
for p,h in bound['source_sha256'].items():assert sha(p)==h,p
records=[];negatives=[]
for f in base['records']:
 for raw in [f['events'][0],f['events'][-1]]:
  event=copy.deepcopy(raw);event['real_recontact_index']=f['counter'];cc=event['context'];t=cc['step'];q=np.zeros((t+1,11));u=np.zeros_like(q);q[t]=cc['current'];u[t-1]=cc['previous_command'];u[t]=event['command'];kind=event['kind'];phase='measured_handover' if kind=='handover' else 'tracking'
  row=dict(step=t,front_recontact_center_phase=phase);coordinate=dict(step=t,controller_kind='verified_unloaded_front_recontact_joint_path',front_recontact_center_override=event,active_side='left',task_inputs=None,contact_normal_tracking=None,contact_bout_yaw_tracking=None)
  if kind=='handover':
   row.update(target_xyz=event['observed_support_xyz'],observed_support_xyz=event['observed_support_xyz'],control_offset_local=event['reference']['reference_local'],projected_support_reference=event['reference'],push_x_anchor_m=None,approach_xy_bias_m=[0.,0.]);coordinate.update(active_support_reference=event['reference'],control_point_positions={'left':event['observed_support_xyz']})
  hold=dict(held=False,output_upper_command=u[t].tolist(),previous_upper_command=u[t-1].tolist(),current_upper_q=q[t].tolist());final=dict(accepted=True,command=u[t].tolist(),current=q[t].tolist(),previous=u[t-1].tolist());experts={t:dict(mode='top_press' if kind=='handover' else 'top_cross')}
  for label in codes:
   ns=dict(np=np,near=near,t=t,event=None,selected=False,front_events={},recovery_events={t:event},verified_front_events={},verified_front_recovery_events={t:event},verified_events={t:event},f=row,c=coordinate,side='left',holds={t:hold},final={t:final},q=q,u=u,experts=experts,controller_frames=0,records=[])
   exec(codes[label],ns)
   if label=='clearance':assert ns['controller_frames']==1
   if label=='task':assert ns['records']==[dict(step=t,override=False,declared_joint_path=True)]
   records.append(dict(run=f['run'],counter=f['counter'],kind=kind,branch=label,passed=True))
   if f is base['records'][0] and kind=='handover':
    bads=['wrong_final_action','wrong_previous','competing_event','wrong_phase'] if label=='pose' else ['missing_admission','competing_override','wrong_counter','wrong_side','wrong_final_action','wrong_previous']
    for name in bads:
     # Preserve event equality aliases within each independently copied namespace.
     case=copy.deepcopy({k:v for k,v in ns.items() if k not in ['np','near','__builtins__']});case.update(np=np,near=near,controller_frames=0,records=[])
     if label=='pose':
      if name=='wrong_final_action':case['holds'][t]['output_upper_command'][0]+=.001
      elif name=='wrong_previous':case['final'][t]['previous'][0]+=.001
      elif name=='competing_event':case['event']={}
      else:case['f']['front_recontact_center_phase']='tracking'
     else:
      if name=='missing_admission':case['verified_events']={}
      elif name=='competing_override':case['c']['front_initial_center_override']={}
      elif name=='wrong_counter':case['c']['front_recontact_center_override']['real_recontact_index']+=1
      elif name=='wrong_side':case['c']['active_side']='right'
      elif name=='wrong_final_action':case['u'][t,0]+=.001
      elif name=='wrong_previous':case['u'][t-1,0]+=.001
     try:exec(codes[label],case)
     except (AssertionError,ValueError,KeyError):negatives.append(dict(branch=label,case=name,rejected=True))
     else:raise AssertionError(('bad branch accepted',label,name))
# Explicit caller wiring: pose's independent map and normal helper must include
# separate recovery evidence, and both task/clearance routes must consume it.
pose=paths['pose'].read_text();assert 'recovery_result=verify_recovery_files(ep)' in pose and 'verified_front_recovery_events=recovery_events' in pose
clear=paths['clearance'].read_text();assert 'from audit_front_recontact_headroom_v2_execution import inspect as inspect_priority' in clear
loaded=(W/'audit_front_recontact_headroom_v3_stage_pose_loaded_execution.py').read_text();assert "geometry['auditor_sha256']==sha(w/'audit_front_recontact_headroom_v3_stage_self_clearance.py')" in loaded
allpaths=[Path(__file__),*paths.values(),W/'audit_front_recontact_headroom_v3_stage_pose_loaded_execution.py',W/'front_recontact_headroom_v3_stage_run_contract.py',S/'INDEPENDENT_STREAM_CHECK.json',S/'AUDIT_FAMILY_PREPARATION.json',D/'PROBE_RESULT.json'];out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,branch_fixtures=records,negative_cases=negatives,source_sha256={str(p):sha(p) for p in allpaths},full_trajectory_fixture=False,simulation_started=False,training_ready=False)
with (S/'NATIVE_JOINT_BRANCH_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,branch_fixtures=len(records),negative=len(negatives))))
