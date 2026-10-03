"""Independent LP feasibility/QP optimality and actual-stop/synthetic-history checks.
No physics replay or future observations after a changed action are claimed.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
from scipy.optimize import linprog,minimize
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));OUT=W/'FRONT_LOADED_MATERIAL_PROJECTION_CHECK.json';assert not OUT.exists()
from front_loaded_material_projection import cap_loaded_reference as candidate
from front_initial_loaded_reference_cap import cap_loaded_reference as old
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={str(p):sha(p) for p in [Path(__file__),W/'front_loaded_material_projection.py',W/'front_initial_loaded_reference_cap.py']}
def constraints(args):
 A=[];b=[]
 for center,radius in [(args['previous_xy'],.003),(args['reference_xy'],.030),(args['surface_xy'],.010)]:
  for i in range(2):
   row=np.eye(2)[i];A.extend([row,-row]);b.extend([center[i]+radius,-center[i]+radius])
 return np.array(A),np.array(b)
def verify(args):
 out=candidate(**args);A,b=constraints(args);lp=linprog([0.,0.],A_ub=A,b_ub=b,bounds=[(None,None)]*2,method='highs');assert lp.status in (0,2),lp.message
 assert out['requires_recontact']==(lp.status==2)
 if lp.status==2:assert out['command_xy'] is None;return out,None
 x=np.array(out['command_xy']);assert np.max(A@x-b)<=1e-12
 parent=np.array(args['parent_xy']);qp=minimize(lambda z:np.sum((z-parent)**2),lp.x,jac=lambda z:2*(z-parent),constraints=[{'type':'ineq','fun':lambda z:b-A@z,'jac':lambda z:-A}],method='SLSQP',options={'ftol':1e-15,'maxiter':200});assert qp.success,qp.message;np.testing.assert_allclose(x,qp.x,rtol=0,atol=2e-8)
 before=old(**args)
 if not before['requires_recontact']:np.testing.assert_allclose(x,before['command_xy'],rtol=0,atol=1e-15)
 return out,before
rng=np.random.default_rng(20261003);counts={'lp_cases':0,'feasible_qp':0,'genuine_empty':0,'old_feasible_unchanged':0,'old_false_empty_repaired':0,'translation_checks':0}
for _ in range(240):
 prev=rng.uniform(-.4,.4,2);args=dict(enabled=True,capture_complete=True,mode='top_push',parent_xy=prev+rng.uniform(-.003,.003,2),previous_xy=prev,reference_xy=prev+rng.uniform(-.045,.045,2),surface_xy=prev+rng.uniform(-.025,.025,2),normal_load_n=3.)
 out,before=verify(args);counts['lp_cases']+=1
 if out['requires_recontact']:counts['genuine_empty']+=1
 else:counts['feasible_qp']+=1;counts['old_false_empty_repaired' if before['requires_recontact'] else 'old_feasible_unchanged']+=1
 shift=rng.uniform(-2,2,2);moved=dict(args)
 for key in ['parent_xy','previous_xy','reference_xy','surface_xy']:moved[key]=np.array(args[key])+shift
 translated=candidate(**moved);assert translated['requires_recontact']==out['requires_recontact']
 if not out['requires_recontact']:np.testing.assert_allclose(np.array(translated['command_xy'])-shift,out['command_xy'],rtol=0,atol=1e-12)
 counts['translation_checks']+=1
actual=[]
for ep in [W/'front_loaded_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin',W/'front_loaded_physical_r1/case_840020/layout_840020_push_box_to_bin']:
 failure=json.loads((ep/'self_clearance.json').read_text())['failure'];r=failure['record'];args=dict(enabled=True,capture_complete=True,mode='top_push',parent_xy=r['parent_xy'],previous_xy=r['previous_command_xy'],reference_xy=r['reference_xy'],surface_xy=r['material_surface_xy'],normal_load_n=r['normal_load_n']);out,before=verify(args);assert before['requires_recontact'] and out['boundary_following_repair'];d=json.loads((ep/'LOADED_CAP_EMPTY_INTERSECTION_V2_DIAGNOSTIC.json').read_text());np.testing.assert_allclose(out['command_xy'],d['unissued_geometric_alternative_xy'],rtol=0,atol=1e-15)
 for f in [ep/'self_clearance.json',ep/'LOADED_CAP_EMPTY_INTERSECTION_V2_DIAGNOSTIC.json']:sources[str(f)]=sha(f)
 actual.append(dict(episode=ep.name,stop_step=failure['step'],candidate=out,scope='Logged stop constraints only; no issued action or future physical outcome'))
histories=[]
for label,axis in [('x_reverse',0),('y_reverse',1)]:
 surface=np.array([.425,-.087]);prev=surface-np.array([.010,.010]);repairs=0;old_stops=0
 for i in range(200):
  surface=surface.copy();surface[axis]+=float((1 if i%2==0 else -1)*.6e-6);hand=prev+np.array([.001,.001]);parent=prev-np.array([.0014,.0014]);args=dict(enabled=True,capture_complete=True,mode='top_push',parent_xy=parent,previous_xy=prev,reference_xy=hand,surface_xy=surface,normal_load_n=3.)
  before=old(**args);out=candidate(**args);assert not out['requires_recontact'];A,b=constraints(args);emitted=np.array(out['command_xy']);assert np.max(A@emitted-b)<=1e-12;repairs+=out['boundary_following_repair'];old_stops+=before['requires_recontact'];prev=emitted
 assert repairs>0 and old_stops>0;histories.append(dict(label=label,synthetic_frames=200,repairs=repairs,old_intersection_stops_on_candidate_history=old_stops,scope='Artificial back-and-forth material drift, not old physics replay'))
base=dict(enabled=True,capture_complete=True,mode='top_push',parent_xy=[0.,0.],previous_xy=[0.,0.],reference_xy=[0.,0.],surface_xy=[0.,0.],normal_load_n=3.)
for changes in [dict(enabled=False),dict(capture_complete=False),dict(mode='parent_guard'),dict(mode='top_release'),dict(normal_load_n=.299)]:
 args=dict(base,**changes);assert candidate(**args)==old(**args)
negative=[dict(base,enabled=1),dict(base,capture_complete=1),dict(base,parent_xy=[float('nan'),0]),dict(base,previous_xy=[0]),dict(base,normal_load_n=-1),dict(base,parent_xy=[.004,0]),dict(base,surface_xy=[float('inf'),0])]
for args in negative:
 try:candidate(**args)
 except ValueError:pass
 else:raise AssertionError('invalid input accepted')
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,counts=counts,actual_stop_checks=actual,synthetic_histories=histories,original_bypass_identity_cases=5,invalid_inputs_rejected=len(negative),source_sha256=sources,original_bounds_unchanged=True,production_wired=False,physical_success_proven=False,training_ready=False);OUT.write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k] for k in ['passed','counts','synthetic_histories','original_bypass_identity_cases','invalid_inputs_rejected','production_wired','physical_success_proven']},indent=2))
