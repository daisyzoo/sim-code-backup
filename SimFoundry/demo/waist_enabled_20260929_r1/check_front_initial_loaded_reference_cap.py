"""Independent feasible-set optimum/boundary checks of an UNWIRED XY candidate.
No new physical result, force capability, or dataset admission is established.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
from scipy.optimize import linprog, minimize
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from front_initial_loaded_reference_cap import cap_loaded_reference
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rng=np.random.default_rng(20261003);passed=0;empty=0;translated=0
for i in range(200):
 surface=rng.uniform(-.4,.4,2);prev=surface+rng.uniform(-.014,.014,2);ref=prev+rng.uniform(-.020,.020,2);parent=prev+rng.uniform(-.003,.003,2)
 args=dict(enabled=True,capture_complete=True,mode='top_push',parent_xy=parent,previous_xy=prev,reference_xy=ref,surface_xy=surface,normal_load_n=1.)
 result=cap_loaded_reference(**args)
 # Independent halfspace construction in metres, checked by LP feasibility.
 A=[];b=[]
 for j in range(2):
  axis=np.eye(2)[j]
  for center,radius in [(prev,.003),(ref,.030),(surface,.010)]:A.extend([axis,-axis]);b.extend([center[j]+radius,-center[j]+radius])
  A.extend([axis,-axis]);b.extend([max(prev[j],parent[j]),-min(prev[j],parent[j])])
 A=np.array(A);b=np.array(b);feasible=linprog([0.,0.],A_ub=A,b_ub=b,bounds=[(None,None)]*2,method='highs',options={'primal_feasibility_tolerance':1e-9})
 assert feasible.success == (not result['requires_recontact'])
 if feasible.success:
  point=np.array(result['command_xy']);assert np.max(A@point-b)<1e-12
  fit=minimize(lambda x:float(np.sum((x-parent)**2)),feasible.x,jac=lambda x:2*(x-parent),constraints=[dict(type='ineq',fun=lambda x:b-A@x,jac=lambda x:-A)],method='SLSQP',options=dict(ftol=1e-14,maxiter=100))
  assert fit.success and np.max(abs(fit.x-point))<2e-6;passed+=1
 else:assert result['command_xy'] is None;empty+=1
 shift=rng.uniform(-2,2,2);shifted=cap_loaded_reference(**dict(args,parent_xy=parent+shift,previous_xy=prev+shift,reference_xy=ref+shift,surface_xy=surface+shift));assert shifted['requires_recontact']==result['requires_recontact']
 if result['command_xy'] is not None:np.testing.assert_allclose(np.array(shifted['command_xy'])-shift,result['command_xy'],rtol=0,atol=2e-15)
 translated+=1
checks=[];base=dict(enabled=True,capture_complete=True,mode='top_push',parent_xy=[.012,0.],previous_xy=[.010,0.],reference_xy=[.010,0.],surface_xy=[0.,0.],normal_load_n=1.)
r=cap_loaded_reference(**base);assert r['changed'] and r['command_xy']==[.01,0.];checks.append('advance_stops_at_material_limit_without_reversing')
r=cap_loaded_reference(**dict(base,surface_xy=[.002,0.]));assert not r['changed'];checks.append('material_motion_reopens_advance_budget')
r=cap_loaded_reference(**dict(base,parent_xy=[-.012,0.],previous_xy=[-.010,0.],reference_xy=[-.010,0.]));assert r['command_xy']==[-.01,0.];checks.append('opposite_direction_symmetric')
for change in [dict(enabled=False),dict(capture_complete=False),dict(mode='front_guard_lift'),dict(mode='top_release'),dict(normal_load_n=.29)]:
 r=cap_loaded_reference(**dict(base,**change));assert not r['applied'] and r['command_xy']==base['parent_xy'];checks.append('original_parent_preserved_'+next(iter(change)))
for change in [dict(enabled='yes'),dict(capture_complete=1),dict(parent_xy=[np.nan,0.]),dict(normal_load_n=np.nan),dict(normal_load_n=-1.),dict(surface_xy=[np.inf,0.]),dict(previous_xy=[0.,0.]),dict(reference_xy=[0.,0.,0.])]:
 try:cap_loaded_reference(**dict(base,**change))
 except ValueError:checks.append('invalid_input_rejected_'+next(iter(change)))
 else:raise AssertionError(change)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,independent_feasible_optima=passed,infeasible_intersections_requiring_recontact=empty,translation_checks=translated,boundary_and_negative_checks=checks,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'front_initial_loaded_reference_cap.py']},simulation_started=False,training_ready=False)
p=W/'FRONT_INITIAL_LOADED_REFERENCE_CAP_CHECK.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','scope']},indent=2))
