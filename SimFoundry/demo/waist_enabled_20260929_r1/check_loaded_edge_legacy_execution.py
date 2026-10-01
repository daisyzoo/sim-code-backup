"""Original loaded/refinement functions exact and original8 stream equivalence.
New edge command chain itself is separately verified by native-file coverage.
"""
from pathlib import Path
import sys,ast,json,hashlib,datetime
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
import audit_recontact_pose_loaded_execution as old
import audit_loaded_edge_loaded_execution as new
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();records=[];sources={}
a=ast.parse((w/'audit_recontact_pose_loaded_execution.py').read_text());b=ast.parse((w/'audit_loaded_edge_loaded_execution.py').read_text())
for name in ['near','verify_refinement','verify_retry_metadata']:
 f=lambda tree:next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
 assert ast.dump(f(a),include_attributes=False)==ast.dump(f(b),include_attributes=False)
for path in sorted((w/'recontact_pose_groups_r1').glob('case_*/layout_*/quality.json')):
 ep=path.parent
 if 'wait' in ep.name:continue
 x=old.replay(ep,w/'staged_recontact_pose/collect_paired_sorting.py');y=new.replay(ep,w/'staged_recontact_pose/collect_paired_sorting.py',verified_edges={});assert x==y,ep.name
 records.append(dict(episode=ep.name,parent_full_push_replay_frames=y['parent_full_push_replay_frames'],refinement_frames=y['refinement_frames'],passed=True));print(records[-1],flush=True)
 for name,h in y.get('source_sha256',{}).items():sources[str(ep/name)]=h
 sources[str(ep.parent/'provenance.json')]=sha(ep.parent/'provenance.json')
 for name,h in json.loads((ep.parent/'provenance.json').read_text())['source_sha256'].items():sources[str(ep.parent/'source_snapshot'/name)]=h
for name in ['check_loaded_edge_legacy_execution.py','audit_loaded_edge_loaded_execution.py','audit_recontact_pose_loaded_execution.py','audit_rear_coupled_execution_live.py','audit_rear_joint_xy_live.py']:sources[str(w/name)]=sha(w/name)
assert len(records)==8
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,original_refinement_math_ast_exact=True,records=records,source_sha256=sources,physical_validation=False,training_ready=False)
(w/'staged_loaded_edge_coverage/LEGACY_EXECUTION_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS eight original streams',flush=True)
