"""Run the separate complete region audit chain after each original push audit.
Retain original failures; no task, controls, images, or training waiver is granted.
"""
from pathlib import Path
import sys,json,hashlib,os,datetime,time,subprocess,traceback
from close_closed_peak_trials import live
W=Path(__file__).resolve().parent;R=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
SUFFIXES=['ACTION_AUDIT','CAUSAL_AUDIT','CONTINUITY_V2_AUDIT','BOUNDS_V2_AUDIT','REAR_XY_V2_AUDIT'];NAMES=['FRONT_INITIAL_REGION_SUPPLEMENT_'+s+'.json' for s in SUFFIXES]
protocol=json.loads((R/'PROTOCOL.json').read_text());prep=json.loads((W/'FRONT_INITIAL_REGION_SUPPLEMENT_PREPARATION.json').read_text());frozen=dict(protocol['frozen_files_sha256'])
for row in prep['adapters']:
 assert sha(row['parent'])==row['parent_sha256'];original=Path(row['parent']).read_text()
 for a,b in row['replacements']:original=original.replace(a,b)
 assert original==Path(row['path']).read_text();frozen[row['path']]=row['sha256']
for p in [Path(__file__),W/'FRONT_INITIAL_REGION_SUPPLEMENT_PREPARATION.json',R/'PROTOCOL.json',R/'REGION_SUPPLEMENT_SEED_EXECUTION.json']:frozen[str(p)]=sha(p)
with (R/'REGION_SUPPLEMENT_PROTOCOL.json').open('x') as f:json.dump(dict(frozen_sha256=frozen,pid=os.getpid(),scope=__doc__,training_ready=False),f,indent=2)
records=[]
def save(status,**kw):
 p=R/'REGION_SUPPLEMENT_STATUS.json';t=p.with_suffix('.tmp');t.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),rows=records,training_ready=False,**kw),indent=2));t.replace(p)
def bound(mapping):
 for p,h in mapping.items():assert sha(p)==h,p
def inspect_reports(ep):
 out={}
 for name in NAMES:
  p=ep/name;r=json.loads(p.read_text());assert r['passed'] is True,(name,r.get('errors'))
  if 'raw_sha256' in r:assert r['raw_sha256']==sha(ep/'raw.npz')
  if 'source_sha256' in r:bound({str(ep/k):v for k,v in r['source_sha256'].items()})
  out[name]=sha(p)
 return out
try:
 save('running')
 while True:
  bound(frozen)
  for case in protocol['plan']['commands']:
   if case['wait']:continue
   for task in case['tasks']:
    ep=R/f"case_{case['layout_id']}"/f"layout_{case['layout_id']}_{task}";execution=ep/'AUDIT_EXECUTION.json'
    if any(r['episode']==ep.name for r in records) or not execution.exists():continue
    original=json.loads(execution.read_text())
    if not original['completed']:continue
    rec=dict(episode=ep.name,original_execution_sha256=sha(execution),original_failed_audits=[r['script'] for r in original['rows'] if r['returncode']],training_ready=False)
    save('running',current_episode=ep.name)
    try:
     seed=json.loads((R/'REGION_SUPPLEMENT_SEED_EXECUTION.json').read_text())
     if seed['episode']==ep.name:
      bound(seed['source_sha256']);reports=inspect_reports(ep);assert reports==seed['reports'];rec['execution_origin']=seed['execution_origin']
     else:
      log=ep/'FRONT_INITIAL_REGION_SUPPLEMENT_EXECUTION.log';assert not log.exists()
      with log.open('x') as f:proc=subprocess.run([sys.executable,str(W/'audit_front_initial_region_rear_xy_supplement.py'),str(ep)],cwd=W.parents[1],stdout=f,stderr=subprocess.STDOUT)
      rec.update(process_returncode=proc.returncode,log_sha256=sha(log),execution_origin='complete_separate_subprocess_chain');assert proc.returncode==0,'supplement process failed; see retained log';reports=inspect_reports(ep)
     rec.update(passed=True,reports=reports,error=None)
    except Exception as e:
     rec.update(passed=False,error=repr(e));(ep/'FRONT_INITIAL_REGION_SUPPLEMENT_FAILURE.log').write_text(traceback.format_exc())
    assert sha(execution)==rec['original_execution_sha256'];records.append(rec);save('running');print(json.dumps(rec),flush=True)
  if len(records)==8:save('complete');break
  state=json.loads((R/'STATUS.json').read_text());audit=json.loads((R/'AUDIT_STATUS.json').read_text())
  if state['status']=='runtime_or_audit_failed' or audit['status'] in ('auditor_failed','incomplete') or (not live(audit['pid'],'watch_front_initial_physical_audits.py') and audit['status']!='complete'):
   save('incomplete',producer_status=state['status'],original_auditor_status=audit['status']);break
  time.sleep(10)
except Exception as e:save('failed',error=repr(e));raise
