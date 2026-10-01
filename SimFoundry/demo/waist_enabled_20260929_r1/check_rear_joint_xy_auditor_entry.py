"""Real CLI with unchanged base audits on isolated actual and synthetic fixtures."""
from pathlib import Path
import copy,hashlib,json,subprocess,sys,tempfile
w=Path(__file__).resolve().parent;stage=w/'staged_rear_joint_xy_probe';script=w/'audit_rear_joint_xy_live.py';fixtures=json.loads((stage/'ENTRY_FIXTURES.json').read_text())['rows'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();results=[]
with tempfile.TemporaryDirectory(prefix='rear-progress-entry-') as tmp:
 root=Path(tmp)
 def run(name,source,log,args,expect,corrupt_archive=False):
  case=root/name;ep=case/source.name;ep.mkdir(parents=True);prov=json.loads((source.parent/'provenance.json').read_text());prov['args']=args
  synthetic_sources={}
  if args.get('rear_joint_xy_progress'):
   prov['source_sha256']={k:v for k,v in prov['source_sha256'].items() if '/staged_' not in k}
   for path in (w/'staged_rear_joint_xy').iterdir():
    if path.suffix not in ('.py','.json') or path.name.endswith('CHECK.json'):continue
    rel=str(path.relative_to(w.parents[1]));synthetic_sources[rel]=path;prov['source_sha256'][rel]=sha(path)
  for n in ['raw.npz','trace.npz','parcel_orientation.npz','solved_contact_forces.json','coordination.json','region_approach.json']:
   if (source/n).exists():(ep/n).symlink_to(source/n)
  snapshot=case/'source_snapshot';snapshot.mkdir()
  for rel in prov['source_sha256']:
   src=synthetic_sources.get(rel,source.parent/'source_snapshot'/rel);dst=snapshot/rel;dst.parent.mkdir(parents=True,exist_ok=True)
   if (corrupt_archive is True and rel=='simfoundry/scene_bridge/isaac_cfg.py') or (corrupt_archive=='helper' and rel.endswith('/rear_joint_xy_progress.py')):dst.write_bytes(src.read_bytes()+b'\n# damaged\n')
   else:dst.symlink_to(src)
  (case/'provenance.json').write_text(json.dumps(prov));(ep/'frontal_bypass.json').write_text(json.dumps(log));p=subprocess.run([sys.executable,str(script),str(ep)],capture_output=True,text=True);report=ep/'REAR_JOINT_XY_LIVE_AUDIT.json'
  assert (p.returncode==0)==expect,(name,p.stdout[-700:],p.stderr[-1800:])
  d=json.loads(report.read_text()) if report.exists() else None
  if expect:
   assert d['passed'] and not d['errors'] and d['auditor_sha256']==sha(script)
   for f,h in d['source_sha256'].items():assert sha(ep/f)==h
  results.append(dict(name=name,expected_accept=expect,returncode=p.returncode,overrides=d['overrides_checked'] if d else None));print(name,p.returncode,flush=True)
 for i,item in enumerate(fixtures):
  src=Path(item['source']);original=json.loads((src/'frontal_bypass.json').read_text());args=json.loads((src.parent/'provenance.json').read_text())['args'];task='box' if 'push_box' in src.name else 'bag';run(task+'_actual_default',src,original,args,True)
  args=dict(args,rear_coupled_progress=True,rear_joint_xy_progress=True);shadow=item['frontal'];run(task+'_enabled_shadow',src,shadow,args,True);run(task+'_declaration_mismatch',src,shadow,dict(args,rear_joint_xy_progress=False),False)
  if i==0:
   run(task+'_corrupt_archive',src,shadow,args,False,True)
   run(task+'_corrupt_helper',src,shadow,args,False,'helper')
   for name,field,value in [('enable_type','enabled',1),('inset','core_inset_m',.02),('fallback','infeasible_fallback','ignore'),('z','parent_z_unchanged',False),('x_step','max_x_step_m',.003),('lead','max_reference_x_lead_m',.04),('guard','original_guard_priority',False),('first','first_loaded_preserved',False)]:
    bad=copy.deepcopy(shadow);bad['plan']['rear_joint_xy_progress'][field]=value;run(task+'_bad_'+name,src,bad,args,False)
 src=w/'front_drive_increment_groups_r1/case_840001/layout_840001_nudge_mailer_to_bin';args=json.loads((src.parent/'provenance.json').read_text())['args'];run('front_excluded_with_flag',src,json.loads((src/'frontal_bypass.json').read_text()),dict(args,rear_coupled_progress=True,rear_joint_xy_progress=True),True)
out=dict(passed=True,rows=results,checker_sha256=sha(Path(__file__)),auditor_sha256=sha(script),fixture_sha256=sha(stage/'ENTRY_FIXTURES.json'),collector_wired=False,physical_started=False,training_ready=False,scope='Real CLI and original base checks in temporary folders. Synthetic loaded waypoints do not alter old raw joint actions; base action checks cover unloaded region overrides and first press/push, not full loaded IK response. This is entry/provenance/config/geometry verification, not physical execution or efficacy; real collector wiring and executed-goal binding remain required.')
(stage/'AUDITOR_ENTRY_CHECK.json').write_text(json.dumps(out,indent=2));print('PASSED',len(results))
