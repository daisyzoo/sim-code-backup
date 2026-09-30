#!/usr/bin/env python3
"""Find candidate label ambiguity in training-only RGB+q; not automatic rejection."""
import argparse
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
from scipy.spatial import cKDTree


def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(exist_ok=False,parents=True)
    records=json.loads((a.dataset/'meta/paired_provenance.json').read_text())['records']
    split=json.loads((a.dataset/'meta/train_validation_split.json').read_text());train=set(split['train']);validation=set(split['validation']);assert not train&validation
    stats=json.loads((a.dataset/'meta/train_only_stats.json').read_text())['observation.state']
    q01=np.array(stats['q01'],np.float32);q99=np.array(stats['q99'],np.float32);denom=q99-q01;denom=np.where(denom==0,np.float32(1e-8),denom)
    items=[];qs=[];acts=[];rgbs=[];tokens=[]
    for eid in sorted(train):
        r=records[eid];raw=Path(r['path']);assert hashlib.sha256(raw.read_bytes()).hexdigest()==r['hash']
        with np.load(raw) as z:
            q=z['q'][:,[*range(13,23),12]].copy();act=z['action'][:,[*range(13,23),12]].copy();rgb=z['rgb']
            for t in range(len(q)):
                items.append({'episode':eid,'frame':t,'task':r['task_id'],'prompt':r['exported_prompt'],'raw':str(raw),'raw_sha256':r['hash'],'layout_id':r['layout_id']})
                qs.append(q[t]);acts.append(act[t]);rgbs.append(cv2.resize(rgb[t].transpose(1,2,0),(80,60),interpolation=cv2.INTER_AREA)[30:].astype(np.float32))
                tokens.append(np.digitize((q[t]-q01)/denom*2-1,np.linspace(-1,1,257)[:-1])-1)
        print('LOADED_TRAIN',eid,flush=True)
    qs=np.stack(qs);acts=np.stack(acts);rgbs=np.stack(rgbs);tokens=np.stack(tokens);assert len(items)==9080
    candidates=[];counts=[]
    for task in sorted({r['task'] for r in items}):
        ids=np.array([i for i,r in enumerate(items) if r['task']==task]);pairs=cKDTree(qs[ids,:10]).query_pairs(.01,p=np.inf,output_type='ndarray')
        count={'task':task,'q_near_pairs':len(pairs),'nonadjacent_pairs':0,'large_action_difference_pairs':0,'strict_visual_candidates':0,'exact_state_bin_candidates':0}
        for start in range(0,len(pairs),20000):
            block=pairs[start:start+20000];i=ids[block[:,0]];j=ids[block[:,1]]
            keep=np.array([items[x]['episode']!=items[y]['episode'] or abs(items[x]['frame']-items[y]['frame'])>=10 for x,y in zip(i,j)])
            i,j=i[keep],j[keep];count['nonadjacent_pairs']+=len(i)
            if not len(i):continue
            diff=np.abs(acts[i,:10]-acts[j,:10]);keep=diff.max(axis=1)>.08;i,j=i[keep],j[keep];count['large_action_difference_pairs']+=len(i)
            for x,y in zip(i,j):
                assert items[x]['prompt']==items[y]['prompt']
                pixel=np.abs(rgbs[x]-rgbs[y]);mae=float(pixel.mean());tile=float(pixel.reshape(3,10,8,10,3).mean(axis=(1,3,4)).max())
                if mae>2 or tile>5:continue
                count['strict_visual_candidates']+=1;same=bool(np.array_equal(tokens[x],tokens[y]));count['exact_state_bin_candidates']+=same
                delta=np.abs(acts[x,:10]-acts[y,:10]);candidates.append({'first':items[x],'second':items[y],'max_arm_q_difference_rad':float(np.abs(qs[x,:10]-qs[y,:10]).max()),'waist_q_difference_rad':float(abs(qs[x,-1]-qs[y,-1])),'max_action_difference_rad':float(delta.max()),'max_action_joint11_index':int(delta.argmax()),'lower_half_80x30_rgb_mae':mae,'maximum_10x10_tile_mae':tile,'same_11_state_bins':same,'different_state_bins':int(np.count_nonzero(tokens[x]!=tokens[y]))})
        counts.append(count);print('TASK_DONE',count,flush=True)
    candidates.sort(key=lambda r:(not r['same_11_state_bins'],r['lower_half_80x30_rgb_mae'], -r['max_action_difference_rad']))
    result={'dataset':str(a.dataset.resolve()),'training_frames':len(items),'training_episodes':len(train),'validation_episodes_read':[],
        'counts':counts,'candidates':candidates[:100],'total_visual_candidates':len(candidates),
        'thresholds':{'arm_q_linf_rad':.01,'action_linf_difference_rad':.08,'same_episode_min_frame_separation':10,'lower_half_rgb_mae':2,'max_tile_mae':5},
        'limitations':'Heuristic near-observation pairs, not proof of inconsistent labels: unobserved velocities/contact and pixel downsampling can hide relevant differences. Only training split read. Exact state-bin flag ignores tokenizer text padding but compares all11 dimensions; synthetic reproduction of normalization is not loaded-processor proof. Candidates require actual full-resolution visual/trajectory review. No data removed or altered; no training/collection admission.',
        'goal_complete':False}
    (a.out/'REPORT.json').write_text(json.dumps(result,indent=2));print('CANDIDATES',len(candidates),flush=True)


if __name__=='__main__':main()
