"""Independent snapshot/FK/raw-action/runtime-body geometry audit.
Never imports clearance_runtime, self_clearance or task_ik. Records failures as
failures. This is not the original contact/control/visual/training admission.
"""
from pathlib import Path
import sys,json,hashlib,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
from simfoundry.calibration.sorting_station import SORTING_ROBOT_POS,SORTING_ROBOT_ROT_XYZW
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
from simfoundry.data.bounded_ik import bounded_damped_step
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def near(a,b,tol=2e-7):
 a,b=np.asarray(a,dtype=float),np.asarray(b,dtype=float)
 assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all() and np.max(abs(a-b),initial=0)<=tol

def audit(ep,verified_events=None,*,verified_front_events=None,verified_front_recovery_events=None):
 ep=Path(ep).resolve();case=ep.parent;prov=json.loads((case/'provenance.json').read_text());assert prov['args']['self_clearance_task_ik'] is True and not prov['args']['policy_port'];snap=case/'source_snapshot';sources=prov['source_sha256']
 for name,h in sources.items():assert sha(snap/name)==h
 for name in ['simfoundry/calibration/sorting_station.py','simfoundry/robots/g1_assets.py','simfoundry/data/bounded_ik.py']:assert sha(repo/name)==sources[name]
 def archived(name):
  names=[n for n in sources if n.endswith('/'+name)];assert len(names)==1;return snap/names[0]
 hulls=json.loads(archived('elbow_torso_hulls.json').read_text());urdf=archived('g1_23dof_rev_1_0_u1_black.urdf');assert sha(urdf)==hulls['urdf_sha256']
 for path,h in hulls['usd_layers_sha256'].items():assert sources[str(Path(path).relative_to(repo))]==h
 xml=ET.parse(urdf).getroot();children={j.find('child').get('link'):j for j in xml.findall('joint')}
 names=['waist_yaw_joint']+[s+'_'+j+'_joint' for s in ['left','right'] for j in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll']];chains={}
 for link in ['torso_link','left_elbow_link','right_elbow_link']:
  chain=[];l=link
  while l in children:
   j=children[l];origin=j.find('origin');M=np.eye(4)
   if origin is not None:M[:3,3]=np.fromstring(origin.get('xyz','0 0 0'),sep=' ');M[:3,:3]=Rotation.from_euler('xyz',np.fromstring(origin.get('rpy','0 0 0'),sep=' ')).as_matrix()
   axis=None if j.find('axis') is None else np.fromstring(j.find('axis').get('xyz'),sep=' ');chain.append((j.get('name'),M,axis));l=j.find('parent').get('link')
  chains[link]=list(reversed(chain))
 def fk(q):
  poses={}
  for link,chain in chains.items():
   M=np.eye(4);M[:3,3]=SORTING_ROBOT_POS;M[:3,:3]=Rotation.from_quat(SORTING_ROBOT_ROT_XYZW).as_matrix()
   for name,O,axis in chain:
    M=M@O
    if axis is not None:
     R=np.eye(4);R[:3,:3]=Rotation.from_rotvec(axis*(q[names.index(name)] if name in names else 0.)).as_matrix();M=M@R
   poses[link]=M
  return poses
 z=np.linspace(-1,1,80);theta=np.arange(80)*np.pi*(3-np.sqrt(5));axes=np.vstack([np.eye(3),np.stack([np.sqrt(1-z*z)*np.cos(theta),np.sqrt(1-z*z)*np.sin(theta),z],axis=1)])
 tv=np.array(hulls['torso']['vertices']);tp=tv@axes.T
 def gap(poses):
  torso=np.array(poses['torso_link']);out=[]
  for side in ['left','right']:
   arm=np.array(poses[side+'_elbow_link']);relative=np.linalg.inv(torso)@arm;v=np.array(hulls[side]['vertices'])@relative[:3,:3].T+relative[:3,3];p=v@axes.T
   out.append(float(max(np.max(p.min(0)-tp.max(0)),np.max(tp.min(0)-p.max(0)))))
  return np.array(out)
 runtime=json.loads((case/'runtime_geometry_provenance.json').read_text());assert runtime['usd_layers_sha256']==hulls['usd_layers_sha256']
 assert sha(case/'runtime_configuration.json')==runtime['configuration_sha256'];assert sha(case/'runtime_collision_arrays.npz')==runtime['collision_arrays_sha256']
 for item in runtime['source_files'].values():assert sha(case/item['snapshot'])==item['sha256']
 record=json.loads((ep/'self_clearance.json').read_text());quality=json.loads((ep/'quality.json').read_text());rows=record['rows'];count=record['recorded_frames'];failure=record['failure']
 if count==0:
  assert failure is not None and not quality['passed'] and not (ep/'raw.npz').exists()
  return dict(passed=True,executed_frames=0,episode_clearance_passed=False,failure=failure,scope=__doc__,training_ready=False)
 with np.load(ep/'raw.npz') as raw:q=raw['q'][:,12:23].copy();u=raw['action'][:,12:23].copy();intrinsics=raw['intrinsics'].copy();meta=json.loads(str(raw['collect_meta']));task=str(raw['task_id'])
 if verified_events is None:
  from audit_joint_transport_j1_v1_stage_pose_live import inspect as inspect_pose,source_contract
  source_contract(ep)
  if task=='wait_no_package':verified_events={}
  else:
   pose=inspect_pose(ep);assert pose==json.loads((ep/'JOINT_TRANSPORT_J1_V1_STAGE_POSE_LIVE_V2_AUDIT.json').read_text())
   verified_events={r['step']:{k:v for k,v in r.items() if k!='step'} for r in json.loads((ep/'recontact_pose.json').read_text())['rows'] if r['kind'] in ('command','handover')}
   assert set(verified_events)=={r['step'] for r in pose['records']}
 if verified_front_events is None:
  if task=='wait_no_package':verified_front_events={}
  else:
   from joint_transport_j1_v1_stage_audit_context import verified_front_events as checked_front
   verified_front_events=checked_front(ep)
 if verified_front_recovery_events is None:
  if task=='wait_no_package':verified_front_recovery_events={}
  else:
   from joint_transport_j1_v1_stage_audit_context import verified_front_recovery_events as checked_recovery
   verified_front_recovery_events=checked_recovery(ep)
 assert not set(verified_events)&set(verified_front_events)
 assert not (set(verified_events)|set(verified_front_events))&set(verified_front_recovery_events)
 verified_events={**verified_events,**verified_front_events,**verified_front_recovery_events}
 assert q.shape==u.shape==(count,11);near(q[0],np.zeros(11),1e-4);near(u[0],np.zeros(11),0);assert meta['assist_frames']==0 and meta['self_clearance_task_ik'] is True and meta['self_clearance_failure']==failure
 grouped={}
 for row in rows:
  key=(row['step'],row['phase']);assert key not in grouped;grouped[key]=row
 lo=np.array(U1_JOINT_LIMIT_LO)[12:23];hi=np.array(U1_JOINT_LIMIT_HI)[12:23];lo[0]=-.98;hi[0]=.98;limits=np.r_[.015,np.full(10,.04)];measured_min=[];command_min=[]
 for t in range(count):
  pre=grouped[(t,'pre')];final=grouped[(t,'final_command')];post=grouped[(t,'post')]
  assert pre['accepted'] is True and final['accepted'] is True
  near(pre['upper_q'],q[t],1e-6);near(final['command'],u[t],0);near(final['current'],q[t],1e-6);near(final['previous'],np.zeros(11) if t==0 else u[t-1],0)
  expected_gaps=gap(fk(u[t]));near(final['gaps_m'],expected_gaps,2e-10)
  assert min(expected_gaps)>=.005-2e-7;assert np.all(u[t]>=lo-2e-7) and np.all(u[t]<=hi+2e-7);assert np.all(abs(u[t]-q[t])<=limits+2e-7)
  if t:assert np.max(abs(u[t]-u[t-1]))<=.0550002
  command_min.append(float(min(expected_gaps)))
  for row in [pre,post]:
   actual={k:np.array(v) for k,v in row['runtime_link_poses'].items()};measured=np.array(row['upper_q']);nominal=fk(measured);coherent=True
   for name in nominal:
    near(actual[name][3],[0,0,0,1],1e-8);near(actual[name][:3,:3].T@actual[name][:3,:3],np.eye(3),1e-6);assert np.linalg.det(actual[name][:3,:3])>.999999
    pos=float(np.linalg.norm(actual[name][:3,3]-nominal[name][:3,3]));angle=float(Rotation.from_matrix(nominal[name][:3,:3].T@actual[name][:3,:3]).magnitude());near([pos,angle],[row['nominal_runtime_errors'][name]['position_m'],row['nominal_runtime_errors'][name]['angle_rad']],2e-10);coherent=coherent and pos<=1e-4 and angle<=1e-4
   gaps=gap(actual);near(gaps,row['runtime_support_gaps_m'],2e-10);near(gap(nominal),row['nominal_support_gaps_m'],2e-10);assert row['model_coherent']==coherent and row['accepted']==bool(coherent and min(gaps)>0);measured_min.append(float(min(gaps)))
  if t+1<count:near(post['upper_q'],q[t+1],1e-6)
  elif not post['accepted']:assert failure is not None and failure['phase']=='post' and failure['step']==t
 # New final refinement is verified independently against actual raw history.
 from audit_joint_transport_j1_v1_execution import inspect as inspect_priority
 priority_validation=inspect_priority(ep)
 assert priority_validation['passed'] and not priority_validation['fixture_only']
 from joint_transport_command_ledger_v1 import load_transport_ledger
 transport_parent,transport_proof=load_transport_ledger(ep)
 priority_records={r['step']:r for r in json.loads((ep/'front_loaded_z_priority.json').read_text())['rows']}
 # Reconstruct the command chain, preserving the original subsequent overrides.
 coordinates=json.loads((ep/'coordination.json').read_text()) if (ep/'coordination.json').exists() else []
 terminals={r['step']:r for r in json.loads((ep/'terminal_joint_hold.json').read_text())['rows']} if (ep/'terminal_joint_hold.json').exists() else {}
 from audit_unloaded_wrist_prior_live import HandModel
 from audit_self_clearance_task_optimality import IndependentElbows
 from audit_joint_edge_clearance_record import verify as verify_intersection
 hand=HandModel(urdf,archived('g1_hand_support_vertices.json'));independent_elbows=IndependentElbows(archived('elbow_torso_hulls.json'),urdf)
 intersection_rows=[]
 if task!='wait_no_package':
  target_key='box' if task=='push_box_to_bin' else 'mailer'
  with np.load(ep/'trace.npz') as z:parcel_xyz=z[target_key].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:parcel_rot=Rotation.from_quat(z[target_key]).as_matrix()
  frontal=json.loads((ep/'frontal_bypass.json').read_text());frontal_rows={f['step']:f for f in frontal['rows']};core=frontal['plan'].get('region_causal_response',{}).get('actual_core',{}).get('collision_core_size_xyz')
 assert prov['args']['edge_clearance_intersection'] is True and meta['edge_clearance_intersection'] is True
 controller_frames=0;overrides=0
 for c in coordinates:
  t=c['step']
  if t>=count:assert failure is not None;continue
  if c.get('controller_kind') in ('verified_unloaded_recontact_joint_path','verified_unloaded_front_initial_joint_path','verified_unloaded_front_recontact_joint_path'):
   kind,field=('verified_unloaded_front_recontact_joint_path','front_recontact_center_override') if t in verified_front_recovery_events else ('verified_unloaded_front_initial_joint_path','front_initial_center_override') if t in verified_front_events else ('verified_unloaded_recontact_joint_path','recontact_pose_override')
   assert c['controller_kind']==kind and t in verified_events and c[field]==verified_events[t]
   assert all(c.get(k) is None for k in ('recontact_pose_override','front_initial_center_override','front_recontact_center_override') if k!=field)
   if t in verified_front_recovery_events:assert c['active_side']==verified_events[t]['context']['scene']['side']==('right' if task=='push_box_to_bin' else 'left') and verified_events[t]['context']['recontacts']>0 and verified_events[t]['real_recontact_index']==verified_events[t]['context']['recontacts']
   event=verified_events[t];assert event['kind'] in ('command','handover') and c['task_inputs'] is None and c['contact_normal_tracking'] is None
   near(event['command'],u[t],0);near(event['context']['current'],q[t],1e-7);near(event['context']['previous_command'],u[t-1],0)
   assert not c.get('region_joint_override') and not c.get('terminal_joint_hold') and not c.get('joint_edge_refinement',{}).get('override')
   assert 'joint_edge_clearance_intersection' not in c
   controller_frames+=1;continue
  assert t not in verified_events
  inp=c['task_inputs'];trace=c['self_clearance_task'];assert trace['accepted'] is True;near(inp['current'],q[t],1e-6);near(inp['previous'],u[t-1],0);near(inp['lower'],lo,0);near(inp['upper'],hi,0);near(inp['step_limits'],limits,0)
  J=np.array(inp['jacobian']);error=np.array(inp['error']);damping=np.array(inp['damping']);prior=np.array(inp['preferred_step']);near(damping,np.sqrt(np.array([np.float32(.12**2)]+[np.float32(.045**2)]*10)),0)
  baseline=(q[t].astype(float)+bounded_damped_step(J,error,q[t],lo,hi,limits,damping,preferred_step=prior)).astype(np.float32)
  if trace['override']:
   assert trace['solver_success'] is True and trace['status']==0;target=np.array(trace['candidate_command'],dtype=np.float32);near(trace['parent_command'],baseline,0);near(trace['task_residual_m'],J@(target-q[t])-error,1e-8);overrides+=1
  else:target=baseline;assert trace['reason']=='original_task_solution_clear'
  assert min(gap(fk(target)))>=.005-2e-7 and np.all(abs(target-q[t])<=limits+2e-7) and np.max(abs(target-u[t-1]))<=.0550002
  if c.get('region_joint_override'):
   near(c['unexecuted_original_upper_target'],target,0);target=np.array(c['region_joint_override']['next_q'])
  if c.get('terminal_joint_hold'):target=np.array(terminals[t]['output_upper_command'])
  target=np.clip(target,u[t-1]-.055,u[t-1]+.055);target=np.clip(target,np.array(U1_JOINT_LIMIT_LO)[12:23],np.array(U1_JOINT_LIMIT_HI)[12:23]);target[0]=np.clip(target[0],-1.,1.);target=target.astype(np.float32)
  if 'joint_edge_refinement' in c:
   ref=c['joint_edge_refinement'];near(ref['parent_final_upper_command'],target,0);target=np.array(ref['final_upper_command'],dtype=np.float32)
  required=bool(c.get('joint_edge_refinement',{}).get('override'))
  assert ('joint_edge_clearance_intersection' in c)==required,'missing or unexpected final-intersection record'
  if required:
   tr=c['joint_edge_clearance_intersection'];near(tr['input_command'],target,0)
   verified=verify_intersection(hand=hand,elbows=independent_elbows,coordinate=c,row=frontal_rows[t],trace=tr,q=q[t].astype(float),previous=u[t-1].astype(float),command=u[t].astype(float),object_xyz=parcel_xyz[t],object_rotation=parcel_rot[t],core_size=core,lower=lo,upper=hi,limits=limits)
   assert verified['passed'];intersection_rows.append(dict(step=t,**verified));target=np.asarray(tr['output_command'],dtype=np.float32)
  priority=priority_records[t];assert c['front_loaded_z_priority']==priority
  near(target,priority['context']['parent_command'],0)
  if priority['applied']:target=np.asarray(priority['output_command'],dtype=np.float32)
  near(target,transport_parent[t],0)
  transport=c['joint_transport_clearance']
  near(transport['parent_command'],target,0);near(transport['output_command'],u[t],0);controller_frames+=1
 if task=='wait_no_package':assert controller_frames==0;near(u,np.zeros_like(u),0)
 else:assert controller_frames==count-1
 if (ep/'viewer_observer.json').exists():
  for row in json.loads((ep/'viewer_observer.json').read_text())['frames']:
   k=np.array(row['policy_camera_intrinsics']);near(intrinsics,[k[0,0],k[1,1],k[0,2],k[1,2]],0)
 if failure is not None:assert not quality['passed']
 elif count!=record['requested_frames']:assert not quality['passed']
 return dict(passed=True,priority_execution_applied=priority_validation['loaded_z_applied'],priority_execution_source_sha256=priority_validation['source_sha256'],executed_frames=count,controller_frames=controller_frames,task_ik_overrides=overrides,intersection_records=intersection_rows,intersection_changed=sum(v["changed"] for v in intersection_rows),episode_clearance_passed=failure is None and count==record['requested_frames'],failure=failure,minimum_actual_support_gap_m=min(measured_min),minimum_command_support_gap_m=min(command_min),runtime_collision_filter_archived=runtime['filter_archive_complete'],remaining_audits=['original contact/refinement eligibility and stationarity','whole-group task quality','actual RGB/external visual review'],scope=__doc__,training_ready=False,source_sha256={p.name:sha(p) for p in ep.iterdir() if p.suffix in ['.json','.npz'] and 'AUDIT' not in p.name})

if __name__=='__main__':
 ep=Path(sys.argv[1]);out=audit(ep);out['auditor_sha256']=sha(Path(__file__));(ep/'JOINT_TRANSPORT_J1_V1_STAGE_SELF_CLEARANCE_V2_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','failure','scope']},indent=2))
