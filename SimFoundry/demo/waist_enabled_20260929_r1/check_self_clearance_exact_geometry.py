"""Independent finite difference and old LP-witness consistency for bilateral guard."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_self_clearance_exact_probe';sys.path[:0]=[str(repo),str(stage),str(w/'staged_joint_edge_command')]
from articulated_hand_geometry import ArticulatedHandGeometry
from self_clearance import BilateralElbowClearance
from pose_projection import project
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');g=BilateralElbowClearance(model,stage/'elbow_torso_hulls.json');checks=0;maxerror=0.;rng=np.random.default_rng(2034)
for cid,task in [(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin')]:
 with np.load(w/f'joint_edge_retry_groups_r1/case_{cid}/layout_{cid}_{task}/raw.npz') as z:q=z['q'][:,12:23].astype(float)
 for t in np.unique(np.r_[0,np.arange(5,1200,17),rng.integers(0,1200,20)]):
  for side in ['left','right']:
   actual=g.evaluate(q[t],side);numeric=[]
   for i in range(11):d=np.zeros(11);d[i]=1e-6;numeric.append((g.evaluate(q[t]+d,side)['gap']-g.evaluate(q[t]-d,side)['gap'])/2e-6)
   error=float(np.max(abs(np.array(numeric)-actual['jacobian'])));assert error<1e-6,(cid,t,side,error);maxerror=max(maxerror,error);checks+=1
 original=json.loads((w/'RECORDED_FULL_ELBOW_TORSO_CHECK.json').read_text());ep=next(e for e in original['rows'] if e['episode']==f'layout_{cid}_{task}')
 for sample in ep['samples']:
  if sample.get('intersects'):assert g.evaluate(q[sample['step']],sample['side'])['gap']<=0
lo=np.array(U1_JOINT_LIMIT_LO)[12:23];hi=np.array(U1_JOINT_LIMIT_HI)[12:23];lo[0]=-.98;hi[0]=.98
for first in [False,True]:
 command,trace=project(enabled=True,parent=np.zeros(11),previous=np.zeros(11),model=model,geometry=g,lo=lo,hi=hi,side='left',offset=[.2,0,.007],first=first);assert np.array_equal(command,np.zeros(11))
for _ in range(50):
 parent=rng.normal(size=11).astype(np.float32);command,trace=project(enabled=False,parent=parent,previous=None,model=None,geometry=None,lo=None,hi=None,side=None,offset=None);assert np.array_equal(command,parent) and trace is None
out=dict(jacobian_checks=checks,max_jacobian_error=maxerror,all_old_lp_intersections_not_marked_separated=True,default_off_identity_cases=50,zero_first_and_wait_unchanged=True,source_sha256={p.name:sha(p) for p in [stage/'self_clearance.py',stage/'pose_projection.py',stage/'elbow_torso_hulls.json']},checker_sha256=sha(Path(__file__)),training_ready=False);(stage/'GEOMETRY_CHECK.json').write_text(json.dumps(out,indent=2));print(out)
