"""Compare completed task ablation with the current-runtime three-way controls."""
from pathlib import Path
import argparse,json
p=argparse.ArgumentParser();p.add_argument('--experiment',type=Path,required=True);p.add_argument('--controls',type=Path,required=True);args=p.parse_args()
reports={v:json.loads((args.controls/f'EVALUATION_{v}.json').read_text()) for v in ['baseline','ordinary','recovery']}
reports['waitonly']=json.loads((args.experiment/'EVALUATION_waitonly.json').read_text())
def key(r):return r['seed'],r['layout_id'],r['task']
index={v:{key(r):r for r in d['rows']} for v,d in reports.items()};assert all(len(d)==21 and set(d)==set(index['ordinary']) for d in index.values())
summary=[]
for task in sorted({k[2] for k in index['ordinary']}):
 keys=[k for k in index['ordinary'] if k[2]==task];s={'task':task,'n':len(keys)}
 for v in index:s[v]=sum(index[v][k]['passed'] for k in keys)
 for v in ['ordinary','recovery']:
  s[f'waitonly_vs_{v}_wins']=sum(index['waitonly'][k]['passed'] and not index[v][k]['passed'] for k in keys)
  s[f'waitonly_vs_{v}_losses']=sum(index[v][k]['passed'] and not index['waitonly'][k]['passed'] for k in keys)
 summary.append(s)
counts={s['task']:s['waitonly'] for s in summary};total=sum(counts.values());screen=total>10 and counts['push_box_to_bin']>=7 and counts['nudge_mailer_to_bin']>=3 and counts['wait_no_package']>=1
rows=[]
for k in sorted(index['ordinary']):
 r={'seed':k[0],'layout':k[1],'task':k[2]}
 for v in index:
  x=index[v][k];r[v]={'passed':x['passed'],'reasons':x['reasons'],'metrics':x['metrics']}
 rows.append(r)
result={'summary':summary,'strict_totals':{v:sum(x['passed'] for x in ix.values()) for v,ix in index.items()},'numerical_replication_screen_met':screen,'screen_rule':'waitonly total>10, box>=7, bag>=3, wait>=1; visual review must also complete before replication','rows':rows,'limits':'Exploratory single-training-seed task ablation; same3push layouts across3inference seeds, narrow workspace. Individual arms marginal state coverage is not full-observation coverage. Per-dataset normalization included in treatment. No reserved confirmation used.'}
(args.experiment/'COMPARISON.json').write_text(json.dumps(result,indent=2));print(json.dumps({'summary':summary,'numerical_replication_screen_met':screen},indent=2))
