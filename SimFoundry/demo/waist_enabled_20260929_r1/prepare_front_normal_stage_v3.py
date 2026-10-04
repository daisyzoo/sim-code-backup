"""Correct final pressure bookkeeping after an admitted recovery, default off.
No physics or changes to frozen stages. Preserve the pre-commit controller row.
"""
from pathlib import Path
import ast,copy,datetime,hashlib,json,shutil
W=Path(__file__).resolve().parent;P=W/'staged_front_normal_nondegradation_v2';S=W/'staged_front_normal_nondegradation_v3';D=W/'front_normal_preparation_r3'
assert not S.exists() and not D.exists();D.mkdir();shutil.copytree(P,S,copy_function=shutil.copy2,ignore=shutil.ignore_patterns('__pycache__'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();parents={str(p):sha(p) for p in P.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
for p,h in parents.items():
 a=Path(p);b=S/a.relative_to(P);assert sha(b)==h and a.stat().st_ino!=b.stat().st_ino
p=S/'collect_paired_sorting.py';s=p.read_text();old='''            commit_original_recovery(normal_record,frontal_state,final_clearance)
''';assert s.count(old)==1
new='''            # Final pressure state must include this post-waypoint recovery.
            # Keep the original decision-time row separately for replay.
            if not args.peak_load_bias_guard or not peak_load_frame_log:
                raise ValueError('Recovery requires its pressure trace')
            pressure_before_recovery=peak_load_frame_log[-1].copy()
            if pressure_before_recovery.get('step')!=step or 'before_final_recovery' in pressure_before_recovery:
                raise ValueError('Stale or repeated final pressure transition')
            if (pressure_before_recovery['top_mode']!=frontal_state.top_mode or
                pressure_before_recovery['bias_m']!=frontal_state.load.bias_m or
                pressure_before_recovery['filtered_n']!=frontal_state.load.filtered_n or
                pressure_before_recovery['pressure_update_count']!=len(frontal_state.load.updates)):
                raise ValueError('Pressure trace differs from actual pre-recovery state')
            commit_original_recovery(normal_record,frontal_state,final_clearance)
            peak_load_frame_log[-1]=dict(pressure_before_recovery,
                top_mode=frontal_state.top_mode,bias_m=frontal_state.load.bias_m,
                filtered_n=frontal_state.load.filtered_n,
                before_final_recovery=pressure_before_recovery,
                final_recovery_transition=normal_record['recovery_transition'])
'''
s=s.replace(old,new);p.write_text(s)
# Removing the diagnostic branch must still recover the original parent AST.
class Strip(ast.NodeTransformer):
 def visit_If(self,n):
  if 'args.front_normal_nondegradation' in ast.unparse(n.test):return None
  return self.generic_visit(n)
 def visit_Expr(self,n):
  if isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='parser.add_argument' and n.value.args and isinstance(n.value.args[0],ast.Constant) and n.value.args[0].value=='--front-normal-nondegradation':return None
  return self.generic_visit(n)
assert ast.dump(Strip().visit(copy.deepcopy(ast.parse(s))),include_attributes=False)==ast.dump(ast.parse((W/'staged_front_effective_height_v1/collect_paired_sorting.py').read_text()),include_attributes=False)
for p,h in parents.items():assert sha(p)==h
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent_stage=str(P),stage=str(S),defaultoff_exact_parent_ast=True,independent_inodes=True,parent_sources_sha256=parents,stage_sources_sha256={str(p):sha(p) for p in S.rglob('*') if p.is_file() and '__pycache__' not in p.parts},physical_launch_allowed=False,training_ready=False,remaining=['Native recovery/pressure check including rejected and stale logs','Independent pressure consumer must validate declared post-waypoint transition','Full saved-source and original command/phase/pressure audit consumer integration','Original storage and full-condition physics gates'])
(D/'STAGE_PREPARATION.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(stage=str(S),defaultoff_exact_parent_ast=True)))
