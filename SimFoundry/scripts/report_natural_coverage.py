#!/usr/bin/env python3
"""Audit completed natural-layout pairs and report every registered group."""
import argparse,collections,hashlib,json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
protocol=json.loads((a.root/'PROTOCOL.json').read_text());episodes=[];groups={}
for layout in protocol['layouts']:
 lid=layout['layout_id'];group=layout['geometry_group'];g=groups.setdefault(group,dict(group=group,stratum=layout['stratum'],layout_ids=[],episodes=[]));g['layout_ids'].append(lid)
 src=Path(layout['path']);assert hashlib.sha256(src.read_bytes()).hexdigest()==layout['sha256'];expected=json.loads(src.read_text())
 case=a.root/f'case_{lid}'
 if not (case/'INTEGRITY.json').exists():continue
 integrity=json.loads((case/'INTEGRITY.json').read_text());assert len(integrity['rows'])==2
 for task,target,direction in [('push_box_to_bin','box',-1),('nudge_mailer_to_bin','mailer',1)]:
  other='mailer' if target=='box' else 'box';folder=case/f'layout_{lid}_{task}';raw=folder/'raw.npz';sha=hashlib.sha256(raw.read_bytes()).hexdigest();assert sha in {x['raw_sha256'] for x in integrity['rows']}
  with np.load(raw) as z:
   meta=json.loads(str(z['collect_meta']));assert meta['layout']==expected and meta['assist_frames']==0 and meta['exit_y']==.30 and meta['staging_palm_z']==.92
   assert len(z['q'])==160 and np.max(np.abs(z['q'][0,12:]))<1e-4 and np.max(np.abs(z['action'][0,12:]))<1e-4 and np.all(z['action'][:,12]==0)
  q=json.loads((folder/'quality.json').read_text());assert not q['training_ready']
  with np.load(folder/'trace.npz') as z:
   t=z[target];o=z[other];zone=float(np.min(direction*t[-10:,1])-.20);progress=float(direction*(t[-1,1]-t[0,1]));non_target=float(np.max(np.linalg.norm(o[:,:2]-o[0,:2],axis=1)))
   assert abs(progress-q['metrics']['target_final_progress_m'])<1e-6 and abs(non_target-q['metrics'][other+'_max_xy_m'])<1e-6
  modes=dict(collections.Counter(x['mode'] for x in json.loads((folder/'expert_control.json').read_text())))
  row=dict(group=group,stratum=layout['stratum'],layout_id=lid,assignment=layout['assignment'],task=task,passed=q['passed'],reasons=q['reasons'],raw_sha256=sha,stable_zone_margin_m=zone,progress_margin_m=progress-.15,non_target_max_xy_m=non_target,phase_frames=modes)
  episodes.append(row);g['episodes'].append(row)
for g in groups.values():
 assert len(g['layout_ids'])==2
 g['complete']=len(g['episodes'])==4;g['passed_tasks']=sum(e['passed'] for e in g['episodes']);g['numeric_group_pass']=g['complete'] and g['passed_tasks']==4
 g['status']='pending' if not g['complete'] else 'numeric_pass_visual_pending' if g['numeric_group_pass'] else 'quality_failed'
summary=dict(completed_episodes=len(episodes),passed_episodes=sum(e['passed'] for e in episodes),registered_groups=len(groups),complete_groups=sum(g['complete'] for g in groups.values()),numeric_pass_groups=sum(g['numeric_group_pass'] for g in groups.values()))
a.out.write_text(json.dumps(dict(summary=summary,groups=list(groups.values()),training_ready=False,goal_complete=False,scope='All registered strata retained; incomplete groups never count as passing. Numeric audit is not visual review or training admission.'),indent=2));print(json.dumps(summary));print([(g['stratum'],g['status'],g['passed_tasks']) for g in groups.values()])
