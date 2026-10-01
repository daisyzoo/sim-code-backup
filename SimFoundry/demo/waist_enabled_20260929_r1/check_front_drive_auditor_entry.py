"""Exercise independent auditor CLI on isolated recorded-input fixtures, never physics."""
from pathlib import Path
import copy, hashlib, json, subprocess, sys, tempfile
w=Path(__file__).resolve().parent
script=w/'audit_front_drive_increment_live.py'
fixture=w/'staged_front_drive_increment_probe/DRIVE_INCREMENT_REPLAY_CHECK.json'
cases=json.loads(fixture.read_text())['rows']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
results=[]
with tempfile.TemporaryDirectory(prefix='front-drive-audit-entry-') as td:
 root=Path(td)
 def run(name,source,log,args,expect):
  parent=root/name;ep=parent/source.name;ep.mkdir(parents=True)
  for f in ['raw.npz','trace.npz','parcel_orientation.npz','solved_contact_forces.json']:(ep/f).symlink_to(source/f)
  (ep/'frontal_bypass.json').write_text(json.dumps(log));(parent/'provenance.json').write_text(json.dumps({'args':args}))
  done=subprocess.run([sys.executable,str(script),str(ep)],capture_output=True,text=True)
  out=ep/'FRONT_DRIVE_INCREMENT_LIVE_AUDIT.json'
  assert (done.returncode==0)==expect,(name,done.returncode,done.stdout[-1000:],done.stderr[-1000:])
  report=json.loads(out.read_text()) if out.exists() else None
  if expect:
   assert report['passed'] and not report['errors'] and report['auditor_sha256']==sha(script)
   for f,h in report['source_sha256'].items():assert sha(ep/f)==h
  results.append(dict(name=name,returncode=done.returncode,expected_accept=expect,loaded_steps_checked=report['loaded_steps_checked'] if report else None,enabled=report['enabled'] if report else None))
 for task in ['nudge_mailer_to_bin','push_box_to_bin']:
  case=next(c for c in cases if '/rear_core_slice_groups_r1/' in c['episode'] and c['episode'].endswith(task))
  source=Path(case['episode']);log=json.loads((source/'frontal_bypass.json').read_text());args=json.loads((source.parent/'provenance.json').read_text())['args']
  run(task+'_default_recorded',source,log,args,True)
  shadow=copy.deepcopy(log);shadow['plan']['front_cop_slip_following']['drive_step_m']=.002;shadow['rows']=[dict(x['counterfactual_row'],step=x['step']) for x in case['records']]
  args=dict(args,front_cop_drive_step_m=.002)
  run(task+'_synthetic_2mm',source,shadow,args,True)
  run(task+'_provenance_mismatch',source,shadow,dict(args,front_cop_drive_step_m=.001),False)
  bad=copy.deepcopy(shadow);bad['plan']['front_cop_slip_following']['drive_step_m']=.004
  run(task+'_out_of_range',source,bad,dict(args,front_cop_drive_step_m=.004),False)
  run(task+'_disabled_with_trace',source,shadow,dict(args,front_cop_route_axis=False),False)
 source=w/'rear_core_slice_groups_r1/case_840001/layout_840001_push_box_to_bin'
 run('rear_disabled_recorded',source,json.loads((source/'frontal_bypass.json').read_text()),json.loads((source.parent/'provenance.json').read_text())['args'],True)
out=dict(passed=True,rows=results,auditor_sha256=sha(script),checker_sha256=sha(Path(__file__)),fixture_sha256=sha(fixture),scope='Actual auditor CLI, source/output bindings, default physical recordings and 2mm synthetic fixed-observation streams; no new physical results.',training_ready=False)
(w/'staged_front_drive_increment/AUDITOR_ENTRY_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
