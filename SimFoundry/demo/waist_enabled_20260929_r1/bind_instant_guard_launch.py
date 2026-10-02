"""Bind actual running collector sources/arguments to the frozen single-change plan.
This is launch provenance, not initial-state, complete data, task or model proof.
"""
from pathlib import Path
import json,hashlib,datetime
W=Path(__file__).resolve().parent;R=W/'instant_guard_groups_r1';P=W/'peak_guard_groups_r1';C=R/'case_840001';B=P/C.name;repo=W.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=json.loads((R/'PROTOCOL.json').read_text());prov=json.loads((C/'provenance.json').read_text());base=json.loads((B/'provenance.json').read_text());stage=W/'staged_instant_load_guard';parent=W/'staged_peak_load_guard';prep=json.loads((stage/'PREPARATION.json').read_text())
for name,h in p['frozen_files_sha256'].items():assert sha(name)==h,name
source=(stage/'collect_paired_sorting.py').read_text()
for block in prep['candidate_blocks']:assert source.count(block)==1;source=source.replace(block,'')
assert source==(parent/'collect_paired_sorting.py').read_text()
diffs={k:[base['args'].get(k),prov['args'].get(k)] for k in set(prov['args'])|set(base['args']) if base['args'].get(k)!=prov['args'].get(k)}
assert set(diffs)=={'instant_load_bias_guard','diagnostic_layout_json','out_dir'}
assert diffs['instant_load_bias_guard']==[None,True]
for key in ['diagnostic_layout_json','out_dir']:assert diffs[key][1].replace(str(R),str(P))==diffs[key][0]
for rel,h in prov['source_sha256'].items():
    assert sha(C/'source_snapshot'/rel)==h==sha(repo/rel)==p['frozen_files_sha256'][str(repo/rel)],rel
runtime=json.loads((C/'SUBSTEP_RUNTIME_BINDING.json').read_text());oldruntime=json.loads((B/'SUBSTEP_RUNTIME_BINDING.json').read_text())
assert runtime['observer_installed'] is True and runtime['original_graph_setting'] is True and runtime['training_ready'] is False
assert runtime['metadata']==oldruntime['metadata'],'runtime observer/body metadata changed'
for path,row in runtime['source_files'].items():assert sha(path)==row['sha256']==sha(C/row['snapshot'])
status=json.loads((R/'STATUS.json').read_text());launch=json.loads((R/'LAUNCH.json').read_text());live={}
for kind,pid in {'runner':launch['processes']['runner']['pid'],'watcher':launch['processes']['watcher']['pid'],'collector':status['collector_pid']}.items():
    cmd=Path(f'/proc/{pid}/cmdline').read_bytes();assert cmd and (b'instant_guard' in cmd or b'staged_instant_load_guard' in cmd);live[kind]=dict(pid=pid,cmdline=cmd.decode().replace('\0',' ').strip())
files=[R/'PROTOCOL.json',R/'LAUNCH.json',C/'provenance.json',C/'SUBSTEP_RUNTIME_BINDING.json',B/'provenance.json',B/'SUBSTEP_RUNTIME_BINDING.json',stage/'PREPARATION.json',Path(__file__)]
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,actual_archived_source_count=len(prov['source_sha256']),frozen_files_verified=len(p['frozen_files_sha256']),actual_arg_differences=diffs,runtime_metadata_matches_parent=True,original_graph_and_observer_retained=True,live_processes=live,source_sha256={str(f):sha(f) for f in files},training_ready=False)
f=R/'INITIAL_SOURCE_BINDING.json';assert not f.exists();f.write_text(json.dumps(out,indent=2));print('ACTUAL_LAUNCH_BOUND',len(prov['source_sha256']),len(p['frozen_files_sha256']),{k:v['pid'] for k,v in live.items()})
