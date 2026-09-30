"""Paired per-case comparison of same-protocol model regression results."""
from pathlib import Path
import argparse,json
from collections import Counter
p=argparse.ArgumentParser();p.add_argument('--experiment',type=Path,required=True);args=p.parse_args()
reports={v:json.loads((args.experiment/f'EVALUATION_{v}.json').read_text()) for v in ('baseline','ordinary','recovery')}
def key(r):return (r['seed'],r['layout_id'],r['task'])
indexed={v:{key(r):r for r in rep['rows']} for v,rep in reports.items()}
assert all(len(x)==21 for x in indexed.values()) and all(set(indexed[v])==set(indexed['baseline']) for v in indexed)
rows=[]
for k in sorted(indexed['baseline']):
 row={'seed':k[0],'layout':k[1],'task':k[2]}
 for v in indexed:
  r=indexed[v][k];m=r['metrics'];row[v]={'passed':r['passed'],'reasons':r['reasons'],'progress_m':m.get('target_final_progress_m'),'left_drift_m':m.get('left_palm_spread_m'),'right_drift_m':m.get('right_palm_spread_m'),'max_action_step_rad':m.get('max_action_step_rad')}
 rows.append(row)
summary=[]
for task in sorted({r['task'] for r in rows}):
 rs=[r for r in rows if r['task']==task]
 summary.append({'task':task,'n':len(rs),**{v:sum(r[v]['passed'] for r in rs) for v in indexed},'recovery_vs_ordinary_wins':sum(r['recovery']['passed'] and not r['ordinary']['passed'] for r in rs),'recovery_vs_ordinary_losses':sum(r['ordinary']['passed'] and not r['recovery']['passed'] for r in rs)})
result={'summary':summary,'rows':rows,'note':'One training seed per new dataset; repeated inference seeds on3push layouts. Correlated observations, not21independent environments. Regression only; reserved confirmation not used. Visual review required separately.'}
(args.experiment/'COMPARISON.json').write_text(json.dumps(result,indent=2));print(json.dumps(summary,indent=2))
