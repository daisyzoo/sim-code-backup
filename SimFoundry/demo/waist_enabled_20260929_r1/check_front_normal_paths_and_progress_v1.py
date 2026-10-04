"""Original continuous static path proofs and independent task-progress check."""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';D=W/'front_normal_nondegradation_audit_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from joint_transport_paths import JointTransportPaths
from clearance_runtime import ClearanceGuard
from independent_cross_track_assets_v1 import independent_hand_model
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=W/'front_normal_nondegradation_probe_r1/RESULT.json';report=read(source);audit=read(D/'RESULT.json');assert audit['contexts']==audit['passed']==32;cs={c['step']:c for c in read(W/'front_effective_height_physical_r1/case_840020/layout_840020_push_box_to_bin/coordination.json')};g=ClearanceGuard(ROOT,S);hand=independent_hand_model(g);paths=JointTransportPaths(ROOT,S);rows=[]
for r in report['rows']:
 if r['command'] is None:continue
 t=r['step'];c=cs[t];tc=c['joint_transport_clearance']['collector_context'];sc=tc['scene'];q=np.array(tc['current']);qp=np.array(tc['previous_q']);prev=np.array(tc['previous_command']);a=np.array(tc['decay']);u=np.array(r['command']);normal=Rotation.from_quat(sc['target_quat']).as_matrix()[:,2];center=np.array(c['active_support_reference']['center_local']);sgn=np.sign(np.array(c['task_inputs']['error'])[3:5])
 def point(x):
  T=hand.fk(x,'right');n=T[:3,:3].T@normal;off=center+n*(min(hand.vertices['right']@n)-center@n);return T[:3,3]+T[:3,:3]@off
 def predict(x):return (1-a)*x+a*q+q-prev-a*(qp-prev)
 reference=point(q);v=predict(u);old=np.array(c['joint_transport_clearance']['output_command']);proofs={name:paths.certify(q,end,sc) for name,end in [('nominal',u),('predicted',v)]}
 deltas={name:(point(x)-reference)*1000 for name,x in [('nominal',u),('predicted',v),('old_nominal',old),('old_predicted',predict(old))]};unique=[]
 for name,transform in [('nominal',lambda x:x),('predicted',predict)]:
  ids=[];gaps=[]
  for d in [np.zeros(11)]+[sign*np.eye(11)[j]*2e-7 for j in range(11) for sign in [-1,1]]:
   T=hand.fk(transform(u+d),'right');s=hand.vertices['right']@(T[:3,:3].T@normal);o=np.sort(s);ids.append(int(np.argmin(s)));gaps.append(float(o[1]-o[0]))
  unique.append(dict(kind=name,unique_stable=len(set(ids))==1 and min(gaps)>1e-12,minimum_vertex_separation_m=min(gaps)))
 np.testing.assert_allclose(deltas['nominal'],r['nominal_delta_mm'],atol=1e-7,rtol=0);np.testing.assert_allclose(deltas['predicted'],r['predicted_delta_mm'],atol=1e-7,rtol=0)
 row=dict(step=t,paths=proofs,all_paths_passed=all(p['passed'] for p in proofs.values()),support_branches=unique,unique_support_branches=all(x['unique_stable'] for x in unique),delta_xyz_mm={k:v.tolist() for k,v in deltas.items()},signed_y_mm={k:float(sgn[1]*v[1]) for k,v in deltas.items()},signed_x_mm={k:float(sgn[0]*v[0]) for k,v in deltas.items()},normal_mm={k:float(normal@v) for k,v in deltas.items()});rows.append(row)
print('static paths completed',len(rows),flush=True)
summary=dict(contexts=len(rows),all_paths_passed=sum(r['all_paths_passed'] for r in rows),unique_branches=sum(r['unique_support_branches'] for r in rows),nominal_y_reversed=sum(r['signed_y_mm']['nominal']<-.0002 for r in rows),predicted_y_reversed=sum(r['signed_y_mm']['predicted']<-.0002 for r in rows),nominal_x_reversed=sum(r['signed_x_mm']['nominal']<-.0002 for r in rows),predicted_x_reversed=sum(r['signed_x_mm']['predicted']<-.0002 for r in rows),predicted_normal_worsened=sum(r['normal_mm']['predicted']>r['normal_mm']['old_predicted']+.0002 for r in rows),mean_signed_y_mm={k:float(np.mean([r['signed_y_mm'][k] for r in rows])) for k in rows[0]['signed_y_mm']},minimum_signed_nominal_y_mm=min(r['signed_y_mm']['nominal'] for r in rows),minimum_signed_predicted_y_mm=min(r['signed_y_mm']['predicted'] for r in rows),nominal_near_zero_x_steps=[r['step'] for r in rows if abs(r['signed_x_mm']['nominal'])<.001],predicted_outward_steps=[r['step'] for r in rows if r['normal_mm']['predicted']>.0002])
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,summary=summary,rows=rows,source_sha256={str(p):sha(p) for p in [Path(__file__),source,D/'RESULT.json',S/'joint_transport_paths.py']},training_ready=False,physics_started=False,limitations=['Original selected geometry continuous static paths only; no dynamic forces or full-body certification.','Predicted normal nondegradation allows existing outward forecast, not a no-loss guarantee.','Zero transverse correction can still be insufficient to restore corridor clearance.','Original2unloaded frames and front-bag contact losses remain unresolved.'])
with (D/'PATHS_AND_TASK_PROGRESS_V1.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
print(json.dumps(summary),flush=True)
