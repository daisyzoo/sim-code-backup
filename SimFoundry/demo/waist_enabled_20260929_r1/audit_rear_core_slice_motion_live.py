"""Independent rear COP and parent Y/Z waypoint reconstruction from recorded inputs."""
from pathlib import Path
import ast,json,hashlib,sys,subprocess
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import linprog


def reconstruct(rows, plan, xyz, quat, packets, key, handover):
    side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer'
    cfg=plan['rear_cop_centering'];size=np.asarray(cfg['actual_core_size_xyz']);half=size[:2]/2-.01
    assert cfg['core_inset_m']==.01 and cfg['feedback_gain']==.05 and cfg['max_x_step_m']==.002 and cfg['max_reference_x_lead_m']==.030
    slice_enabled=cfg.get('core_slice_feedback',False)
    assert type(slice_enabled) is bool
    motion_enabled=cfg.get('core_slice_motion_feedforward',False)
    assert type(motion_enabled) is bool and (not motion_enabled or slice_enabled)
    assert cfg['preserve_first_loaded_push'] and cfg['parent_yz_unchanged'] and cfg['original_guard_priority']
    assert np.all(half>0) and np.isfinite(size).all()
    rotations=Rotation.from_quat(quat).as_matrix();anchor=last_world=last_slice=None;previous=None;previous_mode=None;previous_step=None;errors=[];records=[]
    def near(t,name,a,b):
        err=float(np.max(abs(np.asarray(a)-np.asarray(b))))
        if not np.isfinite(err) or err>2e-6:errors.append([t,name,err])
    def independent_slice(local,rot):
        axis=rot[0,:2];matrix=np.r_[axis,-axis][:,None];bounds=np.r_[half-local[:2],half+local[:2]]
        lower=linprog([1.],A_ub=matrix,b_ub=bounds,bounds=[(None,None)],method='highs')
        upper=linprog([-1.],A_ub=matrix,b_ub=bounds,bounds=[(None,None)],method='highs')
        if lower.status==2 or upper.status==2:return None
        assert lower.success and upper.success
        return np.array([lower.x[0],upper.x[0]])
    for row in rows:
        t=row['step'];f=row.get('rear_cop_centering');actual=np.asarray(row['target_xyz'],float);ref=np.asarray(row['observed_support_xyz'],float)
        if previous_step is not None and t!=previous_step+1:errors.append([t,'noncontiguous_rows'])
        previous_step=t
        if f is None:
            errors.append([t,'missing_feedback']);previous=actual;previous_mode=row['mode'];continue
        parent_command=None
        if row['mode']=='top_push' and handover is not None and t>handover:
            if previous_mode not in ('top_push','top_press'):errors.append([t,'unexpected_push_entry'])
            base=previous.copy() if previous is not None else ref.copy()
            if previous_mode=='top_press':base[2]=ref[2]
            direction=plan['direction'];goal_x=row['push_x_anchor_m'];surface_z=row['parcel_top_xyz'][2];bias=row['contact_load']['applied_z_bias_m']
            parent_command=np.array([base[0]+np.clip(goal_x-base[0],-.002,.002),base[1]+np.clip(direction*min(.34,direction*base[1]+.003)-base[1],-.003,.003),base[2]+np.clip(surface_z+.002+bias-base[2],-.001,.001)])
            near(t,'unchanged_parent_yz',actual[1:],parent_command[1:])
        reason=None
        if handover is None or t<=handover:reason='region_not_handed_over'
        elif row['mode']!='top_push':reason='original_non_push_mode'
        if reason:
            if f.get('override') or f.get('reason')!=reason:errors.append([t,'guard_or_handover_bypass'])
            anchor=last_world=last_slice=None
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
                reason='no_valid_loaded_contact';anchor=last_world=last_slice=None
            else:
                cop_world=np.average(points,axis=0,weights=weights);local=rot.T@(cop_world-obj)
                if anchor is None:
                    anchor=np.r_[np.clip(local[:2],-half,half),local[2]];last_world=obj+rot@anchor;reason='preserve_first_loaded_push'
                    near(t,'initial_anchor',f.get('anchor_local',[np.nan]*3),anchor)
                    if motion_enabled:
                        first_interval=independent_slice(local,rot)
                        last_slice=None if first_interval is None else float(np.clip(last_world[0],*(first_interval+cop_world[0])))
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
                    if slice_enabled and slice_interval is None:reason='no_world_x_core_interior_slice';anchor=last_world=last_slice=None
                    elif lo>hi:reason='no_cartesian_slew_and_lead_interval';anchor=last_world=last_slice=None
                    else:
                        anchor_feed=float(world[0]-last_world[0]);feed=anchor_feed;prior_slice=last_slice
                        if motion_enabled:
                            chosen=float(np.clip(world[0],*(np.array(slice_interval)+cop_world[0])))
                            feed=0. if prior_slice is None else chosen-prior_slice
                        error=(min(slice_interval[1],max(slice_interval[0],0.)) if slice_enabled else float(world[0]-cop_world[0]));desired=base[0]+feed+.05*error
                        command=parent_command.copy();command[0]=min(hi,max(lo,desired))
                        if not f.get('override') or f.get('reason')!='loaded_rear_transverse_centering':errors.append([t,'missing_expected_override'])
                        values=dict(command_xyz=command,anchor_local=anchor,anchor_world=world,cop_world=cop_world,feed_x_m=feed,error_x_m=error,feedback_x_m=.05*error,desired_x_m=desired,feasible_x_interval_m=[lo,hi],command_delta_x_m=command[0]-base[0],command_reference_lead_x_m=command[0]-ref[0])
                        if slice_enabled:
                            if f.get('feedback_frame')!='current_rotated_core_world_x_slice':errors.append([t,'wrong_feedback_frame'])
                            values['core_x_displacement_interval_m']=slice_interval
                        if motion_enabled:
                            if f.get('feedforward_frame')!='moving_core_world_x_slice':errors.append([t,'wrong_feedforward_frame'])
                            values.update(core_slice_target_world_x_m=chosen,object_anchor_feed_x_m=anchor_feed)
                            if prior_slice is None:
                                if 'previous_core_slice_target_world_x_m' not in f or f['previous_core_slice_target_world_x_m'] is not None:errors.append([t,'wrong_previous_slice_reset'])
                            else:values['previous_core_slice_target_world_x_m']=prior_slice
                            last_slice=chosen
                        for k,v in values.items():
                            if k not in f:errors.append([t,'missing_'+k])
                            else:near(t,k,f[k],v)
                        near(t,'emitted_waypoint',actual,command);last_world=world
                        records.append(dict(step=t,command_xyz=command.tolist(),normal_load_n=sum(weights)))
            if reason:
                if f.get('override') or f.get('reason')!=reason:errors.append([t,'fallback_reason',reason])
                if parent_command is not None:near(t,'fallback_parent_command',actual,parent_command)
        previous=actual;previous_mode=row['mode']
    return dict(passed=not errors,errors=errors,overrides_checked=len(records),records=records)


def main():
    w=Path(__file__).resolve().parent;ep=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    subprocess.run([sys.executable,str(w/'audit_region_measured_bounds_live.py'),str(ep)],check=True,stdout=subprocess.DEVNULL)
    fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan'];prov=json.loads((ep.parent/'provenance.json').read_text());enabled=bool(plan.get('rear_cop_centering',{}).get('enabled'))
    if enabled:
        assert bool(plan['rear_cop_centering'].get('core_slice_feedback',False))==bool(prov['args'].get('rear_core_slice_feedback',False))
        assert bool(plan['rear_cop_centering'].get('core_slice_motion_feedforward',False))==bool(prov['args'].get('rear_core_slice_motion_feedforward',False))
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
    names=['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json','REGION_CONTINUITY_LIVE_AUDIT.json','MEASURED_BOUNDS_LIVE_AUDIT.json']
    if (ep/'region_approach.json').exists():names.append('region_approach.json')
    report.update(enabled=enabled,source_sha256={n:sha(ep/n) for n in names},auditor_sha256=sha(Path(__file__)),training_ready=False,scope='Independent prior-packet COP, actual collision core, optional LP world-X slice feedback and independently tracked moving-slice feedforward and unchanged parent Y/Z reconstruction. Requires original raw-joint/region/transition audits; not a success or training admission decision.')
    (ep/'REAR_CORE_SLICE_MOTION_LIVE_AUDIT.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k not in ['records','source_sha256']});sys.exit(0 if report['passed'] else 1)


if __name__=='__main__':main()
