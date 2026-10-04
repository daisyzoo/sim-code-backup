"""Verify source chain and reject historical physical streams for reserve candidate."""
from pathlib import Path
import json,datetime,hashlib,sys,ast
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from joint_transport_reserve_stage_source_binding_v2 import verify_preparation,verify_trial_provenance
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();expected,bound=verify_preparation();assert len(expected)==92
negative=[]
for run in ['front_box_recenter_physical_r2','joint_transport_physical_r1']:
 case=W/run/'case_841011'
 try:verify_trial_provenance(case)
 except (AssertionError,KeyError):negative.append(run)
 else:raise AssertionError('Historical source accepted')
s=W/'staged_joint_transport_reserve_v1';source=(s/'collect_paired_sorting.py').read_text();tree=ast.parse(source)
# Added cached implementation and error derivation must be in collector archive path list.
for name in ['joint_transport_paths_original.py','bounded_support_paths_v1.py','support_cache_probe.py','SUPPORT_ERROR_BOUND.md']:
 assert name in expected and source.count("'"+name+"'")==1
for p in [Path(__file__),W/'joint_transport_reserve_stage_source_binding_v2.py']:bound[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),active_archived_sources=92,old_physical_source_rejected=negative,source_sha256=bound,native_new_fixture_pending=True,training_ready=False)
with (W/'joint_transport_reserve_preparation_r1/SOURCE_PREPARATION_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print('SOURCE_CHAIN92_PASS_2OLD_REJECTED')
