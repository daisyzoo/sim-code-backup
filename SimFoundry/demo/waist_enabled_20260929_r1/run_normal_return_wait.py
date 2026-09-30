"""One fresh ordinary empty-table wait after current experiment review; no queue."""
from pathlib import Path
import argparse,json,hashlib,datetime,subprocess,os,sys
W=Path(__file__).resolve().parent;REPO=W.parents[1];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--out',type=Path);p.add_argument('--validate-only',action='store_true');args=p.parse_args()
prepared=W/'NORMAL_RETURN_DEPTH_PREFLIGHT.json';plan=json.loads(prepared.read_text());settings=list(plan['settings']);settings[settings.index('--layouts')+1]='0';settings+=['--wait-episodes','1','--wait-layout-start','63000','--wait-steps','70']
for path,h in plan['source_sha256'].items():assert sha(path)==h,path
assert '--waist-probe' not in settings and '--idle' not in settings
info=dict(settings=settings,source_sha256=plan['source_sha256'],frames=70,layout_id=63000,task='wait_no_package',prepared_plan_sha256=sha(prepared),runner_sha256=sha(__file__),training_ready=False)
if args.validate_only:print(json.dumps(dict(**info,execution_ready=False,scope='Prepared settings only; requires completed current experiment and later explicit invocation. No wait physics has run.'),indent=2));sys.exit(0)
prior=W/'bounded_top_lead24_groups_r1';assert json.loads((prior/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
review=json.loads((prior/'RESULT.json').read_text());assert len(review['rows'])==12 and all(x['actual_sampled_visual_review']=='completed' for x in review['rows'])
assert args.out is not None;out=args.out.resolve();out.mkdir(exist_ok=False);(out/'PROTOCOL.json').write_text(json.dumps(info,indent=2))
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab',OMNI_KIT_ACCEPT_EULA='yes');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH'];env.setdefault('DISPLAY',':1')
def status(stage,**kw):(out/'STATUS.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False,**kw),indent=2))
try:
 status('running');case=out/'case';cmd=['./isaaclab.sh','-p',str(REPO/'scripts/collect_paired_sorting.py'),*settings,'--out-dir',str(case)]
 with (out/'wait.log').open('w') as log:proc=subprocess.run(cmd,cwd=REPO.parent/'IsaacLab',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
 ep=case/'layout_63000_wait_no_package';assert (ep/'quality.json').exists() and (ep/'raw.npz').exists(),'Wait output incomplete; inspect process, never auto-restart'
 with (out/'wait_audit.log').open('w') as log:check=subprocess.run([sys.executable,str(W/'audit_normal_wait.py'),str(ep)],stdout=log,stderr=subprocess.STDOUT)
 subprocess.run([sys.executable,str(W/'render_episode_frames.py'),str(ep),'0','9','19','29','39','49','59','69'],check=True)
 for path,h in plan['source_sha256'].items():assert sha(path)==h,path
 status('numeric_complete_actual_visual_review_pending',collector_returncode=proc.returncode,original_wait_passed=json.loads((ep/'WAIT_STABILITY_AUDIT.json').read_text())['passed'],audit_returncode=check.returncode)
except BaseException as exc:status('runtime_failed',error=str(exc));raise
