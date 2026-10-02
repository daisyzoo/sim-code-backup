"""Independent chronological terminal-confirmation and release-entry audit.
No candidate observer import. Caller must separately bind full episode coverage,
source flags, measured target positions and the original remaining control gates.
No task success or training admission follows from this component check.
"""
from collections import deque
import math

def verify_rows(rows,*,initial_y,direction,enabled=False,wait=False):
    assert type(enabled) is bool and type(wait) is bool
    assert direction in (-1,1) and math.isfinite(initial_y)
    if wait:
        assert not rows
        return dict(passed=True,wait=True,observations=0,release_entries=[])
    assert rows, 'missing push controller history'
    window=deque(maxlen=10);last=-1;previous_mode=None;observations=0;entries=[]
    for row in rows:
        step=row['step'];assert type(step) is int and step>last;last=step
        if 'terminal_position_confirmed' not in row:
            assert not row['mode'].startswith('top_'), ('missing top confirmation',step)
            previous_mode=row['mode'];continue
        xyz=tuple(row['observed_target']);assert len(xyz)==3 and all(math.isfinite(x) for x in xyz)
        window.append(xyz);observations+=1
        confirmed=bool(len(window)==10 and direction*(xyz[1]-initial_y)>=.15 and all(direction*p[1]>=.20 for p in window) and math.hypot(xyz[0]-window[0][0],xyz[1]-window[0][1])<=.01)
        margin=bool(direction*xyz[1]>=max(.205,direction*initial_y+.16))
        expected=bool(confirmed and (margin or not enabled))
        assert type(row['terminal_position_confirmed']) is bool and row['terminal_position_confirmed']==expected,('confirmation',step)
        if row['mode']=='top_release' and previous_mode!='top_release':
            reason=row['release_reason']
            if reason=='confirmed_original_target_position':assert expected
            elif reason=='original_margin':assert margin
            else:raise AssertionError(('unexpected release entry reason',step,reason))
            entries.append(dict(step=step,reason=reason,progress_m=direction*(xyz[1]-initial_y),signed_y_m=direction*xyz[1],original_margin_satisfied=margin))
        previous_mode=row['mode']
    return dict(passed=True,wait=False,observations=observations,release_entries=entries,original_quality_unchanged=True)
