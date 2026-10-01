"""Original geometry and ordinary action-chain AST identity and all10 frozen
parent replays. Explicit new joint paths have independent native-file audit;
original pre/post/final geometry is still checked on every executed frame.
"""
from pathlib import Path
import sys,ast,json,hashlib,copy
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_recontact_pose_self_clearance import audit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=ast.parse((w/'audit_self_clearance_live.py').read_text());new=ast.parse((w/'audit_recontact_pose_self_clearance.py').read_text());a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=='audit');b=copy.deepcopy(next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='audit'))
b.body=[n for n in b.body if not (isinstance(n,ast.If) and ast.unparse(n.test)=='verified_events is None')]
loop=next(n for n in b.body if isinstance(n,ast.For) and ast.unparse(n.target)=='c');i=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.If) and 'controller_kind' in ast.unparse(n.test));assert isinstance(loop.body[i+1],ast.Assert);del loop.body[i:i+2]
assert ast.dump(ast.Module(body=a.body,type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=b.body,type_ignores=[]),include_attributes=False)
results=[]
for ep in sorted((w/'rear_short_recovery_groups_r1').glob('case_*/layout_*')):
 p=ep/'SELF_CLEARANCE_LIVE_AUDIT.json'
 if not p.exists():continue
 out=audit(ep,verified_events={});old=json.loads(p.read_text())
 for key in ['passed','executed_frames','controller_frames','task_ik_overrides','episode_clearance_passed','failure','minimum_actual_support_gap_m','minimum_command_support_gap_m']:assert out[key]==old[key],(ep.name,key)
 results.append(dict(episode=ep.name,frames=out['executed_frames'],passed=out['passed'],frozen_audit_sha256=sha(p)));print(results[-1],flush=True)
assert len(results)==10
out=dict(passed=True,scope=__doc__,original_math_ast_exact=True,parent_replays=results,total_frames=sum(r['frames'] for r in results),source_sha256={str(p):sha(p) for p in [Path(__file__),w/'audit_recontact_pose_self_clearance.py',w/'audit_self_clearance_live.py']},physical_validation=False,training_ready=False)
(w/'staged_recontact_pose/SELF_CLEARANCE_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',len(results),out['total_frames'],flush=True)
