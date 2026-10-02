"""Snapshot complete fresh raw episodes for data-distribution diagnostics only.
Recomputes query phases from every raw state/action and expert row. Includes failed
members explicitly; no dataset admission, trimming, quota choice or statistics file.
"""
from pathlib import Path
import argparse,collections,datetime,json,hashlib,sys
import numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W.parents[1]))
from simfoundry.data.query_phases import episode_query_phases
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(run,out):
 run=Path(run).resolve();p=json.loads((run/'PROTOCOL.json').read_text());rows=[];missing=[];source={str(run/'PROTOCOL.json'):sha(run/'PROTOCOL.json')}
 for c in p['commands']:
  contract=json.loads(Path(c['contract_path']).read_text());layout=next(x for x in contract['layouts']+contract['wait_layouts'] if x['layout_id']==c['layout_id'])
  for task in c['tasks']:
   ep=run/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}"
   if not (ep/'quality.json').exists():missing.append(ep.name);continue
   quality=json.loads((ep/'quality.json').read_text());raw=ep/'raw.npz';control=json.loads((ep/'expert_control.json').read_text())
   with np.load(raw) as z:q=z['q'].copy();a=z['action'].copy()
   assert len(q)==quality['frames'] and q.shape==a.shape
   try:phase=episode_query_phases(task,q,a,control)
   except ValueError as exc:phase=dict(unavailable=str(exc),counts=None)
   modes=collections.Counter(x['mode'] for x in control);wait=task=='wait_no_package';n=len(q)
   row=dict(episode=ep.name,group=c['group_name'],planned_split=layout['planned_split'],family=contract['layouts'][0]['geometry_family'],task=task,frames=n,quality_passed=quality['passed'],quality_reasons=quality['reasons'],phase=phase,expert_modes=dict(modes),uniform_first3_within_push_fraction=None if wait else 3/n,old_prefix16_within_push_fraction=None if wait else 48/(n+45),waist_action_min_rad=float(a[:,12].min()),waist_action_max_rad=float(a[:,12].max()),source_admitted=False)
   rows.append(row)
   for f in [raw,ep/'quality.json',ep/'expert_control.json']:source[str(f)]=sha(f)
 total_planned_push=sum(len(c['tasks']) for c in p['commands'] if not c['wait']);total_planned_wait=sum(len(c['tasks']) for c in p['commands'] if c['wait']);assert total_planned_push==48 and total_planned_wait==12
 total=total_planned_push*1200+total_planned_wait*70
 hypothetical=dict(scope='Arithmetic scenario if all original60conditions were complete and admitted, NOT current train set; actual future train split/quota must be audited separately.',push_frames=total_planned_push*1200,wait_frames=total_planned_wait*70,uniform_wait_fraction=total_planned_wait*70/total,uniform_first3_within_push_fraction=3/1200,prefix16_first3_within_push_fraction=48/1245)
 aggregate=[]
 for task in sorted({x['task'] for x in rows}):
  selected=[x for x in rows if x['task']==task];aggregate.append(dict(task=task,collected_episodes=len(selected),quality_passed=sum(x['quality_passed'] for x in selected),phase_available=sum(x['phase']['counts'] is not None for x in selected),total_frames=sum(x['frames'] for x in selected),passed_episode_terminal_query_frames=sum(x['phase']['counts'].get('terminal',0) for x in selected if x['quality_passed'] and x['phase']['counts'] is not None)))
 source[str(Path(__file__))]=sha(__file__);source[str(W.parents[1]/'simfoundry/data/query_phases.py')]=sha(W.parents[1]/'simfoundry/data/query_phases.py')
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,aggregate=aggregate,planned_episodes=60,not_yet_complete=missing,hypothetical_full_batch_uniform_exposure=hypothetical,source_sha256=source,training_ready=False)
 with Path(out).open('x') as f:json.dump(report,f,indent=2)
 print(json.dumps(dict(episodes=len(rows),aggregate=aggregate,hypothetical=hypothetical,training_ready=False),indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--out',required=True);a=p.parse_args();main(a.run,a.out)
