#!/usr/bin/env python3
import argparse,json,hashlib,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from simfoundry.data.search_reward import terminal_search_scores
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();rows=[]
for case in json.loads((a.root/'PROTOCOL.json').read_text())['cases']:
 run=a.root/f"case_{case['layout_id']}_{case['condition']}";ep=run/f"layout_{case['layout_id']}_{case['task']}"
 if not (ep/'quality.json').exists():continue
 source=Path(case['source']);assert hashlib.sha256(source.read_bytes()).hexdigest()==case['sha256']
 with np.load(source) as base,np.load(ep/'raw.npz') as actual,np.load(ep/'trace.npz') as trace,np.load(ep/'parcel_orientation.npz') as ori:
  acts=actual['action'];assert acts.shape==(320,23) and np.array_equal(acts[:160],base['action'])
  assert np.abs(actual['q'][0,12:]).max()<1e-4 and np.abs(acts[0,12:]).max()<1e-4 and np.all(acts[:,12]==0) and np.abs(np.diff(acts,axis=0)).max()<=.055001
  meta=json.loads(str(actual['collect_meta']));assert meta['assist_frames']==0 and not meta['push_assist']
  for obj in ['box','mailer']:assert np.abs(trace[obj][0]-base[obj][0]).max()<1e-4
  event=json.loads((ep/'recontact_event.json').read_text())['event']
  if case['condition']=='hold':assert event is None and np.array_equal(acts[160:],np.tile(base['action'][-1],(160,1)))
  else:
   obj='box' if case['task']=='push_box_to_bin' else 'mailer'
   assert event['step']==160 and np.allclose(event['target_xyz'],trace[obj][160],atol=1e-6)
  quality=json.loads((ep/'quality.json').read_text());assert not quality['training_ready']
  _,fitness=terminal_search_scores([quality],[0 if case['task']=='push_box_to_bin' else 1],{k:trace[k][:,None] for k in trace.files},{k:ori[k][:,None] for k in ori.files})
  target='box' if case['task']=='push_box_to_bin' else 'mailer';direction=-1 if target=='box' else 1
  rows.append(dict(case=case,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),first_pass_exact=True,passed=quality['passed'],reasons=quality['reasons'],fitness=fitness[0],second_pass_progress_m=float(direction*(trace[target][-1,1]-trace[target][160,1])),final_xyz=trace[target][-1].tolist(),event=event))
a.out.write_text(json.dumps(dict(rows=rows,training_ready=False,goal_complete=False,scope='Equal-duration far recontact diagnostic; not paired admission or model evaluation'),indent=2));print('Verified',len(rows),'episodes')
