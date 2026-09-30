"""Audit completed new-controller episodes without modifying frozen control/data."""
from pathlib import Path
import sys,os,json,time,subprocess,hashlib,datetime
root=Path(__file__).resolve().parent
run=Path(sys.argv[1]).resolve()
protocol=json.loads((run/'PROTOCOL.json').read_text())
assert '--expert-top-contact-normal-hold' in protocol['settings']
scripts=['audit_contact_normal_live.py','audit_terminal_hold_live.py',
         'audit_terminal_hold_inputs.py','audit_contact_stability_control.py']
results=[];done=set()
def save(stage):
    payload=dict(stage=stage,pid=os.getpid(),rows=results,updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        scope='Independent new normal mapping/lifecycle, terminal hold and contact-control checks on fully written episodes only. Actual visual review, original task/pose, full-group checks and data admission separate.',training_ready=False)
    temp=run/'CONTROL_EVIDENCE_EXECUTION.tmp'
    temp.write_text(json.dumps(payload,indent=2));temp.replace(run/'CONTROL_EVIDENCE_EXECUTION.json')
save('running')
while True:
    for ep in sorted(run.glob('case_*/layout_*')):
        if ep.name in done or not (ep/'quality.json').exists():continue
        raw=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest()
        episode_scripts=list(scripts)+['audit_bounded_top_lead_live.py']
        if (ep/'contact_center_calibration.json').exists():episode_scripts+=['audit_contact_center_live.py','audit_projected_support_live.py']
        for script in episode_scripts:
            with (ep/(script+'.log')).open('w') as log:
                result=subprocess.run([sys.executable,str(root/script),str(ep)],stdout=log,stderr=subprocess.STDOUT)
            report_specs={
                'audit_contact_normal_live.py':('CONTACT_NORMAL_LIVE_AUDIT.json',('summary','recording_and_mapping_passed')),
                'audit_terminal_hold_live.py':('TERMINAL_HOLD_LIVE_AUDIT.json',('recorded_hold_checks_passed',)),
                'audit_terminal_hold_inputs.py':('TERMINAL_HOLD_INPUT_AUDIT.json',('summary','passed')),
                'audit_contact_stability_control.py':('CONTACT_STABILITY_CONTROL_AUDIT.json',('control_checks_passed',)),
                'audit_bounded_top_lead_live.py':('BOUNDED_TOP_LEAD_LIVE_AUDIT.json',('passed',)),
                'audit_contact_center_live.py':('CONTACT_CENTER_LIVE_AUDIT.json',('passed',)),
                'audit_projected_support_live.py':('PROJECTED_SUPPORT_LIVE_AUDIT.json',('summary','mapping_passed')),
            }
            report_name,keys=report_specs[script];report_path=ep/report_name;passed=False;report_hash=None
            if result.returncode==0 and report_path.exists():
                value=json.loads(report_path.read_text())
                for key in keys:value=value[key]
                passed=value is True
                report_hash=hashlib.sha256(report_path.read_bytes()).hexdigest()
            row=dict(episode=ep.name,script=script,returncode=result.returncode if result.returncode else (0 if passed else 1),process_returncode=result.returncode,report_passed=passed,report_sha256=report_hash,auditor_sha256=hashlib.sha256((root/script).read_bytes()).hexdigest(),raw_sha256=raw)
            results.append(row);print(json.dumps(row),flush=True);save('running')
        done.add(ep.name)
    state=json.loads((run/'STATUS.json').read_text())['stage']
    if state!='running':
        expected=len(protocol['layout_ids'])*2
        stage='complete' if len(done)==expected and all(r['returncode']==0 for r in results) else 'incomplete_or_failed'
        save(stage);break
    time.sleep(15)
