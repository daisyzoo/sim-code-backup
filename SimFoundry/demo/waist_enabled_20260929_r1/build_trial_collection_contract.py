"""Collection permission for an unchanged pre-outcome group; no data approval."""
from pathlib import Path
import argparse,hashlib,json,sys,types,inspect
W=Path(__file__).resolve().parent
if W.name=='staged_trial_collection':W=W.parent
REPO=W.parents[1];sys.path.insert(0,str(REPO))
from simfoundry.data.waist_pilot_protocol import PROTOCOL,GATES,REQUIRED_SOURCES,semantic_settings,validate_manifest,validate_waist_contract
from simfoundry.data.waist_trial_collection import EXTRA_SOURCES,CATALOG_SHA256
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
PARENT_RESULT_SHA='bba3f6c0de13598d68eb6fa2492a2990a8a0d8be703d47caa3b38feb183ab3c6'

def build(group_path,source_root,out):
    group_path=Path(group_path).resolve();source_root=Path(source_root).resolve();out=Path(out)
    if out.exists():raise ValueError('Never overwrite an issued contract')
    catalog=W/'fresh_pilot_layout_proposal_r1/PROPOSAL.json'
    if sha(catalog)!=CATALOG_SHA256:raise ValueError('Original catalog changed')
    parent=W/'y_path_nearhalf_groups_r1'
    if sha(parent/'RESULT.json')!=PARENT_RESULT_SHA:raise ValueError('Parent profile comparison changed')
    profile=json.loads((parent/'PROTOCOL.json').read_text());cli=list(profile['settings'])
    cli[cli.index('--role')+1]='pilot';cli=[x for x in cli if x!='--extended-waist-diagnostic']
    if '--expert-top-contact-bout-yaw-hold' in cli:raise ValueError('Rejected yaw candidate cannot enter trial')
    plan=json.loads(group_path.read_text());collector=source_root/'scripts/collect_paired_sorting.py'
    settings=semantic_settings(json.loads((parent/'case_897002/provenance.json').read_text())['args']);settings['expert_top_contact_bout_yaw_hold']=False
    # Exact live source bytes, including admission, complete profile and physics dependencies.
    rels={str(Path(p).relative_to(REPO)) for p in profile['source_sha256']}|REQUIRED_SOURCES|EXTRA_SOURCES
    hashes={p:sha(source_root/p) for p in rels if p!='scripts/collect_paired_sorting.py'}
    source=collector.read_text();marker='try:\n    waist_admission = prepare_waist_pilot'
    if source.count(marker)!=1:raise ValueError('Unknown real parser boundary')
    name='trial_builder_parser';module=types.ModuleType(name);module.__file__=str(collector);sys.modules[name]=module;saved=sys.argv
    try:
        sys.argv=['collector',*cli,'--out-dir','/tmp/trial_builder_NO_COLLECTION','--layout-start',str(plan['layouts'][0]['layout_id']),'--wait-layout-start',str(plan['wait_layouts'][0]['layout_id']),'--wait-episodes','1']
        exec(compile(source.split(marker)[0],str(collector),'exec'),module.__dict__)
        prelaunch=semantic_settings(vars(module.args));launcher=Path(inspect.getfile(module.AppLauncher))
    finally:sys.argv=saved;sys.modules.pop(name,None)
    contract=dict(version=2,admission_kind='frozen_trial_collection',collection_admission_only=True,training_ready=False,approved_for_pilot=True,motion_protocol=PROTOCOL,gates=GATES,feasibility=[],collector_settings=settings,prelaunch_collector_settings=prelaunch,collection_cli=cli,pilot_collector_sha256=sha(collector),controller_source_sha256=hashes,layouts=plan['layouts'],wait_layouts=plan['wait_layouts'],trial_plan=dict(catalog_path=str(catalog.resolve()),catalog_sha256=sha(catalog),group_plan_path=str(group_path),group_plan_sha256=sha(group_path)),profile_reference=dict(root=str(parent.resolve()),result_sha256=PARENT_RESULT_SHA,scope='Controller settings reference only; parent failed groups remain rejected. Not feasibility approval.'),launcher_source=dict(path=str(launcher),sha256=sha(launcher)),builder_sha256=sha(__file__),scope='Original frozen group trial collection only; every recorded full swap+wait requires unchanged original quality, source archive, actual review and converter admission. Not permission to train failures.')
    validate_manifest(contract)
    out.parent.mkdir(parents=True,exist_ok=True);pending=out.with_name(out.name+'.pending')
    if pending.exists():raise ValueError('Existing pending contract')
    pending.write_text(json.dumps(contract,indent=2))
    try:validate_waist_contract(pending)
    except BaseException:pending.unlink();raise
    pending.rename(out)
    return dict(path=str(out.resolve()),sha256=sha(out),training_ready=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--layout-plan',type=Path,required=True);p.add_argument('--source-root',type=Path,default=REPO);p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(json.dumps(build(a.layout_plan,a.source_root,a.out),indent=2))
