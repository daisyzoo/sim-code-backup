#!/usr/bin/env python3
"""Compare complete coverage80 models with predicted horizons50/10 and executionh10 with unchanged gates."""
import argparse,json
from pathlib import Path
from collections import defaultdict
from compare_spatial_evaluations import indexed,TASKS


def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline-root',type=Path,required=True);p.add_argument('--candidate-root',type=Path,required=True);p.add_argument('--protocol',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    protocol=json.loads(a.protocol.read_text());layouts={}
    for f in protocol['layout_files']:
        d=json.loads(Path(f['path']).read_text());layouts[d['layout_id']]=d
    summary=[];details=[]
    for distribution in ['spatial','original']:
        ids=layouts if distribution=='spatial' else [100,101,102];wait=protocol['wait_layout_id'] if distribution=='spatial' else 20000
        keys={(s,l,t) for s in protocol['eval_seeds'] for l in ids for t in TASKS}|{(s,wait,'wait_no_package') for s in protocol['eval_seeds']}
        baseline=indexed(a.baseline_root/f'EVALUATION_coverage_{distribution}.json',keys);candidate=indexed(a.candidate_root/f'EVALUATION_chunk10_{distribution}.json',keys);buckets=defaultdict(list)
        for key in sorted(keys):
            s,l,t=key;old,new=baseline[key],candidate[key];distance='wait' if t=='wait_no_package' else ('original' if distribution=='original' else ('far' if layouts[l]['box_xyz' if t=='push_box_to_bin' else 'mailer_xyz'][0]>=.48 else 'near'))
            row={'distribution':distribution,'seed':s,'layout_id':l,'task':t,'distance':distance,'coverage80':old,'chunk10':new};details.append(row);buckets[(t,distance)].append(row)
        for (t,d),rs in sorted(buckets.items()):summary.append({'distribution':distribution,'task':t,'distance':d,'total':len(rs),'coverage80_passed':sum(r['coverage80']['passed'] for r in rs),'chunk10_passed':sum(r['chunk10']['passed'] for r in rs),'wins':sum(r['chunk10']['passed'] and not r['coverage80']['passed'] for r in rs),'losses':sum(r['coverage80']['passed'] and not r['chunk10']['passed'] for r in rs)})
    out={'summary':summary,'rows':details,'visual_review':'required separately','goal_complete':False,'limitations':'Samecoverage80 dataset/sampler/base/seed42/14480steps; predicted50vs10, executedh10 unchanged. Nativevalidationloss windows differ. Same geometry/seeds; correlated paired trials. Reused evaluation layouts now form a development benchmark, not fresh final generalization evidence. Need new independent layouts after candidate selection.'}
    a.out.write_text(json.dumps(out,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
