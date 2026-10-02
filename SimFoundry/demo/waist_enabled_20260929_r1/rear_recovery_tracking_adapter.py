"""Isolated command selection and post-guard bookkeeping for rear recovery.
Parent controller evidence is retained verbatim. No simulator/object writes,
synthetic contact or inferred measured arrival. Disabled returns the input object.
"""
import copy
import numpy as np
from rear_recovery_tracking_solver_v2 import solve
from rear_corridor_latched_phase_v2 import propose_phase
from rear_corridor_unload_candidate import solve_lift
from rear_corridor_recovery_state import commit_loaded, begin_lift


def propose(*, enabled=False, step, selected=False, parent_command, phase_state=None, side=None, tracking_feedback=False, previous_recovery_record=None, **inputs):
    if type(tracking_feedback) is not bool:
        raise ValueError('Explicit tracking option required')
    if type(enabled) is not bool or type(selected) is not bool:
        raise ValueError('Explicit boolean selection required')
    if type(step) is not int or step < 0:
        raise ValueError('Invalid action step')
    if not enabled or not selected or step == 0:
        return parent_command, dict(kind='unchanged', reason='disabled_or_unselected_or_first_frame', step=step)
    row, coordinate = inputs['row'], inputs['coordinate']
    if row['step'] != step or coordinate['step'] != step:
        raise ValueError('Recovery records do not describe current action')
    phase = propose_phase(state=phase_state, step=step, side=side, row=row, coordinate=coordinate,
                          **{k:inputs[k] for k in ['target_xyz','obstacle_xyz','target_rotation',
                                                   'obstacle_rotation','target_size','obstacle_size']})
    command, recovery = solve(enabled=True, parent_command=parent_command,
                              recovery_active=phase['after']['active'], tracking_feedback=tracking_feedback,
                              previous_recovery_record=previous_recovery_record, **inputs)
    record = dict(step=step, kind='unchanged', recovery=recovery, phase=phase,
                  parent_command=np.asarray(parent_command, float).tolist())
    if command is None:
        if recovery['reason'] != 'no_verified_loaded_recovery':
            return None, dict(record, kind='stop', reason=recovery['reason'])
        command, unload = solve_lift(parent_command=parent_command, recovery_result=recovery,
                                    **{k:inputs[k] for k in ['guard','row','coordinate','current','previous']})
        record['unload'] = unload
        if command is None:
            return None, dict(record, kind='stop', reason=unload['reason'])
        record['kind'] = 'unload'
    elif recovery['applied']:
        record['kind'] = 'loaded_recovery'
    if record['kind'] != 'unchanged':
        record.update(parent_row=copy.deepcopy(row), parent_coordinate=copy.deepcopy(coordinate),
                      proposed_command=np.asarray(command, float).tolist(),
                      geometry={k:np.asarray(inputs[k], float).tolist() for k in [
                          'target_xyz','obstacle_xyz','target_rotation','obstacle_rotation',
                          'target_size','obstacle_size','core_size']})
    return command, record


def commit(*, state, guard, row, coordinate, current, previous, command, record):
    """Call only after the collector's original final command guard accepted."""
    kind = record['kind']
    if kind not in ('loaded_recovery','unload'):
        raise ValueError('No accepted recovery command to commit')
    if 'commit' in record:
        raise ValueError('Duplicate command commit')
    if row != record['parent_row'] or coordinate != record['parent_coordinate']:
        raise ValueError('Parent evidence changed between proposal and emission')
    if not np.array_equal(np.asarray(command), np.asarray(record['proposed_command'])):
        raise ValueError('Actual command differs from proposal')
    fn = commit_loaded if kind == 'loaded_recovery' else begin_lift
    result = record['recovery'] if kind == 'loaded_recovery' else record['unload']
    event = fn(state=state, guard=guard, row=row, coordinate=coordinate, current=current,
               previous=previous, command=command, result=result)
    updated = copy.deepcopy(row)
    reference = event['new']['command'] if kind == 'loaded_recovery' else event['verified_first_lift_reference']
    updated.update(target_xyz=list(reference), mode=state.mode, recontacts=state.recontacts,
                   push_x_anchor_m=state.push_x_anchor, last_recontact_reason=state.last_recontact_reason,
                   rear_corridor_override=dict(kind=kind, step=row['step'], parent_evidence='rear_corridor_recovery.json'))
    if kind == 'unload':
        updated['contact_load'].update(applied_z_bias_m=0., stored_z_bias_m=state.load.bias_m,
                                      rear_recovery_reset_after_original_update=True)
    record['commit'] = event
    record['emitted_command'] = np.asarray(command, float).tolist()
    return updated


def complete_handover(state, event):
    """Clear pending only after actual original handover with fresh +X witness."""
    if not getattr(state, 'rear_corridor_recontact_pending', False):
        return None
    witness = event.get('rear_transport_handover_witness', {})
    context = event.get('context', {})
    if (event.get('kind') != 'handover' or not witness.get('accepted') or
        event.get('measured_ready_count', 0) < 3 or context.get('observed_load_n') != 0. or
        not 0. <= context.get('filtered_load_n', float('inf')) <= .05 or
        context.get('recontacts') != state.recontacts):
        raise ValueError('Recovery requires current measured unloaded directional handover')
    state.rear_corridor_recontact_pending = False
    return dict(step=context['step'], kind='measured_directional_handover',
                recontacts=state.recontacts, nominal_direction_scope='Unloaded geometric witness, not traction proof')


def commit_phase(*, phase_state, record, guard, current, previous, command):
    """Commit once after the ORIGINAL final command guard, including unchanged steps.
    No pending-unload reset: the original measured recontact handover retains its
    own independent state. Phase exits require measured geometry, never nominal FK.
    """
    event = record['phase']
    if event['before'] != phase_state or 'phase_committed' in record:
        raise ValueError('Stale or duplicate phase commit')
    if record['kind'] == 'stop' or record['step'] != event['step']:
        raise ValueError('Cannot commit stopped or mismatched command')
    expected = record['parent_command'] if record['kind'] == 'unchanged' else record['emitted_command']
    if not np.array_equal(np.asarray(command, float), np.asarray(expected, float)):
        raise ValueError('Phase commit requires actual emitted command')
    if not guard.command(command, current, previous)['accepted']:
        raise ValueError('Original final guard rejected phase command')
    record['phase_committed'] = copy.deepcopy(event['after'])
    return copy.deepcopy(event['after'])
