"""Reconstruct exact solver inputs from completed real episode; no simulation."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_region_causal_response';sys.path[:0]=[str(stage),str(repo)]
from contact_patch_approach import contact_patch_step
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
p=Path(sys.argv[1]).resolve();model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');rows={r['step']:r for r in json.loads((p/'region_approach.json').read_text())['rows']};co={r['step']:r for r in json.loads((p/'coordination.json').read_text())}
with np.load(p/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float);task=str(z['task_id'])
with np.load(p/'trace.npz') as z:tr={k:z[k] for k in z.files}
with np.load(p/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
side='right' if task=='push_box_to_bin' else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);osize=(.15,.145,.04) if key=='box' else (.14,.09,.045);lo=np.array(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.array(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98;out=[]
for t in [117,200,500,900,1198]:
 s=rows[t]['solver'];c=s['causal_response'];geometry=lambda v:model.scene_geometry(side,v,target_xyz=tr[key][t],target_quat=ori[key][t],other_xyz=tr[other][t],other_quat=ori[other][t],other_size=osize)
 sol=contact_patch_step(q[t],geometry,lower=lo,upper=hi,step_limits=np.r_[.015,np.full(10,.04)],damping=np.r_[.12,np.full(10,.045)],target_size=size,inactive_anchor=co[t]['inactive_anchor'],tracking_residual=q[t]-u[t-1],preferred_core_scale=np.array(c['core_scale']),response_gain=np.array(c['gain']),response_offset=np.array(c['offset']),command_change_damping=True)
 out.append(dict(step=t,command_max_error=float(np.max(abs(np.array(sol['next_q'])-s['next_q']))),point_max_error=float(np.max(abs(np.array(sol['physical_point_local_xyz'])-s['physical_point_local_xyz']))),inactive_error_delta=sol['inactive_error_m']-s['inactive_error_m'],original=s,replayed=sol,anchor=co[t]['inactive_anchor']))
 print({k:v for k,v in out[-1].items() if k not in ['original','replayed','anchor']},flush=True)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();(p/'EXACT_SOLVER_REPLAY_DIAGNOSIS.json').write_text(json.dumps(dict(rows=out,source_sha256={f:sha(p/f) for f in ['raw.npz','trace.npz','parcel_orientation.npz','coordination.json','region_approach.json']},script_sha256=sha(Path(__file__)),training_ready=False),indent=2))
