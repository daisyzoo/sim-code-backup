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
import importlib.util
candidate=w/'staged_causal_xy_objective_probe/contact_patch_approach.py'
spec=importlib.util.spec_from_file_location('xy_candidate',candidate);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
selected=sorted(t for t,r in rows.items() if r['solver'] and r['solver'].get('joint_override') and not r['solver'].get('handover'))
selected=sorted(set(selected[::10]+[selected[-1]]));assert len(selected)>100
for t in selected:
 s=rows[t]['solver'];c=s['causal_response'];geometry=lambda v:model.scene_geometry(side,v,target_xyz=tr[key][t],target_quat=ori[key][t],other_xyz=tr[other][t],other_quat=ori[other][t],other_size=osize)
 kw=dict(lower=lo,upper=hi,step_limits=np.r_[.015,np.full(10,.04)],damping=np.r_[.12,np.full(10,.045)],target_size=size,inactive_anchor=co[t]['inactive_anchor'],tracking_residual=q[t]-u[t-1],preferred_core_scale=np.array(c['core_scale']),response_gain=np.array(c['gain']),response_offset=np.array(c['offset']),command_change_damping=True)
 default=mod.contact_patch_step(q[t],geometry,**kw);assert np.max(abs(np.array(default['next_q'])-s['next_q']))<1e-12
 proposed=mod.contact_patch_step(q[t],geometry,response_centered_xy_objective=True,**kw)
 def margin(command):
  v=np.array(c['gain'])*command+np.array(c['offset']);g=geometry(v);points=(g['vertices']@g['hand_rotation'].T+g['hand_xyz']-g['target_xyz'])@g['target_rotation'];pt=points[points[:,2].argmin()];half=size[:2]*np.array(c['core_scale'])[:2]/2-.01
  return dict(min_core_margin_m=float(np.min(half-abs(pt[:2]))),xy_core_margin_m=(half-abs(pt[:2])).tolist(),top_gap_m=float(pt[2]-size[2]/2),inactive_error_m=float(np.linalg.norm(g['inactive_palm']-co[t]['inactive_anchor'])))
 if proposed.get('accepted'):
  cmd=np.array(proposed['next_q']);assert np.max(abs(cmd-u[t-1]))<.055002
  if proposed.get('line_search_attempts'):assert all(x['safe'] for x in proposed['line_search_attempts'][-1]['scenarios'])
 out.append(dict(step=t,default_exact=True,original_forecast=margin(np.array(s['next_q'])),proposed_forecast=margin(np.array(proposed['next_q'])) if proposed['accepted'] else None,accepted=proposed['accepted'],reached=proposed['reached'],reason=proposed['reason']))
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();report=dict(rows=out,steps=len(out),all_defaults_exact=True,candidate_accepted=sum(x['accepted'] for x in out),core_margin_improved=sum(x['proposed_forecast'] is not None and x['proposed_forecast']['min_core_margin_m']>x['original_forecast']['min_core_margin_m']+1e-8 for x in out),source_sha256={f:sha(p/f) for f in ['raw.npz','trace.npz','parcel_orientation.npz','coordination.json','region_approach.json']},candidate_sha256=sha(candidate),script_sha256=sha(Path(__file__)),scope='Every10th actual override plus last, uniform complete trajectory sampling. Default candidate reproduces executed solver exactly; new XY command nominal/affine guards and slew checked. Counterfactual forecast margins are not observed new physics or guarantee of subsequent contact. No gates changed.',training_ready=False)
(p/'XY_OBJECTIVE_COUNTERFACTUAL.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k not in ['rows','source_sha256']})
