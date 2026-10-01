"""Explicit third-solve metadata audit; no solver or simulator is executed here.

The two original attempts remain recorded as failures. A third success cannot
rewrite their statuses. This verifies metadata only, not executed FK/KKT or
physical success; callers still need the original independent numerical audit.
"""
def verify_parent_seed_retry_metadata(trace, *, enabled, analytic_enabled, eligible, mode,
                                      original_verifier):
    assert type(enabled) is bool and type(analytic_enabled) is bool
    assert type(eligible) is bool
    assert not enabled or analytic_enabled
    extra = trace.get('parent_seed_retry') if trace else None
    if extra is None:
        return dict(analytic_retry=original_verifier(trace, analytic_enabled, eligible, mode),
                    parent_seed_retry=False)
    assert enabled and analytic_enabled and eligible and mode == 'top_push'
    assert isinstance(trace, dict) and type(trace['override']) is bool
    old = trace.get('analytic_retry')
    assert isinstance(old, dict)
    assert set(old) == {'attempted', 'initial_solver_status', 'initial_iterations',
                        'retry_solver_status', 'retry_iterations', 'initializer'}
    assert old['attempted'] is True and old['initializer'] == 'original_linear_feasible_point'
    for key in ['initial_solver_status', 'retry_solver_status']:
        assert type(old[key]) is int and old[key] == 8
    for key in ['initial_iterations', 'retry_iterations']:
        assert type(old[key]) is int and 0 < old[key] <= 300
    assert isinstance(extra, dict) and set(extra) == {
        'attempted', 'prior_solver_status', 'prior_iterations', 'initializer',
        'retry_solver_status', 'retry_iterations', 'maximum_extra_retries'}
    assert extra['attempted'] is True and extra['initializer'] == 'bounded_parent_delta'
    assert type(extra['maximum_extra_retries']) is int and extra['maximum_extra_retries'] == 1
    assert type(extra['prior_solver_status']) is int and extra['prior_solver_status'] == old['retry_solver_status']
    assert type(extra['prior_iterations']) is int and extra['prior_iterations'] == old['retry_iterations']
    assert type(extra['retry_iterations']) is int and 0 < extra['retry_iterations'] <= 300
    status = extra['retry_solver_status']
    assert type(status) is int and 0 <= status <= 9
    if trace['override']:
        assert trace['reason'] == 'nonlinear_joint_direction' and status == 0
        assert type(trace['iterations']) is int and trace['iterations'] == extra['retry_iterations']
    elif trace['reason'] == 'nonlinear_solver_failed':
        assert type(trace['solver_status']) is int and trace['solver_status'] == status and status != 0
    else:
        assert trace['reason'] in ['final_float32_constraint_violation', 'nonfinite_output'] and status == 0
    return dict(analytic_retry=True, parent_seed_retry=True)
