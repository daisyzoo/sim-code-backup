"""Same-context full episode rear edge adapter/clearance/final guard diagnostic.
Actual q and previous actual commands remain fixed; no recursive physics replay.
All recorded rear edge contexts included, not only the original failure step.
"""
from pathlib import Path
import copy,datetime,functools,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
import joint_edge_inward_adapter as adapter
from joint_edge_clearance_adapter_candidate import repair_record
from joint_edge_inward_analytic_first_candidate_v3 import refine_rear_command as candidate
from audit_joint_edge_clearance_record import verify
from audit_inward_analytic_first_record_v1 import verify as verify_new_record
from audit_unloaded_wrist_prior_live import HandModel
from audit_self_clearance_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());R=W/'front_effective_height_physical_r1';ep=R/'case_840023/layout_840023_push_box_to_bin';D=W/'rear_box_analytic_first_chain_probe_r2';D.mkdir(exist_ok=False)
guard=ClearanceGuard(ROOT,S);hand=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json');elbows=IndependentElbows(S/'elbow_torso_hulls.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf')
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
with np.load(ep/'trace.npz') as z:xyz=z['box'].astype(float)
with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['box']).as_matrix()
fr=read(ep/'frontal_bypass.json');rows={r['step']:r for r in fr['rows']};core=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'];records=[];old_fn=adapter.refine_rear_command
for c in read(ep/'coordination.json'):
 if 'joint_edge_refinement' not in c:continue
 t=c['step'];a=c['task_inputs'];old=c['joint_edge_refinement'];row=rows[t];parent=np.array(old['parent_final_upper_command']);args=dict(enabled=True,row=row,coordinate=c,current=q[t],previous=u[t-1],parent_command=parent,object_xyz=xyz[t],object_rotation=rot[t],core_size=core,model=guard.model,side='right',analytic_retry=True,parent_seed_retry=True)
 # Two representative whole-record defaultoff parity checks plus all default
 # nonpush/ineligible guard outcomes; all selected outputs tested enabled below.
 if t in (225,226) or not old['input_selected'] or row['mode']!='top_push':
  adapter.refine_rear_command=old_fn;original,original_record=adapter.refine_record(**args)
  adapter.refine_rear_command=candidate;off,off_record=adapter.refine_record(**args)
  assert original_record==off_record and np.array_equal(original,off)
 adapter.refine_rear_command=functools.partial(candidate,analytic_first=True);command,trace=adapter.refine_record(**args);changed=copy.deepcopy(c);changed['joint_edge_refinement']=trace;repair=None;edge_check=None;error=None;final=command
 if row['mode']=='top_push' and old['input_selected']:
  offset=np.array(row['control_offset_local'])
  def ipoint(x):
   T=hand.fk(x,'right');return T[:3,3]+T[:3,:3]@offset
  def ipjac(x):
   h=2e-7;return ipoint(x),np.column_stack([(ipoint(x+np.eye(11)[j]*h)-ipoint(x-np.eye(11)[j]*h))/(2*h) for j in range(11)])
  local=rot[t].T@(np.array(row['rear_cop_centering']['cop_world'])-xyz[t])
  verify_new_record(trace,parent,command,u[t-1],q[t],np.array(a['jacobian']),np.array(a['error']),np.array(a['damping']),np.array(a['lower']),np.array(a['upper']),np.array(a['step_limits']),ipjac,rot[t],local,np.array(core),-1,[3,4,5],enabled=True)
 if trace['override']:
  final,repair=repair_record(guard=guard,row=row,coordinate=changed,current=q[t],previous=u[t-1],command=command,object_rotation=rot[t],object_xyz=xyz[t],core_size=core)
  if final is not None:
   changed['joint_edge_clearance_intersection']=repair
   try:edge_check=verify(hand=hand,elbows=elbows,coordinate=changed,row=row,trace=repair,q=q[t],previous=u[t-1],command=final,object_xyz=xyz[t],object_rotation=rot[t],core_size=core,lower=np.array(a['lower']),upper=np.array(a['upper']),limits=np.array(a['step_limits']))
   except AssertionError as e:error=repr(e)
 final_guard=None if final is None else guard.command(final,q[t],u[t-1]);record=dict(step=t,old_override=old['override'],candidate_override=trace['override'],candidate_reason=trace['reason'],emitted_stationarity=trace.get('emitted_stationarity'),edge_original_independent_audit=edge_check,edge_audit_error=error,repair=repair,final_guard=final_guard,command=None if final is None else final.tolist(),command_max_difference_rad=None if final is None else float(np.max(abs(final-u[t]))));records.append(record)
 if t%100==0:print(json.dumps(dict(step=t,contexts=len(records))),flush=True)
adapter.refine_rear_command=old_fn
sources={str(p):sha(p) for p in [Path(__file__),*[ep/n for n in ['raw.npz','coordination.json','frontal_bypass.json','trace.npz','parcel_orientation.npz']]]}
for m in list(sys.modules.values()):
 f=getattr(m,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
summary=dict(contexts=len(records),original_overrides=sum(r['old_override'] for r in records),candidate_overrides=sum(r['candidate_override'] for r in records),stationarity_rejections=sum(r['candidate_reason']=='final_stationarity_violation' for r in records),edge_audit_failures=[dict(step=r['step'],error=r['edge_audit_error']) for r in records if r['edge_audit_error']],original_final_guard_rejections=[r['step'] for r in records if not r['final_guard'] or not r['final_guard']['accepted']],clearance_repair_failures=[r['step'] for r in records if r['command'] is None])
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,summary=summary,records=records,source_sha256=sources,installed=False,training_ready=False,limitations=['Bound to one full rear-box episode with actual history retained; changed commands were never executed.','Unselected front priority/transport remain original identity on this episode; no claim of full source/stream/admission audit.','The new explicit stationarity-rejection reason still requires independent lifecycle/audit support before installation.'])
with (D/'RESULT.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(summary),flush=True)
