"""Actual blocked record/staged adapter output and corrupted-record negatives."""
from pathlib import Path
import json,hashlib,datetime,sys,copy
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from audit_joint_edge_clearance_record import verify
from audit_self_clearance_task_optimality import IndependentElbows
from audit_unloaded_wrist_prior_live import HandModel
r=Path(sys.argv[1]).resolve();ep=r/'case_840015/layout_840015_push_box_to_bin';s=W/'staged_joint_edge_clearance_intersection';output=s/'INDEPENDENT_RECORD_AUDIT_CHECK.json';assert not output.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
urdf=ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';verts=ROOT/'assets/robots/g1_hand_support_vertices.json';hulls=s/'elbow_torso_hulls.json';hand=HandModel(urdf,verts);elbows=IndependentElbows(hulls,urdf);check=json.loads((s/'CHECK.json').read_text());change=check['changes'][0];t=change['step'];coord=next(c for c in json.loads((ep/'coordination.json').read_text()) if c['step']==t);fr=json.loads((ep/'frontal_bypass.json').read_text());row=next(f for f in fr['rows'] if f['step']==t);inp=coord['task_inputs']
with np.load(ep/'substep_contacts.npz') as z:
 i=int(np.flatnonzero(z['action_step']==t-1)[-1]);pose=z['body_q'][i,0].astype(float)
args=dict(hand=hand,elbows=elbows,coordinate=coord,row=row,trace=change['trace'],q=coord['upper_q'],previous=coord['joint_edge_refinement']['previous_upper_command'],command=change['output'],object_xyz=pose[:3],object_rotation=Rotation.from_quat(pose[3:]).as_matrix(),core_size=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'],lower=np.array(inp['lower']),upper=np.array(inp['upper']),limits=np.array(inp['step_limits']))
positive=verify(**args);negative=[]
for name in ['old_unsafe_command','shifted_previous','forged_edge_goal','wrong_source_rotation','unjustified_nochange']:
 bad=dict(args);bad['trace']=copy.deepcopy(args['trace'])
 if name=='old_unsafe_command':bad['command']=coord['joint_edge_refinement']['final_upper_command'];bad['trace']['output_command']=bad['command']
 elif name=='shifted_previous':bad['previous']=np.array(args['previous'])+.001
 elif name=='forged_edge_goal':bad['row']=copy.deepcopy(row);bad['row']['target_xyz'][1]+=.01
 elif name=='wrong_source_rotation':bad['object_rotation']=np.eye(3)
 else:bad['trace']['changed']=False;bad['trace']['reason']='original_final_guard_passed'
 try:verify(**bad)
 except (AssertionError,ValueError):negative.append(name)
 else:raise AssertionError(('corruption accepted',name))
files=[Path(__file__),W/'audit_joint_edge_clearance_record.py',W/'support_vertex_stationarity.py',W/'audit_box_inward_refinement.py',W/'audit_unloaded_wrist_prior_live.py',W/'audit_self_clearance_task_optimality.py',s/'CHECK.json',ep/'coordination.json',ep/'frontal_bypass.json',ep/'substep_contacts.npz',urdf,verts,hulls]
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,episode=ep.name,step=t,independent_result=positive,negative_checks=negative,source_sha256={str(p):sha(p) for p in files},scope='Independent single-record joint constraints and stationarity; source CLI/stage checks separate, no physical rollout or admission.',training_ready=False)
with output.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','independent_result']},indent=2));print('stationarity',positive['certificate']['stationarity_residual'])
