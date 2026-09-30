#!/usr/bin/env python3
"""Quantify near/far branch supervision; diagnostic only, does not change training."""
import argparse,json
from collections import defaultdict
from pathlib import Path
import numpy as np


def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();meta=a.dataset/'meta'
    records=json.loads((meta/'paired_provenance.json').read_text())['records'];split=json.loads((meta/'train_validation_split.json').read_text());stats=json.loads((meta/'train_only_stats.json').read_text())['observation.state'];lo=np.asarray(stats['q01'],dtype=np.float32);hi=np.asarray(stats['q99'],dtype=np.float32);den=np.where(hi-lo==0,np.float32(1e-8),hi-lo)
    ix=[*range(13,23),12];groups=defaultdict(list);frames=0;push_frames=0;push_episodes=0
    def tokens(q):return np.digitize(2*(q-lo)/den-1,np.linspace(-1,1,257)[:-1])-1
    for i in split['train']:
        row=records[i]
        with np.load(row['path'],allow_pickle=False) as data:q=data['q'][:,ix];act=data['action'][:,ix]
        frames+=len(q)
        if row['task_id']=='wait_no_package':continue
        push_frames+=len(q);push_episodes+=1;groups[(row['geometry_group'],row['task_id'])].append((row,q,act,tokens(q)))
    results=[]
    for (group,task),pair in sorted(groups.items()):
        assert len(pair)==2 and {x[0]['assignment'] for x in pair}=={'normal','swapped'}
        first,second=pair;n=min(len(first[1]),len(second[1]));match=np.all(first[3][:n]==second[3][:n],axis=1);qdiff=np.max(np.abs(first[1][:n]-second[1][:n]),axis=1);adiff=np.max(np.abs(first[2][:n]-second[2][:n]),axis=1)
        prefix=[]
        for t in range(min(20,n-49)):
            err=first[2][t:t+50]-second[2][t:t+50];prefix.append({'frame':t,'same_state_tokens':bool(match[t]),'state_max_abs_difference_rad':float(qdiff[t]),'current_action_max_difference_rad':float(adiff[t]),'future50_action_rmse_rad':float(np.sqrt(np.mean(err**2)))})
        firstdiff=lambda ar,threshold: int(np.flatnonzero(ar>threshold)[0]) if np.any(ar>threshold) else None
        results.append({'geometry_group':group,'task':task,'layout_ids':[x[0]['layout_id'] for x in pair],'first_state_difference_gt_0p001_rad':firstdiff(qdiff,.001),'first_action_difference_gt_0p001_rad':firstdiff(adiff,.001),'first_different_state_token_frame':int(np.flatnonzero(~match)[0]) if np.any(~match) else None,'first20':prefix})
    windows=[{'initial_frames_per_push':k,'frames':push_episodes*k,'fraction_of_all_training_frames':push_episodes*k/frames,'expected_samples_in_uniform7240_steps':7240*push_episodes*k/frames} for k in [1,5,10,20,40]]
    zero=[x['first20'][0] for x in results];result={'training_frames':frames,'push_frames':push_frames,'push_episodes':push_episodes,'paired_same_prompt_category_swap_groups':len(results),'unweighted_frame_windows':windows,'all_pairs_initial_state_tokens_equal':all(x['same_state_tokens'] for x in zero),'initial_future50_action_rmse_rad_range':[min(x['future50_action_rmse_rad'] for x in zero),max(x['future50_action_rmse_rad'] for x in zero)],'pairs':results,'method':'Read-only raw state/action and training-only stats. Float32 quantile formula and256bins reproduced from current normalize_processor.py/processor_pi05.py; constant padded state dimensions omitted from equality checks. Future50 window matches policy chunk size. Actual training uses unweighted frame shuffle, batch1.','limitations':'Early-window fractions and near/far supervision differences do not prove the model ignores images, nor that oversampling will improve it. These are sampling diagnostics, not new success gates or changed labels.'}
    if a.out.exists():raise FileExistsError(a.out)
    a.out.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['pairs','method','limitations']},indent=2))
if __name__=='__main__':main()
