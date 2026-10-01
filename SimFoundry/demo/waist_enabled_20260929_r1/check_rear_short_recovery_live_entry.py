"""Independent height auditor on four source-bound counterfactual fixtures.
Fixtures use fixed recorded observations and hypothetical control references;
never physical data/training. Verify true CLI success and each corrupt-input
rejection without leaving a stale positive report.
"""
from pathlib import Path
import sys,json,hashlib,tempfile,copy,subprocess
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_rear_short_recovery';sys.path.insert(0,str(w))
from audit_rear_short_recovery_live import verify_rows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();d=json.loads((stage/'RECORDED_INPUT_REPLAY.json').read_text());assert len(d['episodes'])==4
cfg=dict(enabled=True,initial_travel_z=.91,recontact_travel_z=.86,release_min_z=.91,original_guard_priority=True,selected_rear_region_only=True,loaded_control_unchanged=True,scope='Diagnostic recovery-height only; full physics and quality gates remain required.')
root=Path(tempfile.mkdtemp(prefix='rear_short_recovery_auditor_'));checks=[];independent=[]
for i,episode in enumerate(d['episodes']):
 source=Path(episode['episode']);fr=json.loads((source/'frontal_bypass.json').read_text());controls=json.loads((source/'expert_control.json').read_text());original=verify_rows(fr['rows'],{r['step']:r for r in controls},fr['plan'],False);assert original['selected'] and original['height_rows']>0
 candidate=copy.deepcopy(fr);candidate['rows']=episode['counterfactual_rows'];candidate['plan']['rear_short_recovery']=cfg.copy();by_step={r['step']:r for r in candidate['rows']};cc=copy.deepcopy(controls)
 for r in cc:
  if r['step'] in by_step:r['target_xyz']=by_step[r['step']]['target_xyz']
 evidence=verify_rows(candidate['rows'],{r['step']:r for r in cc},candidate['plan'],True);independent.append(dict(episode=str(source),parent=original,candidate=evidence))
 case=root/f'case_{i}';ep=case/source.name;ep.mkdir(parents=True);(ep/'raw.npz').symlink_to(source/'raw.npz');(ep/'frontal_bypass.json').write_text(json.dumps(candidate));(ep/'expert_control.json').write_text(json.dumps(cc));prov=json.loads((source.parent/'provenance.json').read_text());prov['args']['rear_short_recovery']=True;new_sources={}
 for name in prov['source_sha256']:
  newname=name.replace('/staged_front_diagonal_entry/','/staged_rear_short_recovery/').replace('/staged_micro_clearance_return/','/staged_rear_short_recovery/');actual=repo/newname;assert actual.exists(),actual;dst=case/'source_snapshot'/newname;dst.parent.mkdir(parents=True,exist_ok=True);dst.symlink_to(actual);new_sources[newname]=sha(actual)
 prov['source_sha256']=new_sources;(case/'provenance.json').write_text(json.dumps(prov));(case/'COUNTERFACTUAL_FIXTURE.json').write_text(json.dumps(dict(scope=__doc__,physical_data=False,training_ready=False,source_episode=str(source))))
 report=ep/'REAR_SHORT_RECOVERY_LIVE_AUDIT.json'
 def cli(expect,name):
  if report.exists():report.unlink()
  result=subprocess.run([sys.executable,str(w/'audit_rear_short_recovery_live.py'),str(ep)],capture_output=True,text=True);(case/(name+'.log')).write_text(result.stdout+'\n'+result.stderr)
  assert (result.returncode==0)==expect,(name,result.stderr)
  assert report.exists()==expect,(name,'stale report')
  checks.append(dict(episode=source.name,case=name,expected_pass=expect,returncode=result.returncode))
 cli(True,f'positive_{i}')
 if i==0:
  event=next(j for j,r in enumerate(candidate['rows']) if r.get('recontacts',0)>0 and r['mode']=='top_lift');initial=next(j for j,r in enumerate(candidate['rows']) if r.get('travel_height_m')==.91 and r['mode']=='top_lift');cross=next(j for j,r in enumerate(candidate['rows']) if r.get('recontacts',0)>0 and r['mode']=='top_cross')
  for name in ['disabled_flag','source_hash','weakened_height','initial_lowered','recovery_raised','bad_counter','cross_low_tip','lift_xy_changed','mapping_changed','front_claim']:
   f=copy.deepcopy(candidate);c=copy.deepcopy(cc);p=copy.deepcopy(prov)
   if name=='disabled_flag':p['args']['rear_short_recovery']=False
   elif name=='source_hash':p['source_sha256'][next(iter(p['source_sha256']))]='0'*64
   elif name=='weakened_height':f['plan']['rear_short_recovery']['recontact_travel_z']=.84
   elif name=='initial_lowered':f['rows'][initial]['travel_height_m']=.86
   elif name=='recovery_raised':f['rows'][event]['travel_height_m']=.91
   elif name=='bad_counter':f['rows'][event]['recontacts']+=2
   elif name=='cross_low_tip':f['rows'][cross]['observed_support_xyz'][2]=.81
   elif name=='lift_xy_changed':
    t=f['rows'][event]['step'];f['rows'][event]['target_xyz'][0]+=.03;next(v for v in c if v['step']==t)['target_xyz']=f['rows'][event]['target_xyz']
   elif name=='mapping_changed':next(v for v in c if v['step']==f['rows'][event]['step'])['target_xyz'][2]+=.01
   else:f['plan']['front_route_selected']=True
   (ep/'frontal_bypass.json').write_text(json.dumps(f));(ep/'expert_control.json').write_text(json.dumps(c));(case/'provenance.json').write_text(json.dumps(p));cli(False,name)
  (ep/'frontal_bypass.json').write_text(json.dumps(candidate));(ep/'expert_control.json').write_text(json.dumps(cc));(case/'provenance.json').write_text(json.dumps(prov))
# Nonselected originals must not claim any rear exception, regardless of flag.
for cid,task in [(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin')]:
 ep=w/f'micro_clearance_groups_r1/case_{cid}/layout_{cid}_{task}';f=json.loads((ep/'frontal_bypass.json').read_text());c={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};assert not verify_rows(f['rows'],c,f['plan'],True)['selected']
out=dict(passed=True,scope=__doc__,fixtures=str(root),checks=checks,independent_streams=independent,nonselected_front_streams=2,source_sha256={str(p):sha(p) for p in [Path(__file__),w/'audit_rear_short_recovery_live.py',stage/'RECORDED_INPUT_REPLAY.json',stage/'collect_paired_sorting.py',stage/'region_top_contact.py']},physical_validation=False,training_ready=False);(stage/'CLI_CHECK.json').write_text(json.dumps(out,indent=2));print('passed four parent+candidate streams,4CLI positives,10CLI negatives,2nonselected front streams',root)
