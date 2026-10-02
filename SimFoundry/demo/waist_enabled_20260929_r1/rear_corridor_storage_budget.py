"""Disk budget, separate from every original task and control quality threshold.
Retain original30GiB launch minimum. Reserve1GiB for each two-push case and.25GiB
for each wait case, above measured closed comparison case sizes; preserve25GiB
at every continuation. No deletion, compression or data gate changes.
"""
from pathlib import Path
import shutil
GIB=1024**3

def require_storage(root,commands,completed_cases=0):
    assert type(completed_cases) is int and 0<=completed_cases<=len(commands)
    assert len(commands)==6 and sum(c['wait'] for c in commands)==2
    assert all(len(c['tasks'])==(1 if c['wait'] else 2) for c in commands)
    remaining=sum(.25 if c['wait'] else 1. for c in commands[completed_cases:])
    free=shutil.disk_usage(Path(root)).free/GIB
    assert free>=25.+remaining,('insufficient remaining collection reserve',free,remaining)
    if completed_cases==0:assert free>30.,('original launch minimum',free)
    return dict(free_gib=free,remaining_case_budget_gib=remaining,protected_reserve_gib=25.,completed_cases=completed_cases,launch_minimum_gib=30.,quality_gates_changed=False)
