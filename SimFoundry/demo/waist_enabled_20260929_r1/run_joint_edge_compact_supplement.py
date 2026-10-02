"""Run all transitively affected audits as separate supplemental v2 evidence.
Original audit failures and task failures are retained; no training admission.
"""
from pathlib import Path
import json,os,sys,hashlib,subprocess,datetime
W=Path(__file__).resolve().parent
from joint_edge_stage_run_contract import primary,controls,ADDITIONAL,REPORTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ep=Path(sys.argv[1]).resolve();dest=ep.parent.parent/'COMPACT_V2_AUDIT_STATUS.json';assert not dest.exists();prep=json.loads((W/'JOINT_EDGE_COMPACT_DEPENDENT_AUDITS_PREPARATION.json').read_text());mapping=prep['module_mapping'];reports=prep['report_mapping'];plan=json.loads((ep/'frontal_bypass.json').read_text())['plan'];scripts=list(dict.fromkeys(primary(False)+['audit_joint_edge_stage_contacts.py','audit_joint_edge_stage_pressure.py']+controls(plan)+ADDITIONAL));scripts=[s for s in scripts if s[:-3] in mapping];rows=[]
frozen={str(W/'audit_compact_scene_rejection.py'):sha(W/'audit_compact_scene_rejection.py'),str(W/'audit_joint_edge_stage_pose_live_v2.py'):sha(W/'audit_joint_edge_stage_pose_live_v2.py'),str(Path(__file__)):sha(__file__)}
for f in prep['files']:frozen[str(W/f['new'])]=f['new_sha256']
statusbase=dict(pid=os.getpid(),episode=str(ep),expected_audits=scripts,frozen_supplement_sha256=frozen,original_quality_sha256=sha(ep/'quality.json'),original_task_passed=json.loads((ep/'quality.json').read_text())['passed'],training_ready=False)
def save(status,**kwargs):
 tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(statusbase,status=status,updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),rows=rows,**kwargs),indent=2));tmp.replace(dest)
try:
 for script in scripts:
  for path,h in frozen.items():assert sha(path)==h
  new=mapping[script[:-3]]+'.py';name,keys=REPORTS[script];report=ep/reports[name];save('running',current_auditor=new)
  if script=='audit_joint_edge_stage_pose_live.py':
   assert report.exists();d=json.loads(report.read_text());assert d['auditor_sha256']==sha(W/new) and d['source_sha256']['raw.npz']==sha(ep/'raw.npz');code=0;reused=True
  else:
   assert not report.exists();p=subprocess.run([sys.executable,str(W/new),str(ep)],capture_output=True,text=True);code=p.returncode;(ep/(new+'.log')).write_text(p.stdout+'\n'+p.stderr);reused=False
  value=False
  if report.exists():
   value=json.loads(report.read_text())
   for k in keys:value=value[k]
  row=dict(script=new,report=report.name,passed=bool(code==0 and value is True),process_returncode=code,reused_bound_pose_report=reused,report_sha256=sha(report) if report.exists() else None,auditor_sha256=sha(W/new));rows.append(row);print(json.dumps(row),flush=True)
 save('complete',all_supplemental_audits_passed=all(x['passed'] for x in rows))
except Exception as e:save('supplement_error',error=repr(e));raise
