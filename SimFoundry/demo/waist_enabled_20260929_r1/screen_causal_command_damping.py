"""Same8 historical unloaded starts, two approximate lag plants, old/new core approach.
Frozen objects; no simulator or training admission. Matched surrogate evidence only.
"""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_causal_command_damping_probe';sys.path[:0]=[str(stage),str(w/'staged_front_cop_route_axis'),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry
from causal_unloaded_response import response_parameters
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');lo=np.array(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.array(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();fitpath=w/'unloaded_tracking_dynamics_bias_audit_r1/RESULT.json';fit=json.loads(fitpath.read_text());source=w/'staged_core_interior_unloaded_screen/UNLOADED_CORE_INTERIOR_SCREEN.json';old=json.loads(source.read_text());cases=[r for r in old['rows'] if r['scenario']=='nominal_response' and r['variant']=='core_interior'];assert len(cases)==8
mods={}
for name,path in [('causal_response_baseline',w/'staged_causal_response_probe/contact_patch_approach.py'),('command_change_damping',stage/'contact_patch_approach.py')]:
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);mods[name]=m
out=w/'causal_command_damping_screen_r1';out.mkdir(exist_ok=False);rows=[];source_hashes={}
for plant in ['parent_fixed_bias','initial_actual_bias']:
 for variant,mod in mods.items():
  for ci,case in enumerate(cases):
   ep=Path(case['episode']);t=case['actual_start_frame'];key='box' if 'push_box' in ep.name else 'mailer';task='push_box_to_bin' if key=='box' else 'nudge_mailer_to_bin';side='right' if key=='box' else 'left';other='mailer' if key=='box' else 'box';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);osize=(.15,.145,.04) if key=='box' else (.14,.09,.045)
   with np.load(ep/'raw.npz') as z:q=z['q'][t,12:23].astype(float);previous_q=z['q'][t-1,12:23].astype(float);previous=z['action'][t-1,12:23].astype(float)
   with np.load(ep/'trace.npz') as z:tr={k:z[k][t] for k in z.files}
   with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k][t] for k in z.files}
   co={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};anchor=co[t]['inactive_anchor'];geometry=lambda v:model.scene_geometry(side,v,target_xyz=tr[key],target_quat=ori[key],other_xyz=tr[other],other_quat=ori[other],other_size=osize)
   a=np.array(fit['fits'][task]['a']);b=np.array(fit['fits'][task]['bias_rad']) if plant=='parent_fixed_bias' else (q-previous)-a*(previous_q-previous);history=[]
   for step in range(600):
    kwargs=dict(tracking_residual=q-previous,lower=lo,upper=hi,step_limits=np.r_[.015,np.full(10,.04)],damping=np.r_[.12,np.full(10,.045)],target_size=size,inactive_anchor=anchor,preferred_core_scale=np.array(case['core_scale']))
    if variant in mods:gain,offset=response_parameters(q,previous_q,previous,a);kwargs.update(response_gain=gain,response_offset=offset)
    if variant=='command_change_damping':kwargs['command_change_damping']=True
    try:sol=mod.contact_patch_step(q,geometry,**kwargs)
    except ValueError as e:sol=dict(accepted=False,reached=False,reason=str(e),next_q=q.tolist())
    row=dict(step=step,measured_q=q.tolist(),previous_command=previous.tolist(),solver={k:v for k,v in sol.items() if k not in ['line_search_attempts','constrained_vertex_indices']});history.append(row)
    if sol['reached'] or not sol['accepted'] or sol['reason']=='stagnation':break
    command=np.array(sol['next_q']);assert np.max(abs(command-previous))<=.0550001
    next_q=(1-a)*command+a*q+b;previous_q=q;q=next_q;previous=command
    if step%100==0:(out/'STATUS.json').write_text(json.dumps(dict(plant=plant,variant=variant,case=ci,step=step,pid=__import__('os').getpid(),training_ready=False)))
   result=dict(plant=plant,variant=variant,episode=str(ep),actual_start_frame=t,steps=len(history),reached=sol['reached'],stop=sol['reason'],final_local_xyz=sol.get('physical_point_local_xyz'),top_gap_m=sol.get('top_gap_m'),inactive_error_m=sol.get('inactive_error_m'),history=history);rows.append(result)
   print(json.dumps({k:v for k,v in result.items() if k!='history'}),flush=True)
   source_hashes[str(ep/'raw.npz')]=sha(ep/'raw.npz')
   report=dict(complete=len(rows)==32,rows=rows,source_sha256={**source_hashes,**{str(p):sha(p) for p in [Path(__file__),source,fitpath,stage/'contact_patch_approach.py',stage/'causal_unloaded_response.py',w/'staged_causal_response_probe/contact_patch_approach.py']}},scope='Same8 historical unloaded starts/600step budget, original core-interior goal and geometry constraints, same causal response, measured-q damping baseline vs previous-command damping; same0.98rad, XYweight1 and all original geometry/response/bounds. Two diagonal first-order plants with parent-fitted decay, constant parent bias vs bias inferred from actual initial transition; bias held thereafter. Frozen objects and no loads. These are matched/approximate response surrogates, not new measured dynamics, contact or physical success; local bias may change with posture. All32 conditions retained. No collector wiring or training admission.',training_ready=False);(out/'RESULT.json').write_text(json.dumps(report,indent=2))
