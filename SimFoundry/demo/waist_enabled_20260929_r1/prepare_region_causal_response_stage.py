"""Prepare isolated collector wiring; does not launch or approve physical use."""
from pathlib import Path
import json,hashlib,ast
w=Path(__file__).resolve().parent;parent=w/'staged_front_cop_route_axis';stage=w/'staged_region_causal_response';stage.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for name in ['collect_paired_sorting.py','articulated_hand_geometry.py','region_top_contact.py','region_approach_lifecycle.py','front_cop_route.py','contact_slip_following.py']:(stage/name).write_bytes((parent/name).read_bytes())
probe=w/'staged_causal_command_damping_probe'
for name in ['contact_patch_approach.py','causal_unloaded_response.py']:(stage/name).write_bytes((probe/name).read_bytes())
fitpath=w/'unloaded_tracking_dynamics_bias_audit_r1/RESULT.json';fit=json.loads(fitpath.read_text());params=dict(schema_version=1,fit_report_sha256=sha(fitpath),fit_parent=fit['fit_parent'],tasks={task:dict(decay=v['a'],parent_samples=v['n']) for task,v in fit['fits'].items()},scope='Frozen decay only; bias computed causally from current/previous measured upper11 q and previous executed command. No child parameter fitting. Unloaded rear-region use only.');(stage/'causal_response_parameters.json').write_text(json.dumps(params,indent=2))
p=stage/'region_approach_lifecycle.py';s=p.read_text()
def sub(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new)
sub('    abort_tip: object=None','    abort_tip: object=None\n    causal_decay: object=None\n    preferred_core_scale: object=None')
sub('inactive_anchor,normal_anchor,load_n):','inactive_anchor,normal_anchor,load_n,previous_q=None):')
old="        result=contact_patch_step(q,geometry,lower=lower,upper=upper,step_limits=step_limits,damping=damping,target_size=state.size,inactive_anchor=inactive_anchor,tracking_residual=residual)"
new="""        solver_extra={}
        response_record=None
        if self.causal_decay is not None:
            from causal_unloaded_response import response_parameters
            if previous_q is None:raise ValueError('Causal region response requires actual previous measured q')
            if self.preferred_core_scale is None:raise ValueError('Causal region response requires measured collision core')
            gain,offset=response_parameters(q,previous_q,previous_command,self.causal_decay)
            solver_extra=dict(response_gain=gain,response_offset=offset,preferred_core_scale=self.preferred_core_scale,command_change_damping=True)
            response_record=dict(current_q=np.asarray(q).tolist(),previous_q=np.asarray(previous_q).tolist(),previous_command=np.asarray(previous_command).tolist(),decay=np.asarray(self.causal_decay).tolist(),gain=gain.tolist(),offset=offset.tolist(),core_scale=np.asarray(self.preferred_core_scale).tolist(),command_change_damping=True,scope='Current/past state only, original nominal and affine-response geometry guards.')
        result=contact_patch_step(q,geometry,lower=lower,upper=upper,step_limits=step_limits,damping=damping,target_size=state.size,inactive_anchor=inactive_anchor,tracking_residual=residual,**solver_extra)
        if response_record is not None:result['causal_response']=response_record"""
sub(old,new);p.write_text(s)
p=stage/'collect_paired_sorting.py';s=p.read_text();old="parser.add_argument('--region-tracking-residual', action='store_true', help='Isolated current-q minus previous-command response predictor; requires region approach, diagnostic only.')";sub(old,old+"\nparser.add_argument('--region-causal-response',action='store_true',help='Diagnostic rear-region causal lag/bias, actual core interior and previous-command damping; default off.')")
old="if args.region_top_approach != args.region_tracking_residual:";sub(old,"if args.region_causal_response and not (args.region_top_approach and args.region_tracking_residual and args.trace_solved_contact_forces and args.role=='diagnostic'):\n    parser.error('Causal region response requires traced diagnostic region tracking')\n"+old)
old='                    region_approach = RegionApproachLifecycle()';new="""                    region_extra={}
                    if args.region_causal_response:
                        from isaaclab.sim.utils.stage import get_current_stage
                        from simfoundry.data.parcel_collision_geometry import read_parcel_collision_geometry
                        from causal_unloaded_response import response_parameters
                        actual_core=read_parcel_collision_geometry(get_current_stage(),'/World/envs/env_0/'+('parcel_box' if side=='right' else 'mailer'),expected_size=env.scene['parcel_box' if side=='right' else 'mailer'].cfg.spawn.size)
                        core_scale=np.asarray(actual_core['collision_core_size_xyz'])/np.asarray(target_size)
                        parameters=json.loads((STAGE/'causal_response_parameters.json').read_text())
                        if parameters['schema_version']!=1:raise ValueError('Invalid causal response schema')
                        decay=np.asarray(parameters['tasks'][task_id]['decay'],dtype=float)
                        response_parameters(np.zeros(11),np.zeros(11),np.zeros(11),decay)
                        if core_scale.shape!=(3,) or not np.isfinite(core_scale).all() or np.any(core_scale<=0) or np.any(core_scale>1+1e-7) or not np.isclose(core_scale[2],1.,atol=1e-7,rtol=0):raise ValueError('Unsupported causal region collision core')
                        core_scale[2]=1.
                        region_extra=dict(causal_decay=decay,preferred_core_scale=core_scale)
                        frontal_plan['region_causal_response']=dict(enabled=True,actual_core=actual_core,core_scale=core_scale.tolist(),decay=decay.tolist(),parameters_sha256=hashlib.sha256((STAGE/'causal_response_parameters.json').read_bytes()).hexdigest(),core_inset_m=.01,command_change_damping=True,planner_waist_reserve_rad=min(.02,.1*args.waist_limit_rad),scope='Unloaded rear-region only; original guards, load confirmation, first zero pose and no assistance remain.')
                    region_approach = RegionApproachLifecycle(**region_extra)""";sub(old,new)
old="                    waypoint,reference,region_step=region_approach.update(waypoint,frontal_state,reference,q=q_region,previous_command=(previous[12:23]+default[12:23]),geometry=geometry_region,lower=region_lower,upper=region_upper,step_limits=region_limits,damping=region_damping,inactive_anchor=inactive_anchor['right' if side=='left' else 'left'],normal_anchor=top_contact_normal_anchor,load_n=load_n)"
new="""                    causal_context={}
                    if args.region_causal_response:
                        if np.max(abs(q_region-np.asarray(obs['policy'][0].detach().cpu().numpy()[12:23],dtype=float)))>1e-6:raise ValueError('Causal region state ordering differs from recorded state')
                        causal_context['previous_q']=np.asarray(qs[-1][12:23],dtype=float) if qs else None
                    waypoint,reference,region_step=region_approach.update(waypoint,frontal_state,reference,q=q_region,previous_command=(previous[12:23]+default[12:23]),geometry=geometry_region,lower=region_lower,upper=region_upper,step_limits=region_limits,damping=region_damping,inactive_anchor=inactive_anchor['right' if side=='left' else 'left'],normal_anchor=top_contact_normal_anchor,load_n=load_n,**causal_context)""";sub(old,new)
old="paths.extend([STAGE/name for name in ['contact_patch_approach.py','articulated_hand_geometry.py','region_top_contact.py','region_approach_lifecycle.py','front_cop_route.py','contact_slip_following.py']])";sub(old,"paths.extend([STAGE/name for name in ['contact_patch_approach.py','articulated_hand_geometry.py','region_top_contact.py','region_approach_lifecycle.py','front_cop_route.py','contact_slip_following.py','causal_unloaded_response.py','causal_response_parameters.json']])")
p.write_text(s)
for p in stage.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
(stage/'PREPARATION.json').write_text(json.dumps(dict(status='written_syntax_checked_not_runtime_validated',collector_wired_in_source=True,physical_started=False,source_sha256={p.name:sha(p) for p in stage.iterdir() if p.suffix in ['.py','.json']},basis_probe_check_sha256=sha(probe/'CHECK.json'),basis_screen_sha256=sha(w/'causal_command_damping_screen_r1/RESULT.json'),outstanding=['Default-off lifecycle/collector equivalence','Enabled actual previous-q/current-command dataflow and physical core size check','CLI negative cases and53source archive','Independent full command/geometry audit','Original8push2wait frozen protocol/startup verification/real physics and visual review'],training_ready=False),indent=2));print(str(stage),'prepared; no physics launched')
