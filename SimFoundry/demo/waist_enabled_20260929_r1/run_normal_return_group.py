"""Fresh full development swap group using normal settings; no pilot promotion.
Never queued by this file. Current bounded experiment must finish and be reviewed.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,subprocess,sys,shutil
W=Path(__file__).resolve().parent;REPO=W.parents[1];sys.path.insert(0,str(REPO))
from simfoundry.data.waist_group_audit import validate_complete_swap_layouts
from simfoundry.data.waist_pilot_protocol import REQUIRED_SOURCES
def verify_complete_push_case(case,layout_id,frames,returncode):
 import numpy as np
 status=json.loads((case/'STATUS.json').read_text())
 quality_failure=status.get('status')=='blocked_quality_or_runtime' and status.get('error')=='Quality gate failed. Stop; no retries or training export. See manifest.json.'
 if status.get('status')!='numeric_pass_visual_review_pending' and not quality_failure:raise RuntimeError('Unexpected collector runtime state: '+str(status))
 if returncode and not quality_failure:raise RuntimeError('Collector failed outside declared quality outcome')
 records=[]
 for task in ('push_box_to_bin','nudge_mailer_to_bin'):
  ep=case/f'layout_{layout_id}_{task}';quality=json.loads((ep/'quality.json').read_text())
  with np.load(ep/'raw.npz') as raw:
   if raw['q'].shape!=(frames,23) or raw['action'].shape!=(frames,23) or str(raw['task_id'])!=task:raise RuntimeError('Incomplete/misaligned recorded condition')
  if quality['frames']!=frames:raise RuntimeError('Quality frame count mismatch')
  records.append(dict(episode=ep.name,original_task_passed=quality['passed']))
 return dict(layout_id=layout_id,collector_returncode=returncode,collector_status=status,conditions=records,training_ready=False)

p=argparse.ArgumentParser();p.add_argument('--group',required=True);p.add_argument('--out',type=Path);p.add_argument('--validate-only',action='store_true');args=p.parse_args()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
reference=W/'normal_contact_groups_r1';prior=W/'bounded_top_lead24_groups_r1'
ref=json.loads((reference/'PROTOCOL.json').read_text());parent=json.loads((prior/'PROTOCOL.json').read_text())
assert parent['settings']==ref['settings']+['--expert-top-contact-center-calibration','--expert-top-object-relative-lead-m','.024']
settings=list(ref['settings']);assert settings[settings.index('--role')+1]=='diagnostic' and settings[settings.index('--steps')+1]=='1200'
assert '--expert-top-contact-normal-hold' in settings and '--expert-terminal-joint-hold' in settings
assert '--expert-top-contact-center-calibration' not in settings and '--expert-top-object-relative-lead-m' not in settings
paths=[W/f'development_layouts/{i}.json' for i in range(62000,62016)]
selected=[x for x in paths if json.loads(x.read_text())['geometry_group']==args.group]
layouts=[json.loads(x.read_text()) for x in selected];groups=validate_complete_swap_layouts(layouts)
assert len(layouts)==2 and all(x['planned_split']=='development' for x in layouts)
hashes=parent['source_sha256']
for path,h in hashes.items():assert sha(path)==h,path
assert {str(REPO/x) for x in REQUIRED_SOURCES}<=set(hashes)
ids=[x['layout_id'] for x in layouts];layout_hashes={str(x['layout_id']):sha(f) for x,f in zip(layouts,selected)}
summary=dict(group=args.group,layout_ids=ids,conditions=4,frames=1200,environment_seed=0,settings=settings,source_sha256=hashes,layout_sha256=layout_hashes,normal_reference_protocol_sha256=sha(reference/'PROTOCOL.json'),current_source_protocol_sha256=sha(prior/'PROTOCOL.json'),training_ready=False,scope='Normal settings on current source with center/lead flags disabled. Fresh measured behavior required; not byte-identical historical-source replay. Full4 per group, keep failures. No diagnostic promotion or independent-test geometry.')
if args.validate_only:
 print(json.dumps(dict(**summary,execution_ready=False,reason='Validation only; current full experiment review and explicit later invocation required.'),indent=2));sys.exit(0)
assert args.out is not None,'Fresh output directory required';out=args.out.resolve();assert not out.exists()
assert json.loads((prior/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
a=json.loads((prior/'AUDIT_EXECUTION.json').read_text());assert len(a)==9 and all(x['returncode']==0 for x in a)
r=json.loads((prior/'RESULT.json').read_text());assert len(r['rows'])==12
for row in r['rows']:
 ep=prior/('case_'+row['episode'].split('_')[1])/row['episode'];assert row['actual_sampled_visual_review']=='completed' and sha(ep/'raw.npz')==row['raw_sha256'] and sha(ep/'REVIEW_EVEN.jpg')==row['review_sheet_sha256']
c=json.loads((prior/'CONTROL_EVIDENCE_EXECUTION.json').read_text());assert c['stage']=='complete' and all(x['returncode']==0 and x['report_passed'] for x in c['rows'])
# A failed experiment is valid diagnostic context, never successful feasibility.
g=json.loads((prior/'COMPLETE_GROUP_READINESS.json').read_text());assert len(g['rows'])==12 and all(e.endswith(': task/pose failed') for e in g['errors'])
assert shutil.disk_usage(W).free>=30*2**30
out.mkdir();summary.update(groups=groups,parent_run=str(prior),parent_result_sha256=sha(prior/'RESULT.json'),runner_sha256=sha(__file__),motion_protocol='waist_yaw_enabled_v1',reference_run=str(reference));(out/'PROTOCOL.json').write_text(json.dumps(summary,indent=2))
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab',OMNI_KIT_ACCEPT_EULA='yes');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH'];env.setdefault('DISPLAY',':1')
def status(stage,**kw):(out/'STATUS.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False,**kw),indent=2))
execution=[]
try:
 for i in ids:
  for path,h in hashes.items():assert sha(path)==h,path
  layout=W/f'development_layouts/{i}.json';assert sha(layout)==layout_hashes[str(i)]
  assert shutil.disk_usage(W).free>=30*2**30
  status('running',layout_id=i)
  cmd=['./isaaclab.sh','-p',str(REPO/'scripts/collect_paired_sorting.py'),*settings,'--layout-start',str(i),'--diagnostic-layout-json',str(layout),'--out-dir',str(out/f'case_{i}')]
  with (out/f'case_{i}.log').open('w') as f:q=subprocess.run(cmd,cwd=REPO.parent/'IsaacLab',env=env,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
  execution.append(verify_complete_push_case(out/f'case_{i}',i,1200,q.returncode))
  (out/'COLLECTION_EXECUTION.json').write_text(json.dumps(execution,indent=2))
  for script in ('audit_contacts.py','review_diagnostics.py'):
   with (out/f'{i}_{script}.log').open('w') as f:subprocess.run([sys.executable,str(W/script),str(out/f'case_{i}')],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
 for path,h in hashes.items():assert sha(path)==h,path
 (out/'TERMINAL_SOURCE_VERIFICATION.json').write_text(json.dumps(dict(all_frozen_sources_match=True,training_ready=False)))
 status('numeric_complete_actual_visual_review_pending')
except BaseException as exc:status('runtime_failed',error=str(exc));raise
