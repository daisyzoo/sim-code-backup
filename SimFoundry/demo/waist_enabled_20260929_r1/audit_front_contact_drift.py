"""Read-only phase/contact drift diagnosis from recorded poses and solved forces."""
import collections
import hashlib
import json
import sys
from pathlib import Path
import numpy as np

p = Path(sys.argv[1])
rows = json.loads((p/'frontal_bypass.json').read_text())['rows']
packets = json.loads((p/'solved_contact_forces.json').read_text())['rows']
tr = np.load(p/'trace.npz')
key = 'box' if 'push_box' in p.name else 'mailer'
actor, side, direction = ('parcel_box', 'right', -1) if key == 'box' else ('mailer', 'left', 1)
phases = collections.defaultdict(list)
events = []
previous_count = 0
for i, r in enumerate(rows):
    t = r['step']
    phase = r['mode'] + ('/'+r['route_stage'] if r['mode']=='top_push' else '')
    phases[phase].append(t)
    if r['recontacts'] > previous_count:
        prev = rows[max(0, i-3):i]
        events.append(dict(step=t, reason=r['last_recontact_reason'],
            parcel_xyz=r['observed_target'],
            support_minus_parcel_xy_m=[r['observed_support_xyz'][j]-r['observed_target'][j] for j in (0,1)],
            preceding_modes=[x['mode'] for x in prev],
            preceding_load_n=[x['contact_load']['observed_vertical_load_n'] for x in prev]))
        previous_count=r['recontacts']
stats = {}
for name, steps in phases.items():
    valid=[t for t in steps if t+1<len(tr[key])]
    stats[name]=dict(frames=len(steps),signed_progress_m=float(sum(direction*(tr[key][t+1,1]-tr[key][t,1]) for t in valid)))
friction=collections.defaultdict(set)
for packet in packets:
    for c in packet['parcel_contacts']:
        if not any('/'+actor+'/' in s for s in c['shapes']): continue
        if any(side+'_wrist' in s for s in c['shapes']): kind='hand_target'
        elif any('/table/' in s for s in c['shapes']): kind='table_target'
        else: continue
        friction[kind].add(tuple(c['friction']))
push=[r for r in rows if r['mode']=='top_push']
out=dict(scope='Recorded reference-relative drift and phase timing; virtual support is not a physical contact point. Force packets are sampled after actions, controller rows before actions; no causal/dynamics certificate.',
    raw_sha256=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest(),
    frontal_sha256=hashlib.sha256((p/'frontal_bypass.json').read_bytes()).hexdigest(),
    phase_stats=stats,recontact_events=events,
    max_abs_push_reference_minus_parcel_xy_m=[max(abs(r['observed_support_xyz'][j]-r['observed_target'][j]) for r in push) for j in (0,1)],
    observed_contact_friction={k:sorted(v) for k,v in friction.items()},
    own_progress_at_959_m=float(direction*(tr[key][959,1]-tr[key][0,1])) if len(tr[key])>959 else None,
    own_final_progress_m=float(direction*(tr[key][-1,1]-tr[key][0,1])),training_ready=False)
(p/'FRONT_CONTACT_DRIFT_DIAGNOSIS.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
