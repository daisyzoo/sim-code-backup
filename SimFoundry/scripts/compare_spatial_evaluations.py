#!/usr/bin/env python3
"""Paired numeric comparison with exact coverage checks; never visual approval."""
import argparse,json
from collections import defaultdict
from pathlib import Path

TASKS=('nudge_mailer_to_bin','push_box_to_bin')

def indexed(path,expected):
    d=json.loads(path.read_text());rows=d['rows'];mapping={(r['seed'],r['layout_id'],r['task']):r for r in rows}
    if len(mapping)!=len(rows) or set(mapping)!=expected:raise ValueError(f'Incomplete or duplicate coverage: {path}')
    if not d['paired_reset_checks_passed']:raise ValueError(f'Invalid paired resets: {path}')
    if any(r['variant']!='short' for r in rows):raise ValueError('Prompt mismatch')
    return mapping


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--protocol',type=Path,required=True);a=p.parse_args();root=a.root
    protocol=json.loads(a.protocol.read_text());layouts={}
    for f in protocol['layout_files']:
        d=json.loads(Path(f['path']).read_text());layouts[d['layout_id']]=d
    expected={(seed,lid,t) for seed in protocol['eval_seeds'] for lid in layouts for t in TASKS}|{(seed,protocol['wait_layout_id'],'wait_no_package') for seed in protocol['eval_seeds']}
    original={(seed,lid,t) for seed in protocol['eval_seeds'] for lid in (100,101,102) for t in TASKS}|{(seed,20000,'wait_no_package') for seed in protocol['eval_seeds']}
    rows=[];summary=[];whole_groups=[]
    for distribution,keys in [('spatial',expected),('original',original)]:
        old=indexed(root/f'EVALUATION_ordinary_{distribution}.json',keys);new=indexed(root/f'EVALUATION_spatial_{distribution}.json',keys);buckets=defaultdict(list);geometry=defaultdict(list)
        for key in sorted(keys):
            seed,lid,task=key;o,n=old[key],new[key];distance='wait'
            if task!='wait_no_package':
                distance=('far' if layouts[lid]['box_xyz' if task=='push_box_to_bin' else 'mailer_xyz'][0]>=.48 else 'near') if distribution=='spatial' else 'original'
            row={'distribution':distribution,'seed':seed,'layout_id':lid,'task':task,'distance':distance,'ordinary_passed':o['passed'],'spatial_passed':n['passed'],'ordinary_reasons':o['reasons'],'spatial_reasons':n['reasons'],'ordinary_path':o['path'],'spatial_path':n['path']}
            for label,source in [('ordinary',o),('spatial',n)]:
                metrics=source['metrics'];non_target=None
                if task in TASKS:non_target=metrics.get('mailer_max_xy_m' if task=='push_box_to_bin' else 'box_max_xy_m')
                row[label+'_diagnostics']={'target_progress_m':metrics.get('target_final_progress_m'),'non_target_max_xy_m':non_target,'max_action_step_rad':metrics.get('max_action_step_rad'),'note':'Auxiliary diagnostics do not replace unchanged formal success gate.'}
            rows.append(row);buckets[(task,distance)].append(row)
            if distribution=='spatial' and task!='wait_no_package':geometry[layouts[lid]['geometry_group']].append(row)
        for (task,distance),rs in sorted(buckets.items()):
            summary.append({'distribution':distribution,'task':task,'distance':distance,'total':len(rs),'ordinary':sum(r['ordinary_passed'] for r in rs),'spatial':sum(r['spatial_passed'] for r in rs),'wins':sum(r['spatial_passed'] and not r['ordinary_passed'] for r in rs),'losses':sum(r['ordinary_passed'] and not r['spatial_passed'] for r in rs)})
        for item in summary:
            if item['distribution']!=distribution:continue
            rs=buckets[(item['task'],item['distance'])]
            for label in ['ordinary','spatial']:
                values=[r[label+'_diagnostics'] for r in rs]
                item[label+'_non_target_violations']=sum(v['non_target_max_xy_m'] is not None and v['non_target_max_xy_m']>.015 for v in values)
                item[label+'_target_progress_ge_15cm']=sum(v['target_progress_m'] is not None and v['target_progress_m']>=.15 for v in values) if item['task'] in TASKS else None
        for name,rs in sorted(geometry.items()):whole_groups.append({'geometry_group':name,'trials':len(rs),'ordinary_passed':sum(r['ordinary_passed'] for r in rs),'spatial_passed':sum(r['spatial_passed'] for r in rs),'ordinary_all_passed':all(r['ordinary_passed'] for r in rs),'spatial_all_passed':all(r['spatial_passed'] for r in rs)})
    result={'summary':summary,'whole_geometry_groups':whole_groups,'rows':rows,'visual_review':'required separately; not inferred from numbers','goal_complete':False,'note':'Paired trials use the same geometry/inference seed. Repeated seeds and four tasks/assignments within a geometry are correlated, not independent environments. Small constrained-layout comparison does not establish arbitrary-placement generalization.'}
    dest=root/'NUMERIC_COMPARISON.json'
    if dest.exists():raise FileExistsError(dest)
    dest.write_text(json.dumps(result,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
