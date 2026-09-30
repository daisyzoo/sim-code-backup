"""Explicit force-pilot contracts and trace checks; normal task gates stay intact."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np


def validate_contract(path, *, layouts, waits, push_force, wait_force, wait_side, wait_start):
    path=Path(path);payload=path.read_bytes();contract=json.loads(payload)
    if contract.get('approved_for_pilot') is not True:
        raise ValueError('Recovery contract has not passed feasibility review')
    requested={'layouts':list(layouts),'wait_layouts':list(waits),'push_force_n':push_force,
               'wait_force_n':wait_force,'wait_force_side':wait_side,'wait_force_start':wait_start}
    if requested not in contract['collections']:
        raise ValueError('Collection settings not registered in recovery contract')
    return hashlib.sha256(payload).hexdigest()


def audit_force_trace(meta, task, steps, records):
    """Reject omitted/nonfinite/off-window/unexpected hand forces before export."""
    push=float(meta.get('push_force_n',0));wait=float(meta.get('wait_force_n',0))
    amplitude=push or wait
    if not amplitude or not 0 < amplitude <=80 or (push and wait):
        raise ValueError('Invalid recovery force amplitude')
    if len(records)!=steps:
        raise ValueError('Incomplete external force trace')
    if push:
        if task not in ('push_box_to_bin','nudge_mailer_to_bin'):raise ValueError('Push force on wait task')
        sides=['right'] if task=='push_box_to_bin' else ['left'];start=5
    else:
        if task!='wait_no_package':raise ValueError('Wait force on push task')
        side=meta['wait_force_side'];sides=['left','right'] if side=='both' else [side]
        if side not in ('left','right','both'):raise ValueError('Invalid hand')
        start=int(meta.get('wait_force_start',20))
    for t,row in enumerate(records):
        expected=amplitude*np.sin(np.pi*(t-start+1)/7) if start<=t<=start+5 else 0.
        force=np.asarray(row['force_per_body_world_N'])
        if row['step']!=t or row['bodies']!=[s+'_hand' for s in sides] or force.shape!=(3,) or not np.isfinite(force).all():
            raise ValueError('Invalid force step/body/vector')
        if not np.allclose(force,[expected,0,0],rtol=0,atol=1e-6):
            raise ValueError('Force does not match registered pulse')
    return True
