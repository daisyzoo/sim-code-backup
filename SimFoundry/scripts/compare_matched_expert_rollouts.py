#!/usr/bin/env python3
"""Same-layout expert/policy trace comparison. No force/causal claims or admission."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np


def read(path):
    with np.load(path/'raw.npz', allow_pickle=False) as z:
        raw={k:z[k].copy() for k in ('q','action')}
        meta=json.loads(str(z['collect_meta']))
    with np.load(path/'trace.npz', allow_pickle=False) as z:
        trace={k:z[k].copy() for k in z.files}
    assert raw['q'].shape == raw['action'].shape == (160,23)
    assert np.max(np.abs(raw['q'][0,12:])) < 1e-4
    assert np.all(raw['action'][:,12] == 0) and meta['assist_frames'] == 0
    assert all(v.shape==(160,3) and np.isfinite(v).all() for v in trace.values())
    return raw,trace,meta,json.loads((path/'quality.json').read_text())


def onset(x):
    ids=np.flatnonzero(np.linalg.norm(x[:,:2]-x[0,:2],axis=1)>.005)
    return int(ids[0]) if len(ids) else None


def main():
    p=argparse.ArgumentParser();p.add_argument('--expert-root',type=Path,required=True);p.add_argument('--comparison',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--layout-ids',type=int,nargs='+');a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    protocol=json.loads((a.expert_root/'PROTOCOL.json').read_text());expected={r['layout_id'] for r in protocol['layouts']}
    if a.layout_ids is not None:assert set(a.layout_ids)<=expected;expected=set(a.layout_ids)
    trials=[r for r in json.loads(a.comparison.read_text())['rows'] if r['task']!='wait_no_package' and r['layout_id'] in expected]
    assert len(trials)==len(expected)*6
    rows=[]
    for r in trials:
        lid=r['layout_id'];task=r['task'];ep=a.expert_root/f'layout_{lid}'/f'layout_{lid:04d}_{task}';mp=Path(r['candidate']['path'])
        er,et,em,eq=read(ep);mr,mt,mm,mq=read(mp)
        assert em['layout']==mm['layout'],(ep,mp)
        assert np.max(np.abs(er['action'][0,12:]))<1e-4
        initial=max(float(np.max(np.abs(et[k][0]-mt[k][0]))) for k in ('box','mailer'))
        assert initial<.001,('reset mismatch',initial,mp)
        target,other,side,ix=('box','mailer','right',slice(18,23)) if task=='push_box_to_bin' else ('mailer','box','left',slice(13,18))
        palm='palm_'+side;delta=mt[palm]-et[palm];control=json.loads((ep/'expert_control.json').read_text());assert len(control)==160
        phases=[]
        for mode in dict.fromkeys(x['mode'] for x in control):
            ids=np.array([i for i,x in enumerate(control) if x['mode']==mode]);phases.append({'expert_phase':mode,'frames':ids.tolist(),'palm_rmse_m':float(np.sqrt(np.mean(np.sum(delta[ids]**2,axis=1)))),'active_q_rmse_rad':float(np.sqrt(np.mean((mr['q'][ids,ix]-er['q'][ids,ix])**2))),'mean_palm_delta_xyz_m':delta[ids].mean(axis=0).tolist()})
        snapshots=[]
        for t in [0,10,20,30,40,60,80,100,120,159]:
            snapshots.append({'frame':t,'expert_phase':control[t]['mode'],'policy_minus_expert_palm_xyz_m':delta[t].tolist(),'expert_target_xy_displacement_m':float(np.linalg.norm(et[target][t,:2]-et[target][0,:2])),'policy_target_xy_displacement_m':float(np.linalg.norm(mt[target][t,:2]-mt[target][0,:2]))})
        rows.append({'layout_id':lid,'task':task,'seed':r['seed'],'distribution':r['distribution'],'distance':r['distance'],'expert_path':str(ep.resolve()),'policy_path':str(mp),'expert_passed':eq['passed'],'expert_reasons':eq['reasons'],'policy_passed':mq['passed'],'policy_reasons':mq['reasons'],'initial_objects_max_abs_difference_m':initial,'expert_motion_onset5mm':{k:onset(et[k]) for k in (target,other)},'policy_motion_onset5mm':{k:onset(mt[k]) for k in (target,other)},'phases':phases,'snapshots':snapshots,'raw_hashes':{k:hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest() for k,p in [('expert',ep),('policy',mp)]},'trace_hashes':{k:hashlib.sha256((p/'trace.npz').read_bytes()).hexdigest() for k,p in [('expert',ep),('policy',mp)]}})
    result={'matched_policy_trials':len(rows),'unique_expert_episodes':len(expected)*2,'expert_passed':sum(r['expert_passed'] for r in rows if r['seed']==0),'rows':rows,'method':'Requested layout dictionaries exactly equal; initial measured object XYZ differs <1mm. Compare same recorded frame (no time warping), with expert phase grouping and raw/hash binding. Report failed experts as well.','limitations':'Same-time difference mixes timing and spatial path error; phase names come from expert only. Center trajectories and motion onset do not prove contact forces. Expert contact instrumentation has not yet been parity-tested against an uninstrumented repeat. Diagnostic data are never training-admitted.','training_ready':False,'goal_complete':False}
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['matched_policy_trials','unique_expert_episodes','expert_passed']}))


if __name__=='__main__':main()
