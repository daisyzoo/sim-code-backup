"""Separate active/inactive arm coverage; marginal distances are not full-state coverage."""
from pathlib import Path
import argparse,json
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--experiment',type=Path,required=True);p.add_argument('--variants',nargs='+',default=['baseline','ordinary','recovery']);args=p.parse_args()
WS=Path(__file__).resolve().parents[2];banks={}
for v,folder in [('baseline','lerobot_sim_paired_zero_pilot32_b_20260924'),('ordinary','lerobot_sim_paired_ordinary_pilot40_20260928'),('recovery','lerobot_sim_paired_recovery_pilot40_20260928')]:
 root=WS/'lerobot'/folder/'meta';recs=json.loads((root/'paired_provenance.json').read_text())['records'];split=json.loads((root/'train_validation_split.json').read_text())['train'];bank={}
 for idx in split:
  r=recs[idx]
  with np.load(WS/r['path']) as d:bank.setdefault(r['task_id'],[]).append(d['q'][:,13:23])
 banks[v]={t:np.concatenate(q) for t,q in bank.items()}
def nearest(q,b):return np.concatenate([abs(q[i:i+16,None]-b[None]).max(2).min(1) for i in range(0,len(q),16)])
rows=[]
for v in args.variants:
 for f in sorted(args.experiment.glob(f'{v}_seed*/rollouts/layout_*')):
  if not (f/'quality.json').exists():continue
  with np.load(f/'raw.npz') as d:q=d['q'][:,13:23];task=str(d['task_id'])
  quality=json.loads((f/'quality.json').read_text());row={'variant':v,'path':str(f),'task':task,'passed':quality['passed'],'marginal_arm_distance_rad':{}}
  for bv,b in banks.items():
   arms={}
   for side,sl in [('left',slice(0,5)),('right',slice(5,10))]:
    d=nearest(q[:,sl],b[task][:,sl]);arms[side]={name:{'median':float(np.median(d[a:z])),'max':float(d[a:z].max())} for name,a,z in [('first10',0,10),('transition10_30',10,30),('main30_100',30,min(101,len(q))),('all',0,len(q))]}
   row['marginal_arm_distance_rad'][bv]=arms
  rows.append(row)
result={'method':'Nearest five-joint physical state per arm, same task and training split only. Each arm can match a different reference frame, so low marginal distances do not imply full-state or image coverage. Fixed frame windows are descriptive, not matched contact phases.','rows':rows}
output=args.experiment/('ARM_COVERAGE_'+'-'.join(args.variants)+'.json');output.write_text(json.dumps(result,indent=2));print(output)
for v in args.variants:
 for t in banks['baseline']:
  rr=[r for r in rows if r['variant']==v and r['task']==t]
  if rr:print(v,t,'median nearest own-bank main phase L/R', [round(float(np.median([r['marginal_arm_distance_rad'][v][s]['main30_100']['median'] for r in rr])),5) for s in ('left','right')])
