"""Bind reviewed full runs to a fresh pilot schedule; never promote raw diagnostics.

The resulting contract permits collection only. Every new episode still needs
original gates, actual visual review and converter checks before training.
"""
from pathlib import Path
import argparse,hashlib,json,sys,types,inspect
import numpy as np
W=Path(__file__).resolve().parent;REPO=W.parents[1];sys.path.insert(0,str(REPO))
from simfoundry.data.waist_pilot_protocol import (PROTOCOL,GATES,REQUIRED_SOURCES,
    semantic_settings,validate_feasibility,validate_manifest,validate_waist_contract)
from simfoundry.data.paired_sorting import audit_rollout
from simfoundry.data.prompts import PAIRED_SORTING_PROMPTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def checked_wait(run,settings,controller_hashes):
    run=run.resolve();protocol=json.loads((run/'PROTOCOL.json').read_text())
    status=json.loads((run/'STATUS.json').read_text())
    if status.get('stage')!='numeric_complete_actual_visual_review_pending' or status.get('original_wait_passed') is not True:
        raise ValueError('Wait run is incomplete or failed')
    eps=[p.parent for p in run.glob('case*/layout_*/WAIT_STABILITY_AUDIT.json')]
    if len(eps)!=1:raise ValueError('Expected one ordinary reviewed wait')
    ep=eps[0];audit=json.loads((ep/'WAIT_STABILITY_AUDIT.json').read_text())
    if not audit.get('passed') or audit.get('errors') or audit.get('actual_visual_review')!='completed_actual_view_8RGB':
        raise ValueError('Wait has no completed numeric and actual visual review')
    for name,key in [('raw.npz','raw_sha256'),('trace.npz','trace_sha256'),('REVIEW_EVENTS.jpg','review_sheet_sha256')]:
        if sha(ep/name)!=audit[key]:raise ValueError('Changed wait evidence: '+name)
    if sha(ep.parent/'provenance.json')!=audit['provenance_sha256']:raise ValueError('Changed wait provenance')
    provenance=json.loads((ep.parent/'provenance.json').read_text())
    if semantic_settings(provenance['args'])!=settings:raise ValueError('Wait settings differ from push feasibility')
    for rel,digest in controller_hashes.items():
        if provenance['source_sha256'].get(rel)!=digest or sha(ep.parent/'source_snapshot'/rel)!=digest:
            raise ValueError('Wait controller snapshot differs: '+rel)
    for source,digest in protocol['source_sha256'].items():
        if Path(source).name!='collect_paired_sorting.py' and sha(source)!=digest:raise ValueError('Changed wait control source')
    collector_rel='scripts/collect_paired_sorting.py';old_collector=protocol['source_sha256'][str(REPO/collector_rel)]
    if provenance['source_sha256'][collector_rel]!=old_collector or sha(ep.parent/'source_snapshot'/collector_rel)!=old_collector:
        raise ValueError('Changed frozen wait collector')
    with np.load(ep/'raw.npz') as z,np.load(ep/'trace.npz') as tr:
        meta=json.loads(str(z['collect_meta']))
        if str(z['task_id'])!='wait_no_package' or str(z['instruction'])!=PAIRED_SORTING_PROMPTS['wait_no_package']:
            raise ValueError('Wrong wait instruction')
        for key,want in [('assist_frames',0),('push_assist',False),('motion_protocol',PROTOCOL),('idle_diagnostic',False),('waist_probe',False),('wait_force_n',0.),('push_force_n',0.),('collision_pipeline','newton')]:
            if meta.get(key)!=want:raise ValueError('Invalid ordinary wait metadata: '+key)
        if z['q'].shape!=(settings['wait_steps'],23) or z['action'].shape!=z['q'].shape:raise ValueError('Wait frame count differs')
        report=audit_rollout('wait_no_package',z['q'],z['action'],dict(tr),motion_protocol=PROTOCOL,
            waist_limit_rad=settings['waist_limit_rad'],waist_wait_tolerance_rad=settings['waist_wait_tolerance_rad'])
        if not report['passed']:raise ValueError('Recomputed wait failed original gates')
    return dict(root=str(run),episode=str(ep),audit_sha256=sha(ep/'WAIT_STABILITY_AUDIT.json'),
        protocol_sha256=sha(run/'PROTOCOL.json'),raw_sha256=sha(ep/'raw.npz'),review_sheet_sha256=sha(ep/'REVIEW_EVENTS.jpg'))

def prelaunch_snapshot(collector, cli, layouts, waits):
    # Run the real argument registration only; never construct AppLauncher.
    source=collector.read_text();marker='try:\n    waist_admission = prepare_waist_pilot'
    if source.count(marker)!=1:raise ValueError('Unknown admission/parser boundary')
    prefix=source.split(marker)[0];argv=list(cli);argv[argv.index('--role')+1]='pilot'
    argv=[x for x in argv if x!='--extended-waist-diagnostic']
    argv+=['--out-dir','/tmp/waist_contract_parser_no_output','--layout-start',str(layouts[0]['layout_id']),
           '--wait-layout-start',str(waits[0]['layout_id']),'--wait-episodes','1']
    saved=list(sys.argv);name='waist_contract_real_parser';module=types.ModuleType(name)
    module.__file__=str(collector.resolve());sys.modules[name]=module
    try:
        sys.argv=['collector',*argv];exec(compile(prefix,str(collector),'exec'),module.__dict__)
        raw=semantic_settings(vars(module.args))
        launcher_source=Path(inspect.getfile(module.AppLauncher))
        return raw,dict(path=str(launcher_source),sha256=sha(launcher_source))
    finally:sys.argv=saved;sys.modules.pop(name,None)

def build(feasibility,wait_run,layout_plan,collector,out):
    if out.exists():raise ValueError('Never overwrite a contract')
    if not feasibility:raise ValueError('No complete feasibility runs')
    sources=[];settings=None;hashes=None;diagnostic_ids=set()
    for run in feasibility:
        run=run.resolve();ready=json.loads((run/'COMPLETE_GROUP_READINESS.json').read_text())
        if not ready.get('complete_group_feasibility_passed') or ready.get('errors'):raise ValueError('Incomplete or failed feasibility: '+str(run))
        first=Path(ready['rows'][0]['path']);prov=json.loads((first.parent/'provenance.json').read_text());current=semantic_settings(prov['args'])
        protocol=json.loads((run/'PROTOCOL.json').read_text())
        source_hashes={rel:protocol['source_sha256'][str(REPO/rel)] for rel in REQUIRED_SOURCES}
        if settings is None:settings=current;hashes=source_hashes
        if current!=settings or source_hashes!=hashes:raise ValueError('Mixed settings or controller versions')
        if not REQUIRED_SOURCES<=set(hashes):raise ValueError('Missing controller source bindings')
        item=dict(root=str(run),readiness_sha256=sha(run/'COMPLETE_GROUP_READINESS.json'),result_sha256=sha(run/'RESULT.json'),protocol_sha256=sha(run/'PROTOCOL.json'))
        diagnostic_ids.update(validate_feasibility(item,settings,hashes));sources.append(item)
    wait=checked_wait(wait_run,settings,hashes)
    plan=json.loads(layout_plan.read_text());layouts=plan['layouts'];waits=plan['wait_layouts']
    # A contract may cover one complete group in one split. The production
    # converter combines contracts and enforces global train/validation task
    # coverage; requiring both splits here would unnecessarily couple groups.
    text=collector.read_text()
    if "--waist-pilot-contract" not in text or 'prepare_waist_pilot(vars(args)' not in text:raise ValueError('Collector has no explicit admission wiring')
    prelaunch,launcher_source=prelaunch_snapshot(collector,json.loads((feasibility[0]/'PROTOCOL.json').read_text())['settings'],layouts,waits)
    contract=dict(prelaunch_collector_settings=prelaunch,launcher_source=launcher_source,version=1,motion_protocol=PROTOCOL,approved_for_pilot=True,gates=GATES,
        collector_settings=settings,controller_source_sha256=hashes,pilot_collector_sha256=sha(collector),
        feasibility=sources,layouts=layouts,wait_layouts=waits,ordinary_wait_evidence=wait,
        layout_plan_sha256=sha(layout_plan),builder_sha256=sha(__file__),training_ready=False,
        scope='Permits fresh collection only. Diagnostics remain excluded; full original gates, complete swaps, actual review and train-only conversion remain required.')
    validate_manifest(contract)
    if diagnostic_ids & {x['layout_id'] for x in layouts+waits}:raise ValueError('Reused diagnostic IDs')
    # Validate the exact bytes before atomic publication; failures leave no contract.
    pending=out.with_name(out.name+'.pending');pending.parent.mkdir(parents=True,exist_ok=True)
    if pending.exists():raise ValueError('Existing pending contract needs inspection')
    pending.write_text(json.dumps(contract,indent=2))
    try:validate_waist_contract(pending)
    except BaseException:pending.unlink();raise
    pending.rename(out)
    return dict(path=str(out.resolve()),sha256=sha(out),push_layouts=len(layouts),wait_layouts=len(waits),training_ready=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--feasibility',type=Path,nargs='+',required=True);p.add_argument('--wait-run',type=Path,required=True);p.add_argument('--layout-plan',type=Path,required=True);p.add_argument('--collector',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    print(json.dumps(build(a.feasibility,a.wait_run,a.layout_plan,a.collector,a.out),indent=2))
