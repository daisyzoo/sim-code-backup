#!/usr/bin/env python3
"""Report all candidate outcomes without changing admission or approval."""
import argparse,json
from collections import Counter
from pathlib import Path
import numpy as np
from select_spatial_candidate_groups import group_state


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);a=ap.parse_args();root=a.root.resolve()
    c=json.loads((root/'contract.json').read_text());layout={x['layout_id']:x for x in c['layouts']}
    groups=[group_state(root,g) for g in c['candidate_groups']];episodes=[]
    for g in groups:
        if g['status']=='pending':continue
        for lid in g['layout_ids']:
            for p in sorted((root/f'case_{lid}').glob('layout_*/quality.json')):
                q=json.loads(p.read_text());task=p.parent.name.split('_',2)[2];target='box' if task=='push_box_to_bin' else 'mailer';direction=-1 if target=='box' else 1
                with np.load(p.parent/'trace.npz') as z:
                    t=z[target];other=z['mailer' if target=='box' else 'box']
                    trace={'initial_xyz':t[0].tolist(),'final_xyz':t[-1].tolist(),'x_drift_m':float(t[-1,0]-t[0,0]),'last10_min_signed_y_m':float((direction*t[-10:,1]).min()),'non_target_max_xyz_m':float(np.linalg.norm(other-other[0],axis=1).max())}
                modes=Counter(x['mode'] for x in json.loads((p.parent/'expert_control.json').read_text()))
                episodes.append({'group':g['group'],'partition':g['partition'],'stratum':g['stratum'],'layout_id':lid,'assignment':layout[lid]['assignment'],'task':task,'target_distance':'far' if trace['initial_xyz'][0]>=.48 else 'near','passed':q['passed'],'reasons':q['reasons'],'phase_frames':dict(modes),**trace})
    strata=[]
    for partition,stratum in sorted({(g['partition'],g['stratum']) for g in groups}):
        gs=[g for g in groups if g['partition']==partition and g['stratum']==stratum];complete=[g for g in gs if g['status']!='pending'];ok=[g for g in complete if g['status'] in ('approved_group','numeric_pass_visual_pending')]
        strata.append({'partition':partition,'stratum':stratum,'registered_groups':len(gs),'completed_groups':len(complete),'numeric_complete_groups_passed':len(ok),'visually_approved_groups':sum(g['status']=='approved_group' for g in gs)})
    cells=[]
    for task,distance in sorted({(e['task'],e['target_distance']) for e in episodes}):
        es=[e for e in episodes if e['task']==task and e['target_distance']==distance];cells.append({'task':task,'target_distance':distance,'passed':sum(e['passed'] for e in es),'total':len(es)})
    report={'stage':json.loads((root/'STATUS.json').read_text()),'strata':strata,'task_distance':cells,'groups':groups,'episodes':episodes,'scope':'All completed whole groups, including failures; ongoing/incomplete groups are not counted. Numeric or image review approval is not model success. Repeated tasks/assignments within a geometry are correlated.','training_ready':False}
    (root/'CANDIDATE_REPORT.json').write_text(json.dumps(report,indent=2));print(json.dumps({'strata':strata,'task_distance':cells},indent=2))
if __name__=='__main__':main()
