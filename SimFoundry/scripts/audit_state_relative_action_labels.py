#!/usr/bin/env python3
"""Train-only feasibility audit of state-anchored joint action windows."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--dataset',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists(): raise FileExistsError(a.out)
    records=json.loads((a.dataset/'meta/paired_provenance.json').read_text())['records']
    split=json.loads((a.dataset/'meta/train_validation_split.json').read_text())
    train=set(split['train']); assert not train & set(split['validation'])
    chunks=[]; residuals=[]; masks=[]; tasks=[]; errors=[]; hashes={}
    indices=[*range(13,23),12]
    for eid in sorted(train):
        r=records[eid]; path=Path(r['path'])
        digest=hashlib.sha256(path.read_bytes()).hexdigest(); assert digest==r['hash']; hashes[str(eid)]=digest
        with np.load(path) as z:
            q=z['q'][:,indices].astype(np.float64)
            u=z['action'][:,indices].astype(np.float64)
        assert np.max(np.abs(q[0]))<1e-4 and np.max(np.abs(u[0]))<1e-4
        assert np.all(u[:,-1]==0)
        t=np.arange(len(u))[:,None]+np.arange(50)[None,:]
        valid=t<len(u); absolute=u[np.minimum(t,len(u)-1)]
        # Only arm10 is relative; waist stays absolute-zero as required.
        anchor=q.copy();anchor[:,-1]=0
        relative=absolute-anchor[:,None,:]
        restored=relative+anchor[:,None,:]
        errors.append(float(np.max(np.abs(restored-absolute))))
        chunks.append(absolute);residuals.append(relative);masks.append(valid)
        tasks.extend([r['task_id']]*len(u))
        print('TRAIN_EPISODE',eid,flush=True)
    absolute=np.concatenate(chunks);relative=np.concatenate(residuals);valid=np.concatenate(masks); tasks=np.array(tasks)
    assert max(errors)<1e-12
    def stats(x):
        return {'min':x.min(axis=0).tolist(),'max':x.max(axis=0).tolist(),
                'span':np.ptp(x,axis=0).tolist(), 'rms':np.sqrt(np.mean(x*x,axis=0)).tolist(),
                'p99_absolute':np.quantile(np.abs(x),.99,axis=0).tolist()}
    results={}
    for task in ['all',*sorted(set(tasks))]:
        choose=np.ones(len(tasks),bool) if task=='all' else tasks==task
        results[task]={}
        for horizon in [1,10,50]:
            m=valid[choose,:horizon]
            results[task][str(horizon)]={'valid_scalar_labels':int(m.sum()*11),
                'absolute':stats(absolute[choose,:horizon][m]),
                'state_relative':stats(relative[choose,:horizon][m])}
    report={'dataset':str(a.dataset.resolve()),'train_episodes':len(train),'train_frames':len(tasks),
        'validation_episodes_read':[], 'raw_sha256':hashes, 'max_float64_roundtrip_error':max(errors),
        'definition':'relative[t,k,:10]=absolute[t+k,:10]-q[t,:10]; waist absolute zero; restore with SAME query q[t], not future q or accumulated deltas. Terminal padded entries excluded from stats.',
        'results':results,'limitations':'Reparameterization feasibility only, not evidence it improves a learned model. Train-only raw source windows, not loaded training-processor parity. Must implement identical training/inference normalization and anchor, verify actual processed windows and decoding before training. No source labels, model or physical gate changed.', 'goal_complete':False}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2))
    print('ROUNDTRIP',max(errors))
    for horizon in ['1','10','50']:
        r=results['all'][horizon]
        print('HORIZON',horizon,'ABS_SPAN',r['absolute']['span'],'REL_SPAN',r['state_relative']['span'])

if __name__=='__main__': main()
