"""Exact executed-solver replay and explicit waist-perturbation FK counterfactuals."""
from pathlib import Path
import hashlib,importlib.util,json,sys
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_measured_bounds_probe';parent=w/'staged_region_causal_xy_diagnostics'
sys.path[:0]=[str(parent),str(repo),str(w)]
from articulated_hand_geometry import ArticulatedHandGeometry
from causal_unloaded_response import response_parameters
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
from audit_region_causal_xy_live import inspect_geometry
spec=importlib.util.spec_from_file_location('measured_bound_candidate',stage/'contact_patch_approach.py');candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json')
lower=np.array(U1_JOINT_LIMIT_LO)[12:23].copy();upper=np.array(U1_JOINT_LIMIT_HI)[12:23].copy();lower[0]=-.98;upper[0]=.98;ml=lower.copy();mu=upper.copy();ml[0]=-1.;mu[0]=1.;reports=[];counterfactuals=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for run in ['region_causal_response_groups_r1','region_causal_xy_groups_r2']:
 for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';rows=json.loads((ep/'region_approach.json').read_text())['rows'];coord={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};key='box' if task=='push_box_to_bin' else 'mailer';other='mailer' if key=='box' else 'box';side='right' if key=='box' else 'left';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);osize=(.15,.145,.04) if key=='box' else (.14,.09,.045)
  with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
  with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
  with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
  selected=[r for r in rows if r['solver'] and r['solver'].get('joint_override')];assert selected
  near=[r['step'] for r in selected if abs(q[r['step'],0])>.979]
  chosen=set(near[::max(1,len(near)//8)][:8])
  exact=0;changed_default=0
  for row in selected:
   t=row['step'];s=row['solver'];c=s['causal_response'];geometry=lambda v:model.scene_geometry(side,v,target_xyz=tr[key][t],target_quat=ori[key][t],other_xyz=tr[other][t],other_quat=ori[other][t],other_size=osize)
   kw=dict(lower=lower,upper=upper,step_limits=np.r_[.015,np.full(10,.04)],damping=np.r_[.12,np.full(10,.045)],target_size=size,inactive_anchor=coord[t]['inactive_anchor'],tracking_residual=q[t]-u[t-1],response_gain=np.array(c['gain']),response_offset=np.array(c['offset']),preferred_core_scale=np.array(c['core_scale']),command_change_damping=True,response_centered_xy_objective=c.get('response_centered_xy_objective',False))
   default=candidate.contact_patch_step(q[t],geometry,**kw)
   assert default['accepted'] and default['reached']==s['reached'] and np.max(abs(np.array(default['next_q'])-s['next_q']))<1e-12,(run,task,t)
   enabled=candidate.contact_patch_step(q[t],geometry,**kw,measured_lower=ml,measured_upper=mu)
   assert default==enabled,(run,task,t,'changed_in_domain_result')
   exact+=1
   if t not in chosen:continue
   for excess in [4.710674285890448e-5,.001,.005]:
    cq=q[t].copy();cq[0]=np.sign(cq[0])*(.98+excess)
    gain,offset=response_parameters(cq,q[t-1],u[t-1],np.array(c['decay']));ckw=dict(kw,tracking_residual=cq-u[t-1],response_gain=gain,response_offset=offset)
    out=candidate.contact_patch_step(cq,geometry,**ckw,measured_lower=ml,measured_upper=mu)
    assert not out['reached'],'Handover while outside planning bounds'
    checks=[]
    if out['accepted']:
     cmd=np.array(out['next_q']);assert np.max(abs(cmd-u[t-1]))<=.055+1e-7
     assert np.all(abs(cmd-cq)<=kw['step_limits']+1e-8)
     for name,v in [('nominal',cmd),('forecast',gain*cmd+offset)]:
      check=inspect_geometry(model,side,v,tr[key][t],ori[key][t],tr[other][t],ori[other][t],size,osize);assert not check['errors'],(run,t,excess,name,check)
      checks.append(dict(response=name,**check))
    counterfactuals.append(dict(run=run,episode=ep.name,source_step=t,waist_excess_rad=excess,accepted=out['accepted'],reached=out['reached'],reason=out['reason'],geometry_checks=checks))
  reports.append(dict(run=run,episode=ep.name,all_executed_override_steps_exact=exact,all_in_domain_enabled_equal=True,near_bound_source_steps=sorted(chosen),source_sha256={f:sha(ep/f) for f in ['raw.npz','trace.npz','parcel_orientation.npz','coordination.json','region_approach.json']}));print(reports[-1]['episode'],exact,len(chosen),flush=True)
report=dict(passed=True,rows=reports,counterfactuals=counterfactuals,total_exact_actual_steps=sum(r['all_executed_override_steps_exact'] for r in reports),counterfactual_count=len(counterfactuals),counterfactual_accepted=sum(r['accepted'] for r in counterfactuals),candidate_sha256=sha(stage/'contact_patch_approach.py'),checker_sha256=sha(Path(__file__)),independent_geometry_auditor_sha256=sha(w/'audit_region_causal_xy_live.py'),collector_wired=False,physical_started=False,training_ready=False,scope='Every executed override in four complete rear episodes exactly reproduced; explicit physical-domain enabled results identical inside planning range. Selected real near-bound states have waist only perturbed with causal response recomputed; real FK and original command/forecast geometry inspected. Counterfactuals are not the failed episode geometry or new physical recovery; rejected cases retained.')
(stage/'REAL_GEOMETRY_CHECK.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k not in ['rows','counterfactuals']},flush=True)
