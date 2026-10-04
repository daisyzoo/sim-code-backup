"""Independent effective-height metadata and contact-primal reconstruction.
Does not import the controller's resolver, solver or runtime. Full parent loaded-Z,
source, solver-status, stationarity and continuous-path audits remain required.
"""
from pathlib import Path
import ast,copy
import numpy as np

def contact_task(stage,coordinate,*,side,current,parent_command):
 q=np.asarray(current,float);parent=np.asarray(parent_command,float);task=coordinate['task_inputs'];loaded=coordinate['front_loaded_z_priority'];t=coordinate['step'];zr=2 if side=='left' else 5
 assert side in ('left','right') and type(t) is int and t>0 and type(loaded['applied']) is bool
 assert q.shape==parent.shape==(11,) and np.isfinite(q).all() and np.isfinite(parent).all();assert np.array_equal(task['current'],q) and np.array_equal(parent,loaded['output_command'])
 binding=dict(step=t,version='effective_loaded_contact_task_v1',quarter_enabled=True,loaded_applied=loaded['applied'],full_task_objective_unchanged=True,height_tolerance_m=2e-7,training_ready=False)
 if not loaded['applied']:return copy.deepcopy(task),dict(binding,target='original_task')
 # Explicit enabled stage always runs fraction .25. Missing reduction is rejected.
 r=loaded['reduced_z_task'];ctx=loaded['context'];assert loaded['step']==ctx['step']==t and ctx['side']==side;assert np.array_equal(ctx['current'],q);assert r['fraction']==.25 and type(r['fraction']) is float
 assert r['original_task']==task
 J=np.asarray(task['jacobian'],float);original=np.asarray(task['error'],float);before=np.asarray(ctx['parent_command'],float)
 assert J.shape==(9,11) and original.shape==(9,) and before.shape==(11,) and all(np.isfinite(x).all() for x in [J,original,before])
 start=float(J[zr]@(before-q));assert start>original[zr];want=start+.25*(float(original[zr])-start)
 assert r['parent_linear_z_m']==start and r['original_requested_z_m']==float(original[zr]) and r['modified_requested_z_m']==want
 effective=copy.deepcopy(task);effective['error'][zr]=want;assert r['modified_task']==effective
 residual=float(J[zr]@(parent-q)-want);assert abs(residual)<=2e-7
 tree=ast.parse((Path(stage)/'effective_loaded_contact_task_v1.py').read_text());doc=tree.body[0].value.value
 return effective,dict(binding,target='verified_effective_quarter_task',original_request_m=float(original[zr]),effective_request_m=want,parent_effective_height_residual_m=residual,scope=doc)

def verify_proposal(record,coordinate,*,guard,stage):
 from simfoundry.data.sorting_quality import PALM_OFFSET,PALM_COLLISION_HALF_Z,TABLE_PENETRATION_TOLERANCE
 from simfoundry.calibration.sorting_station import TABLE_TOP_Z
 p=record;side=p['side'];q=np.asarray(p['current']);u=np.asarray(p['command']);parent=np.asarray(p['parent_command']);task=coordinate['task_inputs'];effective,binding=contact_task(stage,coordinate,side=side,current=q,parent_command=parent)
 assert p['effective_loaded_contact_binding']==binding
 J=np.asarray(task['jacobian']);e=np.asarray(task['error']);zr=2 if side=='left' else 5
 target=np.asarray(coordinate['contact_normal_tracking']['target_local_up'],float);target=target/np.linalg.norm(target)
 M,_,_=guard.model.fk(side,u);P,_,_=guard.model.fk(side,parent)
 exact=float(np.linalg.norm(M[:3,:3].T@np.array([0.,0.,1.])-target)-np.linalg.norm(P[:3,:3].T@np.array([0.,0.,1.])-target))
 linear=float(np.linalg.norm(J[6:]@(u-q)-e[6:])-np.linalg.norm(J[6:]@(parent-q)-e[6:]))
 z_error=float(J[zr]@(u-q)-effective['error'][zr]);height=float(J[zr]@(u-parent));table=[]
 for hand in ['left','right']:
  T,_,_=guard.model.fk(hand,u);palm=T[:3,3]+T[:3,:3]@np.asarray(PALM_OFFSET);table.append(float(palm[2]-PALM_COLLISION_HALF_Z-(TABLE_TOP_Z-TABLE_PENETRATION_TOLERANCE)))
 loaded=coordinate['front_loaded_z_priority']['applied'];assert p['original_loaded_z_applied'] is loaded
 assert p['parent_height_task_preserved'] is (abs(height)<=2e-7)
 expected=bool((not loaded or abs(z_error)<=2e-7) and abs(height)<=2e-7 and exact<=1e-6 and linear<=2e-7 and min(table)>=0)
 assert p['original_contact_primal_preserved'] is expected
 assert p['contact_height_equality_residual_m']==height
 if loaded:
  check=p['original_loaded_contact_check'];assert abs(check['z_error_mm']/1000-z_error)<1e-15;assert abs(check['exact_attitude_delta']-exact)<1e-15;assert abs(check['linear_attitude_delta_mm']/1000-linear)<1e-15;assert check['nominal_table_margins_m']==table
 else:assert p['original_loaded_contact_check'] is None
 prelim=bool(p['solver_success'] and p['rounded_constraints_passed'] and p['original_command_guard']['accepted'] and p['all_sampled_paths_passed'] and expected)
 assert p['preliminary_passed'] is prelim
 return dict(effective_contact_binding_verified=True,contact_primal_passed=expected,preliminary_passed=prelim,training_ready=False)
