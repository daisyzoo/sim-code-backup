"""Prepare isolated default-off instrumentation; no simulator or collection launch."""
from pathlib import Path
import shutil,hashlib,json,datetime,ast
W=Path(__file__).resolve().parent;parent=W/'staged_box_inward_correction';stage=W/'staged_substep_observer'
assert not stage.exists();stage.mkdir()
for p in parent.iterdir():
 if p.is_file() and (p.suffix=='.py' or (p.suffix=='.json' and p.name==p.name.lower())):shutil.copy2(p,stage/p.name)
helpers=['substep_contact_observer_prototype.py','substep_contact_runtime_bridge.py','substep_contact_recording.py','substep_contact_setup.py']
for name in helpers:shutil.copy2(W/name,stage/name)
base=(parent/'collect_paired_sorting.py').read_text();source=base;blocks=[]
def add(anchor,code,*,after=False,indent=''):
 global source
 assert source.count(anchor)==1,anchor
 block=indent+'# SUBSTEP_OBSERVER_BEGIN\n'+code+indent+'# SUBSTEP_OBSERVER_END\n'
 source=source.replace(anchor,anchor+block if after else block+anchor);blocks.append(block)
add("parser = argparse.ArgumentParser()\n","parser.add_argument('--trace-substep-contacts',action='store_true',help='Diagnostic-only independent24-substep contact tracing; controller feedback unchanged.')\n",after=True)
add('args = parser.parse_args()\n',"if args.trace_substep_contacts and (args.role!='diagnostic' or not args.trace_solved_contact_forces or args.policy_port or args.idle or args.wait_force_n or args.push_force_n):\n    parser.error('Substep observation requires diagnostic expert and original solved-contact observer, without policy/idle/forces')\n",after=True)
add('    solved_contact_forces = []\n',"    if args.trace_substep_contacts:\n        from substep_contact_recording import EpisodeSubstepRecording\n        substep_recording = EpisodeSubstepRecording(env._substep_contact_bridge)\n",after=True,indent='    ')
step='        obs, _, terminated, truncated, _ = env.step(torch.tensor(action[None], device=env.device))\n'
add(step,"        if args.trace_substep_contacts:\n            env._substep_contact_bridge.begin(step)\n",indent='        ')
add(step,"        if args.trace_substep_contacts:\n            substep_packet = env._substep_contact_bridge.finish()\n",after=True,indent='        ')
add('            solved_contact_forces.append(force_record)\n',"            if args.trace_substep_contacts:\n                substep_recording.record(substep_packet,force_record)\n",after=True,indent='            ')
add("    (folder / 'quality.json').write_text(json.dumps(report, indent=2))\n","    if args.trace_substep_contacts:\n        substep_recording.save(folder,len(qs))\n",indent='    ')
add('    for path in paths:\n',"    if args.trace_substep_contacts:\n        paths.extend([STAGE/name for name in ['substep_contact_observer_prototype.py','substep_contact_runtime_bridge.py','substep_contact_recording.py','substep_contact_setup.py']])\n",indent='    ')
add('        env = ManagerBasedRLEnv(cfg=cfg)\n',"        if args.trace_substep_contacts:\n            from substep_contact_setup import install_observer\n            install_observer(env,cfg,root)\n",after=True,indent='        ')
restored=source
for block in blocks:
 assert restored.count(block)==1;restored=restored.replace(block,'')
assert restored==base;ast.parse(source)
(stage/'collect_paired_sorting.py').write_text(source)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_collector_sha256=sha(parent/'collect_paired_sorting.py'),new_collector_sha256=sha(stage/'collect_paired_sorting.py'),instrumentation_blocks=blocks,removing_instrumentation_recovers_parent_byte_exact=True,original_helper_source_unchanged=all(sha(stage/p.name)==sha(p) for p in parent.iterdir() if p.is_file() and (stage/p.name).exists() and p.name!='collect_paired_sorting.py'),helpers=helpers,source_sha256={str(p):sha(p) for p in [Path(__file__),*[W/n for n in helpers],*[p for p in stage.iterdir() if p.is_file()]]},actual_runtime_launched=False,training_ready=False)
assert report['original_helper_source_unchanged'];(stage/'PREPARATION.json').write_text(json.dumps(report,indent=2));print('STAGED_NOT_LAUNCHED',stage,len(blocks),'instrumentation-only blocks')
