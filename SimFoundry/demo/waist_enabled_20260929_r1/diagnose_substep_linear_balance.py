"""Read-only signed linear impulse check on recorded parcel contacts.

This does not establish angular balance or causality. The end-of-solve COM
velocity is compared with contact impulses from that solve plus gravity.
Unrecorded passive forces and integration details can leave a residual.
"""
from pathlib import Path
import datetime
import hashlib
import json
import sys
import numpy as np


def inspect(ep):
    ep = Path(ep).resolve()
    history = json.loads((ep / 'SUBSTEP_LOAD_HISTORY.json').read_text())
    assert history['independent_audit']['passed']
    record = json.loads((ep / 'SUBSTEP_CONTACT_RECORDING.json').read_text())
    meta = record['metadata']
    cfg = json.loads((ep.parent / 'runtime_configuration.json').read_text())
    gravity = np.asarray(cfg['simulation']['gravity'], dtype=float)
    with np.load(ep / 'substep_contacts.npz') as z:
        a = {k: z[k] for k in z.files}
    n = history['action_intervals']
    stride = 24 + meta['expected_manager_steps']
    assert n * stride == len(a['action_step'])
    bodies = np.asarray(meta['shape_body'])[a['shape_ids']]
    sample_ids = np.repeat(np.arange(n * stride), np.diff(a['contact_offsets']))
    force = np.zeros((n * stride, 2, 3), dtype=float)
    for b, body_id in enumerate(meta['body_ids']):
        # Decoder convention: world contact force acts on geometry slot 1.
        sign = (bodies[:, 1] == body_id).astype(float) - (bodies[:, 0] == body_id)
        np.add.at(force[:, b], sample_ids, sign[:, None] * a['force_torque_world'][:, :3])
    chosen = []
    for step in range(n):
        base = step * stride
        stamps = a['substep_tick'][base:base + stride]
        chosen.append([base + int(np.flatnonzero(stamps == t)[0]) for t in range(25)])
    chosen = np.asarray(chosen)
    mass = np.asarray(meta['body_mass_kg'], dtype=float)
    v = a['body_qd'][chosen, :, :3].astype(float)
    contact_impulse = force[chosen[:, 1:]] * meta['solver_dt_s']
    predicted = contact_impulse + mass[None, None, :, None] * gravity * meta['solver_dt_s']
    measured = np.diff(v, axis=1) * mass[None, None, :, None]
    residual = measured - predicted
    def stats(x):
        x = np.linalg.norm(x, axis=-1)
        return dict(rms=float(np.sqrt(np.mean(x*x))), median=float(np.median(x)),
                    p95=float(np.quantile(x, .95)), maximum=float(x.max()))
    per_body = {}
    for b, label in enumerate(meta['body_labels']):
        per_body[label] = dict(
            measured_substep_impulse_Ns=stats(measured[:, :, b]),
            balance_residual_Ns=stats(residual[:, :, b]),
            first_action_mean_contact_force_N=force[chosen[0, 1:], b].mean(axis=0).tolist(),
            first_action_max_speed_mps=float(np.linalg.norm(v[0, :, b], axis=-1).max()),
            static_expected_support_N=(-mass[b]*gravity).tolist())
    key = 0 if 'push_box' in ep.name else 1
    peaks = [r for r in history['rows'] if max(r['vertical_load_n']) > 10]
    events = []
    for row in peaks:
        step = row['action_step']
        tick = int(np.argmax(row['vertical_load_n']))
        events.append(dict(action_step=step, solver_tick=tick+1,
                           hand_absolute_vertical_peak_N=max(row['vertical_load_n']),
                           target_contact_force_N=force[chosen[step, tick+1], key].tolist(),
                           measured_target_impulse_Ns=measured[step, tick, key].tolist(),
                           predicted_target_impulse_Ns=predicted[step, tick, key].tolist(),
                           residual_target_impulse_Ns=residual[step, tick, key].tolist()))
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    sources = [ep/'substep_contacts.npz', ep/'SUBSTEP_CONTACT_RECORDING.json',
               ep/'SUBSTEP_LOAD_HISTORY.json', ep.parent/'runtime_configuration.json', Path(__file__)]
    state = Path('/home/user/miniconda3/envs/env_isaaclab/lib/python3.12/site-packages/newton/_src/sim/state.py')
    return dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                episode=ep.name, scope=__doc__, body_results=per_body, peak_events=events,
                source_sha256={str(p): sha(p) for p in sources},
                current_state_definition=dict(path=str(state), sha256=sha(state),
                    attribution='Current installed source inspected now; not backfilled historical provenance.',
                    velocity_definition='body_qd first3 world linear COM velocity'),
                limitations=['Sign convention checked against observed quiet initial support; not an independent solver-force derivation.',
                             'No torque or angular impulse inference; force and pose evaluation times may differ.',
                             'Residual includes unrecorded passive forces, numerical integration and observation timing.',
                             'No counterfactual control trajectory or task success is predicted.'],
                training_ready=False)


if __name__ == '__main__':
    ep = Path(sys.argv[1])
    dest = ep/'SUBSTEP_LINEAR_BALANCE.json'
    assert not dest.exists()
    out = inspect(ep)
    dest.write_text(json.dumps(out, indent=2))
    print(json.dumps(dict(episode=out['episode'], body_results=out['body_results'],
                          peak_event_count=len(out['peak_events'])), indent=2))
