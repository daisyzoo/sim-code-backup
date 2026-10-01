"""Freeze new full diagnostic only after complete reviewed parent evidence."""
from pathlib import Path
import json,hashlib,datetime,sys
w=Path(__file__).resolve().parent;repo=w.parents[1];parent=w/'region_continuity_groups_r1';stage=w/'staged_region_contact_x_follow';r=Path(sys.argv[1]).resolve();assert not r.exists();result=json.loads((parent/'RESULT.json').read_text());assert result['push_total']==8 and result['actual_review_complete'] and result['waits_passed']==2
for file in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json']:
 d=json.loads((parent/file).read_text());assert not (Path('/proc')/str(d['pid'])/'cmdline').exists()
manifest=json.loads((stage/'MANIFEST.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for f,h in manifest['source_sha256'].items():assert sha(stage/f)==h
for f,h in manifest['checks_sha256'].items():assert sha(stage/f)==h
p=json.loads((parent/'PROTOCOL.json').read_text());oldstage=str((w/'staged_region_handover_continuity').relative_to(repo));newstage=str(stage.relative_to(repo));sources={}
for rel,h in p['source_sha256'].items():
 nr=rel.replace(oldstage,newstage);sources[nr]=sha(repo/nr)
 if nr==rel:assert sources[nr]==h
r.mkdir();(r/'layouts').mkdir()
layouts={}
for old,h in p['layout_sha256'].items():
 src=Path(old);assert sha(src)==h;dst=r/'layouts'/src.name;dst.write_bytes(src.read_bytes());layouts[str(dst)]=h
for item in p['commands']:item['args']=[x.replace(str(parent),str(r)) for x in item['args']]
p.update(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),source_sha256=sources,layout_sha256=layouts,auditor_dependency_sha256={n:sha(w/n) for n in ['audit_region_continuity_live.py','audit_region_reference_live.py','audit_terminal_hold_inputs.py','audit_initial_near_half_live.py','audit_tracking_region_action_live.py','audit_region_action_live_r2.py']},runner_sha256=sha(w/'run_region_x_follow_groups.py'),audit_sha256=sha(w/'audit_region_x_follow_live.py'),continuity_base_auditor_sha256=sha(w/'audit_region_continuity_live.py'),tracking_base_auditor_sha256=sha(w/'audit_tracking_region_action_live.py'),parent_result_sha256=sha(parent/'RESULT.json'),parent_protocol_sha256=sha(parent/'PROTOCOL.json'),candidate_manifest_sha256=sha(stage/'MANIFEST.json'),scope='Same full original lateral/diagonal swap groups8push+2wait. One region-only change from parent: per-loaded-bout previous-command X anchor plus observed object-X translation; original2mm X slew and all Y/Z/guards retained. No gate/physics/geometry/task/camera changes. Diagnostic only; no admission or success inferred from software checks.',training_ready=False)
(r/'PROTOCOL.json').write_text(json.dumps(p,indent=2));print(json.dumps(dict(path=str(r),sources=len(sources),cases=len(p['commands']),protocol_sha256=sha(r/'PROTOCOL.json'))))
