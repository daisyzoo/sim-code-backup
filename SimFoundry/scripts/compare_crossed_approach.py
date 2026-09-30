#!/usr/bin/env python3
"""Compare the frozen crossed-approach intervention to all registered controls."""
import argparse,collections,hashlib,json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
protocol=json.loads((a.root/'PROTOCOL.json').read_text());baseline=Path(protocol['baseline']);rows=[]
for layout in protocol['layouts']:
 lid=layout['layout_id'];case=a.root/f'case_{lid}'
 if not (case/'INTEGRITY.json').exists():continue
 for task,obj,direction in [('push_box_to_bin','box',-1),('nudge_mailer_to_bin','mailer',1)]:
  relative=Path(f'case_{lid}/layout_{lid}_{task}');paths=[baseline/relative,a.root/relative];records=[];metas=[]
  for folder in paths:
   raw=folder/'raw.npz'
   with np.load(raw) as z:
    m=json.loads(str(z['collect_meta']));metas.append(m)
    assert m['assist_frames']==0 and len(z['q'])==160 and np.abs(z['q'][0,12:]).max()<1e-4 and np.abs(z['action'][0,12:]).max()<1e-4 and np.all(z['action'][:,12]==0)
   q=json.loads((folder/'quality.json').read_text());assert not q['training_ready']
   with np.load(folder/'trace.npz') as z:
    t=z[obj];other=z['mailer' if obj=='box' else 'box'];progress=float(direction*(t[-1,1]-t[0,1]));zone=float(np.min(direction*t[-10:,1])-.20);assert abs(progress-q['metrics']['target_final_progress_m'])<1e-6
    initial={k:z[k][0].tolist() for k in ['box','mailer']}
   modes=dict(collections.Counter(c['mode'] for c in json.loads((folder/'expert_control.json').read_text())))
   records.append(dict(raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),passed=q['passed'],reasons=q['reasons'],progress=progress,stable_zone_margin=zone,non_target_max_xy=float(np.max(np.linalg.norm(other[:,:2]-other[0,:2],axis=1))),phases=modes,initial=initial))
  old,new=metas;assert old['layout']==new['layout']==json.loads(Path(layout['path']).read_text())
  assert new['crossed_contact_offset']==-.04
  changed=direction*new[obj+'_xyz'][1]<-.03
  expected=-.04 if changed else old['contact_side_offset'];assert new['contact_side_offset']==expected
  differences={k:[old.get(k),new.get(k)] for k in set(old)|set(new) if old.get(k)!=new.get(k)}
  # Reset poses may have tiny floating differences; retain and bound them separately.
  allowed={'crossed_contact_offset','contact_side_offset','box_xyz','mailer_xyz','box_quat_xyzw','mailer_quat_xyzw'}
  assert not set(differences)-allowed,differences
  for key in ['box','mailer']:assert np.max(np.abs(np.array(records[0]['initial'][key])-records[1]['initial'][key]))<.001
  rows.append(dict(layout_id=lid,task=task,geometry_group=layout['geometry_group'],intervention_applies=changed,metadata_differences=differences,baseline=records[0],candidate=records[1]))
groups=[]
for group in sorted({x['geometry_group'] for x in protocol['layouts']}):
 rs=[x for x in rows if x['geometry_group']==group];groups.append(dict(group=group,complete=len(rs)==4,baseline_pass=sum(x['baseline']['passed'] for x in rs),candidate_pass=sum(x['candidate']['passed'] for x in rs)))
summary=dict(completed=len(rows),baseline_pass=sum(x['baseline']['passed'] for x in rows),candidate_pass=sum(x['candidate']['passed'] for x in rows),groups=groups)
a.out.write_text(json.dumps(dict(summary=summary,rows=rows,scope='All registered pairs retained; prior controls are not an exact deterministic replay. Actual visual review still required. No training admission.',training_ready=False,goal_complete=False),indent=2));print(json.dumps(summary,indent=2))
