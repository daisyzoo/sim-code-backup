"""Full fixed-geometry repair trial after current pilot/source review; no retries."""
from pathlib import Path
import argparse,ast,datetime,hashlib,json,os,shutil,subprocess,sys
W=Path(__file__).resolve().parent;REPO=W.parents[1]
sys.path.insert(0,str(REPO))
from simfoundry.data.waist_group_audit import validate_complete_swap_layouts
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

# Reuse the established complete-case reader without executing its old CLI.
completion_source=W/'run_normal_return_group.py'
tree=ast.parse(completion_source.read_text())
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='verify_complete_push_case')
exec(compile(ast.Module(body=[node],type_ignores=[]),str(completion_source),'exec'))

p=argparse.ArgumentParser();p.add_argument('--out',type=Path);p.add_argument('--validate-only',action='store_true');a=p.parse_args()
plan_path=W/'INITIAL_NEAR_CONTACT_PLAN.json';plan=json.loads(plan_path.read_text())
layouts=[]
for path,digest in plan['layout_sha256'].items():
    if sha(path)!=digest:raise ValueError('Frozen repair geometry changed')
    layouts.append(json.loads(Path(path).read_text()))
assert validate_complete_swap_layouts(layouts)==plan['groups']
assert len(layouts)==2 and all(x['planned_split']=='development' for x in layouts)
if a.validate_only:
    print(json.dumps(dict(plan_sha256=sha(plan_path),runner_sha256=sha(__file__),
        layout_ids=plan['layout_ids'],conditions=4,execution_ready=False,
        reason='Layout/plan validation only; candidate sources must be installed after current pilot review.',training_ready=False),indent=2))
    sys.exit(0)
for path,digest in plan['source_sha256'].items():
    if sha(path)!=digest:raise ValueError('Repair source not installed or changed: '+path)
prior=W/'initial_top_short_recovery_depth_r1'
assert json.loads((prior/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
review=json.loads((prior/'RESULT.json').read_text());assert len(review['rows'])==4
for row in review['rows']:
    ep=prior/('case_'+row['episode'].split('_')[1])/row['episode']
    assert row['actual_sampled_visual_review']=='completed'
    assert sha(ep/'raw.npz')==row['raw_sha256'] and sha(ep/'REVIEW_EVEN.jpg')==row['review_sheet_sha256']
controls=json.loads((prior/'CONTROL_EVIDENCE_EXECUTION.json').read_text())
assert controls['stage']=='complete' and all(x['returncode']==0 and x['report_passed'] for x in controls['rows'])
assert len(controls['rows'])==28
batch=json.loads((prior/'AUDIT_EXECUTION.json').read_text())
assert len(batch)==9 and all(x['returncode']==0 for x in batch)
assert sha(prior/'RESULT.json')==plan['parent_result_sha256']
for proc in Path('/proc').glob('[0-9]*/cmdline'):
    try:parts=proc.read_bytes().split(b'\0')
    except (FileNotFoundError,PermissionError,ProcessLookupError):continue
    if any(Path(os.fsdecode(x)).name=='collect_paired_sorting.py' for x in parts if x):
        raise RuntimeError('Another simulator is alive; no overlap')
if a.out is None or a.out.exists():raise ValueError('Fresh output path required')
out=a.out.resolve();out.mkdir()
protocol=dict(plan,plan_sha256=sha(plan_path),runner_sha256=sha(__file__),
    completion_reader_source_sha256=sha(completion_source),motion_protocol='waist_yaw_enabled_v1')
(out/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2))
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',
    CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab',OMNI_KIT_ACCEPT_EULA='yes')
env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH'];env.setdefault('DISPLAY',':1')
def status(stage,**kw):
    (out/'STATUS.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),
        updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False,**kw),indent=2))
records=[]
try:
    for identifier,path in zip(plan['layout_ids'],plan['layout_paths']):
        for source,digest in plan['source_sha256'].items():assert sha(source)==digest,source
        assert sha(path)==plan['layout_sha256'][path]
        assert shutil.disk_usage(W).free>30*2**30
        status('running',layout_id=identifier);case=out/f'case_{identifier}'
        cmd=['./isaaclab.sh','-p',str(REPO/'scripts/collect_paired_sorting.py'),*plan['settings'],
            '--layout-start',str(identifier),'--diagnostic-layout-json',path,'--out-dir',str(case)]
        with (out/f'case_{identifier}.log').open('w') as log:
            result=subprocess.run(cmd,cwd=REPO.parent/'IsaacLab',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
        records.append(verify_complete_push_case(case,identifier,plan['frames'],result.returncode))
        (out/'COLLECTION_EXECUTION.json').write_text(json.dumps(records,indent=2))
        for script in ('audit_contacts.py','review_diagnostics.py'):
            with (out/f'{identifier}_{script}.log').open('w') as log:
                subprocess.run([sys.executable,str(W/script),str(case)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    for source,digest in plan['source_sha256'].items():assert sha(source)==digest,source
    (out/'TERMINAL_SOURCE_VERIFICATION.json').write_text(json.dumps(dict(all_frozen_sources_match=True,training_ready=False)))
    status('numeric_complete_actual_visual_review_pending')
except BaseException as exc:
    status('runtime_failed',error=str(exc));raise
