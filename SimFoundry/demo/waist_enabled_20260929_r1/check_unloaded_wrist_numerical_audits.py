"""Source math parity and actual audit entry on eight counterfactual input fixtures.
KKT failures are retained and reported, not treated as fixture construction errors.
Loaded records remain historical; full new action chain requires real collection.
"""
from pathlib import Path
import ast,json,sys,hashlib,subprocess,importlib.util
w=Path(__file__).resolve().parent;stage=w/'staged_unloaded_wrist_prior';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();old=ast.parse((w/'audit_self_clearance_task_optimality.py').read_text());new=ast.parse((w/'audit_unloaded_wrist_task_optimality.py').read_text());fn=lambda a,n:next(x for x in a.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name==n)
for name in ['near','IndependentElbows']:assert ast.dump(fn(old,name))==ast.dump(fn(new,name))
def numerical_body(tree):
 inspect=fn(tree,'inspect');loop=next(x for x in inspect.body if isinstance(x,ast.For) and ast.unparse(x.target)=='c');index=next(i for i,x in enumerate(loop.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='baseline' for t in x.targets));return [ast.dump(x) for x in loop.body[index:]]
assert numerical_body(old)==numerical_body(new)
a=ast.parse((w/'audit_micro_unchanged_loaded_execution.py').read_text());b=ast.parse((w/'audit_unloaded_wrist_loaded_execution.py').read_text())
for name in ['verify_refinement','verify_retry_metadata']:assert ast.dump(fn(a,name))==ast.dump(fn(b,name))
s=ast.unparse(fn(a,'inspect')).replace("w / 'staged_micro_clearance_return' / name", "w / ('staged_unloaded_wrist_prior' if name == 'collect_paired_sorting.py' else 'staged_micro_clearance_return') / name");assert ast.dump(ast.parse(s).body[0])==ast.dump(fn(b,'inspect'))
check=json.loads((stage/'LIVE_ENTRY_CHECK.json').read_text());assert check['passed'] and len(check['episodes'])==8
for name,h in check['source_sha256'].items():assert sha(name)==h
spec=importlib.util.spec_from_file_location('loaded',w/'audit_unloaded_wrist_loaded_execution.py');loaded=importlib.util.module_from_spec(spec);spec.loader.exec_module(loaded);rows=[]
for e in check['episodes']:
 ep=Path(e['fixture']);original=next((w/'rear_short_recovery_groups_r1').glob('case_*/'+e['episode']))
 for name in ['trace.npz','parcel_orientation.npz','solved_contact_forces.json','region_approach.json']:
  if not (ep/name).exists():(ep/name).symlink_to((original/name).resolve())
 kkt_call=subprocess.run([sys.executable,str(w/'audit_unloaded_wrist_task_optimality.py'),str(ep)],capture_output=True,text=True);(ep/'kkt_cli.log').write_text(kkt_call.stdout+kkt_call.stderr);report_path=ep/'UNLOADED_WRIST_TASK_OPTIMALITY_AUDIT.json';assert report_path.exists(),kkt_call.stderr;report=json.loads(report_path.read_text());assert kkt_call.returncode==(0 if report['passed'] else 1) and report['frames']==1199
 replay=loaded.inspect(ep);assert replay['passed'];(ep/'LOADED_REPLAY_FIXTURE.json').write_text(json.dumps(replay,indent=2));rows.append(dict(episode=ep.name,task_kkt_passed=report['passed'],task_kkt_failed_frames=len(report['errors']),max_kkt_residual=report['max_kkt_residual'],loaded_replay_passed=True,loaded_frames=replay['parent_full_push_replay_frames'],kkt_report_sha256=sha(report_path),loaded_report_sha256=sha(ep/'LOADED_REPLAY_FIXTURE.json')));print(rows[-1],flush=True)
out=dict(passed=True,scope=__doc__,original_kkt_math_ast_exact=True,original_loaded_math_ast_exact=True,episodes=rows,task_kkt_failed_frames=sum(x['task_kkt_failed_frames'] for x in rows),source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'LIVE_ENTRY_CHECK.json',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py',w/'audit_unloaded_wrist_loaded_execution.py',w/'audit_self_clearance_task_optimality.py',w/'audit_micro_unchanged_loaded_execution.py']},physical_validation=False,training_ready=False)
(stage/'NUMERICAL_AUDIT_CHECK.json').write_text(json.dumps(out,indent=2));print('Completed eight fixture numerical/loaded audits; KKT failures retained',out['task_kkt_failed_frames'])
