#!/usr/bin/env python3
import argparse,json,hashlib
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();rows=[]
protocol=json.loads((a.root/'PROTOCOL.json').read_text())
for case in protocol['cases']:
    root=a.root/f"case_{case['layout_id']}"
    if not root.exists():continue
    provenance=json.loads((root/'provenance.json').read_text())['args']
    assert provenance['horizon']==10 and provenance['policy_max_action_step']==0 and provenance['policy_port']>0
    manifest=json.loads(Path(case['manifest']).read_text())
    for task,entry in manifest['tasks'].items():
        ep=root/f"layout_{case['layout_id']}_{task}";path=ep/'raw.npz'
        if not (ep/'quality.json').exists():continue
        source=Path(entry['path']);assert hashlib.sha256(source.read_bytes()).hexdigest()==entry['sha256']
        with np.load(source) as original,np.load(path) as actual,np.load(ep/'policy_raw_actions.npz') as policy,np.load(ep/'trace.npz') as trace:
            assert actual['action'].shape==original['action'].shape==(160,23)
            assert np.array_equal(actual['action'],original['action']) and np.array_equal(policy['action'],original['action'])
            assert np.max(np.abs(actual['q'][0,12:]))<1e-4 and np.max(np.abs(actual['action'][0,12:]))<1e-4 and np.all(actual['action'][:,12]==0)
            meta=json.loads(str(actual['collect_meta']));assert meta['assist_frames']==0 and not meta['push_assist'] and meta['policy_action_step_cap']==0
            assert meta['layout']==json.loads(Path(case['layout']).read_text())
            errors={k:float(np.abs(trace[k]-original[k]).max()) for k in ['box','mailer','palm_left','palm_right']}
            for k in ['box','mailer']:assert np.abs(trace[k][0]-original[k][0]).max()<1e-4
            qerror=float(np.abs(actual['q']-original['q']).max())
        quality=json.loads((ep/'quality.json').read_text());assert quality['metrics']['policy_modified_frames']==0 and not quality['training_ready']
        inference=json.loads((ep/'policy_inferences.json').read_text());assert [x['step'] for x in inference]==list(range(0,160,10))
        rows.append(dict(layout_id=case['layout_id'],task=task,source_sha256=entry['sha256'],raw_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),actions_exact=True,max_q_error=qerror,max_trace_errors=errors,passed=quality['passed'],reasons=quality['reasons']))
a.out.write_text(json.dumps(dict(rows=rows,training_ready=False,goal_complete=False,scope='Frozen absolute action transport/replay audit, not learned VLA inference; physical state differences retained. Actual image review required.'),indent=2))
print('verified',len(rows),'episodes; exact actions',all(r['actions_exact'] for r in rows),flush=True)
