"""Bind actual command chain to nominal support descent and recorded load peaks.
Descriptive temporal evidence only. The unissued parent command is not treated
as a counterfactual physical response, and no new controller is installed.
"""
from pathlib import Path
import json,hashlib,datetime,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from audit_unloaded_wrist_prior_live import HandModel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());sources={};allruns=[];model=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json');longaxis=np.linalg.eigh(np.cov(model.vertices['left'].T))[1][:,-1]
def point(q,n,center):
 T=model.fk(np.asarray(q),'left');local=T[:3,:3].T@n;ref=center+local*(min(model.vertices['left']@local)-center@local);return T[:3,3]+T[:3,:3]@ref,T
for run in ['joint_transport_reserve_physical_r1','rear_trailing_physical_r1','front_corridor_lateral_physical_r1']:
 ep=W/run/'case_840023/layout_840023_nudge_mailer_to_bin';fr={r['step']:r for r in read(ep/'frontal_bypass.json')['rows']};co={r['step']:r for r in read(ep/'coordination.json')};meta=read(ep/'SUBSTEP_CONTACT_RECORDING.json');m=meta['metadata'];assert meta['recording_sha256']==sha(ep/'substep_contacts.npz') and meta['action_intervals']==1200
 with np.load(ep/'substep_contacts.npz') as z:a={k:z[k].copy() for k in z.files}
 labels=m['shape_labels'];bag=np.array([i for i,s in enumerate(labels) if '/mailer/' in s]);hand=np.array([i for i,s in enumerate(labels) if 'left_wrist_roll' in s]);pairs=a['shape_ids'];selected=np.isin(pairs,bag).any(1)&np.isin(pairs,hand).any(1);sample_ids=np.repeat(np.arange(len(a['action_step'])),np.diff(a['contact_offsets']));loads=np.bincount(sample_ids[selected],weights=np.abs(a['force_torque_world'][selected,2].astype(float)),minlength=len(a['action_step']));interval=24+m['expected_manager_steps'];peak=[]
 for step in range(1200):
  base=step*interval;stamps=a['substep_tick'][base:base+interval];assert np.all(a['action_step'][base:base+interval]==step);ids=[base+int(np.flatnonzero(stamps==k)[0]) for k in range(1,25)];peak.append(float(max(loads[ids])))
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['mailer']).as_matrix();yaw=np.unwrap(Rotation.from_quat(z['mailer']).as_euler('xyz')[:,2])
 first=next(t for t,r in fr.items() if r.get('route_stop_reason'));events=[];association=[]
 for t,c in co.items():
  priority=c['front_loaded_z_priority']
  if fr[t]['mode']=='top_push' and priority['selected']:
   association.append(dict(step=t,priority_applied=priority['applied'],peak_hand_vertical_abs_n=peak[t],parent_nominal_dz_mm=None if 'parent_exact_support_delta_z_m' not in priority else 1000*priority['parent_exact_support_delta_z_m'],candidate_nominal_dz_mm=None if 'candidate_exact_support_delta_z_m' not in priority else 1000*priority['candidate_exact_support_delta_z_m'],yaw_change_deg=None if t==1199 else float(np.degrees(yaw[t+1]-yaw[t]))))
  if not first-3<=t<first:continue
  transport=c['joint_transport_clearance'];np.testing.assert_array_equal(u[t],transport['output_command']);np.testing.assert_array_equal(priority['output_command'],transport['parent_command']);np.testing.assert_allclose(q[t],priority['context']['current'],atol=1e-7,rtol=0)
  center=np.array(c['active_support_reference']['center_local']);normal=rot[t,:,2];actual,T=point(q[t],normal,center);np.testing.assert_allclose(actual,fr[t]['observed_support_xyz'],atol=2e-6,rtol=0);p0=np.array(priority['context']['parent_command']);pp,PT=point(p0,normal,center);prior,PRT=point(priority['output_command'],normal,center);out,OT=point(u[t],normal,center);dzp=float(pp[2]-actual[2]);dzprior=float(prior[2]-actual[2]);dzo=float(out[2]-actual[2])
  if 'parent_exact_support_delta_z_m' in priority:np.testing.assert_allclose(dzp,priority['parent_exact_support_delta_z_m'],atol=2e-9,rtol=0)
  if priority['applied']:np.testing.assert_allclose(dzprior,priority['candidate_exact_support_delta_z_m'],atol=2e-9,rtol=0)
  heading=lambda M:float(np.arctan2(*(M[:3,:3]@longaxis)[[1,0]]));wrap=lambda v:float(np.arctan2(np.sin(v),np.cos(v)))
  events.append(dict(step=t,observed_previous_load_n=fr[t]['contact_load']['observed_vertical_load_n'],stored_pressure_bias_mm=1000*fr[t]['contact_load']['stored_z_bias_m'],requested_downward_task_mm=None if 'requested_z_m' not in priority['context'] else 1000*priority['context']['requested_z_m'],priority_applied=priority['applied'],priority_reason=priority['reason'],parent_nominal_support_dz_mm=1000*dzp,priority_nominal_support_dz_mm=1000*dzprior,final_nominal_support_dz_mm=1000*dzo,priority_additional_nominal_descent_mm=1000*(dzp-dzprior),transport_additional_nominal_descent_mm=1000*(dzprior-dzo),parent_nominal_heading_change_deg=float(np.degrees(wrap(heading(PT)-heading(T)))),final_nominal_heading_change_deg=float(np.degrees(wrap(heading(OT)-heading(T)))),peak_this_action_hand_vertical_abs_n=peak[t],actual_this_action_yaw_change_deg=float(np.degrees(yaw[t+1]-yaw[t])),transport_applied=transport['applied'],mode=fr[t]['mode'],final_output_equals_priority_output=bool(np.array_equal(u[t],priority['output_command']))))
 summaries=[]
 for applied in [False,True]:
  rr=[r for r in association if r['priority_applied']==applied];v=[r['peak_hand_vertical_abs_n'] for r in rr];summaries.append(dict(priority_applied=applied,frames=len(rr),peaks_above_10n=sum(x>10 for x in v),peak_median_n=None if not v else float(np.median(v)),peak_max_n=None if not v else max(v)))
 out=dict(run=run,first_guard_step=first,last_three_push_commands=events,descriptive_groups=summaries,rows=association);allruns.append(out);print(json.dumps({k:v for k,v in out.items() if k!='rows'}),flush=True)
 for n in ['raw.npz','frontal_bypass.json','coordination.json','parcel_orientation.npz','SUBSTEP_CONTACT_RECORDING.json','substep_contacts.npz']:sources[str(ep/n)]=sha(ep/n)
for p in [Path(__file__),W/'audit_unloaded_wrist_prior_live.py',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json']:sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,runs=allruns,source_sha256=sources,limitations=['Nominal commanded geometry is not actual executed hand trajectory or contact penetration.','Applied/nonapplied groups have different states and selection conditions; descriptive associations are not causal estimates.','The10N value is the existing peak-bias guard threshold, not a newly imposed task acceptance gate.','Parent alternative was not issued; its hypothetical force response remains unknown.'],controller_changed=False,physics_started=False,training_ready=False)
with (W/'front_corridor_lateral_physical_r1/FRONT_BAG_LOADED_Z_BURST_DIAGNOSIS_V2.json').open('x') as f:json.dump(report,f,indent=2)
