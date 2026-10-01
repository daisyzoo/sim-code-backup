"""Same complete parent conditions, only rear-core-slice-feedback added."""
from pathlib import Path
import copy,json,hashlib,datetime,sys
w=Path(__file__).resolve().parent;repo=w.parents[1];parent=w/'rear_core_slice_groups_r1';stage=w/'staged_rear_core_slice_motion';r=Path(sys.argv[1]).resolve();assert not r.exists();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();result=json.loads((parent/'RESULT.json').read_text());assert result['push_total']==8 and result['waits_passed']==2 and result['actual_review_complete'] and result['original_control_reports_verified']==80
for n in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','REGION_DIAGNOSTIC_EXECUTION.json']:
 d=json.loads((parent/n).read_text());assert not Path('/proc',str(d['pid']),'cmdline').exists()
m=json.loads((stage/'MANIFEST.json').read_text())
for n,h in m['source_sha256'].items():assert sha(stage/n)==h
for n,h in m['checks_sha256'].items():assert sha(stage/n)==h
assert sha(w/'audit_rear_core_slice_motion_live.py')==m['auditor_sha256']
p=json.loads((parent/'PROTOCOL.json').read_text());before=copy.deepcopy(p);oldstage=str((w/'staged_rear_cop_core_slice').relative_to(repo));newstage=str(stage.relative_to(repo));sources={}
for rel,h in p['source_sha256'].items():
 nr=rel.replace(oldstage,newstage);sources[nr]=sha(repo/nr)
 if nr==rel:assert sources[nr]==h
assert len(sources)==55;r.mkdir();(r/'layouts').mkdir();layouts={}
for old,h in p['layout_sha256'].items():
 src=Path(old);assert sha(src)==h;dst=r/'layouts'/src.name;dst.write_bytes(src.read_bytes());layouts[str(dst)]=h
for a in p['commands']:a['args']=[s.replace(str(parent),str(r)) for s in a['args']]+['--rear-core-slice-motion-feedforward']
for a,b in zip(before['commands'],p['commands']):
 assert a['layout_id']==b['layout_id'] and a['tasks']==b['tasks'] and a['wait']==b['wait'];assert [s.replace(str(r),str(parent)) for s in b['args'][:-1]]==a['args'];assert b['args'][-1]=='--rear-core-slice-motion-feedforward'
p.update(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),source_sha256=sources,layout_sha256=layouts,settings=p['settings']+['--rear-core-slice-motion-feedforward'],runner_sha256=sha(w/'run_rear_core_slice_motion_groups.py'),rear_cop_auditor_sha256=sha(w/'audit_rear_core_slice_motion_live.py'),candidate_manifest_sha256=sha(stage/'MANIFEST.json'),parent_result_sha256=sha(parent/'RESULT.json'),parent_protocol_sha256=sha(parent/'PROTOCOL.json'),baseline_push_passed=result['push_passed'],baseline_push_total=8,training_ready=False,scope='Identical parent8push2wait/layout/seed/steps/order. Only rear-core-slice-motion-feedforward replaces fixed anchor motion with measured moving slice motion. Parent feedback/YZ/first-loaded and original quality/guards kept; empty interval fallback. Neither release margin nor loaded response model enabled. No dataset admission.')
for name in ['audit_rear_core_slice_motion_live.py','close_rear_core_slice_motion_group.py','close_rear_core_slice_motion_full.py']:p['auditor_dependency_sha256'][name]=sha(w/name)
for n,h in p['auditor_dependency_sha256'].items():assert sha(w/n)==h
(r/'PROTOCOL.json').write_text(json.dumps(p,indent=2));(r/'INPUT_COMPARISON.json').write_text(json.dumps(dict(passed=True,commands_compared=6,only_new_flag='--rear-core-slice-motion-feedforward',same_geometry_seed_steps_order=True,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),protocol_sha256=sha(r/'PROTOCOL.json'),training_ready=False),indent=2));print(str(r),sha(r/'PROTOCOL.json'))
