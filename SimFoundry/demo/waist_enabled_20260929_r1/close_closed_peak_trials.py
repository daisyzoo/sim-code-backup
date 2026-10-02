"""Close the original twelve-group fresh trial only after terminal execution.
Summarize all sixty conditions, including failures. Never grant training approval.
"""
from pathlib import Path
import argparse, collections, datetime, hashlib, json
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def live(pid, script):
 p=Path('/proc')/str(pid)
 try:
  state=(p/'stat').read_text().rsplit(')',1)[1].split()[0]
  cmd=(p/'cmdline').read_bytes().decode().replace('\0',' ')
 except FileNotFoundError:return False
 return state not in ('Z','X') and script in cmd

def close(run,apply=False):
 r=Path(run).resolve();protocol=json.loads((r/'PROTOCOL.json').read_text());commands=protocol['commands'];launch=json.loads((r/'LAUNCH.json').read_text());status=json.loads((r/'STATUS.json').read_text())
 assert launch['protocol_sha256']==sha(r/'PROTOCOL.json')
 groups=list(dict.fromkeys(c['group_name'] for c in commands))
 expected={(c['layout_id'],task) for c in commands for task in c['tasks']}
 assert len(commands)==36 and len(groups)==12 and len(expected)==60 and sum(c['wait'] for c in commands)==12
 running=[j for j in launch['jobs'] if live(j['pid'],j['script'])]
 if status.get('collector_pid') and live(status['collector_pid'],protocol['collector']):running.append(dict(pid=status['collector_pid'],script=protocol['collector']))
 if running:return dict(status='pending_live_jobs',jobs=running,training_ready=False)
 if status['status']!='collection_complete_audits_visual_pending':return dict(status='not_complete',execution_status=status,training_ready=False)
 assert status['completed_conditions']==60 and status['total_conditions']==60
 evidence={}
 def read(p):
  d=json.loads(p.read_text());evidence[str(p)]=sha(p);return d
 for path,h in protocol['frozen_files_sha256'].items():assert sha(path)==h,path
 records=read(r/'COLLECTION_EXECUTION.json');assert len(records)==60 and {(x['layout_id'],x['task']) for x in records}==expected
 control=read(r/'CONTROL_EVIDENCE_EXECUTION.json');extra=read(r/'ADDITIONAL_AUDIT_EXECUTION.json')
 pushes={f"layout_{c['layout_id']}_{task}" for c in commands if not c['wait'] for task in c['tasks']}
 for d in [control,extra]:assert d['stage']=='complete' and set(d['completed_episodes'])==pushes and len(d['completed_episodes'])==48
 missing=[g for g in groups if not (r/'GROUP_REVIEWS'/f'{g}.json').exists()]
 if missing:return dict(status='pending_complete_group_reviews',groups=missing,training_ready=False)
 if not (r/'PRESSURE_SETTING_BINDING.json').exists():return dict(status='pending_pressure_setting_binding',training_ready=False)
 binding=read(r/'PRESSURE_SETTING_BINDING.json');assert binding['passed'] and binding['protocol_sha256']==sha(r/'PROTOCOL.json') and binding['script_sha256']==sha(W/'verify_closed_peak_trial_pressure_setting.py')
 assert len(binding['rows'])==60 and {x['episode'] for x in binding['rows']}=={f'layout_{i}_{t}' for i,t in expected}
 for row in binding['rows']:
  assert row['passed'] and row['expected_top_load_n']==row['actual_cli_top_load_n']==5
  for path,h in row['source_sha256'].items():assert sha(path)==h,path
 summaries=[];allrows=[];families=collections.Counter();splits=collections.Counter();count=collections.Counter()
 for group in groups:
  g=read(r/'GROUP_REVIEWS'/f'{group}.json');cmds=[c for c in commands if c['group_name']==group];contract=read(Path(cmds[0]['contract_path']));family=contract['layouts'][0]['geometry_family'];split=contract['layouts'][0]['planned_split'];families[family]+=1;splits[split]+=1
  assert len(cmds)==3 and g['status']=='complete_group_audited' and g['group']==group and g['auditor_sha256']==sha(W/'audit_closed_peak_trial_group.py')
  assert g['contract_sha256']==sha(Path(cmds[0]['contract_path'])) and g['planned_split']==split
  for path,h in g['evidence_sha256'].items():assert sha(path)==h,path
  expected_group={f"layout_{c['layout_id']}_{t}" for c in cmds for t in c['tasks']};assert len(g['rows'])==5 and {x['episode'] for x in g['rows']}==expected_group
  for c in cmds:
   for task in c['tasks']:
    ep=r/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}";row=next(x for x in g['rows'] if x['episode']==ep.name);q=read(ep/'quality.json');rawhash=sha(ep/'raw.npz');assert row['quality_passed']==q['passed'] and row['frames']==q['frames'] and row['visual']['raw_sha256']==rawhash
    record=next(x for x in records if (x['layout_id'],x['task'])==(c['layout_id'],task));assert record['quality']==q and record['executed_frames']==row['frames'] and record['requested_frames']==row['requested_frames']
    current=[]
    for name,kind in [('PRIMARY_AUDIT_EXECUTION.json','primary'),('OBSERVATION_AUDIT_EXECUTION.json','observer'),('PRESSURE_AUDIT_EXECUTION.json','pressure')]:
     d=read(ep/name);assert d['completed'];current+=d['rows'];count[kind]+=len(d['rows'])
    if not c['wait']:
     for d,kind in [(control,'control'),(extra,'additional')]:
      selected=[x for x in d['rows'] if x['episode']==ep.name];current+=selected;count[kind]+=len(selected)
    assert current==row['audit_invocations']
    for inv in current:
     assert inv['raw_sha256']==rawhash and inv['auditor_sha256']==sha(W/inv['script']) and inv['log_sha256']==sha(ep/(inv['script']+'.log'))
     if inv['report_sha256'] is not None:assert inv['report_sha256']==sha(ep/inv['report'])
     else:assert not (ep/inv['report']).exists() and inv['returncode']!=0
    v=row['visual'];sheet=ep/('REVIEW_EVENTS.jpg' if c['wait'] else 'REVIEW_EVEN.jpg');assert v['review_sheet_sha256']==sha(sheet)
    for name,h in v.get('external_source_sha256',{}).items():assert sha(ep.parent/('viewer_'+ep.name)/name)==h
    allrows.append(dict(group=group,family=family,split=split,task=task,episode=ep.name,wait=c['wait'],numeric_pose_passed=row['fresh_source_numeric_pose']['passed'],controls_passed=row['all_control_audits_passed'],frames=row['frames'],requested_frames=row['requested_frames'],quality=q,visual_observations=v.get('observations',v.get('finding','')),failed_audits=row['failed_audits']))
  passed=all(x['fresh_source_numeric_pose']['passed'] and x['all_control_audits_passed'] and x['frames']==x['requested_frames'] for x in g['rows']);assert passed==g['full_group_checks_passed']
  summaries.append(dict(group=group,family=family,split=split,complete_group_passed=passed,push_passed=g['push_passed'],push_total=4,wait_passed=g['wait_passed'],admitted=False))
 assert len(families)==4 and set(families.values())=={3} and splits==dict(train=8,validation=4)
 assert count['primary']==216 and count['observer']==60 and count['pressure']==60 and count['additional']==336
 assert count['control']==len(control['rows']) and count['additional']==len(extra['rows'])
 by_family_task=[]
 for family in families:
  for task in sorted({x['task'] for x in allrows}):
   subset=[x for x in allrows if x['family']==family and x['task']==task]
   by_family_task.append(dict(family=family,task=task,passed=sum(x['numeric_pose_passed'] for x in subset),total=len(subset),control_failed=sum(not x['controls_passed'] for x in subset)))
 result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='complete_trial_audited',protocol_sha256=sha(r/'PROTOCOL.json'),conditions=60,push_passed=sum(x['numeric_pose_passed'] for x in allrows if not x['wait']),push_total=48,wait_passed=sum(x['numeric_pose_passed'] for x in allrows if x['wait']),wait_total=12,complete_groups_passed=sum(x['complete_group_passed'] for x in summaries),groups=summaries,by_family_task=by_family_task,rows=allrows,audit_counts=dict(count),evidence_sha256=evidence,closer_sha256=sha(__file__),training_ready=False,model_goal_achieved=False,scope=__doc__)
 if apply:
  with (r/'RESULT.json').open('x') as f:json.dump(result,f,indent=2)
 return {k:v for k,v in result.items() if k not in ['rows','evidence_sha256']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--apply',action='store_true');a=p.parse_args();print(json.dumps(close(a.run,a.apply),indent=2))
