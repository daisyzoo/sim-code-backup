#!/usr/bin/env python3
"""Classify predicted chunks against all four same-geometry expert branches."""
import argparse,json
from pathlib import Path
import numpy as np


def main():
    p=argparse.ArgumentParser();p.add_argument('--audit',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    r=json.loads((a.audit/'REPORT.json').read_text());frame=r.get('frame',0);stats=json.loads((Path(r['dataset'])/'meta/train_only_stats.json').read_text())['action'];scale=np.asarray(stats['max'])-np.asarray(stats['min']);scale=np.where(scale>1e-6,scale,1.);ix=[*range(13,23),12];experts={};rows=[]
    for t in r['trials']:
        key=(t['group'],t['task'],t['target_distance'])
        if key not in experts:
            with np.load(t['raw_path'],allow_pickle=False) as z:experts[key]=z['action'][frame:frame+50,ix].astype(float)
    with np.load(a.audit/'predictions.npz') as z:
        for t in r['trials']:
            pred=z[t['prediction_key']][:50];scores=[(float(np.mean(((pred-v)/scale)**2)),task,distance) for (group,task,distance),v in experts.items() if group==t['group']];scores.sort();best=scores[0]
            rows.append({'partition':t['partition'],'group':t['group'],'task':t['task'],'distance':t['target_distance'],'seed':t['seed'],'nearest_task':best[1],'nearest_distance':best[2],'task_match':best[1]==t['task'],'full_branch_match':best[1]==t['task'] and best[2]==t['target_distance'],'nearest_mse':best[0],'scores':scores})
    summary=[]
    for part in ['train','validation']:
        for task in ['nudge_mailer_to_bin','push_box_to_bin']:
            rs=[x for x in rows if x['partition']==part and x['task']==task];summary.append({'partition':part,'task':task,'total':len(rs),'task_match':sum(x['task_match'] for x in rs),'full_branch_match':sum(x['full_branch_match'] for x in rs)})
    out={'frame':frame,'summary':summary,'rows':rows,'method':'Nearest of four expert chunks (two tasks x target near/far) in the same geometry group, using all11 joints with training action-range normalization. Diagnostic only; all candidate branches include different images/prompts. Not an instruction classifier or physical success measurement.'};a.out.write_text(json.dumps(out,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
