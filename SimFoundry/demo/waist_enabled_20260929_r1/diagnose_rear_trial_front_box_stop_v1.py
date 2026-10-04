"""Independent observed front-box recovery stop, before full episode audits.
No tolerance relaxation, no collision claim, and no admission of truncated data.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_trailing_contact_v1';R=W/'rear_trailing_physical_r1';ep=R/'case_840020/layout_840020_push_box_to_bin';sys.path[:0]=[str(S),str(W),str(ROOT)]
from audit_front_recontact_center_events import RecoveryEventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();paths=[ep/n for n in ['self_clearance.json','front_recontact_center.json','quality.json','raw.npz','coordination.json']];data={p.name:json.loads(p.read_text()) for p in paths if p.suffix=='.json'};failure=data['self_clearance.json']['failure'];event=data['front_recontact_center.json']['rows'][-1];ctx=event['context'];assert failure['step']==ctx['step']==1077 and failure['record']=={k:v for k,v in event.items() if k!='step'}
q=np.asarray(ctx['current']);audit=RecoveryEventAudit(ROOT,S);g,_=audit.geometry(q,ctx['scene']);stored=event['proposal']['measured_scene'];audit.compare_geometry(stored,g);assert not g['accepted'];assert ctx['observed_load_n']==0 and ctx['filtered_load_n']<=.05;floor=.005-2e-7;assert g['elbow_gap_m']<floor and min(g['hand_parcel_gaps_m'].values())>=.01 and g['inactive_lowest_z_m']>=.84-2e-7 and g['active_above_top_m']>=.004 and g['physical_bounds']
with np.load(ep/'raw.npz') as raw:
 raw_keys=list(raw.files);qraw=raw['q'];assert len(qraw)==1077;np.testing.assert_allclose(qraw[-1,12:23],ctx['previous_q'],atol=1e-7,rtol=0)
previous=next(e for e in data['front_recontact_center.json']['rows'] if e['step']==1076);assert previous['kind']=='command';np.testing.assert_allclose(previous['command'],ctx['previous_command'],atol=0,rtol=0);proposal=previous['proposal'];pred=np.asarray(proposal['predicted_q']);pg,_=audit.geometry(pred,ctx['scene']);nom,_=audit.geometry(np.asarray(previous['command']),ctx['scene']);prev_g,_=audit.geometry(np.asarray(ctx['previous_q']),previous['context']['scene']);assert nom['elbow_gap_m']>=floor and pg['elbow_gap_m']>=floor
quality=data['quality.json'];assert not quality['passed'] and quality['frames']==1077;start=next(e for e in reversed(data['front_recontact_center.json']['rows'][:-1]) if e.get('planning'));assert start['real_recontact_index']==12
sources={str(p):sha(p) for p in [Path(__file__),*paths,R/'PROTOCOL.json',S/'elbow_torso_hulls.json',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']}
for mod in list(sys.modules.values()):
 f=getattr(mod,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,observed_stop_step=1077,recorded_frames=1077,requested_frames=data['self_clearance.json']['requested_frames'],recontact_index=12,recovery_start_step=start['step'],reason=event['reason'],proposal_reason=event['proposal']['reason'],independent_geometry=g,elbow_original_nominal_floor_m=.005,original_numerical_tolerance_m=2e-7,actual_acceptance_floor_m=floor,observed_shortfall_um=(floor-g['elbow_gap_m'])*1e6,previous_observed_elbow_gap_m=prev_g['elbow_gap_m'],preceding_nominal_elbow_gap_m=nom['elbow_gap_m'],preceding_predicted_elbow_gap_m=pg['elbow_gap_m'],prediction_max_joint_error_rad=float(max(abs(q-pred))),saved_task_passed=False,target_progress_mm=quality['metrics']['target_final_progress_m']*1000,non_target_max_xy_mm=quality['metrics']['mailer_max_xy_m']*1000,source_sha256=sources,independent_full_numeric_and_visual_pending=True,training_ready=False)
with (R/'FRONT_BOX_TRUNCATED_STOP_DIAGNOSIS.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','independent_geometry','scope']},indent=2))
