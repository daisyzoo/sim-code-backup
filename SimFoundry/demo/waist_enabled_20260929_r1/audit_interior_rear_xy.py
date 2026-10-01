"""Independent rear COP and parent Y/Z waypoint reconstruction from recorded inputs."""
from pathlib import Path
import ast,json,hashlib,sys,subprocess
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import linprog


def independent_progress(previous, command, rotation, size, local, direction):
    """Independent current-geometry halfspace LP, never import candidate code."""
    delta=command-previous
    if direction*delta[1]<-1e-10:
        return dict(override=False,reason='parent_nonforward_preserved')
    margins=size[:2]/2-abs(local[:2]);axes=np.flatnonzero(margins<.01)
    if not len(axes):return dict(override=False,reason='no_near_core_edge')
    constants=[];slopes=[];constraints=[];lower,upper=0.,1.
    for axis in axes:
        normal=rotation[:,axis]*(1 if local[axis]>=0 else -1)
        constant=float(normal@np.array([delta[0],0.,delta[2]]))
        slope=float(normal[1]*delta[1]);constants.append(constant);slopes.append(slope)
        constraints.append(dict(axis=int(axis),fixed_m=constant,scaled_m=slope))
        if abs(slope)<1e-14:
            if constant>1e-12:lower,upper=1.,0.
        elif slope>0:upper=min(upper,-constant/slope)
        else:lower=max(lower,-constant/slope)
    evidence=dict(near_axes=axes.tolist(),local_xy_margin_m=margins.tolist(),constraints=constraints,feasible_scale_interval=[lower,upper])
    fit=linprog([-1.],A_ub=np.array(slopes)[:,None],b_ub=-np.array(constants),bounds=[(0.,1.)],method='highs')
    feasible=fit.success and np.max(np.array(constants)+np.array(slopes)*fit.x[0])<=1e-10
    interval_feasible=lower<=upper+1e-10 and upper>=-1e-10 and lower<=1+1e-10
    if feasible!=interval_feasible:raise AssertionError('LP numerical disagreement')
    if not feasible:return dict(override=False,reason='no_Y_only_direction',**evidence)
    scale=float(np.clip(fit.x[0],0,1))
    if scale>=1.-1e-8:return dict(override=False,reason='original_direction_feasible',scale=1.,**evidence)
    emitted=command.copy();emitted[1]=previous[1]+scale*delta[1]
    return dict(override=True,reason='near_edge_forward_Y_scaled',command_xyz=emitted.tolist(),scale=scale,parent_delta_xyz_m=delta.tolist(),projected_local_xy_delta_m=(rotation.T@(emitted-previous))[:2].tolist(),**evidence)


def independent_joint_xy(previous, command, reference, rotation, size, local, direction):
    """Independent LP direction maximization; no candidate helper import."""
    delta=command-previous
    if direction*delta[1]<-1e-10:return dict(override=False,reason='parent_nonforward_preserved')
    axes=np.flatnonzero(size[:2]/2-abs(local[:2])<.010)
    if not len(axes):return dict(override=False,reason='no_near_core_edge')
    low=max(previous[0]-.002,reference[0]-.030);high=min(previous[0]+.002,reference[0]+.030)
    if low>high:return dict(override=False,reason='no_cartesian_slew_and_lead_interval')
    lower,upper=(low-previous[0])*1000,(high-previous[0])*1000
    A=[];b=[]
    for axis in axes:
        normal=rotation[:,axis]*(1 if local[axis]>=0 else -1)
        A.append([float(normal[0]),float(normal[1]*delta[1]*1000)])
        b.append(float(-normal[2]*delta[2]*1000))
    A.extend([[-1,0],[1,0],[0,-1],[0,1]]);b.extend([-lower,upper,0,1]);A=np.asarray(A);b=np.asarray(b)
    evidence=dict(near_axes=axes.tolist(),feasible_x_interval_m=[low,high],constraints_mm=A.tolist(),rhs_mm=b.tolist())
    fit=linprog([0,-1],A_ub=A,b_ub=b,bounds=[(None,None),(None,None)],method='highs',options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
    if not fit.success:
        assert fit.status==2,fit.message
        return dict(override=False,reason='no_joint_XY_direction',**evidence)
    assert np.max(A@fit.x-b)<=1e-8
    scale=float(np.clip(fit.x[1],0.,1.))
    # Separate minimum and maximum X LPs, rather than helper's interval loop.
    opts=dict(A_ub=A,b_ub=b,bounds=[(None,None),(scale,scale)],method='highs',options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
    lf=linprog([1,0],**opts);hf=linprog([-1,0],**opts);assert lf.success and hf.success
    dx=float(np.clip(delta[0]*1000,lf.x[0],hf.x[0]));assert np.max(A@np.array([dx,scale])-b)<=1e-8
    emitted=command.copy();emitted[0]=previous[0]+dx/1000;emitted[1]=previous[1]+scale*delta[1]
    if np.max(abs(emitted-command))<1e-10:return dict(override=False,reason='original_direction_feasible',scale=scale,**evidence)
    return dict(override=True,reason='joint_XY_nonoutward_reference',command_xyz=emitted.tolist(),scale=scale,parent_delta_xyz_m=delta.tolist(),reference_delta_xyz_m=(emitted-previous).tolist(),projected_local_xy_delta_m=(rotation.T@(emitted-previous))[:2].tolist(),**evidence)


def reconstruct(rows, plan, xyz, quat, packets, key, handover):
    side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer'
    cfg=plan['rear_cop_centering'];size=np.asarray(cfg['actual_core_size_xyz']);half=size[:2]/2-.01
    assert cfg['core_inset_m']==.01 and cfg['feedback_gain']==.05 and cfg['max_x_step_m']==.002 and cfg['max_reference_x_lead_m']==.030
    progress_cfg=plan.get('rear_coupled_progress',{})
    progress_enabled=progress_cfg.get('enabled',False)
    assert type(progress_enabled) is bool
    if progress_enabled:
        assert cfg.get('core_slice_feedback') is True
        assert progress_cfg['core_inset_m']==.01 and progress_cfg['parent_xz_unchanged'] is True
        assert progress_cfg['original_guard_priority'] is True and progress_cfg['first_loaded_preserved'] is True
        assert progress_cfg['infeasible_fallback']=='preserve_parent'
    xy_cfg=plan.get('rear_joint_xy_progress',{})
    xy_enabled=xy_cfg.get('enabled',False)
    assert type(xy_enabled) is bool
    if xy_enabled:
        assert progress_enabled and xy_cfg['core_inset_m']==.01
        assert xy_cfg['max_x_step_m']==.002 and xy_cfg['max_reference_x_lead_m']==.030
        assert xy_cfg['parent_z_unchanged'] is True and xy_cfg['original_guard_priority'] is True
        assert xy_cfg['first_loaded_preserved'] is True and xy_cfg['infeasible_fallback']=='parent_Y_governor'
    slice_enabled=cfg.get('core_slice_feedback',False)
    assert type(slice_enabled) is bool
    assert cfg['preserve_first_loaded_push'] and cfg['parent_yz_unchanged'] and cfg['original_guard_priority']
    assert np.all(half>0) and np.isfinite(size).all()
    rotations=Rotation.from_quat(quat).as_matrix();anchor=last_world=None;previous=None;previous_mode=None;previous_step=None;errors=[];records=[]
    def near(t,name,a,b):
        err=float(np.max(abs(np.asarray(a)-np.asarray(b))))
        if not np.isfinite(err) or err>2e-6:errors.append([t,name,err])
    def compare(t,expected,got,path):
        if isinstance(expected,dict):
            if not isinstance(got,dict):errors.append([t,path,'wrong_type']);return
            for k,v in expected.items():
                if k not in got:errors.append([t,path+'.'+k,'missing'])
                else:compare(t,v,got[k],path+'.'+k)
        elif isinstance(expected,list) and expected and isinstance(expected[0],dict):
            if not isinstance(got,list) or len(got)!=len(expected):errors.append([t,path,'wrong_length']);return
            for i,(a,b) in enumerate(zip(expected,got)):compare(t,a,b,path+'.'+str(i))
        elif isinstance(expected,(str,bool)):
            if type(got) is not type(expected) or got!=expected:errors.append([t,path,'wrong_value'])
        else:
            try:
                if np.asarray(expected).shape!=np.asarray(got).shape:errors.append([t,path,'wrong_shape'])
                else:near(t,path,got,expected)
            except (ValueError,TypeError):errors.append([t,path,'invalid_number'])

    for row in rows:
        t=row['step'];f=row.get('rear_cop_centering');actual=np.asarray(row['target_xyz'],float);ref=np.asarray(row['observed_support_xyz'],float)
        if previous_step is not None and t!=previous_step+1:errors.append([t,'noncontiguous_rows'])
        previous_step=t
        expected_joint_xy=None
        if xy_enabled and handover is not None and t>handover:
            expected_joint_xy=dict(override=False,reason='original_rear_not_overridden')
        expected_progress=None
        if progress_enabled and handover is not None and t>handover:
            expected_progress=dict(override=False,reason='original_rear_not_overridden')
        if f is None:
            errors.append([t,'missing_feedback']);previous=actual;previous_mode=row['mode'];continue
        parent_command=None
        if row['mode']=='top_push' and handover is not None and t>handover:
            if previous_mode not in ('top_push','top_press'):errors.append([t,'unexpected_push_entry'])
            base=previous.copy() if previous is not None else ref.copy()
            if previous_mode=='top_press':base[2]=ref[2]
            direction=plan['direction'];goal_x=row['push_x_anchor_m'];surface_z=row['parcel_top_xyz'][2];bias=row['contact_load']['applied_z_bias_m']
            parent_command=np.array([base[0]+np.clip(goal_x-base[0],-.002,.002),base[1]+np.clip(direction*min(.34,direction*base[1]+.003)-base[1],-.003,.003),base[2]+np.clip(surface_z+.002+bias-base[2],-.001,.001)])
            if progress_enabled:near(t,'unchanged_parent_z',actual[2],parent_command[2])
            else:near(t,'unchanged_parent_yz',actual[1:],parent_command[1:])
        reason=None
        if handover is None or t<=handover:reason='region_not_handed_over'
        elif row['mode']!='top_push':reason='original_non_push_mode'
        if reason:
            if f.get('override') or f.get('reason')!=reason:errors.append([t,'guard_or_handover_bypass'])
            anchor=last_world=None
        else:
            obj=np.asarray(xyz[t]);rot=rotations[t];packet=packets.get(t-1);points=[];weights=[]
            if packet:
                near(t,'prior_contact_pose',packet['post_action_pose'][key],obj)
                for c in packet['parcel_contacts']:
                    slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
                    if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
                    force=np.asarray(c['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(force@rot[:,2])
                    if load>.05:points.append(c['position_world']);weights.append(load)
            if not weights or sum(weights)<.3:
                reason='no_valid_loaded_contact';anchor=last_world=None
            else:
                cop_world=np.average(points,axis=0,weights=weights);local=rot.T@(cop_world-obj)
                if anchor is None:
                    anchor=np.r_[np.clip(local[:2],-half,half),local[2]];last_world=obj+rot@anchor;reason='preserve_first_loaded_push'
                    near(t,'initial_anchor',f.get('anchor_local',[np.nan]*3),anchor)
                else:
                    world=obj+rot@anchor;base=previous if previous is not None else ref
                    lo=max(base[0]-.002,ref[0]-.030);hi=min(base[0]+.002,ref[0]+.030)
                    slice_interval=None
                    if slice_enabled:
                        axis=rot[0,:2]
                        matrix=np.r_[axis,-axis][:,None];bounds=np.r_[half-local[:2],half+local[:2]]
                        lower_fit=linprog([1.],A_ub=matrix,b_ub=bounds,bounds=[(None,None)],method='highs')
                        upper_fit=linprog([-1.],A_ub=matrix,b_ub=bounds,bounds=[(None,None)],method='highs')
                        if lower_fit.success and upper_fit.success:slice_interval=[float(lower_fit.x[0]),float(upper_fit.x[0])]
                        elif lower_fit.status not in (2,3) or upper_fit.status not in (2,3):errors.append([t,'slice_lp_failure'])
                    if slice_enabled and slice_interval is None:reason='no_world_x_core_interior_slice';anchor=last_world=None
                    elif lo>hi:reason='no_cartesian_slew_and_lead_interval';anchor=last_world=None
                    else:
                        feed=float(world[0]-last_world[0]);error=(min(slice_interval[1],max(slice_interval[0],0.)) if slice_enabled else float(world[0]-cop_world[0]));desired=base[0]+feed+.05*error
                        command=parent_command.copy();command[0]=min(hi,max(lo,desired))
                        if not f.get('override') or f.get('reason')!='loaded_rear_transverse_centering':errors.append([t,'missing_expected_override'])
                        values=dict(command_xyz=command,anchor_local=anchor,anchor_world=world,cop_world=cop_world,feed_x_m=feed,error_x_m=error,feedback_x_m=.05*error,desired_x_m=desired,feasible_x_interval_m=[lo,hi],command_delta_x_m=command[0]-base[0],command_reference_lead_x_m=command[0]-ref[0])
                        if slice_enabled:
                            if f.get('feedback_frame')!='current_rotated_core_world_x_slice':errors.append([t,'wrong_feedback_frame'])
                            values['core_x_displacement_interval_m']=slice_interval
                        for k,v in values.items():
                            if k not in f:errors.append([t,'missing_'+k])
                            else:near(t,k,f[k],v)
                        emitted=command.copy()
                        if progress_enabled:
                            expected_progress=independent_progress(base,command,rot,size,local,plan['direction'])
                            if expected_progress['override']:emitted=np.array(expected_progress['command_xyz'])
                        if xy_enabled:
                            expected_joint_xy=independent_joint_xy(base,command,ref,rot,size,local,plan['direction'])
                            if expected_joint_xy['override']:emitted=np.array(expected_joint_xy['command_xyz'])
                        near(t,'emitted_waypoint',actual,emitted);last_world=world
                        records.append(dict(step=t,command_xyz=emitted.tolist(),parent_rear_command_xyz=command.tolist(),normal_load_n=sum(weights),progress_override=bool(expected_progress and expected_progress.get('override')),joint_xy_override=bool(expected_joint_xy and expected_joint_xy.get('override'))))
            if reason:
                if f.get('override') or f.get('reason')!=reason:errors.append([t,'fallback_reason',reason])
                if parent_command is not None:near(t,'fallback_parent_command',actual,parent_command)
        got_progress=row.get('rear_coupled_progress')
        if expected_progress is None:
            if got_progress is not None:errors.append([t,'unexpected_progress_trace'])
        elif not isinstance(got_progress,dict):errors.append([t,'missing_progress_trace'])
        else:
            compare(t,expected_progress,got_progress,'progress')
        got_xy=row.get('rear_joint_xy_progress')
        if expected_joint_xy is None:
            if got_xy is not None:errors.append([t,'unexpected_joint_xy_trace'])
        elif not isinstance(got_xy,dict):errors.append([t,'missing_joint_xy_trace'])
        else:compare(t,expected_joint_xy,got_xy,'joint_xy')
        previous=actual;previous_mode=row['mode']
    return dict(passed=not errors,errors=errors,overrides_checked=len(records),records=records)


def main():
    w=Path(__file__).resolve().parent;ep=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    subprocess.run([sys.executable,str(w/'audit_interior_region_bounds.py'),str(ep)],check=True,stdout=subprocess.DEVNULL)
    fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan'];prov=json.loads((ep.parent/'provenance.json').read_text());enabled=bool(plan.get('rear_cop_centering',{}).get('enabled'))
    if enabled:
        assert bool(plan['rear_cop_centering'].get('core_slice_feedback',False))==bool(prov['args'].get('rear_core_slice_feedback',False))
        assert prov['args']['rear_cop_centering'] and not plan.get('front_route_selected') and not plan.get('initial_top_selected')
        region=json.loads((ep/'region_approach.json').read_text())['rows'];handover=next((r['step'] for r in region if r['solver'] and r['solver'].get('handover')),None)
        key='box' if 'push_box' in ep.name else 'mailer'
        with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
        with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].astype(float)
        config=ep.parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py';assert sha(config)==prov['source_sha256']['simfoundry/scene_bridge/isaac_cfg.py']
        node=next(n for n in ast.walk(ast.parse(config.read_text())) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='core_scale' for x in n.targets));assert ast.unparse(node.value.test)=="obj.semantic == 'mailer'"
        scale=np.array(ast.literal_eval(node.value.orelse if key=='box' else node.value.body));size=np.array(plan['top_recontact']['contact_size_xyz']);assert np.max(abs(size*scale-plan['rear_cop_centering']['actual_core_size_xyz']))<1e-7
        packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};report=reconstruct(fr['rows'],plan,xyz,quat,packets,key,handover)
    else:
        assert not any('rear_cop_centering' in r for r in fr['rows'])
        report=dict(passed=True,errors=[],overrides_checked=0,records=[])
    declared=prov['args'].get('rear_coupled_progress',False)
    assert type(declared) is bool
    selected=plan.get('rear_coupled_progress',{}).get('enabled',False)
    assert type(selected) is bool and selected==(declared and enabled)
    if not enabled:assert not any('rear_coupled_progress' in r for r in fr['rows'])
    declared_xy=prov['args'].get('rear_joint_xy_progress',False)
    selected_xy=plan.get('rear_joint_xy_progress',{}).get('enabled',False)
    assert type(declared_xy) is bool and type(selected_xy) is bool
    assert selected_xy==(declared_xy and enabled)
    if declared_xy:assert declared is True
    if not enabled:assert not any('rear_joint_xy_progress' in r for r in fr['rows'])
    if selected_xy:
        for suffix in ['/rear_joint_xy_progress.py','/rear_cop_route.py']:
            matches=[n for n in prov['source_sha256'] if n.endswith(suffix)]
            assert len(matches)==1
            assert sha(ep.parent/'source_snapshot'/matches[0])==prov['source_sha256'][matches[0]]
    names=['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json','INTERIOR_REGION_CONTINUITY_AUDIT.json','INTERIOR_REGION_BOUNDS_AUDIT.json']
    if (ep/'region_approach.json').exists():names.append('region_approach.json')
    report.update(enabled=enabled,source_sha256={n:sha(ep/n) for n in names},auditor_sha256=sha(Path(__file__)),training_ready=False,scope='Independent prior-packet COP and actual core, original world-X slice correction, original internal Y/Z and optional external reference-direction Y halfspace LP reconstruction. Actual emitted history maintained; original Z preserved; optional joint XY independently maximizes Y under original X slew/lead bounds with parent-Y fallback. Requires original raw-joint/region/transition audits; not a success or training admission decision.')
    (ep/'INTERIOR_REAR_XY_AUDIT.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k not in ['records','source_sha256']});sys.exit(0 if report['passed'] else 1)


if __name__=='__main__':main()
