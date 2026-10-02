"""Run declared separate supplements after each ORIGINAL episode audit completes.
Original failed results never change. Only mapped failures receive full new audits;
unknown failures stay unresolved. No retry, data admission, or result replacement.
"""
from pathlib import Path
import sys,json,hashlib,datetime,os,time
W=Path(__file__).resolve().parent
from rear_latched_run_contract_v2 import run_audit,REPORTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();R=Path(sys.argv[1]).resolve();dest=R/'AUDIT_SUPPLEMENT_V2_STATUS.json';assert not dest.exists();prep=json.loads((W/'REAR_LATCHED_AUDIT_SUPPLEMENTS_V2_PREPARATION.json').read_text());mapping={k+'.py':v+'.py' for k,v in prep['mapping'].items()};done=[];rows=[];unresolved=[]
frozen={str(W/'REAR_LATCHED_AUDIT_SUPPLEMENTS_V2_PREPARATION.json'):sha(W/'REAR_LATCHED_AUDIT_SUPPLEMENTS_V2_PREPARATION.json'),str(Path(__file__)):sha(__file__)}
for entry in prep['files']:
 for field,hfield in [('parent','parent_sha256'),('output','output_sha256')]:frozen[str(W/(entry[field]+'.py'))]=entry[hfield]
for name in ['audit_rear_corridor_latched_native_v2.py','audit_rear_corridor_latched_records_v2.py','REAR_LATCHED_AUDIT_EQUALITY_V2_PREPARATION.json']:frozen[str(W/name)]=sha(W/name)
protocol=json.loads((R/'PROTOCOL.json').read_text())
def bound():
 for p,h in {**protocol['frozen_files_sha256'],**frozen}.items():assert sha(p)==h,p

def save(status,**kwargs):
 tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,completed_episodes=done,rows=rows,unmapped_failures=unresolved,frozen_sha256=frozen,training_ready=False,**kwargs),indent=2));tmp.replace(dest)
try:
 save('running')
 while True:
  bound()
  for item in protocol['plan']['commands']:
   for task in item['tasks']:
    ep=R/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}";p=ep/'AUDIT_EXECUTION.json'
    if ep.name in done or not p.exists():continue
    old=json.loads(p.read_text())
    if not old['completed']:continue
    oldhash=sha(p);results=[]
    for original in old['rows']:
     if original['returncode']==0:continue
     name=mapping.get(original['script'])
     if name is None:unresolved.append(dict(episode=ep.name,script=original['script']));continue
     bound();save('running',current_episode=ep.name,current_auditor=name)
     output,keys=REPORTS[name];existing=ep/output
     if existing.exists():
      # The only pre-existing supplement is the explicitly run native V2 audit.
      assert name=='audit_rear_corridor_latched_native_v2.py';d=json.loads(existing.read_text());assert d['auditor_sha256']==sha(W/name) and d['passed'] is True and d['file_sha256']['raw.npz']==sha(ep/'raw.npz')
      row=dict(episode=ep.name,script=name,process_returncode=0,returncode=0,report_passed=True,report=output,report_sha256=sha(existing),raw_sha256=sha(ep/'raw.npz'),auditor_sha256=sha(W/name),log_sha256=sha(ep/(name+'.log')),reused_explicit_completed_native_audit=True)
     else:row=run_audit(ep,name)
     row.update(original_script=original['script'],original_returncode=original['returncode'],original_execution_sha256=oldhash);results.append(row);rows.append(row);assert sha(p)==oldhash
     print(json.dumps(row),flush=True)
    assert sha(p)==oldhash
    out=ep/'AUDIT_SUPPLEMENT_V2_EXECUTION.json';assert not out.exists();out.write_text(json.dumps(dict(completed=True,original_execution_sha256=oldhash,rows=results,original_failures_preserved=True,training_ready=False),indent=2));done.append(ep.name);save('running')
  if len(done)==10:save('complete');break
  main=json.loads((R/'AUDIT_STATUS.json').read_text());proc=Path('/proc')/str(main['pid']);active=proc.exists() and (proc/'stat').read_text().split()[2]!='Z'
  if not active and main['status'] not in ['running','complete']:save('incomplete',original_auditor_status=main['status']);break
  if not active and main['status']=='running':save('incomplete',original_auditor_status='missing_with_stale_running');break
  time.sleep(5)
except BaseException as e:save('failed',error=repr(e));raise
