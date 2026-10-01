"""Causal solver under exogenous recorded transient residuals; NOT simulator."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_tracking_region_approach';sys.path[:0]=[str(stage),str(w/'staged_contact_patch_approach'),str(repo)]
from tracking_region_approach_refined import tracking_region_step
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');lo=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98;limits=np.r_[.015,np.full(10,.04)];damping=np.r_[.12,np.full(10,.045)];reports=[]
source=json.loads((stage/'CONSTANT_RESIDUAL_REFINED_SCREEN.json').read_text())
for case in source['rows']:
 if case['start_kind']!='first_eligible':continue
 ep=Path(case['episode']);t=case['actual_start_frame'];side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box';size=np.array([.14,.09,.045] if side=='right' else [.15,.145,.04]);osize=(.15,.145,.04) if side=='right' else (.14,.09,.045)
 with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float);us=z['action'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
 coords={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};anchor=np.asarray(coords[t]['inactive_anchor']);q=qs[t].copy();previous=us[t-1].copy();stop=next((x['step'] for x in json.loads((ep/'frontal_bypass.json').read_text())['rows'] if x.get('region_guard_reason')),min(t+60,len(qs)-1));stop=max(stop,t+1)
 def geometry(q):return model.scene_geometry(side,q,target_xyz=tr[key][t],target_quat=ori[key][t],other_xyz=tr[other][t],other_quat=ori[other][t],other_size=osize)
 history=[]
 for step in range(600):
  residual=q-previous
  try:s=tracking_region_step(q,geometry,tracking_residual=residual,lower=lo,upper=hi,step_limits=limits,damping=damping,target_size=size,inactive_anchor=anchor)
  except ValueError as exc:s=dict(accepted=False,reached=False,reason=str(exc),next_q=q.tolist())
  row=dict(step=step,measured_q=q.tolist(),estimated_residual=residual.tolist(),solver=s);history.append(row)
  if s['reached'] or not s['accepted'] or s['reason']=='stagnation':break
  # Environment disturbance only: never passed as future data to solver.
  event=min(t+step+1,stop);external=qs[event]-us[event-1];command=np.asarray(s['next_q']);q=command+external;previous=command;row.update(disturbance_source_frame=event,exogenous_residual_rad=external.tolist())
 result=dict(episode=str(ep),actual_start_frame=t,recorded_disturbance_end_frame=stop,steps=len(history),reached=history[-1]['solver']['reached'],stop=history[-1]['solver']['reason'],history=history);reports.append(result);print(json.dumps({k:v for k,v in result.items() if k!='history'}),flush=True)
out=dict(rows=reports,scope='Exogenous stress sequence q_recorded[t+1]-u_recorded[t] to first guard (or60frames), then last value held. Counterfactual commands do not generate these residuals physically; this is a rejection stress, NOT real dynamics nor proof of causal controller success. Solver sees only simulated current q and prior own command, never future disturbance.',training_ready=False,helper_sha256=hashlib.sha256((stage/'tracking_region_approach_refined.py').read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest());(stage/'TRANSIENT_RESIDUAL_STRESS.json').write_text(json.dumps(out,indent=2))
