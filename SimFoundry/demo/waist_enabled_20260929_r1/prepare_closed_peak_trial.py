"""Prepare explicit fresh-v2 collection of the closed peak expert; no simulation.
Changes admission only. Keeps controller body and helper bytes unchanged.
"""
from pathlib import Path
import datetime,hashlib,json,sys,types,inspect
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sys.path.insert(0,str(ROOT))
from simfoundry.data.waist_pilot_protocol import semantic_settings,validate_waist_contract,PROTOCOL,GATES,REQUIRED_SOURCES
from simfoundry.data.waist_trial_collection import EXTRA_SOURCES,CATALOG_SHA256
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
REF=W/'peak_guard_groups_r1';PARENT=W/'staged_peak_load_guard';DEST=W/'staged_closed_peak_trial'
RESULT_SHA='5f1ee4d4d1efa03db9493ae561e93b851335d65547fa0a8fa1a9c616c70d67b4'

def parser_namespace(path,cli,*,full=False):
    src=path.read_text();marker='app = AppLauncher(args, enable_cameras=True).app' if full else 'args = parser.parse_args()'
    prefix=src.split(marker)[0]+('' if full else marker+'\n')
    name='closed_trial_cli';m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m;saved=sys.argv
    try:
        sys.argv=[str(path),*cli];exec(compile(prefix,str(path),'exec'),m.__dict__)
        return dict(vars(m.args)),Path(inspect.getfile(m.AppLauncher))
    finally:sys.argv=saved;sys.modules.pop(name,None)

def main():
    assert sha(REF/'RESULT.json')==RESULT_SHA
    result=json.loads((REF/'RESULT.json').read_text());assert len(result['rows'])==10 and all(x['full_length'] and x['all_audits_passed'] for x in result['rows'])
    protocol=json.loads((REF/'PROTOCOL.json').read_text());assert Path(protocol['collector']).resolve()==(PARENT/'collect_paired_sorting.py').resolve()
    original=(PARENT/'collect_paired_sorting.py').read_text();assert sha(PARENT/'collect_paired_sorting.py')==protocol['frozen_files_sha256'][str(PARENT/'collect_paired_sorting.py')]
    if (DEST/'PREPARATION.json').exists():raise ValueError('Completed preparation cannot be overwritten')
    DEST.mkdir(exist_ok=True);copies={}
    for src in PARENT.iterdir():
        if not src.is_file() or not (src.suffix=='.py' or src.name in ['causal_response_parameters.json','elbow_torso_hulls.json']):continue
        target=DEST/src.name
        if target.exists() and src.name!='collect_paired_sorting.py' and sha(target)!=sha(src):raise ValueError('Changed existing helper')
        if not target.exists():target.write_bytes(src.read_bytes())
        copies[src.name]=sha(src)
    cli=list(protocol['commands'][0]['args'])
    for flag in ['--diagnostic-layout-json','--layout-start','--layouts']:
        i=cli.index(flag);del cli[i:i+2]
    cli.remove('--extended-waist-diagnostic');cli[cli.index('--role')+1]='pilot'
    before,launcher=parser_namespace(PARENT/'collect_paired_sorting.py',cli+['--out-dir','/tmp/closed_trial_NO_COLLECTION'])
    actual=json.loads((REF/'case_840001/provenance.json').read_text())
    expected=semantic_settings(actual['args']);prelaunch=semantic_settings(before)
    profile=dict(reference_root=str(REF),reference_result_sha256=RESULT_SHA,reference_protocol_sha256=sha(REF/'PROTOCOL.json'),reference_collector_sha256=sha(PARENT/'collect_paired_sorting.py'),prelaunch_settings=prelaunch,resolved_settings=expected,scope='Collection-only profile; 7/8 diagnostic pushes, failed rear box retained. No training approval.')
    (DEST/'TRIAL_PROFILE.json').write_text(json.dumps(profile,indent=2))
    # All substitutions are confined to pre-launch admission. Runtime body is byte-identical.
    edits=[]
    def replace(old,new):
        nonlocal original
        assert original.count(old)==1,(old,original.count(old));original=original.replace(old,new);edits.append(dict(old=old,new=new))
    admission="""try:
    waist_admission = prepare_waist_pilot(vars(args), Path(__file__).resolve())
except (ValueError, OSError, KeyError) as exc:
    parser.error(str(exc))
diagnostic_or_waist_pilot = args.role == 'diagnostic' or waist_admission is not None
waist_contract_hash = waist_admission.contract_sha256 if waist_admission else None
"""
    replace(admission,'')
    added="""# CLOSED_PEAK_TRIAL_ADMISSION_BEGIN
"""+admission+"""verified_closed_trial = False
if waist_admission is not None:
    trial, _ = validate_waist_contract(waist_admission.contract_path)
    profile_path = STAGE / 'TRIAL_PROFILE.json'
    trial_profile = json.loads(profile_path.read_text())
    reference = Path(trial_profile['reference_root'])
    if (trial.get('version') != 2 or trial.get('closed_expert_profile_sha256') != hashlib.sha256(profile_path.read_bytes()).hexdigest()
            or hashlib.sha256((reference/'RESULT.json').read_bytes()).hexdigest() != trial_profile['reference_result_sha256']
            or hashlib.sha256((reference/'PROTOCOL.json').read_bytes()).hexdigest() != trial_profile['reference_protocol_sha256']
            or semantic_settings(vars(args)) != trial_profile['prelaunch_settings']
            or trial['collector_settings'] != trial_profile['resolved_settings']):
        parser.error('Closed expert trial requires exact v2 source/profile/settings binding')
    verified_closed_trial = True
diagnostic_or_verified_trial = args.role == 'diagnostic' or verified_closed_trial
# CLOSED_PEAK_TRIAL_ADMISSION_END
"""
    # Alter each exact guard line once so reverse reconstruction is unambiguous.
    pre,body=original.split('app = AppLauncher(args, enable_cameras=True).app',1)
    lines=pre.splitlines(keepends=True)
    for line in lines:
        if not line.startswith('if '):continue
        changed=line
        if line.startswith("if args.role != 'diagnostic' or args.waist_pilot_contract"):
            changed="if not diagnostic_or_verified_trial or (args.waist_pilot_contract and not verified_closed_trial) or args.spatial_pilot_contract or args.recovery_pilot_contract:\n"
        else:
            changed=changed.replace("args.role!='diagnostic'",'not diagnostic_or_verified_trial').replace("args.role=='diagnostic'",'diagnostic_or_verified_trial')
        if changed!=line:replace(line,changed)
    replace('args = parser.parse_args()\n','args = parser.parse_args()\n'+added)
    target=DEST/'collect_paired_sorting.py';target.write_text(original)
    recovered=original
    for edit in reversed(edits):
        assert recovered.count(edit['new'])==1 if edit['new'] else True
        if edit['new']:recovered=recovered.replace(edit['new'],edit['old'])
        else:
            # Original admission occupied the boundary before bounded lead guards.
            marker='if args.expert_top_object_relative_lead_m and not ('
            assert recovered.count(marker)==1;recovered=recovered.replace(marker,edit['old']+marker)
    assert recovered==(PARENT/'collect_paired_sorting.py').read_text()
    assert original.split('app = AppLauncher(args, enable_cameras=True).app',1)[1]==(PARENT/'collect_paired_sorting.py').read_text().split('app = AppLauncher(args, enable_cameras=True).app',1)[1]
    # Bind actual runtime dependencies, including the new staged helper copies.
    hashes={k:sha(ROOT/k) for k in set(actual['source_sha256'])|REQUIRED_SOURCES|EXTRA_SOURCES if not k.startswith(str(PARENT.relative_to(ROOT))+'/')}
    hashes.update({str(p.relative_to(ROOT)):sha(p) for p in DEST.iterdir() if p.is_file() and p.name!='collect_paired_sorting.py'})
    catalog=W/'fresh_pilot_layout_proposal_r1/PROPOSAL.json';assert sha(catalog)==CATALOG_SHA256
    proposal=json.loads(catalog.read_text());out=W/'fresh_closed_peak_trial_contracts_r1';out.mkdir(exist_ok=True);contracts=[]
    for name in sorted(proposal['plan_sha256']):
        gp=catalog.parent/name;plan=json.loads(gp.read_text())
        c=dict(version=2,admission_kind='frozen_trial_collection',collection_admission_only=True,training_ready=False,approved_for_pilot=True,motion_protocol=PROTOCOL,gates=GATES,feasibility=[],collector_settings=expected,prelaunch_collector_settings=prelaunch,collection_cli=cli,pilot_collector_sha256=sha(target),controller_source_sha256=hashes,layouts=plan['layouts'],wait_layouts=plan['wait_layouts'],trial_plan=dict(catalog_path=str(catalog),catalog_sha256=sha(catalog),group_plan_path=str(gp),group_plan_sha256=sha(gp)),profile_reference=profile,closed_expert_profile_sha256=sha(DEST/'TRIAL_PROFILE.json'),launcher_source=dict(path=str(launcher),sha256=sha(launcher)),builder_sha256=sha(__file__),scope='Original complete frozen trial group; all original gates and complete-pair admission remain. Not training permission.')
        path=out/name
        if path.exists():
            prior=json.loads(path.read_text());candidate=dict(c);candidate['builder_sha256']=prior['builder_sha256']
            assert candidate==prior,'Existing contract changed'
        else:path.write_text(json.dumps(c,indent=2))
        validate_waist_contract(path)
        contracts.append(dict(path=str(path),sha256=sha(path),group=gp.stem,split=plan['layouts'][0]['planned_split']))
    report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stage=str(DEST),collector_sha256=sha(target),reference_result_sha256=RESULT_SHA,admission_only_edits=edits,reverse_reconstruction_matches_parent=True,post_launcher_runtime_body_unchanged=True,copied_source_sha256=copies,contracts=contracts,training_ready=False,simulation_started=False,next='Exercise full real CLI and rejection paths, adapt native auditors to explicit pilot source contract, budget original60 fresh episodes, then launch only after current diagnostic closes.')
    (DEST/'PREPARATION.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k] for k in ['stage','reverse_reconstruction_matches_parent','post_launcher_runtime_body_unchanged','training_ready','simulation_started']},indent=2))

if __name__=='__main__':main()
