"""Default-off interior landing preference. Original 12mm planner retained.
20mm is an expert preference, not a relaxed/modified task-admission gate.
A failed preferred endpoint/path explicitly invokes the original planner; its
own failure is preserved. Original measured path tracking and handover remain.
"""
from recontact_plan_original import plan as original_plan

def plan(scene,q,*,step,earlier_seed=None,prefer_interior=False,minimum_motion_pose=False,box_center_preference=False,box_trailing_preference=False):
    if type(box_trailing_preference) is not bool or (box_trailing_preference and not box_center_preference):raise ValueError('Trailing preference requires box center branch')
    if type(box_center_preference) is not bool:raise ValueError('Invalid box center preference')
    if box_center_preference:
        if not (minimum_motion_pose and prefer_interior and scene.side=='right'):raise ValueError('Box center preference requires right-side minimum-motion interior plan')
        from trailing_contact_plan import plan as centered_plan
        parent=plan(scene,q,step=step,earlier_seed=earlier_seed,prefer_interior=prefer_interior,minimum_motion_pose=minimum_motion_pose)
        return centered_plan(scene,q,step=step,parent_plan=parent,enabled=box_trailing_preference)
    if type(minimum_motion_pose) is not bool:raise ValueError('Minimum motion preference must be bool')
    if minimum_motion_pose:
        if not prefer_interior:raise ValueError('Minimum motion preference requires original interior planner')
        from minimum_motion_recontact import plan as preferred_plan
        parent=plan(scene,q,step=step,earlier_seed=earlier_seed,prefer_interior=prefer_interior)
        return preferred_plan(scene,q,step=step,parent_plan=parent)
    if type(prefer_interior) is not bool:raise ValueError('Interior preference must be bool')
    if not prefer_interior:return original_plan(scene,q,step=step,earlier_seed=earlier_seed)
    from recontact_plan_deeper import plan as deeper_plan
    deep=deeper_plan(scene,q,step=step,earlier_seed=earlier_seed)
    path_checks=[scene.check(y) for y in deep['waypoints']] if deep['accepted'] else []
    usable=bool(deep['accepted'] and all(x['accepted'] for x in path_checks))
    result=deep if usable else original_plan(scene,q,step=step,earlier_seed=earlier_seed)
    return dict(result,interior_preference=dict(enabled=True,preferred_inset_m=.020,original_inset_m=.012,selected_inset_m=(.020 if usable else .012) if result['accepted'] else None,selected='preferred' if usable else 'original_fallback',preferred_plan=deep,preferred_path_checks=path_checks,fallback_reason=None if usable else ('preferred_endpoint_rejected' if not deep['accepted'] else 'preferred_path_rejected'),not_physical_contact_proof=True))
