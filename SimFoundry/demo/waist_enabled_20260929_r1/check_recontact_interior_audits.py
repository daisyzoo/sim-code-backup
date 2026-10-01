"""Explicit version parity and independent interior-preference tamper rejection.
Original region/normal/reference/geometry/task/loaded audit mathematics retained.
New source and preference records must be independently checked, not bypassed.
"""
from pathlib import Path
import ast,sys,json,hashlib,copy
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_recontact_interior';sys.path[:0]=[str(w),str(repo)];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();mapping=json.loads((w/'INTERIOR_AUDIT_VERSION_MAP.json').read_text())
def rename(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 return s
pairs=[];sources={}
for name,new in mapping.items():
 if name.endswith('.json') or name in ['staged_recontact_pose','audit_recontact_pose_events','audit_recontact_pose_live']:continue
 old=w/(name+'.py');path=w/(new+'.py');assert old.exists() and path.exists();assert ast.dump(ast.parse(rename(old.read_text())),include_attributes=False)==ast.dump(ast.parse(path.read_text()),include_attributes=False),(name,new);pairs.append([name,new]);sources[str(old)]=sha(old);sources[str(path)]=sha(path)
from audit_recontact_interior_events import EventAudit
from audit_recontact_pose_events import EventAudit as OriginalAudit
assert EventAudit.__bases__==(OriginalAudit,)
for n in ast.walk(ast.parse((w/'audit_recontact_interior_events.py').read_text())):
 if isinstance(n,ast.ImportFrom):assert n.module not in ['recontact_plan','recontact_lifecycle','recontact_plan_deeper','recontact_plan_original']
fixture=stage/'LIFECYCLE_CHECK.json';d=json.loads(fixture.read_text());assert d['passed'];positive=[];preferred=None;fallback=None
for r in d['rows']:
 if not r['summary']['prefer_interior']:continue
 e=r['trace'][0];ctx=e['context'];audit=EventAudit(repo,stage);args=dict(current=ctx['current'],scene=ctx['scene'],step=ctx['step']);out=audit.verify_preference(e['planning'],**args);positive.append(out)
 if out['selected']=='preferred' and preferred is None:preferred=(e['planning'],args)
 if out['selected']=='original_fallback' and fallback is None:fallback=(e['planning'],args)
assert len(positive)==16 and preferred is not None and fallback is not None
mutations={
 'disabled_preference':lambda p:p['interior_preference'].__setitem__('enabled',False),
 'changed_preferred_inset':lambda p:p['interior_preference'].__setitem__('preferred_inset_m',.012),
 'changed_original_inset':lambda p:p['interior_preference'].__setitem__('original_inset_m',.008),
 'false_choice':lambda p:p['interior_preference'].__setitem__('selected','original_fallback'),
 'false_selected_inset':lambda p:p['interior_preference'].__setitem__('selected_inset_m',.012),
 'false_fallback_reason':lambda p:p['interior_preference'].__setitem__('fallback_reason','invented'),
 'false_endpoint':lambda p:p['interior_preference']['preferred_plan']['endpoint'].__setitem__(1,0.),
 'false_objective':lambda p:p['interior_preference']['preferred_plan']['attempts'][0].__setitem__('objective',-1.),
 'false_constraint_margin':lambda p:p['interior_preference']['preferred_plan']['attempts'][0].__setitem__('minimum_constraint',1.),
 'false_path_acceptance':lambda p:p['interior_preference']['preferred_path_checks'][0].__setitem__('accepted',False),
 'false_path_gap':lambda p:p['interior_preference']['preferred_path_checks'][0].__setitem__('elbow_gap_m',1.),
 'false_waypoint':lambda p:p['interior_preference']['preferred_plan']['waypoints'][0].__setitem__(2,0.),
}
rejected=[]
for name,change in mutations.items():
 p,args=copy.deepcopy(preferred);change(p)
 try:EventAudit(repo,stage).verify_preference(p,**args)
 except (AssertionError,ValueError,KeyError):rejected.append(name)
 else:raise AssertionError('Accepted '+name)
p,args=copy.deepcopy(fallback);p['interior_preference']['selected']='preferred'
try:EventAudit(repo,stage).verify_preference(p,**args)
except AssertionError:rejected.append('failed_endpoint_cannot_be_preferred')
else:raise AssertionError('Failed endpoint selected')
for p in [Path(__file__),w/'INTERIOR_AUDIT_VERSION_MAP.json',w/'audit_interior_pose_live.py',w/'audit_recontact_interior_events.py',w/'audit_recontact_pose_events.py',w/'audit_recontact_pose_normal.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py',fixture]:sources[str(p)]=sha(p)
out=dict(passed=True,scope=__doc__,unchanged_version_pairs=pairs,original_command_handover_auditor_inherited=True,independent_preference_cases=len(positive),rejected_corruptions=rejected,source_sha256=sources,physical_validation=False,training_ready=False);(stage/'AUDIT_VERSION_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',len(pairs),'unchanged versions',len(positive),'preferences',len(rejected),'rejections',flush=True)
