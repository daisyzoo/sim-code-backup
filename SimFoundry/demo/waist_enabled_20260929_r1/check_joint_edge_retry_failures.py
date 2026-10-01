"""Inject optimizer failures at a real rear-bag state. No physics/data changes."""
from pathlib import Path
import sys,json,hashlib,copy
from types import SimpleNamespace
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];probe=w/'staged_joint_edge_retry_probe';stage=w/'staged_joint_edge_command'
sys.path[:0]=[str(probe),str(stage),str(repo),str(w)]
import joint_edge_command as helper
import joint_edge_adapter as adapter
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.data.top_contact_bypass import rotation_xyzw
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ep=w/'joint_edge_groups_r1/case_840004/layout_840004_nudge_mailer_to_bin';t=444
with np.load(ep/'raw.npz') as z:q=z['q'][t,12:23].copy();previous=z['action'][t-1,12:23].copy()
with np.load(ep/'trace.npz') as z:xyz=z['mailer'][t].copy()
with np.load(ep/'parcel_orientation.npz') as z:rotation=rotation_xyzw(z['mailer'][t].tolist())
fr=json.loads((ep/'frontal_bypass.json').read_text());f=next(x for x in fr['rows'] if x['step']==t);c=next(x for x in json.loads((ep/'coordination.json').read_text()) if x['step']==t)
parent=np.asarray(c['joint_edge_refinement']['parent_final_upper_command'],dtype=np.float32)
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json')
args=dict(enabled=True,row=f,coordinate=c,current=q,previous=previous,parent_command=parent,object_xyz=xyz,object_rotation=rotation,core_size=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'],model=model,side='left',analytic_retry=True)
original=helper.minimize;original_refine=adapter.refine_rear_command;captured={};solves=[];calls=[]
def capture_refine(**kw):captured.update(kw);return original_refine(**kw)
def capture_solve(*a,**kw):
 r=original(*a,**kw);solves.append(copy.deepcopy(r));return r
adapter.refine_rear_command=capture_refine;helper.minimize=capture_solve
try:command,trace=adapter.refine_record(**args)
finally:helper.minimize=original;adapter.refine_rear_command=original_refine
assert len(solves)==2 and solves[0].status==8 and solves[1].success and trace['override']
rows=[]
def fake(status,x=None,success=False):return SimpleNamespace(status=status,success=success,nit=3,x=np.array(solves[1].x if x is None else x,copy=True))
def run(name,sequence,expected_calls,reason,override=False,change=None,jacobian=False):
 calls=[]
 def mocked(fun,initial,**kw):
  idx=len(calls);assert idx<len(sequence),'Unbounded retry';calls.append(dict(initial=initial.copy(),kwargs=kw,fun=fun))
  if jacobian and 'jac' in kw['constraints'][0]:kw['constraints'][0]['jac'](initial)
  return copy.deepcopy(sequence[idx])
 kw=dict(captured);kw.update(change or {});helper.minimize=mocked
 try:out=original_refine(**kw)
 finally:helper.minimize=original
 assert len(calls)==expected_calls and out['reason']==reason and out['override']==override,(name,out)
 if expected_calls==2:
  a,b=calls;assert np.array_equal(a['initial'],b['initial']);assert a['fun'] is b['fun'];assert a['kwargs']['jac'] is b['kwargs']['jac'];assert a['kwargs']['bounds'] is b['kwargs']['bounds'] or (np.array_equal(a['kwargs']['bounds'].lb,b['kwargs']['bounds'].lb) and np.array_equal(a['kwargs']['bounds'].ub,b['kwargs']['bounds'].ub));assert a['kwargs']['options']==b['kwargs']['options']==dict(ftol=1e-11,maxiter=300);assert 'jac' not in a['kwargs']['constraints'][0] and 'jac' in b['kwargs']['constraints'][0]
 else:assert 'analytic_retry' not in out
 if not override:assert 'command' not in out
 rows.append(dict(name=name,calls=len(calls),reason=reason,override=override))
 return out
run('primary_success_never_retries',[solves[1]],1,'nonlinear_joint_direction',True,dict(point_jacobian_fn=lambda x:(_ for _ in ()).throw(AssertionError('unnecessary derivative'))))
run('default_off_status8_no_retry',[solves[0]],1,'nonlinear_solver_failed',change=dict(analytic_retry=False,point_jacobian_fn=None))
run('status9_no_retry',[fake(9)],1,'nonlinear_solver_failed')
run('status8_nonfinite_no_retry',[fake(8,np.full(11,np.nan))],1,'nonlinear_solver_failed')
run('status8_then_success',[solves[0],solves[1]],2,'nonlinear_joint_direction',True,jacobian=True)
for status in [8,9,4]:run('retry_failure_'+str(status),[solves[0],fake(status)],2,'nonlinear_solver_failed')
run('retry_success_nonfinite_rejected',[solves[0],fake(0,np.full(11,np.nan),True)],2,'nonlinear_solver_failed')
run('retry_success_out_of_bounds_rejected',[solves[0],fake(0,np.full(11,3.),True)],2,'final_float32_constraint_violation')
for name,value in [('wrong_shape',np.zeros((11,3))),('nonfinite',np.full((3,11),np.nan))]:
 try:run(name,[solves[0],solves[1]],2,'unused',change=dict(point_jacobian_fn=lambda x,v=value:v),jacobian=True)
 except ValueError as e:assert str(e)=='Invalid analytic FK Jacobian';rows.append(dict(name=name,rejected=True))
 else:raise AssertionError(name)
for name,change in [('missing_callback',dict(point_jacobian_fn=None)),('nonbool_flag',dict(analytic_retry=1))]:
 try:original_refine(**dict(captured,**change))
 except ValueError:rows.append(dict(name=name,rejected=True))
 else:raise AssertionError(name)
# Actual adapter must retain parent exactly when both solves fail.
n=[0]
def both_fail(*a,**kw):n[0]+=1;return copy.deepcopy(solves[0])
helper.minimize=both_fail
try:out,tr=adapter.refine_record(**args)
finally:helper.minimize=original
assert n[0]==2 and np.array_equal(out,parent) and tr['reason']=='nonlinear_solver_failed' and not tr['override'];rows.append(dict(name='adapter_double_failure_exact_parent',calls=n[0]))
report=dict(passed=True,rows=rows,fixture_step=t,fixture_episode=ep.name,source_sha256={x:sha(ep/x) for x in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json']},probe_source_sha256={x:sha(probe/x) for x in ['joint_edge_command.py','joint_edge_adapter.py']},checker_sha256=sha(Path(__file__)),scope=__doc__,training_ready=False)
(probe/'FAILURE_PATH_CHECK.json').write_text(json.dumps(report,indent=2));print('passed',len(rows),'failure/branch checks')
