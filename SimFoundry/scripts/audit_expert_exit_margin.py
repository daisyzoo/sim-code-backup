#!/usr/bin/env python3
"""Read-only paired endpoint comparison; numerical evidence never admits data."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
protocol=json.loads((a.root/'PROTOCOL.json').read_text());rows=[]
for endpoint in protocol['conditions']:
 for layout in protocol['layouts']:
  lid=layout['layout_id'];expected=json.loads(Path(layout['path']).read_text())
  assert hashlib.sha256(Path(layout['path']).read_bytes()).hexdigest()==layout['sha256']
  case=a.root/f'exit{round(endpoint*100)}_{lid}'
  for task,target,other,direction in [('push_box_to_bin','box','mailer',-1),('nudge_mailer_to_bin','mailer','box',1)]:
   folder=case/f'layout_{lid}_{task}';raw=folder/'raw.npz'
   with np.load(raw) as z:
    m=json.loads(str(z['collect_meta']));assert m['layout']==expected and m['exit_y']==endpoint
    assert m['assist_frames']==0 and m['collection_role']=='diagnostic'
    assert len(z['q'])==160 and np.max(np.abs(z['q'][0,12:]))<1e-4
    assert np.max(np.abs(z['action'][0,12:]))<1e-4 and np.all(z['action'][:,12]==0)
    assert np.isfinite(z['q']).all() and np.isfinite(z['action']).all()
   q=json.loads((folder/'quality.json').read_text());assert not q['training_ready']
   with np.load(folder/'trace.npz') as z:
    t=z[target];o=z[other];assert t.shape==o.shape==(160,3)
    zone=float(np.min(direction*t[-10:,1])-.20)
    progress=float(direction*(t[-1,1]-t[0,1]));non_target=float(np.max(np.linalg.norm(o[:,:2]-o[0,:2],axis=1)))
    assert abs(progress-q['metrics']['target_final_progress_m'])<1e-6
    assert abs(non_target-q['metrics'][other+'_max_xy_m'])<1e-6
   rows.append(dict(endpoint=endpoint,layout_id=lid,task=task,raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),passed=q['passed'],reasons=q['reasons'],stable_zone_margin_m=zone,progress_margin_m=progress-.15,non_target_max_xy_m=non_target,max_action_step_rad=q['metrics']['max_action_step_rad']))
summary={str(e):dict(passed=sum(r['passed'] for r in rows if r['endpoint']==e),total=4,min_stable_zone_margin_m=min(r['stable_zone_margin_m'] for r in rows if r['endpoint']==e),min_progress_margin_m=min(r['progress_margin_m'] for r in rows if r['endpoint']==e)) for e in protocol['conditions']}
result=dict(rows=rows,summary=summary,actual_visual_review_required=True,training_ready=False,goal_complete=False)
a.out.write_text(json.dumps(result,indent=2));print(json.dumps(summary,indent=2))
