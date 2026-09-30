#!/usr/bin/env python3
"""Read-only action continuity and tracking-gap audit from completed evaluation rows."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np


def main():
    p=argparse.ArgumentParser();p.add_argument('--evaluation',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    rows=json.loads(a.evaluation.read_text())['rows'];episodes=[];events=[];boundary=[];interior=[]
    for row in rows:
        if row['task']=='wait_no_package':continue
        path=Path(row['path'])/'raw.npz'
        with np.load(path,allow_pickle=False) as z:
            act=z['action'][:,12:23].astype(float);q=z['q'][:,12:23].astype(float);meta=json.loads(str(z['collect_meta']));names=z['joint_names'][12:23].tolist()
        assert meta['expert']=='pi05_h10' and meta['policy_action_step_cap']==0
        dif=np.abs(np.diff(act,axis=0));maxs=dif.max(axis=1);episode_events=[]
        for idx,v in enumerate(maxs):
            t=idx+1;is_boundary=t%10==0;(boundary if is_boundary else interior).append(float(v))
            if v<=.08:continue
            j=int(dif[idx].argmax());event={'seed':row['seed'],'layout_id':row['layout_id'],'task':row['task'],'frame':t,'at_chunk_boundary':is_boundary,'joint':str(names[j]),'action_step_rad':float(v),'previous_action_rad':float(act[t-1,j]),'observed_q_rad':float(q[t,j]),'new_action_rad':float(act[t,j]),'previous_command_tracking_gap_rad':float(abs(q[t,j]-act[t-1,j])),'new_command_to_state_gap_rad':float(abs(act[t,j]-q[t,j]))}
            events.append(event);episode_events.append(event)
        episodes.append({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'events':len(episode_events),'max_action_step_rad':float(maxs.max()),'formal_passed':row['passed']})
    def stats(xs):return {'count':len(xs),'mean':float(np.mean(xs)),'p95':float(np.quantile(xs,.95)),'max':float(np.max(xs))} if xs else None
    out={'episodes':episodes,'events':events,'summary':{'push_episodes':len(episodes),'episodes_with_abrupt_step':sum(x['events']>0 for x in episodes),'events':len(events),'events_at_chunk_boundary':sum(x['at_chunk_boundary'] for x in events),'boundary_step_rad':stats(boundary),'interior_step_rad':stats(interior),'event_previous_tracking_gap_rad':stats([x['previous_command_tracking_gap_rad'] for x in events])},'method':'Absolute23D action joints12:23; frame t observation precedes action t. Original>.08rad threshold, originalh10/cap0. Tracking gap is a diagnostic, not an altered gate or proof of cause.'}
    a.out.write_text(json.dumps(out,indent=2));print(json.dumps(out['summary'],indent=2))
if __name__=='__main__':main()
