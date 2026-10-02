"""Audit one complete fresh category-swap+wait group without approving data.
Can audit finished groups while later groups run. Binds per-episode reports,
not mutable global watcher files. Actual visual review is required, never made up.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W.parents[1]))
from closed_peak_trial_run_contract import primary,controls,ADDITIONAL,REPORTS
from closed_peak_trial_data_audit import audit_waist_pilot_episode
from simfoundry.data.schema import load_episode
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def audit(run,group):
 run=Path(run).resolve();protocol=json.loads((run/'PROTOCOL.json').read_text());commands=[c for c in protocol['commands'] if c['group_name']==group]
 if len(commands)!=3 or sum(len(c['tasks']) for c in commands)!=5 or sum(c['wait'] for c in commands)!=1:raise ValueError('Not an exact registered4push+wait group')
 expected={f"layout_{c['layout_id']}_{t}" for c in commands for t in c['tasks']};ctrl=json.loads((run/'CONTROL_EVIDENCE_EXECUTION.json').read_text());extra=json.loads((run/'ADDITIONAL_AUDIT_EXECUTION.json').read_text());completed=set(ctrl['completed_episodes'])&set(extra['completed_episodes']);pushes={f"layout_{c['layout_id']}_{t}" for c in commands if not c['wait'] for t in c['tasks']}
 if not pushes<=completed:return dict(status='pending_control_audits',group=group,missing=sorted(pushes-completed),training_ready=False)
 contract_path=Path(commands[0]['contract_path']);digest=sha(contract_path)
 assert all(c['contract_sha256']==digest and c['contract_path']==str(contract_path) for c in commands)
 contract=json.loads(contract_path.read_text());assert len(contract['layouts'])==2 and len(contract['wait_layouts'])==1
 for p,h in protocol['frozen_files_sha256'].items():assert sha(p)==h,p
 evidence={};rows=[]
 def read(path):
  d=json.loads(path.read_text());evidence[str(path)]=sha(path);return d
 def invocation(ep,row):
  script=row['script'];name,keys=REPORTS[script]
  assert row['auditor_sha256']==sha(W/script) and row['raw_sha256']==sha(ep/'raw.npz')
  assert row['log_sha256']==sha(ep/(script+'.log')) and row['report']==name
  if row['report_sha256'] is None:
   assert not (ep/name).exists() and row['returncode']!=0;return False
  assert row['report_sha256']==sha(ep/name);d=read(ep/name)
  for p,h in d.get('source_sha256',{}).items():assert sha(ep/p)==h,(script,p)
  value=d
  for key in keys:value=value[key]
  assert row['report_passed']==(value is True)
  assert row['returncode']==(row['process_returncode'] if row['process_returncode'] else (0 if value is True else 1))
  return row['returncode']==0
 for c in commands:
  case=run/f"case_{c['layout_id']}";prov=read(case/'provenance.json');assert sha(case/'waist_pilot_contract.json')==digest
  for task in c['tasks']:
   ep=case/f"layout_{c['layout_id']}_{task}";wait=c['wait'];needed=['PRIMARY_AUDIT_EXECUTION.json','OBSERVATION_AUDIT_EXECUTION.json','PRESSURE_AUDIT_EXECUTION.json','ACTUAL_REVIEW_BINDING.json']
   missing=[n for n in needed if not (ep/n).exists()]
   if missing:return dict(status='pending_episode_evidence',group=group,episode=ep.name,missing=missing,training_ready=False)
   main=read(ep/'PRIMARY_AUDIT_EXECUTION.json');observer=read(ep/'OBSERVATION_AUDIT_EXECUTION.json');pressure=read(ep/'PRESSURE_AUDIT_EXECUTION.json')
   assert main['completed'] and [x['script'] for x in main['rows']]==primary(wait)
   assert observer['completed'] and [x['script'] for x in observer['rows']]==['audit_closed_peak_trial_contacts.py']
   assert pressure['completed'] and [x['script'] for x in pressure['rows']]==['audit_closed_peak_trial_pressure.py']
   invocations=main['rows']+observer['rows']+pressure['rows']
   if not wait:
    plan=read(ep/'frontal_bypass.json')['plan'];cr=[x for x in ctrl['rows'] if x['episode']==ep.name];er=[x for x in extra['rows'] if x['episode']==ep.name]
    assert [x['script'] for x in cr]==controls(plan) and [x['script'] for x in er]==ADDITIONAL;invocations+=cr+er
   checks=[invocation(ep,x) for x in invocations]
   quality=read(ep/'quality.json');visual=read(ep/'ACTUAL_REVIEW_BINDING.json');n=quality['frames']
   assert visual['raw_sha256']==sha(ep/'raw.npz') and visual['sampled_rgb_frames']==np.linspace(0,n-1,8,dtype=int).tolist()
   if wait:
    assert visual['actual_visual_review']=='completed_actual_view_8RGB' and visual['review_sheet_sha256']==sha(ep/'REVIEW_EVENTS.jpg')
   else:
    assert visual['actual_sampled_visual_review']=='completed' and visual['review_sheet_sha256']==sha(ep/'REVIEW_EVEN.jpg')
    assert len(visual['sampled_viewer_frames'])==4
    for name,h in visual['external_source_sha256'].items():assert sha(case/('viewer_'+ep.name)/name)==h
   episode=load_episode(ep/'raw.npz')
   try:fresh=dict(passed=True,report=audit_waist_pilot_episode(ep/'raw.npz',episode,prov))
   except ValueError as e:fresh=dict(passed=False,error=str(e))
   rows.append(dict(episode=ep.name,wait=wait,frames=n,requested_frames=70 if wait else 1200,quality_passed=quality['passed'],fresh_source_numeric_pose=fresh,all_control_audits_passed=all(checks),failed_audits=[x['script'] for x,ok in zip(invocations,checks) if not ok],audit_invocations=invocations,visual=visual,training_ready=False))
   del episode
 assert {r['episode'] for r in rows}==expected
 eligible=all(r['fresh_source_numeric_pose']['passed'] and r['all_control_audits_passed'] and r['frames']==r['requested_frames'] for r in rows)
 result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),group=group,status='complete_group_audited',full_group_checks_passed=eligible,push_passed=sum(r['fresh_source_numeric_pose']['passed'] for r in rows if not r['wait']),push_total=4,wait_passed=all(r['fresh_source_numeric_pose']['passed'] for r in rows if r['wait']),rows=rows,evidence_sha256=evidence,contract_sha256=digest,planned_split=contract['layouts'][0]['planned_split'],admitted=False,training_ready=False,reason='Ready for unchanged converter whole-group/pair/split checks and explicit source review binding.' if eligible else 'Entire complete group remains quarantined: original source/task/pose/wait/control failure.',auditor_sha256=sha(__file__))
 out=run/'GROUP_REVIEWS';out.mkdir(exist_ok=True)
 with (out/(group+'.json')).open('x') as f:json.dump(result,f,indent=2)
 return {k:v for k,v in result.items() if k not in ['rows','evidence_sha256']}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('group');a=p.parse_args();print(json.dumps(audit(a.run,a.group),indent=2))
