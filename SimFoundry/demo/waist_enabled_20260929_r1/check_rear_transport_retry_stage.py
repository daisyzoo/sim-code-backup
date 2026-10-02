"""Actual parser/collector constructor selection and independent retry corruption checks."""
from pathlib import Path
from types import SimpleNamespace
import sys,ast,json,hashlib,datetime,copy,contextlib,io
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_transport_retry';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
from audit_rear_transport_witness import EventAudit
from audit_rear_transport_retry_witness import verify_retry_witness
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((S/'PREPARATION.json').read_text());frozen={str(S/n):h for n,h in prep['stage_sha256'].items()};frozen[str(Path(__file__))]=sha(__file__)
for p,h in frozen.items():assert sha(p)==h,p
source=W/'rear_tracking_physical_r1/case_840015/layout_840015_push_box_to_bin/REAR_TRANSPORT_FEASIBLE_RETRY_FAILURE_CHECK.json';record=json.loads(source.read_text());event=json.loads((source.parent/'recontact_pose.json').read_text())['rows'][-1];sources={str(source):sha(source),str(source.parent/'recontact_pose.json'):sha(source.parent/'recontact_pose.json')};dest=S/'CHECK.json';assert not dest.exists();rows=[];negative=[]
base=list(json.loads((W/'rear_tracking_physical_preparation_r1/PLAN.json').read_text())['commands'][0]['args']);tree=ast.parse((S/'collect_paired_sorting.py').read_text());blocks=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.unloaded_recontact_pose' and any(isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='recontact_lifecycle' for t in x.targets) for x in n.body)];assert len(blocks)==1
construct=compile(ast.fix_missing_locations(ast.Module(body=blocks,type_ignores=[])),str(S/'collect_paired_sorting.py'),'exec')
for name,args,expected in [('default_off',base,True),('enabled',base+['--rear-transport-feasible-retry'],True),('missing_recovery',[x for x in base if x not in ['--rear-corridor-recovery','--rear-corridor-hysteresis','--rear-recovery-tracking']]+['--rear-transport-feasible-retry'],False)]:
 try:
  with contextlib.redirect_stderr(io.StringIO()):settings,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True)
  valid=True
 except (ValueError,SystemExit):valid=False
 assert valid==expected
 if not valid:negative.append(name);continue
 assert settings['rear_transport_feasible_retry']==(name=='enabled');sys.path[:0]=[str(S),str(W),str(ROOT)]
 for side in ['left','right']:
  env=dict(args=SimpleNamespace(**settings),side=side);exec(construct,env);obj=env['recontact_lifecycle'];child=getattr(obj,'original',obj)
  assert getattr(child,'transport_feasible_retry',False)==(name=='enabled')
  expected_module=('rear_transport_retry_entry_lifecycle' if side=='right' else 'rear_transport_retry_lifecycle') if name=='enabled' else ('rear_transport_entry_lift_lifecycle' if side=='right' else 'rear_transport_recontact_lifecycle')
  assert type(obj).__module__==expected_module;rows.append(dict(case=name,side=side,module=expected_module,actual_collector_constructor=True))
audit=EventAudit(ROOT,S);witness=record['candidate'];ctx=event['context'];proof=verify_retry_witness(audit,witness,endpoint=ctx['current'],scene=ctx['scene'],retry_enabled=True);assert proof['retry_attempted'] and proof['original_failed_seed_geometry_passed']
mutations=[('missing_metadata',lambda x:x.pop('feasible_endpoint_retry')),('two_retries',lambda x:x['feasible_endpoint_retry'].update(maximum_extra_retries=2)),('bool_retry_count',lambda x:x['feasible_endpoint_retry'].update(maximum_extra_retries=True)),('changed_tolerance',lambda x:x['feasible_endpoint_retry'].update(original_ftol=1e-6)),('accepted_original',lambda x:x['feasible_endpoint_retry']['original_attempt'].update(accepted=True)),('success_original',lambda x:x['feasible_endpoint_retry']['original_attempt'].update(solver_status=0)),('fake_seed',lambda x:x['feasible_endpoint_retry']['original_attempt']['candidate'].__setitem__(0,99.)),('wrong_seed_residual',lambda x:x['feasible_endpoint_retry']['original_attempt']['equality_residual_m'].__setitem__(0,.001)),('false_no_retry',lambda x:x['feasible_endpoint_retry'].update(attempted=False))]
for label,mutate in mutations:
 bad=copy.deepcopy(witness);mutate(bad)
 try:verify_retry_witness(audit,bad,endpoint=ctx['current'],scene=ctx['scene'],retry_enabled=True)
 except (AssertionError,ValueError,KeyError):negative.append(label)
 else:raise AssertionError('Corruption accepted '+label)
for p,h in {**sources,**frozen}.items():assert sha(p)==h,p
for n in ['audit_rear_transport_retry_witness.py','audit_rear_transport_witness.py']:frozen[str(W/n)]=sha(W/n)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='complete',passed=True,scope=__doc__,rows=rows,negative_checks=negative,independent_retry_witness=proof,source_sha256=sources,frozen_sha256=frozen,simulation_started=False,training_ready=False)
with dest.open('x') as f:json.dump(out,f,indent=2)
print('passed actual constructor selections',len(rows),'negative checks',len(negative))
