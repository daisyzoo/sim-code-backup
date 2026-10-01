"""Replay unchanged normal audit against eight physical parent records and test
explicit measured reanchor plus stale/undeclared-anchor rejection on fixtures.
New-branch fixtures are not physical evidence.
"""
from pathlib import Path
import sys,json,hashlib,copy
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_unloaded_wrist_prior_live import HandModel
from audit_recontact_pose_normal import verify_normal_rows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();model=HandModel(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');results=[]
for ep in sorted((w/'unloaded_wrist_prior_groups_r1').glob('case_*/layout_*')):
 if not (ep/'frontal_bypass.json').exists():continue
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float)
 coords=json.loads((ep/'coordination.json').read_text());experts={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};topsteps={r['step'] for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};side='right' if 'push_box' in ep.name else 'left'
 r=verify_normal_rows(q,coords,experts,topsteps,{},model,side)
 results.append(dict(episode=ep.name,**{k:v for k,v in r.items() if k!='records'},source_sha256={n:sha(ep/n) for n in ['raw.npz','coordination.json','expert_control.json','frontal_bypass.json']}));print(ep.name,r['normal_frames'],flush=True)
assert len(results)==8
fixture=w/'staged_recontact_pose_probe/LIFECYCLE_CHECK.json';data=json.loads(fixture.read_text());synthetic=[];rejections=[]
for case in data['rows']:
 side='right' if 'push_box' in case['episode'] else 'left'
 for plant in case['plants']:
  ev=copy.deepcopy(plant['trace'][-1]);assert ev['kind']=='handover';q0=np.array(ev['context']['current']);q1=q0.copy();q1[5 if side=='left' else 10]+=.002
  current=model.fk(q1,side)[2,:3];anchor=np.array(ev['captured_normal_local_up']);old=anchor+np.array([.03,0,0]);mode={1:dict(mode='top_press'),2:dict(mode='top_push')}
  normal=dict(current_local_up=current.tolist(),target_local_up=anchor.tolist(),error=(.15*np.clip(.72*(anchor-current),-.1,.1)).tolist(),angle_error_rad=float(np.arccos(np.clip(current@anchor,-1,1))),weight_m=.15,jacobian=np.zeros((3,11)).tolist())
  rows=[dict(step=1,controller_kind='verified_unloaded_recontact_joint_path',contact_normal_tracking=None,task_inputs=None,recontact_pose_override=ev),dict(step=2,contact_normal_tracking=normal)]
  q=np.array([q0,q0,q1]);r=verify_normal_rows(q,rows,mode,{1,2},{1:ev},model,side);assert r['normal_frames']==1 and r['measured_recapture_steps']==[1];synthetic.append(dict(episode=case['episode'],plant=plant['summary']['plant'],start=case['step']))
  for kind in ['stale_anchor','missing_declaration','normal_task_during_joint_path','bad_capture']:
   bad=copy.deepcopy(rows);events={1:copy.deepcopy(ev)}
   if kind=='stale_anchor':bad[1]['contact_normal_tracking']['target_local_up']=old.tolist()
   if kind=='missing_declaration':events={}
   if kind=='normal_task_during_joint_path':bad[0]['contact_normal_tracking']=normal
   if kind=='bad_capture':events[1]['captured_normal_local_up']=old.tolist();bad[0]['recontact_pose_override']=events[1]
   try:verify_normal_rows(q,bad,mode,{1,2},events,model,side)
   except AssertionError:rejections.append(kind)
   else:raise AssertionError('Accepted '+kind)
out=dict(passed=True,scope=__doc__,parent_physical_rows=results,synthetic_handovers=len(synthetic),rejected_corruptions=len(rejections),fixture_sha256=sha(fixture),source_sha256={str(p):sha(p) for p in [Path(__file__),w/'audit_recontact_pose_normal.py',w/'audit_unloaded_wrist_prior_live.py',repo/'simfoundry/calibration/sorting_station.py',repo/'assets/robots/g1_hand_support_vertices.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']},new_candidate_physical_validation=False,training_ready=False)
(w/'staged_recontact_pose/NORMAL_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',len(results),len(synthetic),len(rejections),flush=True)
