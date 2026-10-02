"""Recorded rear-approach task error, bounded IK and solved-contact diagnosis.
Local Jacobian singular values and a waist bound do not prove global unreachable
geometry. Force magnitudes are not signed resultant force or causal intervention.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W.parents[1]));sys.path.insert(0,str(W))
from audit_closed_peak_trial_contacts import audit
from simfoundry.data.bounded_ik import bounded_damped_step
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main(ep):
 ep=Path(ep).resolve();validated=audit(ep);assert validated['passed'];key='box' if 'push_box' in ep.name else 'mailer';hand='right' if key=='box' else 'left';actor='/parcel_box/' if key=='box' else '/mailer/';idx=slice(3,6) if hand=='right' else slice(0,3);arm=slice(6,11) if hand=='right' else slice(1,6)
 prov=json.loads((ep.parent/'provenance.json').read_text());ik=W.parents[1]/'simfoundry/data/bounded_ik.py';assert sha(ik)==prov['source_sha256']['simfoundry/data/bounded_ik.py']
 coord=json.loads((ep/'coordination.json').read_text());fr={x['step']:x for x in json.loads((ep/'frontal_bypass.json').read_text())['rows']};final={x['step']:x for x in json.loads((ep/'self_clearance.json').read_text())['rows'] if x['phase']=='final_command'}
 with np.load(ep/'trace.npz') as z:target=z[key].copy()
 with np.load(ep/'raw.npz') as z:q=z['q'].copy();action=z['action'].copy()
 m=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text())['metadata'];labels=m['shape_labels']
 with np.load(ep/'substep_contacts.npz') as z:arrays={k:z[k] for k in z.files}
 a=arrays;off=a['contact_offsets'];force=np.linalg.norm(a['force_torque_world'][:,:3],axis=1);target_label=np.array([actor in s for s in labels]);hand_label=np.array([hand+'_wrist_roll' in s for s in labels]);ids=a['shape_ids'];mask=target_label[ids].any(axis=1)&hand_label[ids].any(axis=1);R=24+m['expected_manager_steps'];loads=[]
 for t in range(len(q)):
  base=t*R;ticks=a['substep_tick'][base:base+R];chosen=[base+int(np.flatnonzero(ticks==tick)[0]) for tick in range(1,25)];v=[]
  for j in chosen:
   sl=slice(int(off[j]),int(off[j+1]));v.append(float(force[sl][mask[sl]].sum()))
  loads.append(v)
 loads=np.array(loads);positive=np.argwhere(loads>1e-6);rows=[];replay=[];skipped=[]
 for c in coord:
  t=c['step'];f=fr[t]
  if f['mode']!='rear_push':continue
  inp=c['task_inputs'];J=np.array(inp['jacobian']);e=np.array(inp['error']);cur=np.array(inp['current']);command=np.array(final[t]['command']);assert np.max(abs(cur-q[t,12:23]))<1e-6 and np.max(abs(command-action[t,12:23]))<1e-6
  if not c['self_clearance_task']['override'] and not c['joint_edge_refinement']['override']:
   step=bounded_damped_step(J,e,cur,**{k:np.array(inp[k]) for k in ['lower','upper','step_limits','damping','preferred_step']});error=float(abs(cur+step-command).max());assert error<1e-6;replay.append(error)
  else:skipped.append(t)
  sv=np.linalg.svd(J[idx,arm],compute_uv=False);err=(np.array(f['target_xyz'])-np.array(c['control_point_positions'][hand]))*1000;pred=J@(command-cur)
  rows.append(dict(step=t,target_xyz=target[t].tolist(),rear_clearance_measured=f.get('rear_clearance_measured'),rear_goal_x_m=f.get('rear_goal_x'),rear_x_remaining_mm=(f['rear_goal_x']-target[t,0])*1000,active_point_error_mm=err.tolist(),requested_solver_error_mm=(e[idx]*1000).tolist(),linear_predicted_delta_mm=(pred[idx]*1000).tolist(),active_arm_jacobian_singular_values=sv.tolist(),waist_command_rad=float(command[0]),waist_upper_rad=inp['upper'][0],positive_hand_contact_substeps=int(np.sum(loads[t]>1e-6)),peak_hand_contact_magnitude_sum_n=float(loads[t].max())))
 assert rows and replay;selected=np.array([x['step'] for x in rows]);last=rows[-1];direction=-1 if key=='box' else 1
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),episode=ep.name,scope=__doc__,rear_push_frames=len(rows),bounded_ik_replayed=len(replay),bounded_ik_replay_max_error_rad=max(replay),protected_override_frames_not_replayed=skipped,waist_at_upper_command_frames=int(np.sum(abs(action[:,12]-last['waist_upper_rad'])<1e-6)),rear_frames_with_positive_hand_contact=int(np.sum(loads[selected].max(axis=1)>1e-6)),last_positive_solved_hand_contact_action_tick=[int(positive[-1,0]),int(positive[-1,1])+1] if len(positive) else None,target_initial=target[0].tolist(),target_final=target[-1].tolist(),target_final_signed_y_progress_mm=float((target[-1,1]-target[0,1])*direction*1000),target_last100_xy_change_mm=((target[-1,:2]-target[-100,:2])*1000).tolist(),last=last,rows=rows,source_sha256={str(p):sha(p) for p in [Path(__file__),ik,ep/'coordination.json',ep/'frontal_bypass.json',ep/'self_clearance.json',ep/'trace.npz',ep/'raw.npz',ep/'substep_contacts.npz',ep/'SUBSTEP_CONTACT_RECORDING.json']},independent_contact_audit=validated,runtime_changed=False,training_ready=False)
 with (ep/'REAR_APPROACH_STALL_DIAGNOSIS.json').open('x') as f:json.dump(report,f,indent=2)
 print(json.dumps({k:v for k,v in report.items() if k not in ['rows','source_sha256','independent_contact_audit']},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('episode');a=p.parse_args();main(a.episode)
