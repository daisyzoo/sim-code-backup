"""Freeze same complete eight pushes/two waits with only rear COP flag added."""
from pathlib import Path
import copy,datetime,hashlib,json,sys
w=Path(__file__).resolve().parent;repo=w.parents[1];parent=w/'region_causal_xy_groups_r2';stage=w/'staged_rear_cop_centering';r=Path(sys.argv[1]).resolve();assert not r.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=json.loads((parent/'RESULT.json').read_text());assert result['push_total']==8 and result['waits_passed']==2 and result['actual_review_complete'] and result['original_control_reports_verified']==80
for name in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','REGION_DIAGNOSTIC_EXECUTION.json']:
 d=json.loads((parent/name).read_text());assert not (Path('/proc')/str(d['pid'])/'cmdline').exists()
m=json.loads((stage/'MANIFEST.json').read_text())
for name,h in m['source_sha256'].items():assert sha(stage/name)==h
for name,h in m['checks_sha256'].items():assert sha(stage/name)==h
assert sha(w/'audit_rear_cop_centering_live.py')==m['auditor_sha256']
p=json.loads((parent/'PROTOCOL.json').read_text());before=copy.deepcopy(p);oldstage=str((w/'staged_region_causal_xy_diagnostics').relative_to(repo));newstage=str(stage.relative_to(repo));sources={}
for rel,h in p['source_sha256'].items():
 nr=rel.replace(oldstage,newstage);sources[nr]=sha(repo/nr)
 if nr==rel:assert sources[nr]==h
for name in ['rear_cop_centering.py','rear_cop_route.py']:sources[str((stage/name).relative_to(repo))]=sha(stage/name)
assert len(sources)==55
r.mkdir();(r/'layouts').mkdir();layouts={}
for old,h in p['layout_sha256'].items():
 src=Path(old);assert sha(src)==h;dst=r/'layouts'/src.name;dst.write_bytes(src.read_bytes());layouts[str(dst)]=h
for item in p['commands']:item['args']=[a.replace(str(parent),str(r)) for a in item['args']]+['--rear-cop-centering']
for a,b in zip(before['commands'],p['commands']):
 assert a['layout_id']==b['layout_id'] and a['tasks']==b['tasks'] and a['wait']==b['wait']
 assert [s.replace(str(r),str(parent)) for s in b['args'][:-1]]==a['args'] and b['args'][-1]=='--rear-cop-centering'
for key in ['observation_only_change','failed_observation_status_sha256','failed_observation_protocol_sha256']:p.pop(key,None)
p.update(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),source_sha256=sources,layout_sha256=layouts,settings=p['settings']+['--rear-cop-centering'],runner_sha256=sha(w/'run_rear_cop_centering_groups.py'),rear_cop_auditor_sha256=sha(w/'audit_rear_cop_centering_live.py'),candidate_manifest_sha256=sha(stage/'MANIFEST.json'),parent_result_sha256=sha(parent/'RESULT.json'),parent_protocol_sha256=sha(parent/'PROTOCOL.json'),baseline_push_passed=result['push_passed'],baseline_push_total=8,training_ready=False,scope='Same full parent8push2wait,geometry/assignment/seed/steps/order preserved. Only rear-cop-centering flag: after measured region handover and original loadedpush guard, boundedX-only priorCOP correction. ParentY/Z, firstpush, original quality, zero start and noassist unchanged. Release margin probe not included. R1 unexplained bounds failure retained; no training admission.')
for name in ['audit_rear_cop_centering_live.py','close_rear_cop_centering_group.py','close_rear_cop_centering_full.py']:p['auditor_dependency_sha256'][name]=sha(w/name)
for name,h in p['auditor_dependency_sha256'].items():assert sha(w/name)==h
(r/'PROTOCOL.json').write_text(json.dumps(p,indent=2))
(r/'INPUT_COMPARISON.json').write_text(json.dumps(dict(passed=True,commands_compared=6,same_geometry_seed_steps_order=True,only_new_flag='--rear-cop-centering',parent_protocol_sha256=sha(parent/'PROTOCOL.json'),protocol_sha256=sha(r/'PROTOCOL.json'),training_ready=False),indent=2))
print(r,sha(r/'PROTOCOL.json'))
