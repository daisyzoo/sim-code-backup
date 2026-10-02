"""Prepare a new isolated default-off candidate only after reference closure.
--check-only validates source construction without creating a stage or running
physics. Original observer/controller sources remain immutable.
"""
from pathlib import Path
import argparse
import ast
import datetime
import hashlib
import json
import shutil

W=Path(__file__).resolve().parent
parent=W/'staged_substep_observer'
stage=W/'staged_peak_load_guard'
reference=W/'substep_reference03_groups_r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
helpers=['peak_load_bias_guard.py','peak_load_control_adapter.py','peak_load_observation.py','peak_load_update_trace.py']


def construct():
    base=(parent/'collect_paired_sorting.py').read_text()
    source=base;blocks=[]
    def add(anchor,code,*,after=False,indent=''):
        nonlocal source
        assert source.count(anchor)==1,anchor
        block=indent+'# PEAK_LOAD_GUARD_BEGIN\n'+code+indent+'# PEAK_LOAD_GUARD_END\n'
        source=source.replace(anchor,anchor+block if after else block+anchor)
        blocks.append(block)
    add('parser = argparse.ArgumentParser()\n',
        "parser.add_argument('--peak-load-bias-guard',action='store_true',help='Diagnostic previous-action peak guard for downward pressure-bias increments; default off.')\n",after=True)
    add('args = parser.parse_args()\n',
        "if args.peak_load_bias_guard and (args.role!='diagnostic' or not args.trace_substep_contacts or not args.expert_frontal_top_recontact or args.expert_frontal_top_load_n!=5. or args.expert_top_tilt_recontact_rad!=.03 or args.policy_port or args.idle or args.expert_contact_load_n or args.expert_frontal_load_n or args.wait_force_n or args.push_force_n):\n"
        "    parser.error('Peak guard requires original5N/.03 diagnostic top expert, complete substep observer, no policy/idle/other force controller')\n",after=True)
    add('                frontal_state.load.desired_n=args.expert_frontal_top_load_n\n',
        "                if args.peak_load_bias_guard:\n"
        "                    from peak_load_update_trace import TracedPeakLoadControl\n"
        "                    parent_load = frontal_state.load\n"
        "                    frontal_state.load = TracedPeakLoadControl(parent_load.desired_n,bias_m=parent_load.bias_m,filtered_n=parent_load.filtered_n,min_bias_m=parent_load.min_bias_m)\n"
        "                    frontal_state.load.bind_owner(frontal_state)\n"
        "                    frontal_plan['peak_load_bias_guard'] = dict(enabled=True,previous_action_substeps=24,peak_threshold_multiplier=2.,negative_increment_only=True,original_filter_and_upward_relief=True,original_guard_priority=True,training_ready=False)\n",
        after=True,indent='                ')
    add('    force_log = []\n',
        "    if args.peak_load_bias_guard:\n        peak_load_frame_log = []\n",after=True,indent='    ')
    add("                waypoint = frontal_state.update(palm_xyz(robot,hands[side]),parcel_xyz(env,target_actor),parcel_xyz(env,obstacle_actor),\n",
        "                if args.peak_load_bias_guard:\n"
        "                    from peak_load_observation import extract as extract_peak_observation\n"
        "                    if len(substep_recording.rows)!=step:\n                        raise ValueError('Missing preceding complete action observation')\n"
        "                    peak_observation = extract_peak_observation(substep_recording.rows[-1],env._substep_contact_bridge.metadata,after_action_step=step-1,side=side,target_name=target_actor)\n"
        "                    frontal_state.load.observe(action_step=step,after_action_step=step-1,vertical_load_n=peak_observation['vertical_load_n'])\n",
        indent='                ')
    add('                frontal_log.append(dict(step=step,**waypoint))\n',
        "                if args.peak_load_bias_guard:\n"
        "                    peak_load_frame_log.append(dict(step=step,mode=waypoint['mode'],top_mode=frontal_state.top_mode,bias_m=frontal_state.load.bias_m,filtered_n=frontal_state.load.filtered_n,pressure_update_count=len(frontal_state.load.updates)))\n",
        indent='                ')
    add('    if clearance_guard is not None and len(qs)<10:\n',
        "    if args.peak_load_bias_guard:\n        episode.collect_meta['peak_load_bias_guard']=True\n",indent='    ')
    add("    (folder / 'quality.json').write_text(json.dumps(report, indent=2))\n",
        "    if args.peak_load_bias_guard:\n"
        "        peak_updates = frontal_state.load.updates if frontal_state is not None else []\n"
        "        (folder/'peak_load_updates.json').write_text(json.dumps(dict(rows=peak_updates,final_control_states=peak_load_frame_log,executed_action_count=len(qs),wait=task_id=='wait_no_package',training_ready=False,scope='Pressure mutation boundary; original phase/reset and executed-action audits remain required.'),indent=2))\n",
        indent='    ')
    add('    for path in paths:\n',
        "    if args.peak_load_bias_guard:\n        paths.extend([STAGE/name for name in "+repr(helpers)+"])\n",indent='    ')
    restored=source
    for block in blocks:
        assert restored.count(block)==1
        restored=restored.replace(block,'')
    assert restored==base
    ast.parse(source)
    return source,blocks


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check-only',action='store_true');args=parser.parse_args()
    protocol=json.loads((reference/'PROTOCOL.json').read_text())
    for path,digest in protocol['frozen_files_sha256'].items():assert sha(path)==digest,path
    for name in ['PEAK_LOAD_BIAS_GUARD_BOUNDARY_CHECK.json','PEAK_LOAD_CONTROL_ADAPTER_CHECK.json','PEAK_LOAD_OBSERVATION_CHECK.json','PEAK_LOAD_UPDATE_MATH_CHECK.json']:
        report=json.loads((W/name).read_text());assert report['passed']
        for path,digest in report['source_sha256'].items():
            p=Path(path);p=p if p.is_absolute() else W/p
            assert sha(p)==digest,path
    source,blocks=construct()
    if args.check_only:
        print(json.dumps(dict(source_construction_valid=True,blocks=len(blocks),
                              parent_recovered_byte_exact=True,stage_created=False,physical_launched=False)))
        return
    result=json.loads((reference/'RESULT.json').read_text())
    assert result['status']=='diagnostic_closed_not_training_admission' and len(result['rows'])==10
    assert result['actual_sampled_visual_review_complete'] and all(r['all_audits_passed'] for r in result['rows'])
    for name in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','ADDITIONAL_AUDIT_EXECUTION.json']:
        status=json.loads((reference/name).read_text());assert not Path(f"/proc/{status['pid']}/cmdline").exists()
    assert not stage.exists();stage.mkdir()
    for p in parent.iterdir():
        if p.is_file() and (p.suffix=='.py' or (p.suffix=='.json' and p.name==p.name.lower())):
            shutil.copy2(p,stage/p.name)
    for name in helpers:shutil.copy2(W/name,stage/name)
    (stage/'collect_paired_sorting.py').write_text(source)
    unchanged=all(sha(stage/p.name)==sha(p) for p in parent.iterdir()
                  if p.is_file() and (stage/p.name).exists() and p.name!='collect_paired_sorting.py')
    assert unchanged
    report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                parent_collector_sha256=sha(parent/'collect_paired_sorting.py'),
                parent_result_sha256=sha(reference/'RESULT.json'),
                new_collector_sha256=sha(stage/'collect_paired_sorting.py'),
                candidate_blocks=blocks,removing_candidate_recovers_parent_byte_exact=True,
                original_helpers_unchanged=unchanged,helpers=helpers,training_ready=False,
                actual_runtime_launched=False,
                source_sha256={str(p):sha(p) for p in [Path(__file__),*[W/n for n in helpers],
                               *[p for p in stage.iterdir() if p.is_file()]]})
    (stage/'PREPARATION.json').write_text(json.dumps(report,indent=2))
    print('STAGED_NOT_LAUNCHED',stage)


if __name__=='__main__':main()
