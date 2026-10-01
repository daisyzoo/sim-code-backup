"""Compare a complete COP episode against the same complete parent condition."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
from simfoundry.data.top_contact_load_geometry import loaded_forward_margin
ep=Path(sys.argv[1]).resolve();cid=ep.name.split('_')[1];parent=w/'joint_edge_groups_r1'/('case_'+cid)/ep.name;reports=[]
for folder in [parent,ep]:
 fr=json.loads((folder/'frontal_bypass.json').read_text());rows=fr['rows'];key='box' if 'push_box' in folder.name else 'mailer';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer';direction=-1 if key=='box' else 1;size=np.array(fr['plan']['top_recontact']['contact_size_xyz']);core=np.array(fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'])
 with np.load(folder/'trace.npz') as z:xyz=z[key].astype(float)
 with np.load(folder/'parcel_orientation.npz') as z:quat=z[key].astype(float)
 packets={r['after_action_step']:r for r in json.loads((folder/'solved_contact_forces.json').read_text())['rows']};assert len(xyz)==1200
 previous=None;events=[];bouts=[];active=[];last=None
 for row in rows:
  t=row['step']
  if row['mode']=='top_push':
   active.append(row);c=loaded_forward_margin(packets.get(t-1),side,actor,xyz[t],quat[t],size,direction)
   if c['valid'] and c['normal_load_n']>=.3:last=dict(step=t,load_n=c['normal_load_n'],core_xy_margin_mm=((core[:2]/2-abs(np.array(c['weighted_contact_local'])[:2]))*1000).tolist())
  elif active:
   bouts.append(dict(start=active[0]['step'],end=active[-1]['step'],steps=len(active),loaded_vertical_steps=sum(x['contact_load']['observed_vertical_load_n']>=.2 for x in active),exit_mode=row['mode'],reason=('terminal_release' if row['mode']=='top_release' else row.get('last_recontact_reason')),last_cop=last));active=[];last=None
  previous=row
 if active:bouts.append(dict(start=active[0]['step'],end=active[-1]['step'],steps=len(active),loaded_vertical_steps=sum(x['contact_load']['observed_vertical_load_n']>=.2 for x in active),exit_mode='episode_end',reason=None,last_cop=last))
 q=json.loads((folder/'quality.json').read_text());region=json.loads((folder/'region_approach.json').read_text())['rows'];handover=next((r['step'] for r in region if r['solver'] and r['solver'].get('handover')),None)
 feedback=[r['rear_cop_centering'] for r in rows if r.get('rear_cop_centering',{}).get('override')];audit=json.loads((folder/'MEASURED_BOUNDS_LIVE_AUDIT.json').read_text());assert audit['passed'];record=dict(run=folder.parent.parent.name,episode=folder.name,original_quality_passed=q['passed'],progress_mm=q['metrics']['target_final_progress_m']*1000,minimum_final10_signed_y_mm=float(np.min(direction*xyz[-10:,1])*1000),non_target_max_xy_mm=q['metrics'][('mailer' if key=='box' else 'box')+'_max_xy_m']*1000,region_handover=handover,actual_COP_overrides=len(feedback),loaded_push_steps=sum(b['loaded_vertical_steps'] for b in bouts),bouts=bouts,exit_counts=dict(collections.Counter(b['reason'] for b in bouts)),domain_outside_command_states=sum(r['outside_command_domain'] for r in audit['checks']),actual_inward_recovery_commands=audit['inward_recovery_commands'],source_sha256={n:sha(folder/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','region_approach.json','solved_contact_forces.json','quality.json','MEASURED_BOUNDS_LIVE_AUDIT.json']})
 if feedback:record['feedback_summary']=dict(median_abs_x_feedback_mm=float(np.median([abs(f['feedback_x_m'])*1000 for f in feedback])),max_abs_x_step_mm=max(abs(f['command_delta_x_m'])*1000 for f in feedback))
 audit_name='REAR_JOINT_XY_LIVE_AUDIT.json'
 a=json.loads((folder/audit_name).read_text());assert a['passed'] and a['overrides_checked']==len(feedback);record['independent_rear_audit_sha256']=sha(folder/audit_name)
 for n,h in a['source_sha256'].items():assert sha(folder/n)==h
 coupled=[r for r in rows if r.get('rear_coupled_progress',{}).get('override')]
 record['upstream_Y_governor_trace_summary']=dict(changed_steps=len(coupled),first_changed_step=coupled[0]['step'] if coupled else None,median_Y_scale=float(np.median([r['rear_coupled_progress']['scale'] for r in coupled])) if coupled else None,infeasible_parent_fallbacks=sum(r.get('rear_coupled_progress',{}).get('reason')=='no_Y_only_direction' for r in rows),zero_or_nearly_zero_Y_steps=sum(r['rear_coupled_progress']['scale']<.01 for r in coupled))
 if coupled:record['first_changed_object_xyz']=xyz[coupled[0]['step']].tolist()
 if (folder/'REAR_COUPLED_EXECUTION_LIVE_AUDIT.json').exists():
  ex=json.loads((folder/'REAR_COUPLED_EXECUTION_LIVE_AUDIT.json').read_text());assert ex['passed'] and ex['selected'] and not ex['historical_sampled'] and ex['complete_push_coverage'] and ex['checked_push_frames']==ex['expected_push_frames']
  for n,h in ex['source_sha256'].items():assert sha(folder/n)==h
  record['execution_replay']=dict(checked_push_frames=ex['checked_push_frames'],maximum_action_error_rad=ex['maximum_action_error_rad'],audit_sha256=sha(folder/'REAR_COUPLED_EXECUTION_LIVE_AUDIT.json'))
 execution_name='JOINT_EDGE_EXECUTION_LIVE_AUDIT.json' if folder==parent else 'JOINT_EDGE_RETRY_EXECUTION_LIVE_AUDIT.json'
 execution_script='audit_joint_edge_execution_live.py' if folder==parent else 'audit_joint_edge_retry_execution_live.py'
 if folder in [parent,ep]:
  ex=json.loads((folder/execution_name).read_text());assert ex['passed'] and ex['selected'] and not ex['errors'] and ex['auditor_sha256']==sha(w/execution_script)
  assert ex['parent_full_push_replay_frames']==sum(r['mode']=='top_push' for r in rows)
  for n,h in ex['source_sha256'].items():assert sha(folder/n)==h
  changes=[r for r in ex['records'] if r['refined']];fallbacks=[r for r in ex['records'] if r.get('numeric_fallback')]
  record['final_joint_direction_summary']=dict(refined_frames=len(changes),first_refined_step=changes[0]['step'] if changes else None,numeric_fallback_frames=len(fallbacks),fallback_reasons=dict(collections.Counter(r['reason'] for r in fallbacks)),parent_full_push_replay_frames=ex['parent_full_push_replay_frames'],maximum_stationarity_residual=ex['max_stationarity_residual'],audit_sha256=sha(folder/execution_name))
  record['retry_attempts']=ex.get('retry_attempts',0)
  if changes:record['first_final_joint_changed_object_xyz']=xyz[changes[0]['step']].tolist()
 xy=[r for r in rows if r.get('rear_joint_xy_progress',{}).get('override')]
 record['joint_xy_summary']=dict(changed_steps=len(xy),first_changed_step=xy[0]['step'] if xy else None,median_Y_scale=float(np.median([r['rear_joint_xy_progress']['scale'] for r in xy])) if xy else None,median_abs_additional_X_mm=float(np.median([abs(r['rear_joint_xy_progress']['reference_delta_xyz_m'][0]-r['rear_joint_xy_progress']['parent_delta_xyz_m'][0])*1000 for r in xy])) if xy else None,infeasible_parent_Y_fallbacks=sum(r.get('rear_joint_xy_progress',{}).get('reason') in ['no_joint_XY_direction','numerical_infeasible','no_cartesian_slew_and_lead_interval'] for r in rows))
 record['upstream_Y_governor_trace_summary']['scope']='Parent Y proposal; a jointXY override replaces it in the final candidate command.'
 if xy:record['first_joint_xy_changed_object_xyz']=xyz[xy[0]['step']].tolist()
 rotations=Rotation.from_quat(quat).as_matrix();h=core[:2]/2-.01;directions=[]
 for row in rows:
  f=row.get('rear_cop_centering',{});t=row['step']
  if not f.get('override'):continue
  local=rotations[t].T@(np.array(f['cop_world'])-xyz[t]);low,high=-float('inf'),float('inf')
  for j in range(2):
   axis=rotations[t][0,j]
   if abs(axis)<1e-10:
    if abs(local[j])>h[j]:low,high=1.,0.
   else:
    ends=sorted([(-h[j]-local[j])/axis,(h[j]-local[j])/axis]);low=max(low,ends[0]);high=min(high,ends[1])
  needed=float(np.clip(0,low,high)) if low<=high and np.isfinite([low,high]).all() else None
  directions.append(dict(step=t,needed_x_m=needed,feedback_opposes=bool(needed is not None and abs(needed)>.0001 and needed*f['error_x_m']<0),command_opposes=bool(needed is not None and abs(needed)>.0001 and needed*f['command_delta_x_m']<0)))
 record['core_direction_summary']=dict(overrides=len(directions),outside_with_x_solution=sum(x['needed_x_m'] is not None and abs(x['needed_x_m'])>.0001 for x in directions),feedback_opposes=sum(x['feedback_opposes'] for x in directions),command_opposes=sum(x['command_opposes'] for x in directions),empty_slice=sum(x['needed_x_m'] is None for x in directions),fallback_rows=sum(x.get('rear_cop_centering',{}).get('reason')=='no_world_x_core_interior_slice' for x in rows))
 record['direction_rows']=directions
 reports.append(record)
out=dict(rows=reports,checker_sha256=sha(Path(__file__)),training_ready=False,scope='Complete same-condition parent/new raw comparison, independent current-COP/XY and measured-domain audits required. Vertical>=.2N previous-substep counts differ from last normal>=.3N weighted COP. Final joint direction changes measured separately from Cartesian reference overrides. Single same-seed runs may vary before activation; no broad causal efficacy, group, training or model claim.')
(ep/'JOINT_EDGE_RETRY_ACTUAL_COMPARISON.json').write_text(json.dumps(out,indent=2))
for r in reports:print({k:v for k,v in r.items() if k not in ['bouts','source_sha256','direction_rows']})
