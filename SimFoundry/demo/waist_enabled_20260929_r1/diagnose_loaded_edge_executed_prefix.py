"""Independent executed-prefix diagnosis of an explicitly FAILED short episode.
Does not relax full-length admission or emit an admission audit. The unexecuted
stop at step862 is excluded and separately diagnosed, never counted as executed.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_loaded_edge_coverage';sys.path[:0]=[str(w),str(repo)]
from audit_loaded_edge_coverage_decision import verify_decision
from audit_unloaded_wrist_prior_live import HandModel
from audit_unloaded_wrist_task_optimality import IndependentElbows
p=w/'loaded_edge_coverage_groups_r1/case_840001/layout_840001_push_box_to_bin';read=lambda n:json.loads((p/n).read_text());quality=read('quality.json');assert quality['passed'] is False and quality['frames']==862
with np.load(p/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].copy()
with np.load(p/'trace.npz') as z:xyz=z['box'].astype(float)
with np.load(p/'parcel_orientation.npz') as z:quat=z['box'].astype(float)
fr=read('frontal_bypass.json');fs={r['step']:r for r in fr['rows']};cs={r['step']:r for r in read('coordination.json')};packets={r['after_action_step']:r for r in read('solved_contact_forces.json')['rows']};traces=read('loaded_edge_coverage.json')['rows'];assert traces[-1]['step']==len(q) and traces[-1]['accepted'] is False
urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=repo/'assets/robots/g1_hand_support_vertices.json';hand=HandModel(urdf,vertices);elbows=IndependentElbows(stage/'elbow_torso_hulls.json',urdf);records=[];errors=[]
for tr in traces[:-1]:
 t=tr['step'];assert t<len(q);c=cs[t];assert c['loaded_edge_coverage']==tr
 try:r=verify_decision(tr,row=fs[t],previous_row=fs.get(t-1),coordinate=c,current=q[t],previous_command=u[t-1],parent_command=c['joint_edge_refinement']['final_upper_command'],final_command=u[t],packet=packets[t-1],object_xyz=xyz[t],object_quat=quat[t],core_size=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'],side='right',selected=True,hand=hand,elbows=elbows)
 except AssertionError as e:r=dict(step=t,passed=False,error=str(e))
 records.append(r)
 if not r['passed']:errors.append(r)
assert len(records)==861
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();files=[p/n for n in ['raw.npz','trace.npz','parcel_orientation.npz','quality.json','frontal_bypass.json','coordination.json','solved_contact_forces.json','loaded_edge_coverage.json']]+[Path(__file__),w/'audit_loaded_edge_coverage_decision.py',w/'audit_loaded_edge_coverage_record.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py',stage/'elbow_torso_hulls.json',urdf,vertices]
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=p.name,executed_decisions=861,executed_overrides=sum(bool(r.get('override')) for r in records),prefix_math_passed=not errors,errors=errors,max_new_override_stationarity_residual=max((r.get('stationarity_residual',0) for r in records),default=0),records=records,source_sha256={str(f):sha(f) for f in files},episode_passed=False,training_ready=False)
(w/'LOADED_EDGE_FIRST_EXECUTED_PREFIX_DIAGNOSIS.json').write_text(json.dumps(out,indent=2));print({k:out[k] for k in ['executed_decisions','executed_overrides','prefix_math_passed','errors','max_new_override_stationarity_residual']})
