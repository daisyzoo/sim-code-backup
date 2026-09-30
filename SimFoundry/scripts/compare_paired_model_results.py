#!/usr/bin/env python3
"""Strict matched60 comparison; model prefixes explicit, quality gates unchanged."""
import argparse,json
from pathlib import Path
from collections import defaultdict
from compare_spatial_evaluations import indexed,TASKS

def main():
 p=argparse.ArgumentParser()
 for n in ['baseline-root','candidate-root','protocol','out']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--baseline-prefix',required=True);p.add_argument('--candidate-prefix',required=True);a=p.parse_args()
 if a.out.exists():raise FileExistsError(a.out)
 protocol=json.loads(a.protocol.read_text());layouts={}
 for f in protocol['layout_files']:
  row=json.loads(Path(f['path']).read_text());layouts[row['layout_id']]=row
 rows=[];buckets=defaultdict(list)
 for distribution in ['spatial','original']:
  ids=layouts if distribution=='spatial' else [100,101,102];wait=protocol['wait_layout_id'] if distribution=='spatial' else 20000
  keys={(s,l,t) for s in protocol['eval_seeds'] for l in ids for t in TASKS}|{(s,wait,'wait_no_package') for s in protocol['eval_seeds']}
  old=indexed(a.baseline_root/f'EVALUATION_{a.baseline_prefix}_{distribution}.json',keys)
  new=indexed(a.candidate_root/f'EVALUATION_{a.candidate_prefix}_{distribution}.json',keys)
  for key in sorted(keys):
   seed,lid,task=key;distance='wait' if task=='wait_no_package' else ('original' if distribution=='original' else ('far' if layouts[lid]['box_xyz' if task=='push_box_to_bin' else 'mailer_xyz'][0]>=.48 else 'near'))
   row={'distribution':distribution,'seed':seed,'layout_id':lid,'task':task,'distance':distance,'baseline':old[key],'candidate':new[key]};rows.append(row);buckets[(distribution,task,distance)].append(row)
 assert len(rows)==60
 summary=[]
 for (distribution,task,distance),rs in sorted(buckets.items()):
  summary.append({'distribution':distribution,'task':task,'distance':distance,'total':len(rs),'baseline_passed':sum(x['baseline']['passed'] for x in rs),'candidate_passed':sum(x['candidate']['passed'] for x in rs),'wins':sum(x['candidate']['passed'] and not x['baseline']['passed'] for x in rs),'losses':sum(x['baseline']['passed'] and not x['candidate']['passed'] for x in rs)})
 totals={'total':len(rows),'baseline_passed':sum(x['baseline']['passed'] for x in rows),'candidate_passed':sum(x['candidate']['passed'] for x in rows)}
 out={'baseline':str(a.baseline_root.resolve()),'baseline_prefix':a.baseline_prefix,'candidate':str(a.candidate_root.resolve()),'candidate_prefix':a.candidate_prefix,'totals':totals,'summary':summary,'rows':rows,'visual_review':'required separately','limitations':'Strict same60 geometry/task/noise-seed keys on reused development benchmarks; not final independent generalization, not proof of causal effect without matching training protocol. Quality results remain unchanged; require actual visual review.','goal_complete':False}
 a.out.write_text(json.dumps(out,indent=2));print(json.dumps(totals))
if __name__=='__main__':main()
