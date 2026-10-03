"""Independent one-step hypotheses at every current rear-box edge-off event.
Each history remains original through t-1, whose action is unchanged; only its
post-commit cursor is hypothetically reconciled. Measured t and runtime J thus
remain valid inputs for one next command. No resulting t+1 pose is claimed.
Full route-state integration/replay and actual physics remain required.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;root=w.parents[1];stage=w/'staged_front_corridor_midpoint_integrated';draft=w/'rear_waypoint_reconciliation_draft_r1';sys.path[:0]=[str(stage),str(draft),str(w),str(root)]
from clearance_runtime import ClearanceGuard
from task_ik_precision import solve
from loaded_z_priority_checks import nominal_separation_path
from audit_self_clearance_task_optimality import IndependentElbows
from support_vertex_stationarity import certificate
from simfoundry.data.sorting_quality import PALM_OFFSET,PALM_COLLISION_HALF_Z,TABLE_PENETRATION_TOLERANCE
from simfoundry.calibration.sorting_station import TABLE_TOP_Z
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();r=w/'front_corridor_midpoint_physical_r1';ep=r/'case_840023/layout_840023_push_box_to_bin'
dpath=r/'REAR_BOX_CURRENT_EDGE_COMMAND_RESIDUAL_DIAGNOSTIC.json';d=json.loads(dpath.read_text());run=next(x for x in d['results'] if x['run']==r.name);by={x['step']:x for x in run['records']};events=[x['step'] for x in run['records'] if not x['edge_input_selected'] and by.get(x['step']-1,{}).get('edge_input_selected')];assert len(events)==20
checkpath=draft/'HISTORICAL_POST_COMMIT_CHECK.json';check=json.loads(checkpath.read_text());assert check['passed'];source={}
for path,h in check['source_sha256'].items():assert sha(path)==h,path;source[path]=h
proposals={x['step']:x for x in next(z for z in check['results'] if z['run']==r.name)['proposals']}
fr={x['step']:x for x in json.loads((ep/'frontal_bypass.json').read_text())['rows']};cs={x['step']:x for x in json.loads((ep/'coordination.json').read_text())}
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
with np.load(ep/'trace.npz') as z:other=z['mailer'].astype(float)
with np.load(ep/'parcel_orientation.npz') as z:otherrot=Rotation.from_quat(z['mailer']).as_matrix()
guard=ClearanceGuard(root,stage);independent=IndependentElbows(stage/'elbow_torso_hulls.json',root/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf');records=[]
def point(cmd,offset):
 T,_,_=guard.model.fk('right',cmd);return T[:3,3]+T[:3,:3]@offset
for t in events:
 assert t-1 in proposals;prior=proposals[t-1];f=fr[t];c=cs[t];a=c['task_inputs'];assert f['mode']==fr[t-1]['mode']=='top_push' and not c['terminal_joint_hold'] and not c.get('region_joint_override');assert not c['front_loaded_z_priority']['applied'];assert not c['joint_edge_refinement']['input_selected'];assert abs(f['target_xyz'][1]-fr[t-1]['target_xyz'][1]+.0015)<1e-12
 # Base route increments continuous Y by1.5mm. In these edge-off observations,
 # downstream XY governors preserve parent Y. X/Z and all measured state stay.
 assert not f['rear_coupled_progress']['override'] and not f['rear_joint_xy_progress']['override']
 target=np.asarray(f['target_xyz']).copy();target[1]=prior['next_state_command_xyz'][1]-.0015;assert target[1]>-.34
 old_error=np.array(a['error']);new_error=old_error.copy();new_error[4]=np.clip(np.float32(.72)*(np.float32(target[1])-np.float32(c['control_point_positions']['right'][1])),np.float32(-.035),np.float32(.035))
 kwargs={k:np.array(a[k]) for k in ['jacobian','current','previous','lower','upper','step_limits','damping','preferred_step']}
 np.testing.assert_allclose(kwargs['current'],q[t],rtol=0,atol=1e-7);np.testing.assert_array_equal(kwargs['previous'],u[t-1])
 parent,oldmeta=solve(enabled=True,error=old_error,geometry=guard.geometry,**kwargs);assert parent is not None;np.testing.assert_array_equal(parent,u[t])
 cmd,meta=solve(enabled=True,error=new_error,geometry=guard.geometry,**kwargs)
 entry=dict(step=t,prior_post_commit_proposal=prior,parent_command_reproduced_exactly=True,original_target_xyz=f['target_xyz'],hypothetical_target_xyz=target.tolist(),changed_error_rows=np.flatnonzero(new_error!=old_error).tolist(),solve=meta,candidate=None)
 assert entry['changed_error_rows']==[4]
 if cmd is not None:
  cmd=np.asarray(cmd,dtype=float);g=guard.command(cmd,q[t],u[t-1]);offset=np.asarray(f['control_offset_local']);oldmotion=(point(parent,offset)-point(u[t-1],offset))*1000;newmotion=(point(cmd,offset)-point(u[t-1],offset))*1000
  cert=None
  if meta['override']:
   xq=kwargs['current'];J=kwargs['jacobian'];grad=J.T@(J@(cmd-xq)-new_error)+kwargs['damping']**2*(cmd-xq-kwargs['preferred_step']);lo=np.maximum.reduce([kwargs['lower'],xq-kwargs['step_limits'],kwargs['previous']-.055]);hi=np.minimum.reduce([kwargs['upper'],xq+kwargs['step_limits'],kwargs['previous']+.055]);cert=certificate(geometry=independent,x=cmd,gradient=grad,lower=lo,upper=hi)
  paths={side:nominal_separation_path(guard.model,q[t],cmd,side,other[t],otherrot[t],np.nextafter(np.array([.15,.145,.04],np.float32),np.float32(np.inf)).astype(float)) for side in ['left','right']}
  table=[]
  for side in ['left','right']:
   T,_,_=guard.model.fk(side,cmd);palm=T[:3,3]+T[:3,:3]@np.array(PALM_OFFSET);table.append(float(palm[2]-PALM_COLLISION_HALF_Z-(TABLE_TOP_Z-TABLE_PENETRATION_TOLERANCE)))
  entry.update(candidate=cmd.tolist(),original_final_guard=g,independent_override_stationarity=cert,nominal_hands_non_target_paths=paths,nominal_palm_table_margins_m=table,old_nominal_reference_command_step_mm=oldmotion.tolist(),candidate_nominal_reference_command_step_mm=newmotion.tolist(),nominal_checks_passed=bool(g['accepted'] and (cert is None or cert['passed']) and all(p['certified'] for p in paths.values()) and min(table)>=0))
 records.append(entry)
 print(t,'solved',cmd is not None,'nominalchecks',entry.get('nominal_checks_passed'), 'old/new Y',entry.get('old_nominal_reference_command_step_mm',[None,None])[1],entry.get('candidate_nominal_reference_command_step_mm',[None,None])[1],flush=True)
for p in [Path(__file__),checkpath,dpath,ep/'raw.npz',ep/'coordination.json',ep/'frontal_bypass.json',ep/'trace.npz',ep/'parcel_orientation.npz',w/'support_vertex_stationarity.py',w/'audit_self_clearance_task_optimality.py']+list(stage.glob('*.py'))+list(stage.glob('*.json')):source[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,events=len(records),parent_commands_reproduced_exactly=len(records),solved=sum(x['candidate'] is not None for x in records),nominal_checks_passed=sum(x.get('nominal_checks_passed',False) for x in records),records=records,source_sha256=source,collector_connected=False,physical_rollout=False,training_ready=False)
with (draft/'SINGLE_STEP_COMMAND_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print({k:v for k,v in report.items() if k not in ['records','source_sha256','scope']},flush=True)
