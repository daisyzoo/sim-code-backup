"""Construct an isolated final-sample guard after full parent closure.
--check-only builds and validates source in memory, without creating a stage.
Original physics, observer, phases and default-off behavior remain unchanged.
"""
from pathlib import Path
import argparse,ast,datetime,hashlib,json,shutil
W=Path(__file__).resolve().parent
parent=W/'staged_peak_load_guard';stage=W/'staged_instant_load_guard';reference=W/'peak_guard_groups_r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
helpers=['instant_load_bias_guard.py','instant_load_control_adapter.py','instant_load_update_trace.py']
checks=['INSTANT_LOAD_BIAS_GUARD_CHECK.json','INSTANT_LOAD_CONTROL_ADAPTER_CHECK.json','INSTANT_LOAD_UPDATE_MATH_CHECK.json','INSTANT_GUARD_PRESSURE_STREAM_CHECK.json']

def construct():
    base=(parent/'collect_paired_sorting.py').read_text();source=base;blocks=[]
    def add(anchor,code,*,after=False,indent=''):
        nonlocal source
        assert source.count(anchor)==1,anchor
        block=indent+'# INSTANT_LOAD_GUARD_BEGIN\n'+code+indent+'# INSTANT_LOAD_GUARD_END\n'
        source=source.replace(anchor,anchor+block if after else block+anchor);blocks.append(block)
    add('parser = argparse.ArgumentParser()\n',"parser.add_argument('--instant-load-bias-guard',action='store_true',help='Diagnostic final-sample pressure guard; requires peak guard and defaults off.')\n",after=True)
    add('args = parser.parse_args()\n',"if args.instant_load_bias_guard and not args.peak_load_bias_guard:\n    parser.error('Instant load guard requires the original peak guard and its diagnostic5N/.03 restrictions')\n",after=True)
    add('                    frontal_state.load.bind_owner(frontal_state)\n',
        "                    if args.instant_load_bias_guard:\n"
        "                        from instant_load_update_trace import TracedInstantLoadControl\n"
        "                        peak_load = frontal_state.load\n"
        "                        frontal_state.load = TracedInstantLoadControl(peak_load.desired_n,bias_m=peak_load.bias_m,filtered_n=peak_load.filtered_n,min_bias_m=peak_load.min_bias_m)\n",indent='                    ')
    add("                    frontal_plan['peak_load_bias_guard'] = dict(enabled=True,previous_action_substeps=24,peak_threshold_multiplier=2.,negative_increment_only=True,original_filter_and_upward_relief=True,original_guard_priority=True,training_ready=False)\n",
        "                    if args.instant_load_bias_guard:\n"
        "                        frontal_plan['instant_load_bias_guard'] = dict(enabled=True,previous_action_substeps=24,final_sample_at_least_desired_n=True,desired_vertical_load_n=5.,retains_peak_guard=True,negative_increment_only=True,original_filter_and_upward_relief=True,original_guard_priority=True,training_ready=False)\n",after=True,indent='                    ')
    add('    if clearance_guard is not None and len(qs)<10:\n',"    if args.instant_load_bias_guard:\n        episode.collect_meta['instant_load_bias_guard']=True\n",indent='    ')
    add('    for path in paths:\n',"    if args.instant_load_bias_guard:\n        paths.extend([STAGE/name for name in "+repr(helpers)+"])\n",indent='    ')
    restored=source
    for block in blocks:assert restored.count(block)==1;restored=restored.replace(block,'')
    assert restored==base;ast.parse(source)
    return source,blocks

def main():
    p=argparse.ArgumentParser();p.add_argument('--check-only',action='store_true');args=p.parse_args()
    protocol=json.loads((reference/'PROTOCOL.json').read_text())
    for path,digest in protocol['frozen_files_sha256'].items():assert sha(path)==digest,path
    for name in checks:
        report=json.loads((W/name).read_text());assert report['passed']
        for path,digest in report['source_sha256'].items():
            path=Path(path);path=path if path.is_absolute() else W/path
            assert sha(path)==digest,str(path)
    source,blocks=construct()
    if args.check_only:
        print(json.dumps(dict(source_construction_valid=True,blocks=len(blocks),parent_recovered_byte_exact=True,stage_created=False,physical_launched=False)));return
    result=json.loads((reference/'RESULT.json').read_text())
    assert result['status']=='diagnostic_closed_not_training_admission' and len(result['rows'])==10
    assert result['actual_sampled_visual_review_complete'] and all(r['all_audits_passed'] for r in result['rows'])
    pressure=json.loads((reference/'PRESSURE_SETTING_BINDING.json').read_text());assert pressure['passed'] and len(pressure['rows'])==10
    for name in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','ADDITIONAL_AUDIT_EXECUTION.json']:
        status=json.loads((reference/name).read_text());assert not Path(f"/proc/{status['pid']}/cmdline").exists()
    assert not stage.exists();stage.mkdir()
    for f in parent.iterdir():
        if f.is_file() and (f.suffix=='.py' or (f.suffix=='.json' and f.name==f.name.lower())):shutil.copy2(f,stage/f.name)
    for name in helpers:shutil.copy2(W/name,stage/name)
    (stage/'collect_paired_sorting.py').write_text(source)
    unchanged=all(sha(stage/f.name)==sha(f) for f in parent.iterdir() if f.is_file() and (stage/f.name).exists() and f.name!='collect_paired_sorting.py');assert unchanged
    paths=[Path(__file__),*[W/n for n in helpers+checks],*[f for f in stage.iterdir() if f.is_file()]]
    report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_collector_sha256=sha(parent/'collect_paired_sorting.py'),parent_result_sha256=sha(reference/'RESULT.json'),new_collector_sha256=sha(stage/'collect_paired_sorting.py'),candidate_blocks=blocks,removing_candidate_recovers_parent_byte_exact=True,original_helpers_unchanged=unchanged,helpers=helpers,training_ready=False,actual_runtime_launched=False,source_sha256={str(f):sha(f) for f in paths})
    (stage/'PREPARATION.json').write_text(json.dumps(report,indent=2));print('STAGED_NOT_LAUNCHED',stage)

if __name__=='__main__':main()
