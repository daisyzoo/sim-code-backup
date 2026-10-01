"""Versioned region audit chain: exact old mathematics outside explicit measured
capture admission, full eight parent-file replays, and sixteen capture fixtures.
No simulator data generated; all old data are read-only symlinks in /tmp.
"""
from pathlib import Path
import sys,json,hashlib,ast,subprocess,tempfile,copy
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from recontact_audit_context import selected_after_capture,verified_events
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();mapping=json.loads((w/'RECONTACT_REGION_VERSION_MAP.json').read_text());pairs=list(mapping.items())[:5]
for original,new in pairs:
 src=(w/new).read_text()
 if original=='audit_region_action_live_r2.py':
  src=src.replace('from recontact_audit_context import verified_events,selected_after_capture\nverified_recontacts=verified_events(p)\n','')
  src=src.replace(' selected=selected_after_capture(row,selected,verified_recontacts)\n','')
  src=src.replace("verified_recontact_frames=len(verified_recontacts),verified_recontact_handovers=sum(e['kind']=='handover' for e in verified_recontacts.values()),",'')
 for a,b in mapping.items():src=src.replace(b,a)
 assert ast.dump(ast.parse(src),include_attributes=False)==ast.dump(ast.parse((w/original).read_text()),include_attributes=False),new
base=Path(tempfile.mkdtemp(prefix='recontact_region_chain_'));results=[]
for original_ep in sorted((w/'rear_short_recovery_groups_r1').glob('case_*/layout_*')):
 if not (original_ep/'frontal_bypass.json').exists():continue
 parent=base/original_ep.parent.name;parent.mkdir(exist_ok=True)
 for name in ['source_snapshot','provenance.json']:
  path=parent/name
  if not path.exists():path.symlink_to((original_ep.parent/name).resolve(),target_is_directory=name=='source_snapshot')
 ep=parent/original_ep.name;ep.mkdir()
 # No old output reports are linked; any unintended old-name write is detectable.
 for f in original_ep.iterdir():
  if f.is_file() and f.suffix in ('.npz','.json') and 'AUDIT' not in f.name:(ep/f.name).symlink_to(f.resolve())
 result=subprocess.run([sys.executable,str(w/'audit_recontact_rear_xy.py'),str(ep)],capture_output=True,text=True)
 (ep/'chain_stdout.log').write_text(result.stdout);(ep/'chain_stderr.log').write_text(result.stderr)
 assert result.returncode==0,(original_ep.name,result.stdout[-3000:],result.stderr[-3000:])
 reports={}
 for a,b in list(mapping.items())[5:]:
  actual=json.loads((ep/b).read_text());old=json.loads((original_ep/a).read_text());assert actual['passed']==old['passed'] is True
  for key in ['errors','override_steps','handover','override_rows','forecast_steps_checked','checks','handovers','transitions_checked','records','solver_records_checked','inward_recovery_commands','overrides_checked']:
   if key in old:assert actual[key]==old[key],(original_ep.name,a,key)
  reports[b]=sha(ep/b)
 assert not any((ep/n).exists() for n in list(mapping)[5:])
 assert verified_events(ep)=={}
 results.append(dict(episode=ep.name,reports_sha256=reports,fixture=str(ep)));print(ep.name,'full chain passed',flush=True)
assert len(results)==8
fixture=w/'staged_recontact_pose_probe/LIFECYCLE_CHECK.json';data=json.loads(fixture.read_text());handovers=0;rejected=[]
for case in data['rows']:
 for plant in case['plants']:
  event=plant['trace'][-1];step=event['context']['step'];row=dict(step=step,mode='top_press',active=False,solver=None,center_local=event['captured_center_local'],selected_surface_local_xy=event['selected_surface_local_xy']);events={step:event};old=[.001,.002]
  assert selected_after_capture(row,old,events)==event['selected_surface_local_xy'];assert selected_after_capture(row,old,{}) is old;handovers+=1
  for name in ['center','surface','mode','active','conflict']:
   bad=copy.deepcopy(row)
   if name=='center':bad['center_local'][0]+=.001
   if name=='surface':bad['selected_surface_local_xy'][0]+=.001
   if name=='mode':bad['mode']='top_push'
   if name=='active':bad['active']=True
   if name=='conflict':bad['solver']=dict(joint_override=True)
   try:selected_after_capture(bad,old,events)
   except AssertionError:rejected.append(name)
   else:raise AssertionError('Accepted '+name)
# Disabled metadata cannot smuggle a candidate path into the old audit branch.
ep=Path(results[0]['fixture']);path=ep/'recontact_pose.json';path.write_text(json.dumps(dict(rows=[dict(kind='command')])))
try:verified_events(ep)
except AssertionError:rejected.append('disabled_nonempty_events')
else:raise AssertionError('Accepted undeclared events')
path.unlink()
sources=[Path(__file__),w/'recontact_audit_context.py',w/'RECONTACT_REGION_VERSION_MAP.json',w/'audit_recontact_pose_live.py']+[w/n for pair in pairs for n in pair]
out=dict(passed=True,scope=__doc__,original_math_ast_exact=True,parent_replays=results,synthetic_handovers=handovers,rejected_corruptions=len(rejected),fixture_sha256=sha(fixture),source_sha256={str(p):sha(p) for p in sources},fixture_root=str(base),physical_validation=False,training_ready=False)
(w/'staged_recontact_pose/REGION_CHAIN_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',len(results),handovers,len(rejected),flush=True)
