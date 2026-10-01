"""Run actual edge auditor entry on isolated fixtures, source checks and negative declarations."""
from pathlib import Path
import copy,hashlib,json,subprocess,sys,tempfile
w=Path(__file__).resolve().parent;script=w/'audit_front_edge_speed_live.py';fixture=w/'staged_front_edge_speed_probe/EDGE_SPEED_REPLAY_CHECK.json';cases=json.loads(fixture.read_text())['rows'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();results=[]
with tempfile.TemporaryDirectory(prefix='front-edge-entry-') as tmp:
 root=Path(tmp)
 def run(name,source,log,args,expect,corrupt_archive=False):
  parent=root/name;ep=parent/source.name;ep.mkdir(parents=True);prov=json.loads((source.parent/'provenance.json').read_text());prov['args']=args
  for f in ['raw.npz','trace.npz','parcel_orientation.npz','solved_contact_forces.json']:(ep/f).symlink_to(source/f)
  cfg=parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py';cfg.parent.mkdir(parents=True)
  if corrupt_archive:cfg.write_bytes((source.parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py').read_bytes()+b'\n# changed\n')
  else:cfg.symlink_to(source.parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py')
  (parent/'provenance.json').write_text(json.dumps(prov));(ep/'frontal_bypass.json').write_text(json.dumps(log))
  proc=subprocess.run([sys.executable,str(script),str(ep)],capture_output=True,text=True);report=ep/'FRONT_EDGE_SPEED_LIVE_AUDIT.json'
  assert (proc.returncode==0)==expect,(name,proc.stdout[-1000:],proc.stderr[-1200:])
  a=json.loads(report.read_text()) if report.exists() else None
  if expect:
   assert a['passed'] and not a['errors'] and a['auditor_sha256']==sha(script)
   for f,h in a['source_sha256'].items():assert sha(ep/f)==h
  results.append(dict(case=name,returncode=proc.returncode,expected_accept=expect,loaded_steps_checked=a['loaded_steps_checked'] if a else None))
 for task in ['nudge_mailer_to_bin','push_box_to_bin']:
  case=next(c for c in cases if '/front_drive_increment_groups_r1/' in c['episode'] and c['episode'].endswith(task));source=Path(case['episode']);log=json.loads((source/'frontal_bypass.json').read_text());args=json.loads((source.parent/'provenance.json').read_text())['args'];run(task+'_actual2mm_default_off',source,log,args,True)
  shadow=copy.deepcopy(log);shadow['rows']=[dict(x['counterfactual_row'],step=x['step']) for x in case['records']];core=[.1344,.0864,.045] if 'push_box' in task else [.135,.1276,.04];shadow['plan']['front_cop_slip_following']['edge_speed']=dict(enabled=True,minimum_drive_step_m=.001,warning_distance_m=.010,actual_core_size_xyz=core);args=dict(args,front_cop_edge_speed=True)
  run(task+'_synthetic_edge',source,shadow,args,True)
  run(task+'_flag_mismatch',source,shadow,dict(args,front_cop_edge_speed=False),False)
  run(task+'_nominal_mismatch',source,shadow,dict(args,front_cop_drive_step_m=.001),False)
  run(task+'_corrupt_archive',source,shadow,args,False,True)
  for name,field,value in [('core','actual_core_size_xyz',[.20,.20,.04]),('warning','warning_distance_m',.020),('minimum','minimum_drive_step_m',.0),('enable_type','enabled',1)]:
   bad=copy.deepcopy(shadow);bad['plan']['front_cop_slip_following']['edge_speed'][field]=value;run(task+'_bad_'+name,source,bad,args,False)
 source=w/'front_drive_increment_groups_r1/case_840001/layout_840001_push_box_to_bin';run('rear_disabled_actual',source,json.loads((source/'frontal_bypass.json').read_text()),json.loads((source.parent/'provenance.json').read_text())['args'],True)
out=dict(passed=True,rows=results,auditor_sha256=sha(script),checker_sha256=sha(Path(__file__)),fixture_sha256=sha(fixture),scope='Real auditor CLI with archived collision source/provenance, actual disabled front/rear and enabled fixed-observation shadows. No physical efficacy claim.',training_ready=False);(w/'staged_front_edge_speed_probe/AUDITOR_ENTRY_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
