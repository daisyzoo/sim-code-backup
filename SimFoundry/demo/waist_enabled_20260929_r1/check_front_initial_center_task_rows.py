"""Original full physical KKT failure must survive new front-path audit routing.
Additional small fabricated command records test routing only, never task admission.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy,tempfile
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_initial_center';sys.path[:0]=[str(W),str(ROOT)]
from audit_front_initial_center_task_rows import verify_task_rows,IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=W/'FRONT_INITIAL_CENTER_TASK_ROWS_CHECK.json';assert not out.exists()
ep=W/'terminal_lead_physical_r1/case_840015/layout_840015_nudge_mailer_to_bin';old=ep/'TERMINAL_LEAD_STAGE_TASK_OPTIMALITY_V2_AUDIT.json'
report=dict(status='running',scope=__doc__,simulation_started=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'audit_front_initial_center_task_rows.py',old]})
def save():report['updated_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();out.write_text(json.dumps(report,indent=2))
try:
 save();geometry=IndependentElbows(S/'elbow_torso_hulls.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf');result=verify_task_rows(ep,geometry,{})
 baseline=json.loads(old.read_text())
 for key in ['passed','errors','frames','overrides','max_kkt_residual','records','source_sha256']:assert result[key]==baseline[key],key
 assert result['passed'] is False and len(result['errors'])==1 and result['errors'][0]['step']==210
 report['physical_failure_preserved']=dict(frames=result['frames'],errors=result['errors'],max_kkt_residual=result['max_kkt_residual'],entire_records_identical=True);save()
 preparation=json.loads((W/'FRONT_INITIAL_CENTER_TASK_ROWS_PREPARATION.json').read_text());text=(W/'audit_front_initial_center_task_rows.py').read_text()
 for e in reversed(preparation['edits']):assert text.count(e['new'])==1;text=text.replace(e['new'],e['old'])
 assert text==(W/'audit_terminal_margin_stage_task_optimality.py').read_text().split('\ndef inspect(ep):',1)[0]
 report['original_task_math_reverse_diff']=True;report['routing_checks']=[]
 with tempfile.TemporaryDirectory(prefix='front-task-routing-fixture-') as tmp:
  p=Path(tmp);q=np.zeros((2,23));u=np.zeros((2,23));np.savez_compressed(p/'raw.npz',q=q,action=u,task_id='nudge_mailer_to_bin',fixture_only=True)
  event=dict(kind='command',command=[0.]*11,context=dict(current=[0.]*11,previous_command=[0.]*11))
  coordinate=dict(step=1,controller_kind='verified_unloaded_front_initial_joint_path',front_initial_center_override=event,task_inputs=None,contact_normal_tracking=None,contact_bout_yaw_tracking=None)
  (p/'expert_control.json').write_text(json.dumps([dict(step=0,mode='fixture'),dict(step=1,mode='top_cross')]))
  (p/'self_clearance.json').write_text(json.dumps(dict(failure=None)))
  for label in ['separately_verified_front','unverified_front','wrong_current','wrong_command','wrong_controller','conflicting_rear','loaded_mode']:
   c=copy.deepcopy(coordinate);events={1:copy.deepcopy(event)};rear={};experts=[dict(step=0,mode='fixture'),dict(step=1,mode='top_cross')]
   if label=='unverified_front':events={}
   if label=='wrong_current':c['front_initial_center_override']['context']['current'][0]+=.001;events={1:c['front_initial_center_override']}
   if label=='wrong_command':c['front_initial_center_override']['command'][0]+=.001;events={1:c['front_initial_center_override']}
   if label=='wrong_controller':c['controller_kind']='verified_unloaded_recontact_joint_path'
   if label=='conflicting_rear':rear=copy.deepcopy(events)
   if label=='loaded_mode':experts[1]['mode']='top_push'
   (p/'coordination.json').write_text(json.dumps([c]));(p/'expert_control.json').write_text(json.dumps(experts));accepted=True
   try:r=verify_task_rows(p,geometry,rear,verified_front_events=events);assert r['passed'] and r['records']==[dict(step=1,override=False,declared_joint_path=True)]
   except (AssertionError,ValueError,KeyError):accepted=False
   assert accepted==(label=='separately_verified_front'),label;report['routing_checks'].append(dict(case=label,accepted=accepted));save()
 report.update(status='complete',passed=True);save();print('full physical failure unchanged, routing 7 cases passed',flush=True)
except Exception as e:report.update(status='failed',error=repr(e));save();raise
