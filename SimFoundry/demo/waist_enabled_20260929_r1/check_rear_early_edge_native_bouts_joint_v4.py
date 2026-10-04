"""Native continuous loaded-bout replay from recorded initial controller states.

Each bout is initialized once after its first loaded action; subsequent candidate
commands/pressure/COP state propagate without resets. Recorded observations are
fixed, so this is neither full-prefix planning nor counterfactual physics. The original joint IK/edge refinement/final guard is checked on fixed measured states.
No recursive physical or complete-prefix claim is made.
"""
from pathlib import Path
from types import SimpleNamespace
import ast,copy,datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import linprog

W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_box_trailing_v2';C=W/'rear_early_edge_candidate_v1'
sys.path[:0]=[str(C),str(S),str(ROOT)]
from rear_cop_route_early import RearCopRouteState
from simfoundry.data.frontal_bypass import FrontalBypassState,extent_x_from_quat
from simfoundry.data.contact_load_control import hand_target_vertical_load
from simfoundry.data.top_contact_load_geometry import loaded_forward_margin
from margin_confirmed_position_release import ConfirmedPositionRelease
from peak_load_update_trace import TracedPeakLoadControl
from clearance_runtime import ClearanceGuard
from native_joint_replay_v2 import replay
guard=ClearanceGuard(ROOT,S)
joint_results=[]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources={}
def bound(p):sources[str(p)]=sha(p);return p
def read(p):return json.loads(bound(p).read_text())
collector=bound(S/'collect_paired_sorting.py');nodes=list(ast.walk(ast.parse(collector.read_text())))
construct=next(n for n in nodes if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='top_cls')
construct_code=compile(ast.Module(body=[construct],type_ignores=[]),str(collector),'exec')
comparison=read(W/'front_box_trailing_physical_r2/REAR_BOX_CONTACT_COMPARISON_V2.json')
independent_source=bound(W/'audit_substep_rear_xy.py')
independent_nodes=[n for n in ast.parse(independent_source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ['independent_joint_xy','independent_progress']]
ind_env={'np':np,'linprog':linprog};exec(compile(ast.Module(body=independent_nodes,type_ignores=[]),str(independent_source),'exec'),ind_env)
independent10=ind_env['independent_joint_xy'];independent_y=ind_env['independent_progress']
node=next(n for n in independent_nodes if n.name=='independent_joint_xy');code=ast.unparse(node);assert code.count('< 0.01')==1
exec(compile(code.replace('< 0.01','< 0.02'),str(independent_source),'exec'),ind_env);independent20=ind_env['independent_joint_xy']
results=[];total=0;changed=0;independent_calls=0;guard_tests=[]
for version in ['r1','r2']:
    case=W/('front_box_trailing_physical_'+version)/'case_840023';ep=case/'layout_840023_push_box_to_bin'
    args=SimpleNamespace(**read(case/'provenance.json')['args'])
    fr=read(ep/'frontal_bypass.json');plan=fr['plan'];rows={r['step']:r for r in fr['rows']}
    coords={r['step']:r for r in read(ep/'coordination.json')}
    with np.load(bound(ep/'raw.npz')) as z:qs=z['q'][:,12:23].copy();actions=z['action'][:,12:23].copy()
    assert read(ep/'front_initial_center.json')['selected'] is False
    assert read(ep/'front_recontact_center.json')['selected'] is False
    regions={r['step']:r for r in read(ep/'region_approach.json')['rows']};experts=read(ep/'expert_control.json')
    packets={p['after_action_step']:p for p in read(ep/'solved_contact_forces.json')['rows']}
    with np.load(bound(ep/'trace.npz')) as z:trace={k:z[k].astype(float) for k in z.files}
    with np.load(bound(ep/'parcel_orientation.npz')) as z:orient={k:z[k].astype(float) for k in z.files}
    recording=read(ep/'SUBSTEP_CONTACT_RECORDING.json');assert recording['recording_sha256']==sha(ep/'substep_contacts.npz')
    m=recording['metadata'];labels=m['shape_labels'];stride=24+m['expected_manager_steps']
    with np.load(bound(ep/'substep_contacts.npz')) as z:a={k:z[k].copy() for k in ['shape_ids','contact_offsets','force_torque_world','action_step','substep_tick']}
    obj=np.array([i for i,x in enumerate(labels) if '/parcel_box/' in x]);hand=np.array([i for i,x in enumerate(labels) if 'right_wrist_roll' in x])
    selected=np.isin(a['shape_ids'],obj).any(1)&np.isin(a['shape_ids'],hand).any(1)
    samples=np.repeat(np.arange(len(a['action_step'])),np.diff(a['contact_offsets']))
    loads=np.bincount(samples[selected],weights=abs(a['force_torque_world'][selected,2].astype(float)),minlength=len(a['action_step']))
    def native(early,lo):
        extra=dict(recontact_travel_z=.86,rear_slow_drag=True,rear_cop_enabled=True,rear_core_slice_enabled=True,rear_coupled_progress_enabled=True,rear_joint_xy_enabled=True,rear_cop_core_size=plan['rear_cop_centering']['actual_core_size_xyz'],rear_early_edge_enabled=early)
        rear=FrontalBypassState(copy.deepcopy(plan),staging_z=args.expert_staging_z,press_z=args.expert_frontal_press_z,feedback_rear_endpoint=args.expert_frontal_feedback,follow_target_y=args.expert_frontal_follow_y,rear_contact_y_offset_m=args.expert_frontal_rear_y_offset_m,rear_contact_object_frame=args.expert_frontal_rear_object_frame,recontact_after_rear=args.expert_frontal_recontact,planned_sweep_x=args.expert_frontal_sweep_x,tracked_sweep=args.expert_frontal_track_sweep,sweep_lead_y=args.expert_frontal_sweep_lead_y)
        env=dict(top_cls=RearCopRouteState,frontal_state=rear,side='right',contact_size=tuple(plan['top_recontact']['contact_size_xyz']),top_extra=extra,args=args,front_route_selected=False,effective_drag_step_m=.0015,effective_top_fraction=plan['top_recontact']['effective_top_fraction'])
        exec(construct_code,env);s=env['frontal_state'];r=rows[lo];f=r['contact_load'];cop=r['rear_cop_centering']
        assert cop['reason']=='preserve_first_loaded_push' and f['observed_vertical_load_n']>=.2
        s.top_mode=s.mode='top_push';s.mode_step=experts[lo]['mode_step'];s.command=tuple(r['target_xyz']);s.last_waypoint_xy=tuple(r['target_xyz'][:2]);s.push_x_anchor=r['push_x_anchor_m'];s.selected_surface_local_xy=tuple(regions[lo]['selected_surface_local_xy']);s.recontacts=r['recontacts'];s.last_recontact_reason=r['last_recontact_reason'];s.approach_xy_bias=list(r['approach_xy_bias_m']);s.lost_contact_steps=0
        s.rear_cop.anchor_local=np.asarray(cop['anchor_local']);s.rear_cop.last_anchor_world=trace['box'][lo]+Rotation.from_quat(orient['box'][lo]).apply(s.rear_cop.anchor_local)
        s.load=TracedPeakLoadControl(args.expert_frontal_top_load_n,bias_m=f['stored_z_bias_m'],filtered_n=f['filtered_vertical_load_n'],min_bias_m=-.006);s.load.bind_owner(s);s.load._last_action_step=lo
        s.position_release_monitor=ConfirmedPositionRelease(plan['initial_target_xyz'][1],plan['direction'])
        for xyz in trace['box'][max(0,lo-9):lo+1]:s.position_release_monitor.observe(xyz)
        return s
    for bout in comparison['results'][version]['bouts']:
        lo=bout['start'];end=bout['exit_step'] if bout['exit_step'] is not None else bout['end'];off=native(False,lo);on=native(True,lo);records=[];fixture=None
        joint_previous=actions[lo].copy();joint_stopped=False;joint_rows=[]
        for t in range(lo+1,end+1):
            previous=t-1;ids=np.arange(previous*stride,(previous+1)*stride);ticks=a['substep_tick'][ids];ix=[int(ids[np.flatnonzero(ticks==k)[0]]) for k in range(1,25)]
            packet=packets[previous];load=hand_target_vertical_load(packet,'right','parcel_box');contact=loaded_forward_margin(packet,'right','parcel_box',trace['box'][t],orient['box'][t],off.size,plan['direction'])
            r=rows[t];kw=dict(tip=r['observed_support_xyz'],quat=orient['box'][t],control_offset_local=r['observed_support_offset_local'],load_n=load,hand_obstacle_gap_m=r.get('hand_obstacle_gap_m'),slip_contact=contact)
            obs=(trace['palm_right'][t],trace['box'][t],trace['mailer'][t],extent_x_from_quat(off.size,orient['box'][t]),extent_x_from_quat((.15,.145,.04),orient['mailer'][t]))
            if fixture is None:fixture=(copy.deepcopy(obs),copy.deepcopy(kw),loads[ix].copy(),t)
            candidate_previous=np.asarray(on.command if on.command is not None else (*on.last_waypoint_xy,kw['tip'][2]))
            emitted=[]
            for state in [off,on]:
                state.load.observe(action_step=t,after_action_step=previous,vertical_load_n=loads[ix]);emitted.append(state.update(*obs,**kw))
            baseline,candidate=emitted
            feedback=candidate.get('rear_cop_centering',{})
            if feedback.get('override'):
                rot=Rotation.from_quat(orient['box'][t]).as_matrix();local=rot.T@(np.asarray(feedback['cop_world'])-trace['box'][t]);core=np.asarray(plan['rear_cop_centering']['actual_core_size_xyz']);parent_xyz=np.asarray(feedback['command_xyz']);ref=np.asarray(kw['tip'])
                old=independent10(candidate_previous,parent_xyz,ref,rot,core,local,plan['direction']);early=independent20(candidate_previous,parent_xyz,ref,rot,core,local,plan['direction']);chosen=early if early['override'] else old
                y=independent_y(candidate_previous,parent_xyz,rot,core,local,plan['direction']);fallback=y.get('command_xyz',parent_xyz);expected=chosen.get('command_xyz',fallback)
                np.testing.assert_allclose(candidate['target_xyz'],expected,atol=2e-7,rtol=0,err_msg=f'{version}:{t}:independent candidate chain')
                assert candidate['rear_joint_xy_progress']['override']==chosen['override'] and candidate['rear_joint_xy_progress']['reason']==chosen['reason']
                independent_calls+=1
            assert baseline['mode']==r['mode'],(version,t,baseline['mode'],r['mode'])
            np.testing.assert_allclose(baseline['target_xyz'],r['target_xyz'],atol=2e-6,rtol=0,err_msg=f'{version}:{t}:native baseline')
            np.testing.assert_allclose(baseline['contact_load']['stored_z_bias_m'],r['contact_load']['stored_z_bias_m'],atol=1e-9,rtol=0)
            delta=np.asarray(candidate['target_xyz'])-np.asarray(baseline['target_xyz']);different=bool(np.max(abs(delta))>1e-9 or candidate['mode']!=baseline['mode']);total+=1;changed+=different
            context=dict(guard=guard,coordinate=coords[t],current=qs[t],object_xyz=trace['box'][t],object_rotation=Rotation.from_quat(orient['box'][t]).as_matrix(),core_size=plan['region_causal_response']['actual_core']['collision_core_size_xyz'])
            original_u,original_j=replay(row=r,previous=actions[t-1],original=True,**context)
            assert original_u is not None,(version,t,'baseline rejected')
            np.testing.assert_allclose(original_u,actions[t],atol=2e-6,rtol=0,err_msg=f'{version}:{t}:original native joint chain')
            jr=dict(step=t,baseline_matches_actual=True,baseline_max_abs_error_rad=float(np.max(abs(original_u-actions[t]))))
            if not joint_stopped:
                np.testing.assert_allclose(candidate['control_offset_local'],r['control_offset_local'],atol=1e-9,rtol=0)
                candidate_u,candidate_j=replay(row=candidate,previous=joint_previous,**context)
                jr['candidate']=candidate_j
                if candidate_u is None:joint_stopped=True
                else:joint_previous=candidate_u.copy()
            else:jr['candidate_skipped_after_original_guard_stop']=True
            joint_rows.append(jr)
            records.append(dict(step=t,baseline_mode=baseline['mode'],candidate_mode=candidate['mode'],baseline_target_xyz=baseline['target_xyz'],candidate_target_xyz=candidate['target_xyz'],changed=different,early_edge=candidate.get('rear_joint_xy_progress',{}).get('early_edge')))
        if not guard_tests:
            for label in ['tilt','lost_contact','release']:
                obs0,kw0,loads0,t0=copy.deepcopy(fixture);state=native(True,lo);obs0=list(obs0)
                if label=='tilt':kw0['quat']=(Rotation.from_euler('x',.06)*Rotation.from_quat(kw0['quat'])).as_quat()
                elif label=='lost_contact':state.lost_contact_steps=2;kw0['load_n']=0.;kw0['slip_contact']=None;loads0=np.zeros(24)
                else:obs0[1]=np.array(obs0[1]);obs0[1][1]=-.30
                state.load.observe(action_step=t0,after_action_step=t0-1,vertical_load_n=loads0);row=state.update(*obs0,**kw0)
                if label=='release':assert row['mode']=='top_release' and row['target_xyz'][2]>=.91
                else:assert row['mode']=='top_lift' and row['last_recontact_reason']==('incipient_tilt_independent' if label=='tilt' else 'lost_contact')
                assert not row.get('rear_joint_xy_progress',{}).get('override')
                guard_tests.append(dict(case=label,mode=row['mode'],passed=True,synthetic_modified_observation=True))
        joint_results.append(dict(version=version,start_state_after_action=lo,last_action=end,stopped=joint_stopped,rows=joint_rows))
        results.append(dict(version=version,start_state_after_action=lo,last_action=end,frames=len(records),baseline_matches_actual=True,own_candidate_command_state_propagated=True,records=records))
        print(json.dumps({k:v for k,v in results[-1].items() if k!='records'}),flush=True)
for p,h in sources.items():assert sha(p)==h,p
for module in list(sys.modules.values()):
    name=getattr(module,'__file__',None)
    if name:
        p=Path(name).resolve()
        if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
sources[str(Path(__file__).resolve())]=sha(__file__)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,joint_results=joint_results,joint_candidate_all_accepted=all(not b['stopped'] for b in joint_results),segments=len(results),native_action_updates=total,changed_actions=changed,independent_composed_candidate_calls=independent_calls,native_guard_tests=guard_tests,rows=results,source_sha256=sources,full_prefix_replay=False,final_joint_guard_verified=False,physics_verified=False,training_ready=False)
with (C/'NATIVE_LOADED_BOUT_JOINT_REPLAY_V4.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['rows','source_sha256','joint_results']},indent=2))
