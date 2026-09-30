#!/usr/bin/env python3
"""Verify instrumented replay parity and report post-action contact candidates."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np


def diff(a,b):
    assert a.shape == b.shape and np.isfinite(a).all() and np.isfinite(b).all()
    return {'exact_equal':bool(np.array_equal(a,b)),'max_abs_difference':float(np.max(np.abs(a.astype(np.float64)-b.astype(np.float64))))}


def onset(values):
    ids=np.flatnonzero(values)
    return int(ids[0]) if len(ids) else None


def main():
    p=argparse.ArgumentParser();p.add_argument('--workflow',type=Path,required=True);p.add_argument('--case',choices=['original100_seed2','spatial58004_seed1'],required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    lid,seed,dist=(100,2,'original') if a.case=='original100_seed2' else (58004,1,'spatial')
    base=a.baseline/f'relative10_{dist}_seed{seed}';base=base/'rollouts' if dist=='original' else base/f'layout_{lid}'
    rows=[]
    for task,side,target,other in [('push_box_to_bin','right','box','mailer'),('nudge_mailer_to_bin','left','mailer','box')]:
        name=f'layout_{lid:04d}_{task}';cur=a.workflow/a.case/'rollouts'/name;old=base/name
        parity={}
        with np.load(cur/'raw.npz') as x,np.load(old/'raw.npz') as y:
            cm=json.loads(str(x['collect_meta']));om=json.loads(str(y['collect_meta']));assert cm['layout']==om['layout']
            assert abs(x['q'][0,12:]).max()<1e-4 and np.all(x['action'][:,12]==0) and cm['assist_frames']==0
            for key in ['q','action','rgb']:parity[key]=diff(x[key],y[key])
        with np.load(cur/'trace.npz') as x,np.load(old/'trace.npz') as y:
            tr={k:x[k].copy() for k in x.files}
            for k in tr:parity['trace_'+k]=diff(x[k],y[k])
        contact=json.loads((cur/'episode_contacts.json').read_text());cs=contact['rows'];assert len(cs)==160
        assert [r['after_action_step'] for r in cs]==list(range(160))
        post={k:np.array([r['post_action_pose'][k] for r in cs]) for k in tr}
        alignment={k:diff(post[k][:-1],tr[k][1:]) for k in tr}
        assert all(r['max_abs_difference']<1e-6 for r in alignment.values()),alignment
        hand=f'/{side}_wrist_roll_rubber_hand/';inactive=f'/{"left" if side=="right" else "right"}_wrist_roll_rubber_hand/'
        obj={'box':'/parcel_box/','mailer':'/mailer/'}
        types={'active_target':(hand,obj[target]),'active_non_target':(hand,obj[other]),'inactive_target':(inactive,obj[target]),'inactive_non_target':(inactive,obj[other]),'object_object':(obj[target],obj[other])}
        frames={k:[] for k in types}
        for i,r in enumerate(cs):
            for label,(u,v) in types.items():
                if any((u in pair['shapes'][0] and v in pair['shapes'][1]) or (v in pair['shapes'][0] and u in pair['shapes'][1]) for pair in r['target_pairs']):frames[label].append(i)
        motion={k:np.linalg.norm(post[k][:,:2]-tr[k][0,:2],axis=1) for k in (target,other)}
        q=json.loads((cur/'quality.json').read_text());oq=json.loads((old/'quality.json').read_text())
        rows.append({'task':task,'current':str(cur.resolve()),'baseline':str(old.resolve()),'parity':parity,'all_arrays_exact':all(v['exact_equal'] for v in parity.values()),'same_quality_decision':q['passed']==oq['passed'] and q['reasons']==oq['reasons'],'quality':q,'post_action_to_next_trace_alignment':alignment,'candidate_contact_frames_after_action':frames,'motion_onset_after_action':{str(mm):{k:onset(v>mm/1000) for k,v in motion.items()} for mm in (2,5,15)},'raw_sha256':hashlib.sha256((cur/'raw.npz').read_bytes()).hexdigest(),'contacts_sha256':hashlib.sha256((cur/'episode_contacts.json').read_bytes()).hexdigest()})
    out={'case':a.case,'rows':rows,'all_arrays_exact':all(r['all_arrays_exact'] for r in rows),'limitations':'Candidate pairs are last physics tick only, not force/impulse measurements or every substep. Contact frame indices are AFTER action, while raw/trace indices are BEFORE action. Exact replay required before interpreting this as original failure; divergence requires an uninstrumented control repeat. No training admission.','goal_complete':False}
    a.out.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'case':a.case,'all_arrays_exact':out['all_arrays_exact'],'tasks':[{'task':r['task'],'passed':r['quality']['passed'],'same_quality_decision':r['same_quality_decision'],'first_candidate_contacts':{k:(v[0] if v else None) for k,v in r['candidate_contact_frames_after_action'].items()},'motion_onset5mm':r['motion_onset_after_action']['5']} for r in rows]},indent=2))


if __name__=='__main__':main()
