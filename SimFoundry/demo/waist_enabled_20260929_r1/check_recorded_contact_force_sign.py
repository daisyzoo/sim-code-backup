"""Independent force-side and timing check from recorded linear momentum.
Compare geom1-positive and geom0-positive force hypotheses with actual24-step
COM velocity changes, mass and configured gravity. No simulator state mutations.
This does not establish contact-point/end-pose simultaneity or intervention causality.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W.parents[1])]
from audit_closed_peak_trial_contacts import audit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
PKG=Path('/home/user/miniconda3/envs/env_isaaclab/lib/python3.12/site-packages')
def main(run):
 run=Path(run).resolve();sources={str(Path(__file__)):sha(__file__)};records=[]
 for f in sorted(run.glob('case_*/*/frontal_bypass.json')):
  ep=f.parent
  if not (ep/'quality.json').exists():continue
  data=json.loads(f.read_text());plan=data['plan']
  if not plan['required'] or plan.get('front_route_selected') or plan.get('initial_top_selected'):continue
  checked=audit(ep);assert checked['passed'];recording=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text());m=recording['metadata'];labels=m['shape_labels'];mass=np.array(m['body_mass_kg']);dt=m['solver_dt_s'];R=24+m['expected_manager_steps'];frames=checked['action_intervals'];ownership=np.array(m['shape_body']);config=json.loads((ep.parent/'runtime_configuration.json').read_text());gravity=np.array(config['simulation']['gravity']);assert gravity.shape==(3,)
  support=PKG/'mujoco_warp/_src/support.py';archived=list((ep.parent/'substep_runtime_sources').glob('*_support.py'));assert len(archived)==1 and sha(archived[0])==sha(support)
  with np.load(ep/'substep_contacts.npz') as z:a={k:z[k] for k in z.files}
  off=a['contact_offsets'];body_pair=ownership[a['shape_ids']];force=a['force_torque_world'][:,:3].astype(float);tick0=np.arange(frames)*R;indices=np.array([[int(base)+int(np.flatnonzero(a['substep_tick'][base:base+R]==tick)[0]) for tick in range(1,25)] for base in tick0]);allforce=np.zeros((frames,24,2,3));handforce=np.zeros_like(allforce)
  for bi,body in enumerate(m['body_ids']):
   sign=(body_pair[:,1]==body).astype(int)-(body_pair[:,0]==body).astype(int);weighted=force*sign[:,None];cs=np.vstack([np.zeros(3),np.cumsum(weighted,axis=0)]);allforce[:,:,bi]=cs[off[indices+1]]-cs[off[indices]]
   mask=np.array([('left_wrist_roll' in s or 'right_wrist_roll' in s) for s in labels])[a['shape_ids']].any(1);cs=np.vstack([np.zeros(3),np.cumsum(weighted*mask[:,None],axis=0)]);handforce[:,:,bi]=cs[off[indices+1]]-cs[off[indices]]
  # Newton state documents body_qd=[linear(COM,world),angular(world)].
  velocity=a['body_qd'][:,:,:3].astype(float);before=np.concatenate([velocity[tick0][:,None],velocity[indices[:,:-1]]],axis=1);dv=velocity[indices]-before;required=mass[None,None,:,None]*(dv/dt-gravity[None,None,None,:]);results=[]
  for sign in [1,-1]:
   residual=sign*allforce-required;results.append(dict(force_on_shape1_sign=sign,rms_force_balance_error_n=float(np.sqrt(np.mean(residual**2))),max_abs_force_balance_error_n=float(abs(residual).max()),rms_xyz_n=np.sqrt(np.mean(residual**2,axis=(0,1,2))).tolist(),rms_interval_momentum_error_ns=float(np.sqrt(np.mean((residual.sum(1)*dt)**2)))))
  target_index=0 if ep.name.endswith('push_box_to_bin') else 1;rear_steps=np.array([x['step'] for x in data['rows'] if x['mode']=='rear_push']);hand_impulse=handforce[rear_steps,:,target_index].sum((0,1))*dt
  row=dict(episode=ep.name,substep_pairs=frames*24*2,comparisons=results,geom1_positive_hand_force_time_sum_xyz_ns=hand_impulse.tolist(),task_direction=plan['direction'],geom1_positive_hand_signed_task_y_force_time_sum_ns=float(hand_impulse[1]*plan['direction']),recorded_linear_state_convention='Newton body_qd first3=world COM linear velocity',nominal_source_derivation='contact Jacobian = J_body2-J_body1; contact_force_fn returns contact components rotated to world; shape IDs preserve geom ordering. Constraint source is currently installed, support decoder also matches archived runtime.',rows=None)
  # Keep per-action signed candidate values to diagnose temporal direction after validation.
  row['rear_rows']=[dict(step=int(t),hand_force_time_sum_xyz_ns=(handforce[t,:,target_index].sum(0)*dt).tolist()) for t in rear_steps];records.append(row)
  for path in [ep/'SUBSTEP_CONTACT_RECORDING.json',ep/'substep_contacts.npz',ep.parent/'runtime_configuration.json',f,support,archived[0],PKG/'mujoco_warp/_src/constraint.py',PKG/'mujoco_warp/_src/solver.py',PKG/'newton/_src/sim/state.py']:sources[str(path)]=sha(path)
  print(json.dumps({k:v for k,v in row.items() if k!='rear_rows'}),flush=True)
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,source_sha256=sources,runtime_changed=False,original_observer_metadata_changed=False,training_ready=False)
 with (run/'RECORDED_CONTACT_FORCE_SIGN_CHECK.json').open('x') as out:json.dump(report,out,indent=2)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run');a=p.parse_args();main(a.run)
