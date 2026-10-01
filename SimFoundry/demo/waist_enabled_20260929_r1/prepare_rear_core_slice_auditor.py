from pathlib import Path
import ast
w=Path(__file__).resolve().parent;source=w/'audit_rear_cop_measured_bounds_live.py';s=source.read_text()
s=s.replace('from scipy.spatial.transform import Rotation','from scipy.spatial.transform import Rotation\nfrom scipy.optimize import linprog')
s=s.replace("    assert cfg['preserve_first_loaded_push']", "    slice_enabled=cfg.get('core_slice_feedback',False)\n    assert type(slice_enabled) is bool\n    assert cfg['preserve_first_loaded_push']")
s=s.replace("                    if lo>hi:reason='no_cartesian_slew_and_lead_interval';anchor=last_world=None", """                    slice_interval=None
                    if slice_enabled:
                        axis=rot[0,:2]
                        matrix=np.r_[axis,-axis][:,None];bounds=np.r_[half-local[:2],half+local[:2]]
                        lower_fit=linprog([1.],A_ub=matrix,b_ub=bounds,bounds=[(None,None)],method='highs')
                        upper_fit=linprog([-1.],A_ub=matrix,b_ub=bounds,bounds=[(None,None)],method='highs')
                        if lower_fit.success and upper_fit.success:slice_interval=[float(lower_fit.x[0]),float(upper_fit.x[0])]
                        elif lower_fit.status not in (2,3) or upper_fit.status not in (2,3):errors.append([t,'slice_lp_failure'])
                    if slice_enabled and slice_interval is None:reason='no_world_x_core_interior_slice';anchor=last_world=None
                    elif lo>hi:reason='no_cartesian_slew_and_lead_interval';anchor=last_world=None""")
s=s.replace("error=float(world[0]-cop_world[0]);desired", "error=(min(slice_interval[1],max(slice_interval[0],0.)) if slice_enabled else float(world[0]-cop_world[0]));desired")
s=s.replace("                        for k,v in values.items():", """                        if slice_enabled:
                            if f.get('feedback_frame')!='current_rotated_core_world_x_slice':errors.append([t,'wrong_feedback_frame'])
                            values['core_x_displacement_interval_m']=slice_interval
                        for k,v in values.items():""")
s=s.replace("    (ep/'REAR_COP_LIVE_AUDIT.json')", "    (ep/'REAR_COP_CORE_SLICE_LIVE_AUDIT.json')")
s=s.replace('Independent prior-packet COP, actual collision core, X correction', 'Independent prior-packet COP, actual collision core, optional LP world-X slice correction')
# Any new live run must declare its collector flag consistently with the plan.
s=s.replace("        assert prov['args']['rear_cop_centering']", "        assert bool(plan['rear_cop_centering'].get('core_slice_feedback',False))==bool(prov['args'].get('rear_core_slice_feedback',False))\n        assert prov['args']['rear_cop_centering']")
ast.parse(s);p=w/'audit_rear_cop_core_slice_live.py';assert not p.exists();p.write_text(s);print(p)
