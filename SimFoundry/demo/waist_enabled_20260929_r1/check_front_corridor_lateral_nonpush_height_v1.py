"""Original height/reference audit at actual593 and single unissued594 boundary.
No synthesized physical future; matching-XY error coverage remains native route's responsibility.
"""
from pathlib import Path
import sys,json,copy,hashlib,datetime
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));D=W/'front_corridor_lateral_preparation_r1'
from audit_front_corridor_lateral_r1_v1_stage_front_height import audit
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ep=W/'joint_transport_reserve_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin'
b=json.loads((D/'INTEGRATED_NATIVE_BOUNDARY_CHECK.json').read_text())
for p,h in b['source_sha256'].items():assert sha(Path(p))==h
fr=json.loads((ep/'frontal_bypass.json').read_text());controls=json.loads((ep/'expert_control.json').read_text());actual=next(r for r in fr['rows'] if r['step']==593)
new=dict(copy.deepcopy(b['candidate_row']),step=594);log=dict(fr,rows=[actual,new]);cs=[controls[593],dict(controls[594],target_xyz=new['target_xyz'])]
result=audit(log,cs);assert result['passed'],result
negative=[]
for label in ['unmatched_xy','matched_wrong_height','wrong_recovery_height','decreased_recontacts','latched_guard_exited']:
 l=copy.deepcopy(log);c=copy.deepcopy(cs)
 if label=='unmatched_xy':l['rows'][1]['target_xyz'][0]+=.01
 elif label=='matched_wrong_height':l['rows'][1]['target_xyz'][2]=c[1]['target_xyz'][2]=.82
 elif label=='wrong_recovery_height':l['rows'][1]['travel_height_m']=.82
 elif label=='decreased_recontacts':l['rows'][1]['recontacts']=2
 else:l['rows'][0]['mode']='front_guard_lift';l['rows'][0]['target_xyz'][2]=c[0]['target_xyz'][2]=.91
 r=audit(l,c);assert not r['passed'],label;negative.append(dict(label=label,errors=r['errors']))
# A matching XY forgery is outside this layer: preserve this limitation explicitly.
l=copy.deepcopy(log);c=copy.deepcopy(cs);l['rows'][1]['target_xyz'][0]+=.01;c[1]['target_xyz'][0]+=.01
assert audit(l,c)['passed']
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,native_boundary_rows=[593,594],original_height_audit=result,negative_cases=negative,matching_xy_requires_native_route_verification=True,independent_trajectory_claim=False,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'audit_front_corridor_lateral_r1_v1_stage_front_height.py',D/'INTEGRATED_NATIVE_BOUNDARY_CHECK.json',ep/'frontal_bypass.json',ep/'expert_control.json']},physical_execution=False,training_ready=False)
with (D/'NONPUSH_HEIGHT_BOUNDARY_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,negative=len(negative),matching_xy_scope_limited=True)))
