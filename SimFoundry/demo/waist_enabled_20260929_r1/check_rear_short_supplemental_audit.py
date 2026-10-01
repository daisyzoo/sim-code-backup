"""Independent audit adaptation check: original math exact; bad source bindings rejected.
Counterfactual fixtures use read-only source symlinks and own copied metadata.
"""
from pathlib import Path
import ast,importlib.util,json,tempfile,hashlib
w=Path(__file__).resolve().parent;orig=w/'audit_micro_unchanged_loaded_execution.py';new=w/'audit_rear_short_unchanged_loaded_execution.py';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
a=ast.parse(orig.read_text());b=ast.parse(new.read_text())
fn=lambda tree,name:next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
for name in ['module','near','verify_refinement','verify_retry_metadata']:
 assert ast.dump(fn(a,name))==ast.dump(fn(b,name)),name
text=ast.unparse(fn(a,'inspect'));text=text.replace("w / 'staged_micro_clearance_return' / name", "w / ('staged_rear_short_recovery' if name == 'collect_paired_sorting.py' else 'staged_micro_clearance_return') / name")
assert ast.dump(ast.parse(text).body[0])==ast.dump(fn(b,'inspect'))
spec=importlib.util.spec_from_file_location('supplemental',new);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
ep=w/'rear_short_recovery_groups_r1/case_840001/layout_840001_push_box_to_bin';mod.verify_version_binding(ep)
root=Path(tempfile.mkdtemp(prefix='rear_short_supplemental_negative_'));checks=[]
def replace_json(p,edit):
 d=json.loads(p.read_text());p.unlink();edit(d);p.write_text(json.dumps(d))
for case in ['valid','flag_disabled','provenance_digest','collector_content','wrong_collector','height_failure','reference_failure','missing_failure_log']:
 r=root/case;c=r/ep.parent.name;e=c/ep.name;e.mkdir(parents=True)
 (r/'PROTOCOL.json').symlink_to((ep.parent.parent/'PROTOCOL.json').resolve());(c/'provenance.json').symlink_to((ep.parent/'provenance.json').resolve())
 for p in (ep.parent/'source_snapshot').rglob('*'):
  dst=c/'source_snapshot'/p.relative_to(ep.parent/'source_snapshot')
  if p.is_dir():dst.mkdir(exist_ok=True,parents=True)
  elif p.is_file():dst.symlink_to(p.resolve())
 for p in ep.iterdir():
  if p.is_file():(e/p.name).symlink_to(p.resolve())
 if case=='flag_disabled':replace_json(c/'provenance.json',lambda d:d['args'].__setitem__('rear_short_recovery',False))
 if case=='provenance_digest':replace_json(c/'provenance.json',lambda d:d['source_sha256'].__setitem__(next(iter(d['source_sha256'])),'0'*64))
 if case=='collector_content':
  p=next((c/'source_snapshot').rglob('collect_paired_sorting.py'));s=p.read_text();p.unlink();p.write_text(s+'\n# tampered\n')
 if case=='wrong_collector':replace_json(r/'PROTOCOL.json',lambda d:d.__setitem__('collector',str(w/'staged_micro_clearance_return/collect_paired_sorting.py')))
 if case=='height_failure':replace_json(e/'REAR_SHORT_RECOVERY_LIVE_AUDIT.json',lambda d:d.__setitem__('passed',False))
 if case=='reference_failure':replace_json(e/'REAR_JOINT_XY_LIVE_AUDIT.json',lambda d:d.__setitem__('passed',False))
 if case=='missing_failure_log':(e/'audit_micro_unchanged_loaded_execution.py.log').unlink()
 failed=False
 try:mod.verify_version_binding(e)
 except (AssertionError,FileNotFoundError):failed=True
 assert failed==(case!='valid'),case
 checks.append(dict(case=case,rejected=failed))
out=dict(passed=True,original_math_ast_exact=True,source_expectation_only_for_new_collector=True,checks=checks,fixtures=str(root),scope=__doc__,source_sha256={str(p):sha(p) for p in [Path(__file__),orig,new]},training_ready=False)
(w/'REAR_SHORT_SUPPLEMENTAL_AUDIT_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','scope']}))
