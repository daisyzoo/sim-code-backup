"""Real accepted/rejected inputs plus independent corner and fail-closed tests.
Supplemental versioned math verification, never overwrites a frozen native audit.
"""
from pathlib import Path
import sys,hashlib,json,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from support_vertex_stationarity import certificate,VERSION
from audit_self_clearance_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=Path(sys.argv[1]).resolve();out=r/'SUPPORT_VERTEX_STATIONARITY_CHECK.json';assert not out.exists();geom=IndependentElbows(W/'staged_closed_peak_trial/elbow_torso_hulls.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf');rows=[];sources={}
for c,task in [('840007','nudge_mailer_to_bin'),('840012','push_box_to_bin'),('840015','nudge_mailer_to_bin')]:
 ep=r/f'case_{c}'/f'layout_{c}_{task}';coord=json.loads((ep/'coordination.json').read_text());diagnosis=ep/'POSE_KKT_SUPPORT_VERTEX_DIAGNOSIS.json';prior={x['step']:x for x in json.loads(diagnosis.read_text())['rows']};checks=[]
 for row in coord:
  tr=row.get('self_clearance_task')
  if not tr or not tr.get('override'):continue
  inp=row['task_inputs'];q=np.array(inp['current']);prev=np.array(inp['previous']);x=np.array(tr['candidate_command']);J=np.array(inp['jacobian']);e=np.array(inp['error']);d=np.array(inp['damping']);lo=np.maximum.reduce([np.array(inp['lower']),q-inp['step_limits'],prev-.055]);hi=np.minimum.reduce([np.array(inp['upper']),q+inp['step_limits'],prev+.055]);grad=J.T@(J@(x-q)-e)+d*d*(x-q-inp['preferred_step']);cert=certificate(geometry=geom,x=x,gradient=grad,lower=lo,upper=hi)
  assert cert['primal_feasible'] and cert['reason']!='ambiguous_active_axis';p=prior[row['step']];assert abs(cert['stationarity_residual']-p['per_vertex_residual'])<1e-12;assert cert['passed']==p['per_vertex_stationary'];checks.append(dict(step=row['step'],**cert))
 assert len(checks)==len(prior);rows.append(dict(episode=ep.name,count=len(checks),failed=[x['step'] for x in checks if not x['passed']],checks=checks))
 for p in [ep/'coordination.json',diagnosis]:sources[str(p)]=sha(p)
 print(json.dumps({k:v for k,v in rows[-1].items() if k!='checks'}),flush=True)
assert rows[0]['failed']==[194] and rows[1]['failed']==rows[2]['failed']==[]
# Corner proof exercises the actual NNLS certificate's extra-inequality path.
q=np.zeros(11);lo=np.full(11,-1.);hi=np.ones(11);assert min(geom.gap(q))>.005001;G=np.eye(11)[:2];grad=np.zeros(11);grad[:2]=[1.,2.]
corner=certificate(geometry=geom,x=q,gradient=grad,lower=lo,upper=hi,extra_values=[0.,0.],extra_jacobian=G);assert corner['passed'] and corner['stationarity_residual']==0
single=certificate(geometry=geom,x=q,gradient=grad,lower=lo,upper=hi,extra_values=[0.],extra_jacobian=np.array([(G[0]+G[1])/2]));assert not single['passed']
noactive=certificate(geometry=geom,x=q,gradient=grad,lower=lo,upper=hi);assert not noactive['passed']
badextra=certificate(geometry=geom,x=q,gradient=np.zeros(11),lower=lo,upper=hi,extra_values=[-.0002],extra_jacobian=G[:1]);assert not badextra['primal_feasible']
badbound=q.copy();badbound[0]=1.1;assert not certificate(geometry=geom,x=badbound,gradient=np.zeros(11),lower=lo,upper=hi)['primal_feasible']
p=r/'case_840015/layout_840015_push_box_to_bin/JOINT_EDGE_CLEARANCE_INTERSECTION_PROBE.json';probe=json.loads(p.read_text());bad=np.array(probe['original_guard']['command']);assert not certificate(geometry=geom,x=bad,gradient=np.zeros(11),lower=np.full(11,-4.),upper=np.full(11,4.))['primal_feasible']
try:certificate(geometry=geom,x=np.full(11,np.nan),gradient=grad,lower=lo,upper=hi)
except ValueError:pass
else:raise AssertionError('nonfinite input accepted')
for p in [Path(__file__),W/'support_vertex_stationarity.py',W/'audit_self_clearance_task_optimality.py',W/'staged_closed_peak_trial/elbow_torso_hulls.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),version=VERSION,passed=True,episodes=rows,corner_residual=corner['stationarity_residual'],single_gradient_corner_residual=single['stationarity_residual'],negative_checks=6,source_sha256=sources,native_audit_changed=False,runtime_changed=False,training_ready=False)
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k not in ['episodes','source_sha256']},indent=2))
