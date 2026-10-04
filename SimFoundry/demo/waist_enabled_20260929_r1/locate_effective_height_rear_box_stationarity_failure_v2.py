"""Reuse the unchanged independent record auditor to localize its failure.
This is a diagnostic subset, not a replacement for full original source/control
audits. The original failure, tolerance and report remain untouched.
"""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from audit_joint_edge_clearance_record import verify
from audit_unloaded_wrist_prior_live import HandModel
from audit_self_clearance_task_optimality import IndependentElbows
R=W/'front_effective_height_physical_r1';ep=R/'case_840023/layout_840023_push_box_to_bin';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prov=read(ep.parent/'provenance.json');snap=ep.parent/'source_snapshot'
def archived(name):
 ps=[snap/n for n in prov['source_sha256'] if n.endswith('/'+name)];assert len(ps)==1;p=ps[0];assert sha(p)==prov['source_sha256'][str(p.relative_to(snap))];return p
urdf=archived('g1_23dof_rev_1_0_u1_black.urdf');vertices=archived('g1_hand_support_vertices.json');hulls=archived('elbow_torso_hulls.json');hand=HandModel(urdf,vertices);elbows=IndependentElbows(hulls,urdf)
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
with np.load(ep/'trace.npz') as z:xyz=z['box'].astype(float)
with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['box']).as_matrix()
fr=read(ep/'frontal_bypass.json');rows={r['step']:r for r in fr['rows']};core=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'];out=[]
for c in read(ep/'coordination.json'):
 if 'joint_edge_clearance_intersection' not in c:continue
 t=c['step'];a=c['task_inputs'];kw=dict(hand=hand,elbows=elbows,coordinate=c,row=rows[t],trace=c['joint_edge_clearance_intersection'],q=q[t],previous=u[t-1],command=u[t],object_xyz=xyz[t],object_rotation=rot[t],core_size=core,lower=np.array(a['lower']),upper=np.array(a['upper']),limits=np.array(a['step_limits']))
 try:result=verify(**kw);out.append(dict(step=t,passed=True,result=result))
 except AssertionError as e:out.append(dict(step=t,passed=False,error=repr(e),recorded_intersection_changed=c['joint_edge_clearance_intersection']['changed']));print(json.dumps(out[-1]),flush=True)
files=[Path(__file__),urdf,vertices,hulls,*[ep/n for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json','audit_front_effective_height_r1_v3_stage_self_clearance.py.log']]];sources={str(p):sha(p) for p in files}
for m in list(sys.modules.values()):
 f=getattr(m,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=out,failures=[x for x in out if not x['passed']],checked_intersections=len(out),original_stationarity_threshold=1e-6,original_failure_unchanged=True,source_sha256=sources,training_ready=False)
with (R/'REAR_BOX_STATIONARITY_FAILURE_LOCALIZATION_V2.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(checked=len(out),failures=report['failures'])))
