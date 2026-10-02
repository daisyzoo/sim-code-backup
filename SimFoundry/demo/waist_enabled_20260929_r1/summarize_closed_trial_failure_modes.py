"""Summarize every closed-trial condition; observed failure modes, not causal proof.
Task success and independent control/admission success remain separate.
"""
from pathlib import Path
import json,sys,hashlib,collections,datetime
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def summarize(run):
 r=Path(run).resolve();result=json.loads((r/'RESULT.json').read_text());assert result['status']=='complete_trial_audited' and result['conditions']==60
 rows=[];source={str(r/'RESULT.json'):sha(r/'RESULT.json')}
 for x in result['rows']:
  ep=next(r.glob('case_*/'+x['episode']));q=json.loads((ep/'quality.json').read_text());assert q==x['quality'];entry={k:x[k] for k in ['episode','family','split','task','wait','numeric_pose_passed','controls_passed','frames','requested_frames','failed_audits']};entry['quality_reasons']=q['reasons'];entry['task_progress_m']=q['metrics'].get('target_final_progress_m');source[str(ep/'quality.json')]=sha(ep/'quality.json')
  if x['wait']:entry['observed_failure_mode']='wait_pass' if x['numeric_pose_passed'] else 'wait_failure'
  else:
   p=ep/'frontal_bypass.json';f=json.loads(p.read_text());source[str(p)]=sha(p);modes=collections.Counter(v['mode'] for v in f['rows']);stops=[v for v in f['rows'] if v.get('route_stop_reason')];tilt=lost=0
   for prev,nxt in zip(f['rows'],f['rows'][1:]):
    if prev['mode']=='top_push' and nxt['mode']!='top_push':tilt+=nxt.get('last_recontact_reason')=='incipient_tilt_independent';lost+=nxt.get('last_recontact_reason')=='lost_contact'
   entry.update(phase_counts=dict(modes),tilt_exits=tilt,lost_contact_exits=lost,first_route_stop=None if not stops else dict(step=stops[0]['step'],reason=stops[0]['route_stop_reason']),top_push_fraction=modes['top_push']/len(f['rows']))
   if x['numeric_pose_passed']:mode='task_pass'
   elif x['frames']<x['requested_frames']:mode='incomplete_guard_stop'
   elif stops:mode='latched_'+stops[0]['route_stop_reason']
   elif modes['top_push']==0 and modes['rear_push']>0:mode='rear_approach_without_top_push'
   else:mode='full_horizon_without_task_completion'
   entry['observed_failure_mode']=mode
  rows.append(entry)
 assert len(rows)==60
 groups=[]
 for family in sorted({x['family'] for x in rows}):
  for task in sorted({x['task'] for x in rows}):
   subset=[x for x in rows if x['family']==family and x['task']==task];groups.append(dict(family=family,task=task,task_passed=sum(x['numeric_pose_passed'] for x in subset),total=len(subset),control_passed=sum(x['controls_passed'] for x in subset),observed_modes=dict(collections.Counter(x['observed_failure_mode'] for x in subset))))
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,conditions=60,by_family_task=groups,observed_modes=dict(collections.Counter(x['observed_failure_mode'] for x in rows)),failures=[x for x in rows if not x['numeric_pose_passed']],rows=rows,source_sha256=source,summarizer_sha256=sha(__file__),training_ready=False)
 with (r/'FAILURE_MODE_SUMMARY.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps({k:v for k,v in out.items() if k not in ['rows','source_sha256','failures']},indent=2));return out
if __name__=='__main__':summarize(sys.argv[1])
