"""Checked nonlinear task-parent execution before original edge refinement.
Original task KKT is recomputed for every row; original loaded reconstruction
checks all task inputs and float32 slew. No candidate nonlinear solver imports.
"""
from pathlib import Path
import json
import numpy as np
from audit_parent_seed_pose_loaded_execution import near
from audit_rear_coupled_execution_live import replay_record
from audit_box_center_pose_task_optimality import verify_task_rows,IndependentElbows

def build_parent_verifier(ep,stage):
 ep,stage=Path(ep),Path(stage);repo=Path(__file__).resolve().parents[2]
 events={r['step']:{k:v for k,v in r.items() if k!='step'} for r in json.loads((ep/'recontact_pose.json').read_text())['rows'] if r['kind'] in ('command','handover')};pose=json.loads((ep/'BOX_CENTER_POSE_LIVE_AUDIT.json').read_text());assert pose['passed'];assert set(events)=={r['step'] for r in pose['records']}
 geom=IndependentElbows(stage/'elbow_torso_hulls.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf');task=verify_task_rows(ep,geom,events);assert task['passed'],task['errors'];task_records={r['step']:r for r in task['records']};evidence=dict(independent_task_frames=task['frames'],independent_task_max_kkt=task['max_kkt_residual'],loaded_task_overrides_checked=[])
 def loaded_parent(c,f,expert,q,previous,parent,side,solver):
  tr=c['self_clearance_task'];assert tr['accepted'] is True and type(tr['override']) is bool
  if not tr['override']:return replay_record(c,f,expert,q,previous,parent,side,solver)
  proof=task_records[c['step']];assert proof['override'] and proof['stationary'] and proof['kkt_residual']<=1e-6
  inp=c['task_inputs'];candidate=np.asarray(tr['candidate_command'],dtype=np.float32);assert np.array_equal(candidate,np.asarray(tr['candidate_command']));assert tr['solver_success'] is True and tr['status']==0
  def task_delta(J,E,current,lower,upper,limits,damping,*,preferred_step):
   for value,key in [(J,'jacobian'),(E,'error'),(current,'current'),(lower,'lower'),(upper,'upper'),(limits,'step_limits'),(damping,'damping'),(preferred_step,'preferred_step')]:near(value,inp[key],0)
   baseline=(current+solver(J,E,current,lower,upper,limits,damping,preferred_step=preferred_step)).astype(np.float32);near(baseline,tr['parent_command'],0);near(previous,tr['previous_command'],0)
   return (candidate-current).astype(np.float32)
  out=replay_record(c,f,expert,q,previous,parent,side,task_delta);evidence['loaded_task_overrides_checked'].append(dict(step=c['step'],task_kkt_residual=proof['kkt_residual'],task_to_parent_max_action_error_rad=out['max_action_error_rad']));return out
 return loaded_parent,evidence
