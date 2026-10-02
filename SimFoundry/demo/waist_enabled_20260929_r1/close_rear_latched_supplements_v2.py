"""Bind separate full audit corrections without changing original failure reports.
Task failures and complete paired-group rejections remain authoritative.
"""
from pathlib import Path
import sys,json,hashlib,datetime
W=Path(__file__).resolve().parent
from rear_latched_run_contract_v2 import REPORTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
R=Path(sys.argv[1]).resolve();dest=R/'RESULT_WITH_SUPPLEMENT_V2.json';assert not dest.exists();sources={}
def read(p):
 p=Path(p);sources[str(p)]=sha(p);return json.loads(p.read_text())
old=read(R/'RESULT.json');supp=read(R/'AUDIT_SUPPLEMENT_V2_STATUS.json');protocol=read(R/'PROTOCOL.json');prep=read(W/'REAR_LATCHED_AUDIT_SUPPLEMENTS_V2_PREPARATION.json')
assert supp['status']=='complete' and len(supp['completed_episodes'])==10
proc=Path('/proc')/str(supp['pid']);assert not proc.exists() or (proc/'stat').read_text().split()[2]=='Z'
for p,h in {**protocol['frozen_files_sha256'],**supp['frozen_sha256'],**old['source_sha256']}.items():assert sha(p)==h,p
mapping={k+'.py':v+'.py' for k,v in prep['mapping'].items()};resolved=[];unresolved=[];all_rows=[];expected=[]
for item in protocol['plan']['commands']:
 for task in item['tasks']:
  ep=R/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}";original=read(ep/'AUDIT_EXECUTION.json');extra=read(ep/'AUDIT_SUPPLEMENT_V2_EXECUTION.json')
  assert extra['completed'] and extra['original_failures_preserved'] and extra['original_execution_sha256']==sha(ep/'AUDIT_EXECUTION.json')
  failed=[x for x in original['rows'] if x['returncode']!=0];by={x['original_script']:x for x in extra['rows']};assert len(by)==len(extra['rows'])
  assert set(by)=={x['script'] for x in failed if x['script'] in mapping}
  for f in failed:
   key=dict(episode=ep.name,script=f['script']);expected.append(key)
   if f['script'] not in by:unresolved.append(dict(key,reason='unmapped'));continue
   x=by[f['script']];assert x['original_returncode']==f['returncode'] and x['original_execution_sha256']==sha(ep/'AUDIT_EXECUTION.json') and x['script']==mapping[f['script']]
   assert x['raw_sha256']==sha(ep/'raw.npz') and x['auditor_sha256']==sha(W/x['script']) and x['log_sha256']==sha(ep/(x['script']+'.log'))
   name,keys=REPORTS[x['script']]
   if x['report_sha256'] is not None:assert x['report_sha256']==sha(ep/name)
   if x['returncode']==0 and x['report_passed']:
    d=read(ep/name)
    for k in keys:d=d[k]
    assert d is True;resolved.append(dict(key,supplement=x['script'],report=name,report_sha256=x['report_sha256']))
   else:unresolved.append(dict(key,reason='supplement_failed',supplement=x['script']))
  all_rows.extend(extra['rows'])
assert all_rows==supp['rows']
assert sorted((x['episode'],x['script']) for x in expected)==sorted((x['episode'],x['script']) for x in old['failed_audit_invocations'])
groups=[]
for g in old['groups']:
 group=dict(g);group['all_task_and_control_passed_after_supplements']=g['push_passed']==g['push_total'] and g['wait_passed'] and not any(x['episode'] in {v['episode'] for v in old['rows'] if v['group']==g['group']} for x in unresolved);group['training_admitted']=False;groups.append(group)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='diagnostic_closed_original_failures_preserved',conditions=old['conditions'],push_passed=old['push_passed'],push_total=old['push_total'],wait_passed=old['wait_passed'],wait_total=old['wait_total'],baseline_push_passed=old['baseline_push_passed'],groups=groups,original_audit_invocations=old['audit_invocations'],original_failed_audit_count=len(expected),supplement_invocations=len(all_rows),resolved_audit_failures=resolved,unresolved_audit_failures=unresolved,source_sha256=sources,closer_sha256=sha(__file__),training_ready=False,model_goal_achieved=False,interpretation='Separate audit correction does not repair task failures or admit partial paired groups.')
with dest.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','resolved_audit_failures']},indent=2))
