"""Actual-history default parity, independent response equation and FK derivative checks."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_causal_command_damping_probe';sys.path[:0]=[str(stage),str(w/'staged_front_cop_route_axis'),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry
from causal_unloaded_response import response_parameters
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');lo=np.array(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.array(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98
mods=[]
for name,p in [('old',w/'staged_core_interior_probe/contact_patch_approach.py'),('new',stage/'contact_patch_approach.py')]:
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);mods.append(m)
source=w/'staged_core_interior_unloaded_screen/UNLOADED_CORE_INTERIOR_SCREEN.json';d=json.loads(source.read_text());cases=[r for r in d['rows'] if r['scenario']=='nominal_response' and r['variant']=='core_interior'];assert len(cases)==8;parity=[];jacmax=0.;model_rows=0;maxeq=0.;fitreport=w/'unloaded_tracking_dynamics_bias_audit_r1/RESULT.json';fit=json.loads(fitreport.read_text())
for case in cases:
 ep=Path(case['episode']);t=case['actual_start_frame'];key='box' if 'push_box' in ep.name else 'mailer';side='right' if key=='box' else 'left';other='mailer' if key=='box' else 'box';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);osize=(.15,.145,.04) if key=='box' else (.14,.09,.045)
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
 co={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};anchor=co[t]['inactive_anchor'];geometry=lambda v:model.scene_geometry(side,v,target_xyz=tr[key][t],target_quat=ori[key][t],other_xyz=tr[other][t],other_quat=ori[other][t],other_size=osize)
 # Full input/output dictionaries must be exactly unchanged with optional response off.
 for h in [case['history'][i] for i in sorted(set([0,len(case['history'])//2,len(case['history'])-1]))]:
  qq=np.array(h['measured_q']);residual=np.array(h['solver'].get('causal_tracking_residual_rad',q[t]-u[t-1]));kwargs=dict(tracking_residual=residual,lower=lo,upper=hi,step_limits=np.r_[.015,np.full(10,.04)],damping=np.r_[.12,np.full(10,.045)],target_size=size,inactive_anchor=anchor,preferred_core_scale=np.array(case['core_scale']))
  outputs=[]
  for m in mods:
   try:outputs.append(m.contact_patch_step(qq,geometry,**kwargs))
   except ValueError as e:outputs.append(dict(error=str(e)))
  assert outputs[0]==outputs[1],(ep.name,h['step']);parity.append(dict(episode=str(ep),history_step=h['step'],default_exact=True))
 # Independently differentiate a fixed true hull point under an affine response.
 task='push_box_to_bin' if key=='box' else 'nudge_mailer_to_bin';a=np.array(fit['fits'][task]['a']);gain,offset=response_parameters(q[t],q[t-1],u[t-1],a);cmd=q[t].copy();responded=gain*cmd+offset;T,jl,jw=model.fk(side,responded);point=model.vertices[side][0];v=T[:3,:3]@point
 skew=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]]);analytic=(jl-skew@jw)*gain[None,:];numerical=np.zeros((3,11));eps=1e-6
 for k in range(11):
  plus=cmd.copy();minus=cmd.copy();plus[k]+=eps;minus[k]-=eps;P=model.fk(side,gain*plus+offset)[0];M=model.fk(side,gain*minus+offset)[0];numerical[:,k]=(P[:3,3]+P[:3,:3]@point-M[:3,3]-M[:3,:3]@point)/(2*eps)
 jacmax=max(jacmax,float(np.max(abs(analytic-numerical))))
assert jacmax<1e-7
for row in fit['rows']:
 ep=next((w/'front_cop_route_axis_groups_r1').glob('case_*/'+row['episode']));task='push_box_to_bin' if 'push_box' in ep.name else 'nudge_mailer_to_bin';a=np.array(fit['fits'][task]['a'])
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 for t in row['actual_frames']:
  gain,offset=response_parameters(q[t],q[t-1],u[t-1],a);want=u[t]+a*(q[t]-u[t])+(q[t]-u[t-1])-a*(q[t-1]-u[t-1]);err=float(np.max(abs(gain*u[t]+offset-want)));maxeq=max(maxeq,err);model_rows+=1
assert maxeq<2e-15
rejected=0
for args in [(np.zeros(10),np.zeros(11),np.zeros(11),np.zeros(11)),(np.full(11,np.nan),np.zeros(11),np.zeros(11),np.zeros(11)),(np.zeros(11),np.zeros(11),np.zeros(11),np.ones(11)),(np.zeros(11),np.zeros(11),np.zeros(11),np.full(11,-.1))]:
 try:response_parameters(*args)
 except ValueError:rejected+=1
assert rejected==4
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();result=dict(default_parity=parity,actual_response_rows=model_rows,response_equation_max_error_rad=maxeq,fk_chain_rule_max_error_m_per_rad=jacmax,invalid_inputs_rejected=rejected,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'contact_patch_approach.py',stage/'causal_unloaded_response.py',w/'staged_core_interior_probe/contact_patch_approach.py',source,fitreport]},scope='Unwired probe; default exact on24 real/historical solver inputs from8 starts; all8episode eligible response rows independently reconstructed; fixed-hull-point response Jacobian differentiated on8 actual states. Does not prove physical response or full candidate solver safety.',training_ready=False);(stage/'CHECK.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['default_parity','source_sha256']}))
