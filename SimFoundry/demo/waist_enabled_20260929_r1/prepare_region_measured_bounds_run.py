"""Single-variable physical-domain handling against the fully reviewed XY parent."""
from pathlib import Path
import copy,datetime,hashlib,json,sys
w=Path(__file__).resolve().parent;repo=w.parents[1];parent=w/'region_causal_xy_groups_r2';stage=w/'staged_region_measured_bounds';r=Path(sys.argv[1]).resolve();assert not r.exists();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=json.loads((parent/'RESULT.json').read_text());assert result['push_total']==8 and result['waits_passed']==2 and result['actual_review_complete'] and result['original_control_reports_verified']==80
for name in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','REGION_DIAGNOSTIC_EXECUTION.json']:
 d=json.loads((parent/name).read_text());assert not (Path('/proc')/str(d['pid'])/'cmdline').exists()
failure=w/'rear_cop_centering_groups_r1/RUNTIME_FAILURE.json';f=json.loads(failure.read_text());assert f['context']['violating_indices']==[0]
for pid in f['actual_all_processes_ended']:assert not (Path('/proc')/str(pid)/'cmdline').exists()
m=json.loads((stage/'MANIFEST.json').read_text())
for name,h in m['source_sha256'].items():assert sha(stage/name)==h
for name,h in m['checks_sha256'].items():assert sha(stage/name)==h
assert sha(w/'audit_region_measured_bounds_live.py')==m['auditor_sha256']
p=json.loads((parent/'PROTOCOL.json').read_text());before=copy.deepcopy(p);oldstage=str((w/'staged_region_causal_xy_diagnostics').relative_to(repo));newstage=str(stage.relative_to(repo));sources={}
for rel,h in p['source_sha256'].items():
 nr=rel.replace(oldstage,newstage);sources[nr]=sha(repo/nr)
 if nr==rel:assert sources[nr]==h
assert len(sources)==53
r.mkdir();(r/'layouts').mkdir();layouts={}
for old,h in p['layout_sha256'].items():
 src=Path(old);assert sha(src)==h;dst=r/'layouts'/src.name;dst.write_bytes(src.read_bytes());layouts[str(dst)]=h
for item in p['commands']:item['args']=[a.replace(str(parent),str(r)) for a in item['args']]+['--region-separate-measured-bounds']
for a,b in zip(before['commands'],p['commands']):
 assert a['layout_id']==b['layout_id'] and a['tasks']==b['tasks'] and a['wait']==b['wait']
 assert [s.replace(str(r),str(parent)) for s in b['args'][:-1]]==a['args'] and b['args'][-1]=='--region-separate-measured-bounds'
for key in ['observation_only_change','failed_observation_status_sha256','failed_observation_protocol_sha256']:p.pop(key,None)
p.update(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),source_sha256=sources,layout_sha256=layouts,settings=p['settings']+['--region-separate-measured-bounds'],runner_sha256=sha(w/'run_region_measured_bounds_groups.py'),measured_bounds_auditor_sha256=sha(w/'audit_region_measured_bounds_live.py'),candidate_manifest_sha256=sha(stage/'MANIFEST.json'),parent_result_sha256=sha(parent/'RESULT.json'),parent_protocol_sha256=sha(parent/'PROTOCOL.json'),captured_failure_sha256=sha(failure),baseline_push_passed=result['push_passed'],baseline_push_total=8,training_ready=False,scope='Same full parent8push2wait,layout/seed/steps/order unchanged. Only region-separate-measured-bounds: measured waist original1.0, commands and forecast remain0.98, original geometry/slew and within-command measured hold. Rear loadedCOP and release-margin probes excluded. Captured failure retained; no training admission.')
for name in ['audit_region_measured_bounds_live.py','close_region_measured_bounds_group.py','close_region_measured_bounds_full.py']:p['auditor_dependency_sha256'][name]=sha(w/name)
for name,h in p['auditor_dependency_sha256'].items():assert sha(w/name)==h
(r/'PROTOCOL.json').write_text(json.dumps(p,indent=2));(r/'INPUT_COMPARISON.json').write_text(json.dumps(dict(passed=True,commands_compared=6,same_geometry_seed_steps_order=True,only_new_flag='--region-separate-measured-bounds',parent_protocol_sha256=sha(parent/'PROTOCOL.json'),protocol_sha256=sha(r/'PROTOCOL.json'),training_ready=False),indent=2));print(r,sha(r/'PROTOCOL.json'))
