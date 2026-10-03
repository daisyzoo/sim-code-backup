"""Validate near-axis proof plus unchanged real accepted/rejected KKT history."""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
w=Path(__file__).resolve().parent;sys.path.insert(0,str(w))
from support_vertex_stationarity import certificate as original,planes
from support_vertex_stationarity_rigid_segment_v2 import certificate,prove_axis_stability,VERSION
from audit_self_clearance_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=w/'front_corridor_midpoint_physical_r1';sources={};cases=[]
def bind(p):sources[str(p)]=sha(p)
g=IndependentElbows(w/'staged_closed_peak_trial/elbow_torso_hulls.json',w.parents[1]/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf')
def inputs(inp,tr):
 q=np.array(inp['current']);prev=np.array(inp['previous']);x=np.array(tr['candidate_command']);J=np.array(inp['jacobian']);E=np.array(inp['error']);d=np.array(inp['damping']);lo=np.maximum.reduce([np.array(inp['lower']),q-inp['step_limits'],prev-.055]);hi=np.minimum.reduce([np.array(inp['upper']),q+inp['step_limits'],prev+.055]);grad=J.T@(J@(x-q)-E)+d*d*(x-q-inp['preferred_step'])
 return dict(geometry=g,x=x,gradient=grad,lower=lo,upper=hi)
# Original report gives expected actual accepted/rejected inputs, not just a new oracle.
history=w/'fresh_closed_peak_trials_r1';p=history/'SUPPORT_VERTEX_STATIONARITY_CHECK.json';h=json.loads(p.read_text());assert h['passed'];bind(p)
for epitem in h['episodes']:
 ep=history/('case_'+epitem['episode'].split('_')[1])/epitem['episode'];coord=ep/'coordination.json';bind(coord);rr={x['step']:x for x in json.loads(coord.read_text())};failed=[]
 for expected in epitem['checks']:
  row=rr[expected['step']];args=inputs(row['task_inputs'],row['self_clearance_task']);new=certificate(**args);old=original(**args);changed=dict(new);changed['version']=old['version'];assert changed==old
  assert new['passed']==expected['passed'] and abs(new['stationarity_residual']-expected['stationarity_residual'])<1e-12
  if not new['passed']:failed.append(expected['step'])
 assert failed==epitem['failed'];cases.append(dict(episode=ep.name,checked=len(epitem['checks']),rejected=failed));print(cases[-1],flush=True)
ep=r/'case_840023/layout_840023_nudge_mailer_to_bin';p=ep/'coordination.json';bind(p);row=next(x for x in json.loads(p.read_text()) if x['step']==1039);args=inputs(row['task_inputs'],row['self_clearance_task']);original_result=original(**args);assert not original_result['passed'] and original_result['reason']=='ambiguous_active_axis';actual=certificate(**args);assert actual['passed'] and actual['stationarity_residual']<1e-6
negative=[]
# Exact duplicate and near-tied competing support axes must still be rejected.
for separation in [0.,1e-8]:
 gg=copy.deepcopy(g);gg.axes=np.vstack([g.axes,g.axes[40]]);gg.tmin=np.r_[g.tmin,g.tmin[40]+separation];gg.tmax=np.r_[g.tmax,g.tmax[40]+separation]
 c=certificate(**{**args,'geometry':gg});assert not c['passed'] and c['reason']=='ambiguous_active_axis';negative.append(dict(kind='duplicate_competing_axis',separation=separation,reason=c['reason']))
# Keep every active support vertex; wrong axis/missing support set are rejected.
p=planes(g,args['x'],'left');active=np.flatnonzero(p[:,40]-.005<=1e-6)
for branch,vertices in [(127,active),(40,[])]:
 proof=prove_axis_stability(g,args['x'],'left',branch,vertices);assert not proof['passed'];negative.append(dict(kind='invalid_axis_or_vertex_set',reason=proof['reason']))
# Bound/extra/primal/nonfinite checks and objective rejection.
x=args['x'].copy();badlo=args['lower'].copy();badlo[0]=x[0]+.001
assert not certificate(**{**args,'lower':badlo})['primal_feasible'];negative.append(dict(kind='primal_bound'))
assert not certificate(**args,extra_values=[-.001],extra_jacobian=np.zeros((1,11)))['primal_feasible'];negative.append(dict(kind='extra_primal'))
grad=args['gradient'].copy();grad[0]+=10.;assert not certificate(**{**args,'gradient':grad})['passed'];negative.append(dict(kind='nonstationary_gradient'))
try:certificate(**{**args,'x':np.full(11,np.nan)})
except ValueError:negative.append(dict(kind='nonfinite'))
else:raise AssertionError('nonfinite accepted')
# Active vertex corner requires both normals, not an averaged/min gradient.
q=np.zeros(11);G=np.eye(11)[:2];grad=np.zeros(11);grad[:2]=[1.,2.];base=dict(geometry=g,x=q,gradient=grad,lower=np.full(11,-1.),upper=np.ones(11))
assert certificate(**base,extra_values=[0.,0.],extra_jacobian=G)['passed']
assert not certificate(**base,extra_values=[0.],extra_jacobian=np.array([(G[0]+G[1])/2]))['passed'];negative.append(dict(kind='averaged_corner_normal'))
for p in [Path(__file__),w/'support_vertex_stationarity.py',w/'support_vertex_stationarity_rigid_segment_v2.py',w/'audit_self_clearance_task_optimality.py',w/'staged_closed_peak_trial/elbow_torso_hulls.json',w.parents[1]/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',r/'RIGID_AXIS_CERTIFICATE_PREPARATION.json',r/'TASK_AXIS_SEPARATION_DIAGNOSTIC.json']:bind(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,version=VERSION,historical_cases=cases,historical_rows=sum(c['checked'] for c in cases),near_axis_actual_frame=actual,negative_checks=negative,source_sha256=sources,original_audit_changed=False,runtime_changed=False,training_ready=False)
with (r/'RIGID_AXIS_CERTIFICATE_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,historical_rows=report['historical_rows'],negative_checks=len(negative),actual_residual=actual['stationarity_residual'])),flush=True)
