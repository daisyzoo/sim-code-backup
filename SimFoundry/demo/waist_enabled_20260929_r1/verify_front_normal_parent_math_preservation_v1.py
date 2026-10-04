"""Check that versioned consumers retain independent parent mathematical bodies.
Does not prove new candidate dynamics; file and command tests are separate.
"""
from pathlib import Path
import ast,datetime,hashlib,json
W=Path(__file__).resolve().parent;D=W/'front_normal_parent_math_preservation_r1';D.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
renames={'audit_front_normal_recovery_stream_v1':'audit_front_effective_height_front_recovery_stream_v2','audit_front_normal_initial_live_v1':'audit_front_effective_height_r1_initial_live'}
checks=[];sources={}
for old,new,names in [
 ('audit_front_effective_height_front_recovery_stream_v2.py','audit_front_normal_recovery_stream_v1.py',['RecoveryStreamAudit','unique','verify_files']),
 ('audit_front_effective_height_r1_initial_live.py','audit_front_normal_initial_live_v1.py',['verify_files']),
 ('audit_front_effective_height_r1_v1_stage_pose_live.py','audit_front_normal_pose_live_v1.py',['unique','loads','verify_files']),
 ('audit_front_effective_height_r1_v2_z_execution.py','audit_front_normal_z_execution_v1.py',['recorded_rotation','RuntimeGapRepresentation']),
 ('front_effective_height_r1_loaded_episode_inputs.py','front_normal_loaded_episode_inputs_v1.py',['indexed']),
]:
 a=(W/old).read_text();b=(W/new).read_text()
 for newname,oldname in renames.items():b=b.replace(newname,oldname)
 at=ast.parse(a);bt=ast.parse(b)
 for name in names:
  aa=next(n for n in at.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name);bb=next(n for n in bt.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name)
  assert ast.dump(aa,include_attributes=False)==ast.dump(bb,include_attributes=False),(new,name)
  checks.append(dict(new_file=new,original_file=old,body=name,exact_parent_ast_after_import_rename=True))
 for p in [W/old,W/new]:sources[str(p)]=sha(p)
# Independent final guard body and per-frame actual history remain byte-for-byte AST.
for filename in ['front_effective_height_r1_loaded_episode_inputs.py','front_normal_loaded_episode_inputs_v1.py']:
 tree=ast.parse((W/filename).read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='EpisodeInputs');node=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='verify_actual_final_guard')
 value=ast.dump(node,include_attributes=False)
 if filename.startswith('front_effective'):original=value
 else:assert value==original;checks.append(dict(body='EpisodeInputs.verify_actual_final_guard',exact_parent_ast=True))
sources[str(Path(__file__))]=sha(Path(__file__))
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,checks=checks,source_sha256=sources,training_ready=False,physical_rollout_verified=False)
(D/'RESULT.json').write_text(json.dumps(out,indent=2));print(dict(passed=True,unchanged_mathematical_bodies=len(checks)))
