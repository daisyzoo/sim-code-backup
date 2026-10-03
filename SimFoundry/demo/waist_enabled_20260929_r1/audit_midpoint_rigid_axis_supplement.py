"""Full unchanged native episode checks with scoped near-axis certificate injection.
Original failed audit is retained. This explicitly versioned supplement cannot
admit the failed physical task or any incomplete category-exchange group.
"""
from pathlib import Path
import sys,json,hashlib,datetime,types
w=Path(__file__).resolve().parent;sys.path.insert(0,str(w))
import audit_front_corridor_midpoint_stage_task_optimality as native
import audit_front_initial_center_task_rows as rows
import support_vertex_stationarity_rigid_segment_v2 as proof
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inspect(ep):
 ep=Path(ep).resolve();r=w/'front_corridor_midpoint_physical_r1';assert ep==r/'case_840023/layout_840023_nudge_mailer_to_bin'
 checkpath=r/'RIGID_AXIS_CERTIFICATE_CHECK.json';check=json.loads(checkpath.read_text());assert check['passed'] and check['historical_rows']==1319 and len(check['negative_checks'])==9
 sources={str(checkpath):sha(checkpath)}
 for p,h in check['source_sha256'].items():assert sha(p)==h,p;sources[p]=h
 originalpath=ep/'FRONT_CORRIDOR_MIDPOINT_STAGE_TASK_OPTIMALITY_V2_AUDIT.json';original=json.loads(originalpath.read_text());before=sha(originalpath);assert not original['passed'] and [x['step'] for x in original['errors']]==[1039]
 # New function objects with separate globals: no monkey-patching of modules.
 # Original source contract, pose replay, bounds, task inputs and objective execute.
 rowglobals={**rows.verify_task_rows.__globals__,'certificate':proof.certificate,'VERSION':proof.VERSION}
 verify=types.FunctionType(rows.verify_task_rows.__code__,rowglobals,rows.verify_task_rows.__name__,rows.verify_task_rows.__defaults__,rows.verify_task_rows.__closure__);verify.__kwdefaults__=rows.verify_task_rows.__kwdefaults__
 fullglobals={**native.inspect.__globals__,'verify_task_rows':verify,'VERSION':proof.VERSION}
 full=types.FunctionType(native.inspect.__code__,fullglobals,native.inspect.__name__,native.inspect.__defaults__,native.inspect.__closure__)
 result=full(ep);assert result['passed'] and result['frames']==1199 and result['overrides']==705 and len(result['records'])==len(original['records'])
 changed=[]
 for old,new in zip(original['records'],result['records']):
  assert old['step']==new['step'];normalized=json.loads(json.dumps(new))
  if 'vertex_certificate' in normalized:normalized['vertex_certificate']['version']=old['vertex_certificate']['version']
  if normalized!=old:changed.append(old['step'])
 assert changed==[1039],changed
 assert sha(originalpath)==before
 for p in [originalpath,Path(__file__),Path(native.__file__),Path(rows.__file__),Path(proof.__file__),r/'RIGID_AXIS_CERTIFICATE_PREPARATION.json']:sources[str(p)]=sha(p)
 result.update(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,stationarity_version=proof.VERSION,vertex_certificate_source_sha256=sha(proof.__file__),supplement_auditor_sha256=sha(__file__),supplement_source_sha256=sources,original_failed_report_sha256=before,original_failed_steps=[1039],changed_certificate_steps=changed,original_failures_retained=True,source_contract_and_full_pose_replay_executed=True,physical_task_passed=False,training_ready=False)
 return result
if __name__=='__main__':
 ep=Path(sys.argv[1]);out=ep/'MIDPOINT_RIGID_AXIS_TASK_OPTIMALITY_SUPPLEMENT.json';assert not out.exists();d=inspect(ep)
 with out.open('x') as f:json.dump(d,f,indent=2)
 print(json.dumps({k:v for k,v in d.items() if k not in ['records','source_sha256','supplement_source_sha256','scope']},indent=2))
