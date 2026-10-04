"""Six actual saved recovery contexts; shifted preferred contact feasibility only.
Includes passing parent and failing latest run. No physics or force predictions.
Original geometry/path/selection checks retained with explicit changed objective.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_joint_transport_v1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from offset_plan import plan
from offset_audit import PlanAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S);audit=PlanAudit(ROOT,S);rows=[];sources={};result=D/'RESULT.json';assert not result.exists()
def save(complete):
 for mod in list(sys.modules.values()):
  f=getattr(mod,'__file__',None)
  if f:
   p=Path(f).resolve()
   if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
 for p in [D/'PLAN.json',D/'probe.py',D/'offset_plan.py',D/'offset_audit.py',S/'elbow_torso_hulls.json',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:sources[str(p)]=sha(p)
 result.write_text(json.dumps(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),complete=complete,scope=__doc__,rows=rows,source_sha256=sources,physical_execution=False,contact_success_established=False,training_ready=False),indent=2))
for run in ['front_box_recenter_physical_r2','joint_transport_physical_r1']:
 ep=W/run/'case_840023/layout_840023_push_box_to_bin';p=ep/'recontact_pose.json';events=json.loads(p.read_text())['rows'];sources[str(p)]=sha(p)
 with np.load(ep/'raw.npz',allow_pickle=False) as z:actual=z['q'][:,12:23].copy()
 sources[str(ep/'raw.npz')]=sha(ep/'raw.npz')
 starts=[e for e in events if (e.get('planning') or {}).get('box_center_preference_pose') is not None];assert len(starts)>=3
 for i in [0,len(starts)//2,len(starts)-1]:
  e=starts[i];q=np.asarray(e['context']['current']);np.testing.assert_array_equal(q,actual[e['step']]);scene=RecontactScene(guard,**e['context']['scene']);parent=e['planning']['box_center_preference_pose']['parent_plan']
  restored=plan(scene,q,step=e['step'],parent_plan=parent,preferred_xy=np.zeros(2));assert {k:v for k,v in restored.items() if k!='scope'}=={k:v for k,v in e['planning'].items() if k!='scope'},'Zero-offset must exactly reproduce all recorded original plan values; only explicit probe scope prose differs'
  audit.preferred_xy=np.zeros(2);audit.verify_preference(restored,current=q,scene=scene.record(),step=e['step'])
  direction=(scene.rotation.T@np.array([0.,1.,0.]))[:2];preferred=.020*direction/np.linalg.norm(direction)
  proposed=plan(scene,q,step=e['step'],parent_plan=parent,preferred_xy=preferred);audit.preferred_xy=preferred;proof=audit.verify_preference(proposed,current=q,scene=scene.record(),step=e['step']);_,old=audit.geometry(restored['endpoint'],scene.record());_,new=audit.geometry(proposed['endpoint'],scene.record());neg=[]
  if proposed['box_center_preference_pose']['endpoint_attempts']:
   broken=copy.deepcopy(proposed);broken['box_center_preference_pose']['endpoint_attempts'][0]['objective']+=1
   try:audit.verify_preference(broken,current=q,scene=scene.record(),step=e['step'])
   except AssertionError:neg.append('corrupted_objective')
   else:raise AssertionError('Corrupt objective accepted')
  row=dict(run=run,step=e['step'],context_index=i,zero_offset_reproduces_all_original_values_except_scope_prose=True,preferred_xy_m=preferred.tolist(),selection=proof['selected'],original_local_point_m=old['point'].tolist(),candidate_local_point_m=new['point'].tolist(),original_waypoints=len(restored['waypoints']),candidate_waypoints=len(proposed['waypoints']),independent_original_geometry_and_shifted_objective_passed=True,negative_rejections=neg,proposal=proposed);rows.append(row);save(False);print(json.dumps({k:v for k,v in row.items() if k!='proposal'}),flush=True)
assert len(rows)==6;save(True);print('SIX_UNISSUED_CONTEXTS_COMPLETE',flush=True)
