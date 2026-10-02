"""One-step offline vertical-task weighting hypothesis on original recorded inputs.
Resolves the original bounded IK first and compares its output to saved commands.
Weight factor2 is a single explicit probe, not an optimized parameter or a runtime
change. Nonlinear clearance, contact dynamics and cumulative rollout untested.
"""
from pathlib import Path
import json,hashlib,datetime,sys
import numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W.parents[1]))
from simfoundry.data.bounded_ik import bounded_damped_step
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def one(ep):
 fr=json.loads((ep/'frontal_bypass.json').read_text());fr={x['step']:x for x in fr['rows']};coord={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};final={x['step']:x for x in json.loads((ep/'self_clearance.json').read_text())['rows'] if x['phase']=='final_command'};history=json.loads((ep/'CLOSED_PEAK_TRIAL_LOAD_HISTORY.json').read_text());assert history['independent_audit']['passed'];rows=[]
 for name,h in history['source_sha256'].items():assert sha(ep/name)==h
 for t,f in fr.items():
  if f['mode']!='top_push' or np.mean(history['rows'][t]['vertical_load_n'])<.3:continue
  c=coord[t];a=c['task_inputs'];assert a is not None and not c['self_clearance_task']['override'] and not c['terminal_joint_hold']
  J=np.asarray(a['jacobian']);e=np.asarray(a['error']);q=np.asarray(a['current']);prev=np.asarray(a['previous']);command=np.asarray(final[t]['command']);np.testing.assert_allclose(final[t]['current'],q,atol=1e-7,rtol=0)
  args={k:np.asarray(a[k]) for k in ['lower','upper','step_limits','damping','preferred_step']};step=bounded_damped_step(J,e,q,**args);parent=q+step;identity=float(np.max(abs(parent-command)))
  assert identity<1e-6,(ep.name,t,identity)
  weighted=J.copy();desired=e.copy();weighted[2]*=2;desired[2]*=2;candidate_step=bounded_damped_step(weighted,desired,q,**args);candidate=q+candidate_step
  assert np.all(candidate>=args['lower']-1e-9) and np.all(candidate<=args['upper']+1e-9) and np.all(abs(candidate-q)<=args['step_limits']+1e-9)
  pred=J@step;pred_new=J@candidate_step
  rows.append(dict(step=t,parent_command_max_error_rad=identity,original_requested_z_mm=float(e[2]*1000),parent_predicted_z_mm=float(pred[2]*1000),candidate_predicted_z_mm=float(pred_new[2]*1000),parent_z_residual_mm=float((e[2]-pred[2])*1000),candidate_z_residual_mm=float((e[2]-pred_new[2])*1000),parent_xy_residual_norm_mm=float(np.linalg.norm(e[:2]-pred[:2])*1000),candidate_xy_residual_norm_mm=float(np.linalg.norm(e[:2]-pred_new[:2])*1000),parent_inactive_xyz_residual_norm_mm=float(np.linalg.norm(e[3:6]-pred[3:6])*1000),candidate_inactive_xyz_residual_norm_mm=float(np.linalg.norm(e[3:6]-pred_new[3:6])*1000),candidate_previous_slew_max_rad=float(abs(candidate-prev).max()),candidate_changes_command_max_rad=float(abs(candidate-command).max())))
 def mean(key):return float(np.mean([x[key] for x in rows]))
 return dict(episode=ep.name,rows=rows,summary=dict(frames=len(rows),parent_match_max_rad=max(x['parent_command_max_error_rad'] for x in rows),parent_abs_z_residual_mean_mm=float(np.mean([abs(x['parent_z_residual_mm']) for x in rows])),candidate_abs_z_residual_mean_mm=float(np.mean([abs(x['candidate_z_residual_mm']) for x in rows])),parent_xy_residual_mean_mm=mean('parent_xy_residual_norm_mm'),candidate_xy_residual_mean_mm=mean('candidate_xy_residual_norm_mm'),parent_inactive_residual_mean_mm=mean('parent_inactive_xyz_residual_norm_mm'),candidate_inactive_residual_mean_mm=mean('candidate_inactive_xyz_residual_norm_mm'),candidate_previous_slew_max_rad=max(x['candidate_previous_slew_max_rad'] for x in rows),original_joint_and_measured_step_bounds_preserved=True),source_sha256={str(p):sha(p) for p in [ep/'frontal_bypass.json',ep/'coordination.json',ep/'self_clearance.json',ep/'CLOSED_PEAK_TRIAL_LOAD_HISTORY.json']})
if __name__=='__main__':
 run=Path(sys.argv[1]).resolve();rows=[one(run/f'case_{i}/layout_{i}_nudge_mailer_to_bin') for i in [840002,840003]];out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,vertical_row_multiplier=2,rows=rows,nonlinear_clearance_verified=False,cumulative_dynamics_verified=False,runtime_candidate_installed=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),W.parents[1]/'simfoundry/data/bounded_ik.py']});dest=run/'BAG_VERTICAL_PRIORITY_OFFLINE_SCREEN.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2));print(json.dumps([dict(episode=x['episode'],**x['summary']) for x in rows],indent=2))
