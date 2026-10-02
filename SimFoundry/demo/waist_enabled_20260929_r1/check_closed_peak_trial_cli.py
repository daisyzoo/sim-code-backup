"""Exercise actual collector pre-launch code, never instantiate AppLauncher."""
from pathlib import Path
import contextlib,datetime,hashlib,io,json,sys,tempfile,copy
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from prepare_closed_peak_trial import parser_namespace
from run_fresh_waist_pilot import prepare
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
stage=W/'staged_closed_peak_trial';collector=stage/'collect_paired_sorting.py'
contracts=sorted((W/'fresh_closed_peak_trial_contracts_r1').glob('fresh_*.json'));assert len(contracts)==12
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector_sha256=sha(collector),accepted=[],rejected=[],simulation_started=False,training_ready=False)
for cp in contracts:
    c,digest,commands=prepare(cp,collector)
    for item in commands:
        args=item['args']+['--out-dir','/tmp/closed_trial_CLI_NO_COLLECTION']
        actual,_=parser_namespace(collector,args,full=True)
        assert actual['role']=='pilot' and not actual['extended_waist_diagnostic']
        report['accepted'].append(dict(contract=cp.name,layout=item['layout_id'],wait=item['wait'],contract_sha256=digest))
# Exercise parent diagnostic path as a regression, without changing role.
ref=json.loads((W/'peak_guard_groups_r1/PROTOCOL.json').read_text())
for item in ref['commands']:
    args=item['args']+['--out-dir','/tmp/closed_trial_CLI_NO_COLLECTION']
    parent,_=parser_namespace(W/'staged_peak_load_guard/collect_paired_sorting.py',args,full=True)
    candidate,_=parser_namespace(collector,args,full=True)
    assert candidate==parent
report['diagnostic_cli_parity_cases']=len(ref['commands'])
base=prepare(contracts[0],collector)[2][0]['args']+['--out-dir','/tmp/closed_trial_CLI_NO_COLLECTION']
def replace(args,key,value):
    args=list(args);args[args.index(key)+1]=value;return args
cases=[]
a=list(base);i=a.index('--waist-pilot-contract');del a[i:i+2];cases.append(('unbound_pilot',a))
cases.extend((label,replace(base,key,value)) for label,key,value in [('changed_load','--expert-frontal-top-load-n','4.'),('changed_horizon','--steps','1199'),('changed_waist','--waist-limit-rad','.9'),('unregistered_layout','--layout-start','999999'),('diagnostic_role_with_contract','--role','diagnostic')])
cases.extend((name,base+[flag]) for name,flag in [('idle','--idle'),('waist_probe','--waist-probe')])
cases.append(('external_force',base+['--push-force-n','1']))
cases.append(('policy',base+['--policy-port','5555']))
with tempfile.TemporaryDirectory(prefix='closed_peak_trial_cli_') as td:
    c=json.loads(contracts[0].read_text())
    for label,mutation in [('lowered_non_target_gate',lambda x:x['gates'].update(non_target_max_xy_m=.02)),('false_profile_binding',lambda x:x.update(closed_expert_profile_sha256='0'*64)),('altered_target_geometry',lambda x:x['layouts'][0]['box_xyz'].__setitem__(0,x['layouts'][0]['box_xyz'][0]+.001)),('changed_training_split',lambda x:x['layouts'][0].update(planned_split='validation' if x['layouts'][0]['planned_split']=='train' else 'train')),('unbound_helper_source',lambda x:x['controller_source_sha256'].__setitem__(next(k for k in x['controller_source_sha256'] if k.endswith('peak_load_bias_guard.py')),'0'*64))]:
        altered=copy.deepcopy(c);mutation(altered);p=Path(td)/(label+'.json');p.write_text(json.dumps(altered));cases.append((label,replace(base,'--waist-pilot-contract',str(p))))
    for label,args in cases:
        try:
            with contextlib.redirect_stderr(io.StringIO()):parser_namespace(collector,args,full=True)
        except (ValueError,SystemExit,AssertionError) as e:
            report['rejected'].append(dict(case=label,error_type=type(e).__name__))
        else:raise AssertionError('Accepted invalid trial: '+label)
report['passed']=True;report['source_sha256']={str(p):sha(p) for p in [Path(__file__),W/'prepare_closed_peak_trial.py',W/'run_fresh_waist_pilot.py',stage/'TRIAL_PROFILE.json']}
with (stage/'CLI_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,accepted=len(report['accepted']),rejected=len(report['rejected']),diagnostic_cli_parity_cases=report['diagnostic_cli_parity_cases'],simulation_started=False)))
