"""Exact short-first(.28m far endpoint) two-pass pilot contract; no implicit approval."""
from copy import deepcopy
from simfoundry.data.twopass_protocol import EXPERT as ORIGINAL_EXPERT, _validate_twopass_contract

EXPERT = deepcopy(ORIGINAL_EXPERT)
EXPERT['kind'] = 'cartesian_twopass_short_first_v1'
EXPERT['first']['far_exit_y'] = .28


def validate_twopass_contract(path, *, layout_id, steps):
    return _validate_twopass_contract(path, layout_id=layout_id, steps=steps, expected_expert=EXPERT)
