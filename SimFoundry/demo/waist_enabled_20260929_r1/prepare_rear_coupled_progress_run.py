"""Same full closed edge-speed parent8+2; only rear progress flag and read-only trace."""
from pathlib import Path
import json,copy,hashlib,datetime,sys
w=Path(__file__).resolve().parent;repo=w.parents[1];parent=w/'front_edge_speed_groups_r1';stage=w/'staged_rear_coupled_progress';r=Path(sys.argv[1]).resolve();assert not r.exists();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();result=json.loads((parent/'RESULT.json').read_text());assert result['push_total']==8 and result['waits_passed']==2 and result['actual_review_complete'] and result['original_control_reports_verified']==80
for name in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','REGION_DIAGNOSTIC_EXECUTION.json']:
 d=json.loads((parent/name).read_text())
 for key in ['pid','collector_pid']:
  if key in d:assert not Path('/proc',str(d[key]),'cmdline').exists()
m=json.loads((stage/'MANIFEST.json').read_text())
for n,h in m['source_sha256'].items():assert sha(stage/n)==h
for n,h in m['checks_sha256'].items():assert sha(stage/n)==h
for n,h in m['checker_sha256'].items():assert sha(w/n)==h
for field,name in [('auditor_sha256','audit_rear_coupled_progress_live.py'),('execution_auditor_sha256','audit_rear_coupled_execution_live.py'),('front_auditor_sha256','audit_front_edge_speed_live.py')]:assert sha(w/name)==m[field]
p=json.loads((parent/'PROTOCOL.json').read_text());before=copy.deepcopy(p);oldstage=str((w/'staged_front_edge_speed').relative_to(repo));newstage=str(stage.relative_to(repo));sources={}
for rel,h in p['source_sha256'].items():
 nr=rel.replace(oldstage,newstage);sources[nr]=sha(repo/nr)
 if nr==rel:assert sources[nr]==h
assert len(sources)==56
newhelper=str((stage/'rear_coupled_progress.py').relative_to(repo));assert newhelper not in sources;sources[newhelper]=sha(stage/'rear_coupled_progress.py');assert len(sources)==57
r.mkdir();(r/'layouts').mkdir();layouts={}
for old,h in p['layout_sha256'].items():
 src=Path(old);assert sha(src)==h;dst=r/'layouts'/src.name;dst.write_bytes(src.read_bytes());layouts[str(dst)]=h
for command in p['commands']:command['args']=[a.replace(str(parent),str(r)) for a in command['args']]+['--rear-coupled-progress']
for a,b in zip(before['commands'],p['commands']):
 assert a['layout_id']==b['layout_id'] and a['tasks']==b['tasks'] and a['wait']==b['wait'];assert [x.replace(str(r),str(parent)) for x in b['args'][:-1]]==a['args']
p.update(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),source_sha256=sources,layout_sha256=layouts,settings=p['settings']+['--rear-coupled-progress'],runner_sha256=sha(w/'run_rear_coupled_progress_groups.py'),rear_cop_auditor_sha256=sha(w/'audit_rear_coupled_progress_live.py'),rear_execution_auditor_sha256=sha(w/'audit_rear_coupled_execution_live.py'),candidate_manifest_sha256=sha(stage/'MANIFEST.json'),parent_result_sha256=sha(parent/'RESULT.json'),parent_protocol_sha256=sha(parent/'PROTOCOL.json'),baseline_push_passed=result['push_passed'],baseline_push_total=8,training_ready=False,scope='Identical closed front-edge parent8push2wait/layout/seed/steps/order. Only rear current-COP reference-direction Y governor0..1 flag; new read-only every-rear-top_push Jacobian trace for exact executed-action replay. Original X/Z, first load, mode/quality/limits unchanged.57archives. Diagnostic, no data admission.')
for name in ['audit_rear_coupled_progress_live.py','audit_rear_coupled_execution_live.py','close_rear_coupled_progress_group.py','close_rear_coupled_progress_full.py']:p['auditor_dependency_sha256'][name]=sha(w/name)
for n,h in p['auditor_dependency_sha256'].items():assert sha(w/n)==h
(r/'PROTOCOL.json').write_text(json.dumps(p,indent=2));(r/'INPUT_COMPARISON.json').write_text(json.dumps(dict(passed=True,commands_compared=6,only_new_flag='--rear-coupled-progress',same_geometry_seed_steps_order=True,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),protocol_sha256=sha(r/'PROTOCOL.json'),additional_readonly_logging='every selected rear top_push IK Jacobian',training_ready=False),indent=2));print(r,sha(r/'PROTOCOL.json'))
