"""Run actual staged CLI up to simulator launch; no Isaac or policy inference."""
from pathlib import Path
import ast,contextlib,hashlib,io,json,sys,types
W=Path(__file__).resolve().parent;repo=W.parents[1];stage=W/'staged_waist_policy_evaluation';sys.path.insert(0,str(repo))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class AppLauncher:
 @staticmethod
 def add_app_launcher_args(p):
  p.add_argument('--device',default='cuda');p.add_argument('--headless',action='store_true');p.add_argument('--viz',default='none')
app=types.ModuleType('isaaclab.app');app.AppLauncher=AppLauncher;sys.modules['isaaclab.app']=app
live=(repo/'scripts/collect_paired_sorting.py').read_text();candidate=(stage/'collect_paired_sorting.py').read_text();marker='app = AppLauncher(args, enable_cameras=True).app'
base=['--out-dir','/tmp/not_created_waist_policy_evaluation','--role','diagnostic','--policy-port','8000','--horizon','10','--motion-protocol','waist_yaw_enabled_v1','--waist-limit-rad','1.0','--environment-seed','0']
on=base+['--waist-policy-evaluation']
def without(argv,key,value=True):
 a=list(argv);i=a.index(key);del a[i:i+(2 if value else 1)];return a
trials=[('live_rejects_extended_policy',live,base,False),('default_still_rejects_extended',candidate,base,False),('enabled_h10',candidate,on,True),('wait_h10',candidate,on+['--layouts','0','--wait-episodes','1'],True),('disabled_legacy_default',candidate,['--out-dir','/tmp/not_created_waist_policy_evaluation'],True),('normal_expert_unchanged',candidate,json.loads((W/'normal_contact_groups_r1/PROTOCOL.json').read_text())['settings']+['--out-dir','/tmp/not_created_waist_policy_evaluation'],True),('missing_seed',candidate,without(on,'--environment-seed'),False),('no_policy',candidate,without(on,'--policy-port'),False)]
for label,flags in [('locked',['--motion-protocol','waist_locked_v1']),('h50',['--horizon','50']),('slew',['--policy-max-action-step','.02']),('nan_slew',['--policy-max-action-step','nan']),('probe',['--waist-probe']),('expert',['--waist-coordinated-expert']),('force',['--push-force-n','1']),('wait_force',['--wait-force-n','1']),('idle',['--idle']),('expert_range_flag',['--extended-waist-diagnostic']),('overrange',['--waist-limit-rad','1.01']),('nan_range',['--waist-limit-rad','nan']),('pilot',['--role','pilot']),('unified_prompt',['--prompt-variant','unified_ablation']),('bad_port',['--policy-port','65536'])]:trials.append((label,candidate,on+flags,False))
rows=[]
for label,source,argv,want in trials:
 sys.argv=['collector',*argv];accepted=True;err=io.StringIO()
 try:
  with contextlib.redirect_stderr(err):exec(compile(source.split(marker)[0],'actual_collector_cli','exec'),{'__file__':str(repo/'scripts/collect_paired_sorting.py'),'__name__':'actual_cli'})
 except SystemExit as exc:assert exc.code==2;accepted=False
 assert accepted==want,(label,err.getvalue());rows.append(dict(case=label,accepted=accepted))
# No inference/control/quality behavior edits: suffix differs only in new metadata field.
old=live.split(marker)[1];new=candidate.split(marker)[1].replace(" 'waist_policy_evaluation': args.waist_policy_evaluation,",'')
assert old==new
m=json.loads((stage/'MANIFEST.json').read_text());assert sha(stage/'collect_paired_sorting.py')==m['candidate_collector_sha256']
for p,h in m['source_sha256'].items():assert sha(p)==h,p
out=dict(passed=True,cli_cases=rows,execution_body_unchanged_except_explicit_metadata=True,checker_sha256=sha(__file__),candidate_collector_sha256=m['candidate_collector_sha256'],production_source_unchanged=True,scope='Actual parser/validation prefix; AppLauncher option registration stubbed. No policy connection, model, physical action or training admission demonstrated.',applied=False,training_ready=False)
(stage/'CLI_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
