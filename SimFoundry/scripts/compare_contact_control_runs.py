#!/usr/bin/env python3
"""Three-way descriptive repeatability audit; never infer instrumentation causality."""
import argparse,hashlib,itertools,json
from pathlib import Path
import numpy as np


def differences(x,y):
    assert x.shape==y.shape and np.isfinite(x).all() and np.isfinite(y).all()
    maxima=[];means=[]
    for a,b in zip(x,y):
        d=np.abs(a.astype(np.float64)-b.astype(np.float64));maxima.append(float(d.max()));means.append(float(d.mean()))
    idx=np.flatnonzero(np.asarray(maxima)>0)
    return {'exact_equal':len(idx)==0,'max_abs_difference':max(maxima),'mean_abs_difference':float(np.mean(means)),'first_nonidentical_frame':int(idx[0]) if len(idx) else None,'sampled_frames':{str(i):{'max_abs_difference':maxima[i],'mean_abs_difference':means[i]} for i in (0,1,10,30,60,100,159)}}


def main():
    p=argparse.ArgumentParser();p.add_argument('--workflow',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--case',choices=['original100_seed2','spatial58004_seed1'],required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    lid,seed,dist=(100,2,'original') if a.case=='original100_seed2' else (58004,1,'spatial')
    old=a.baseline/f'relative10_{dist}_seed{seed}';old=old/'rollouts' if dist=='original' else old/f'layout_{lid}'
    rows=[]
    for task in ('push_box_to_bin','nudge_mailer_to_bin'):
        name=f'layout_{lid:04d}_{task}';paths={'original':old/name,'instrumented':a.workflow/a.case/'rollouts'/name,'control':a.workflow/'uninstrumented_control'/a.case/'rollouts'/name};raws={};traces={};meta={};quality={};hashes={}
        for label,path in paths.items():
            with np.load(path/'raw.npz',allow_pickle=False) as z:
                raws[label]={k:z[k].copy() for k in ('q','action','rgb')};meta[label]=json.loads(str(z['collect_meta']))
                assert np.max(np.abs(z['q'][0,12:]))<1e-4 and np.all(z['action'][:,12]==0) and meta[label]['assist_frames']==0
            with np.load(path/'trace.npz') as z:traces[label]={k:z[k].copy() for k in z.files}
            quality[label]=json.loads((path/'quality.json').read_text());hashes[label]=hashlib.sha256((path/'raw.npz').read_bytes()).hexdigest()
        assert meta['original']['layout']==meta['instrumented']['layout']==meta['control']['layout']
        assert not (paths['control']/'episode_contacts.json').exists()
        pairs=[]
        for left,right in itertools.combinations(paths,2):
            diff={k:differences(raws[left][k],raws[right][k]) for k in raws[left]}
            diff.update({'trace_'+k:differences(traces[left][k],traces[right][k]) for k in traces[left]})
            pairs.append({'left':left,'right':right,'all_arrays_exact':all(d['exact_equal'] for d in diff.values()),'differences':diff})
        rows.append({'task':task,'paths':{k:str(v.resolve()) for k,v in paths.items()},'quality':quality,'raw_sha256':hashes,'pairs':pairs})
    a.out.write_text(json.dumps({'case':a.case,'rows':rows,'method':'All160 frames, exact elementwise q/action/RGB/object/palm comparison across original evaluation, contact-instrumented repeat and uninstrumented repeat. Fixed checkpoint, layout and flow seed.','limitations':'One repeat per condition does not estimate a variance distribution or identify causal effects of instrumentation. Initial image differences and closed-loop amplification can confound comparisons. Record all failures unchanged.','goal_complete':False},indent=2)+'\n')
    for r in rows:
        print(r['task'],{k:v['passed'] for k,v in r['quality'].items()})
        for pair in r['pairs']:
            ds=pair['differences'];print(pair['left'],pair['right'],'exact',pair['all_arrays_exact'],'actionmax',ds['action']['max_abs_difference'],'rgb0mae',ds['rgb']['sampled_frames']['0']['mean_abs_difference'])


if __name__=='__main__':main()
