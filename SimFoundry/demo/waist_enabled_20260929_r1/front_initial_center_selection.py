"""Current/past-only local-response feasibility before taking initial-front control.
Predicted observations are explicitly hypothetical: their captures are discarded.
No prediction may trigger actual handover. Original live lifecycle must still
observe three actual ready frames, all guards and at most 240 commands.
"""
import copy
import numpy as np
from front_initial_center_plan import plan as static_plan
from front_initial_center_lifecycle_v2 import FrontInitialCenterLifecycle


def select_planned(planning, scene, current, *, step, previous_q, previous_command, decay):
    q0, qp0, prev0, a = [np.asarray(v, float) for v in [current, previous_q, previous_command, decay]]
    if any(v.shape != (11,) or not np.isfinite(v).all() for v in [q0,qp0,prev0,a]):
        raise ValueError('Invalid causal initial transfer input')
    if type(step) is not int or step < 1 or np.any(a < 0.) or np.any(a > .95):
        raise ValueError('Invalid causal initial transfer step/decay')
    if planning['scene'] != scene.record() or planning['step'] != step or not np.array_equal(planning['start'],q0):
        raise ValueError('Static plan is not bound to current observation')
    if not planning['accepted']:
        return planning
    candidates = sorted([v for v in planning['attempts'] if v['endpoint_accepted']
                         and v['nominal_path']['accepted']], key=lambda v:v['objective'])
    trials = []
    initial = dict(step=step,current=q0.tolist(),previous_q=qp0.tolist(),previous_command=prev0.tolist(),decay=a.tolist())
    for candidate in candidates:
        p = {k:v for k,v in planning.items() if k != 'attempts'}
        p.update(endpoint=candidate['endpoint'],waypoints=candidate['nominal_path']['waypoints'],
                 selected_seed=candidate['seed'],nominal_path_nodes=len(candidate['nominal_path']['waypoints']))
        # This is a private, hypothetical lifecycle. Never pass its state or
        # captured references to the actual collector/controller.
        probe = FrontInitialCenterLifecycle(enabled=True)
        probe.active = probe.attempted = True
        probe.plan = p
        probe.scene = scene
        q,qp,previous = q0.copy(),qp0.copy(),prev0.copy()
        events=[]
        for tick in range(241):
            event=probe.update(step=step+tick,selected=True,parent_mode='top_cross',recontacts=0,guard_stop=False,
                observed_load_n=0.,filtered_load_n=0.,scene=scene,current=q,previous_q=qp,previous_command=previous,
                decay=a,observed_hand_pose=scene.guard.model.fk(scene.side,q)[0],
                observed_inactive_hand_pose=scene.guard.model.fk(scene.inactive,q)[0])
            events.append(dict(kind=event['kind'],ticks=probe.ticks,waypoint_index=probe.index,
                               measured_ready_count=probe.ready,reason=event.get('reason')))
            if event['kind']!='command':
                break
            command=np.asarray(event['command'])
            bias=q-previous-a*(qp-previous)
            predicted=(1-a)*command+a*q+bias
            if np.max(abs(predicted-np.asarray(event['proposal']['predicted_q'])))>1e-12:
                raise ValueError('Preflight response arithmetic mismatch')
            qp,q,previous=q,predicted,command
        accepted=event['kind']=='handover'
        trials.append(dict(seed=candidate['seed'],objective=candidate['objective'],nominal_nodes=p['nominal_path_nodes'],
                           predicted_transport_accepted=accepted,outcome=event['kind'],reason=event.get('reason'),
                           predicted_ticks=probe.ticks,events=events,
                           rejected_proposal=event.get('proposal') if not accepted else None))
        if accepted:
            metadata=dict(accepted=True,initial_context=initial,trials=trials,selected_seed=candidate['seed'],
                          scope=__doc__,predicted_capture_discarded=True,training_ready=False)
            return dict(planning,endpoint=p['endpoint'],waypoints=p['waypoints'],selected_seed=p['selected_seed'],
                        nominal_path_nodes=p['nominal_path_nodes'],transport_preflight=metadata)
    # Before a first command, no feasible new path means unchanged parent behavior.
    return dict(planning,accepted=False,reason='no_original_budget_causal_transport_candidate',
                transport_preflight=dict(accepted=False,initial_context=initial,trials=trials,scope=__doc__,
                                         predicted_capture_discarded=True,training_ready=False))


def plan(scene, current, *, step, previous_q, previous_command, decay):
    planning=static_plan(scene,current,step=step)
    return select_planned(planning,scene,current,step=step,previous_q=previous_q,
                          previous_command=previous_command,decay=decay)
