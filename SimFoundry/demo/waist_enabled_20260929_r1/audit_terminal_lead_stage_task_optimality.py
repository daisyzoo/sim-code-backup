"""Original task KKT mathematics, with separately verified unloaded joint paths.
Original loaded/ordinary task bounds, objective and1e-6 stationarity are retained.
A joint-path event is accepted here only after the independent full live audit.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from support_vertex_stationarity import certificate,VERSION
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_self_clearance_task_optimality import IndependentElbows,near
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
from simfoundry.data.bounded_ik import bounded_damped_step
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def verify_task_rows(ep,geom,verified_events):
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float);side='right' if str(z['task_id'])=='push_box_to_bin' else 'left'
 rows=json.loads((ep/'coordination.json').read_text());experts={x['step']:x for x in json.loads((ep/'expert_control.json').read_text())};failure=json.loads((ep/'self_clearance.json').read_text())['failure'];records=[]
 lo=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98;limits=np.r_[.015,np.full(10,.04)];damping=np.sqrt(np.array([np.float32(.12**2)]+[np.float32(.045**2)]*10)).astype(float)
 for c in rows:
  t=c['step']
  if t>=len(q):assert failure is not None;continue
  if c.get('controller_kind')=='verified_unloaded_recontact_joint_path':
   assert t in verified_events and c['recontact_pose_override']==verified_events[t]
   event=verified_events[t];assert event['kind'] in ('command','handover') and experts[t]['mode'] in ('top_cross','top_press')
   assert c['task_inputs'] is None and c['contact_normal_tracking'] is None and c['contact_bout_yaw_tracking'] is None
   near(event['command'],u[t],0);near(event['context']['current'],q[t],1e-7);near(event['context']['previous_command'],u[t-1],0)
   records.append(dict(step=t,override=False,declared_joint_path=True));continue
  assert t not in verified_events,'Declared recovery did not execute its verified branch'
  assert c['bounded_solver'] is True and c['contact_bout_yaw_tracking'] is None
  inp=c['task_inputs'];tr=c['self_clearance_task'];near(inp['current'],q[t],1e-6);near(inp['previous'],u[t-1],0);near(inp['lower'],lo,0);near(inp['upper'],hi,0);near(inp['step_limits'],limits,0);near(inp['damping'],damping,0)
  errors=[]
  for hand in ['left','right']:
   goal=experts[t]['target_xyz'] if hand==side else c['inactive_anchor'];point=c['control_point_positions'][hand];errors.extend(np.clip(np.float32(.72)*(np.array(goal,dtype=np.float32)-np.array(point,dtype=np.float32)),np.float32(-.035),np.float32(.035)).tolist())
  J=np.array(inp['jacobian']);E=np.array(inp['error']);assert J.shape[1]==11
  if 'control_jacobian_world' in c:near(J[:6],c['control_jacobian_world'],0)
  normal=c['contact_normal_tracking']
  if normal is not None:errors.extend(np.asarray(normal['error'],dtype=np.float32).tolist());near(J[6:],np.asarray(normal['jacobian'],dtype=np.float32),0)
  else:assert J.shape==(6,11)
  near(E,errors,0);prior=np.zeros(11);prior[0]=c['preferred_waist_step_rad'];near(inp['preferred_step'],prior,0)
  if c['waist_preference_rad'] is None:assert prior[0]==0
  else:near(prior[0],float(np.float32(np.clip(np.float32(.15)*np.float32(c['waist_preference_rad']-q[t,0]),-.015,.015))),1e-7)
  baseline=(q[t]+bounded_damped_step(J,E,q[t],lo,hi,limits,damping,preferred_step=prior)).astype(np.float32).astype(float)
  low=np.maximum.reduce([lo,q[t]-limits,u[t-1]-.055]);high=np.minimum.reduce([hi,q[t]+limits,u[t-1]+.055]);assert np.all(low<high)
  baseline_valid=bool(np.all(baseline>=low-2e-7) and np.all(baseline<=high+2e-7) and min(geom.gap(baseline))>=.005-2e-7)
  assert tr['accepted'] is True and type(tr['override']) is bool
  if not tr['override']:
   assert baseline_valid and tr['reason']=='original_task_solution_clear';records.append(dict(step=t,override=False));continue
  assert not baseline_valid and tr['solver_success'] is True and tr['status']==0 and 0<tr['iterations']<=150
  x=np.array(tr['candidate_command']);near(x,x.astype(np.float32),0);near(tr['parent_command'],baseline,0);near(tr['previous_command'],u[t-1],0)
  gap=geom.gap(x);near(gap,tr['candidate_gaps_m'],2e-10);assert min(gap)>=.005-2e-7 and np.all(x>=low-2e-7) and np.all(x<=high+2e-7)
  delta=x-q[t];near(tr['task_residual_m'],J@delta-E,1e-10);gradient=J.T@(J@delta-E)+damping*damping*(delta-prior)
  cert=certificate(geometry=geom,x=x,gradient=gradient,lower=low,upper=high)
  records.append(dict(step=t,override=True,kkt_residual=cert['stationarity_residual'],stationary=cert['passed'],vertex_certificate=cert))
 bad=[r for r in records if r.get('stationary') is False];return dict(passed=not bad,errors=bad,frames=len(records),overrides=sum(r['override'] for r in records),max_kkt_residual=max((r.get('kkt_residual') or 0 for r in records),default=0),records=records,scope=__doc__,training_ready=False,source_sha256={n:sha(ep/n) for n in ['raw.npz','coordination.json','expert_control.json','self_clearance.json']},auditor_sha256=sha(Path(__file__)))

def inspect(ep):
 from audit_terminal_lead_stage_pose_live import inspect as inspect_pose,source_contract
 ep=Path(ep).resolve();stage=source_contract(ep);pose=inspect_pose(ep)
 assert pose==json.loads((ep/'TERMINAL_LEAD_STAGE_POSE_LIVE_V2_AUDIT.json').read_text())
 prov=json.loads((ep.parent/'provenance.json').read_text());src=prov['source_sha256'];snap=ep.parent/'source_snapshot'
 assert not prov['args'].get('expert_top_contact_bout_yaw_hold')
 for n in ['simfoundry/robots/g1_assets.py','simfoundry/data/bounded_ik.py']:assert sha(repo/n)==src[n]
 names=[n for n in src if n.endswith('/task_ik.py')];assert len(names)==1 and sha(snap/names[0])==sha(w/'staged_rear_short_recovery/task_ik.py')
 events={r['step']:{k:v for k,v in r.items() if k!='step'} for r in json.loads((ep/'recontact_pose.json').read_text())['rows'] if r['kind'] in ('command','handover')}
 assert set(events)=={r['step'] for r in pose['records']}
 geom=IndependentElbows(stage/'elbow_torso_hulls.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf')
 out=verify_task_rows(ep,geom,events);out.update(pose_audit_sha256=sha(ep/'TERMINAL_LEAD_STAGE_POSE_LIVE_V2_AUDIT.json'),pose_auditor_sha256=sha(w/'audit_terminal_lead_stage_pose_live.py'),original_auditor_sha256=sha(w/'audit_self_clearance_task_optimality.py'))
 out.update(stationarity_version=VERSION,math_revision_manifest_sha256=sha(w/'POSE_TASK_VERTEX_V2_REVISION.json'),vertex_certificate_source_sha256=sha(w/'support_vertex_stationarity.py'),frozen_parent_auditor_sha256=sha(w/'audit_closed_peak_trial_pose_task_optimality.py'),original_episode_parent_report_required=False,admission_protocol_changed=False)
 return out
if __name__=='__main__':
 ep=Path(sys.argv[1]);path=ep/'TERMINAL_LEAD_STAGE_TASK_OPTIMALITY_V2_AUDIT.json';assert not path.exists();out=inspect(ep);path.write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ['records','scope','source_sha256']});sys.exit(0 if out['passed'] else 1)
