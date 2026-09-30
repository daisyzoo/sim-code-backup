"""Diagnostic palm path for physical frontward repositioning; no parcel writes."""
def front_reposition_target(state, palm):
    x=state.parcel_x+.06
    y=state.parcel_y
    z=state.contact_palm_z
    staging=(x,y,state.staging_palm_z)
    contact=(x,y,z)
    if state.mode=='lift' and palm[2]>=state.staging_palm_z-.025:
        state.mode,state.mode_step='cross_x',0
    elif state.mode=='cross_x':
        if abs(palm[0]-x)<.035 and abs(palm[1]-y)<.025 and palm[2]>=state.staging_palm_z-.025:
            state.mode,state.mode_step='press_x',0
    elif state.mode=='press_x':
        ready=abs(palm[0]-x)<.035 and abs(palm[1]-y)<.025 and palm[2]<=z+.012
        state.contact_settle_count=state.contact_settle_count+1 if ready else 0
        if state.contact_settle_count>=3:
            state.front_reposition_start_x = float(palm[0]) if state.front_reposition_measured_start else x
            state.front_reposition_start_yz = (float(palm[1]),float(palm[2])) if state.front_reposition_hold_yz else None
            state.mode,state.mode_step='retreat_x',0
    elif state.mode=='retreat_x' and state.mode_step>=58:
        state.mode,state.mode_step='hold_x',0
    if state.mode=='lift':target=(state.start_palm[0],state.start_palm[1],state.staging_palm_z)
    elif state.mode=='cross_x':target=staging
    elif state.mode=='press_x':target=contact
    else:
        t=min(1.,max(0.,state.mode_step/57.)) if state.mode=='retreat_x' else 1.
        s=t*t*(3-2*t)
        assert state.front_reposition_start_x is not None
        if state.front_reposition_hold_yz:
            assert state.front_reposition_start_yz is not None
            y,z=state.front_reposition_start_yz
        target=(state.front_reposition_start_x-state.front_reposition_distance*s,y,z)
    state.last_target_xyz=tuple(float(v) for v in target)
    state.mode_step+=1
    return target
