"""Preserve R1 failures; rerun16 affected audits under independent region FK."""
from pathlib import Path
import sys,json,subprocess,hashlib,copy,datetime
w=Path(__file__).resolve().parent;r=Path(sys.argv[1]).resolve();p=r/'CONTROL_EVIDENCE_EXECUTION.json';d=json.loads(p.read_text());backup=r/'CONTROL_EVIDENCE_EXECUTION_R1.json';assert not backup.exists();backup.write_bytes(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();changes=[]
spec={'audit_terminal_hold_inputs.py':('TERMINAL_HOLD_INPUT_AUDIT.json',('summary','passed')),'audit_initial_near_half_live.py':('INITIAL_NEAR_HALF_LIVE_AUDIT.json',('passed',))}
for x in d['rows']:
 if x['script'] not in spec:continue
 old=copy.deepcopy(x);ep=next(r.glob('case_*/'+x['episode']));report,keys=spec[x['script']];rp=ep/report;rp.with_name(rp.stem+'_R1.json').write_bytes(rp.read_bytes());log=ep/(x['script']+'.log');log.with_name(log.name+'.r1').write_bytes(log.read_bytes())
 with log.open('w') as f:proc=subprocess.run([sys.executable,str(w/x['script']),str(ep)],stdout=f,stderr=subprocess.STDOUT)
 value=json.loads(rp.read_text())
 for k in keys:value=value[k]
 passed=bool(proc.returncode==0 and value is True);x.update(returncode=0 if passed else 1,process_returncode=proc.returncode,report_passed=passed,report_sha256=sha(rp),auditor_sha256=sha(w/x['script']),region_reference_auditor_sha256=sha(w/'audit_region_reference_live.py'),revision='region_aware_r2');changes.append(dict(original=old,revised=copy.deepcopy(x)));print(x['episode'],x['script'],passed,flush=True)
assert len(changes)==16
d.update(stage='complete' if all(x['returncode']==0 and x['report_passed'] for x in d['rows']) else 'incomplete_or_failed',updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reconciliation='Original R1 execution/reports retained. Two reference reconstruction checks support independently verified region handover; no tolerance/task/control changes.')
p.write_text(json.dumps(d,indent=2));(r/'REGION_REFERENCE_AUDIT_RECONCILIATION.json').write_text(json.dumps(dict(changes=changes,passed=d['stage']=='complete',old_execution_sha256=sha(backup),new_execution_sha256=sha(p),helper_sha256=sha(w/'audit_region_reference_live.py'),training_ready=False),indent=2));assert d['stage']=='complete'
