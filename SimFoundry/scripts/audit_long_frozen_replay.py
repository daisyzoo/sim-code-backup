#!/usr/bin/env python3
import argparse,json,hashlib,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from simfoundry.data.search_reward import terminal_search_scores
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();protocol=json.loads((a.root/'PROTOCOL.json').read_text());rows=[]
for c in protocol['cases']:
 ep=a.root/f"case_{c['layout_id']}/layout_{c['layout_id']}_{c['task']}";source=Path(c['source'])
 if not (ep/'quality.json').exists():continue
 assert hashlib.sha256(source.read_bytes()).hexdigest()==c['sha256']
 provenance=json.loads((ep.parent/'provenance.json').read_text());assert provenance['args']['policy_port']==0 and provenance['args']['steps']==640
 assert provenance['source_sha256']['scripts/collect_frozen_long_diagnostic.py']==protocol['collector_sha256']
 with np.load(source) as old,np.load(ep/'raw.npz') as new,np.load(ep/'trace.npz') as trace,np.load(ep/'parcel_orientation.npz') as ori:
  assert new['action'].shape==(640,23) and np.array_equal(new['action'],old['action'])
  assert np.abs(new['q'][0,12:]).max()<1e-4 and np.abs(new['action'][0,12:]).max()<1e-4 and np.all(new['action'][:,12]==0) and np.abs(np.diff(new['action'],axis=0)).max()<=.055001
  meta=json.loads(str(new['collect_meta']));assert meta['assist_frames']==0 and not meta['push_assist'] and meta['collection_role']=='diagnostic'
  for obj in ['box','mailer']:assert np.abs(trace[obj][0]-old[obj][0]).max()<1e-4
  q=json.loads((ep/'quality.json').read_text());assert not q['training_ready']
  _,fit=terminal_search_scores([q],[0 if c['task']=='push_box_to_bin' else 1],{k:trace[k][:,None] for k in trace.files},{k:ori[k][:,None] for k in ori.files})
  rows.append(dict(case=c,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),actions_exact=True,max_q_error=float(np.abs(new['q']-old['q']).max()),max_trace_errors={k:float(np.abs(trace[k]-old[k]).max()) for k in trace.files},passed=q['passed'],reasons=q['reasons'],fitness=fit[0]))
a.out.write_text(json.dumps(dict(rows=rows,scope='Frozen640-frame direct-joint diagnostic replay; exact action checks, physical differences retained. Not model h10 evaluation or training admission.',training_ready=False,goal_complete=False),indent=2));print('Verified',len(rows),'episodes')
