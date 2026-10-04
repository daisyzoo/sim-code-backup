"""Prepare a full matched early-edge launcher and closer; do not launch.
Fresh complete comparison, original guards, storage and actual reviews retained.
"""
from pathlib import Path
import ast,json,hashlib,re,datetime
W=Path(__file__).resolve().parent;P=W/'rear_early_edge_physical_preparation_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
mapping={'watch_joint_transport_reserve_trial1_physical_audits_r1':'watch_front_box_trailing_trial2_physical_audits_r1','joint_transport_reserve_physical_r1':'front_box_trailing_physical_r2','front_box_trailing_trial2_numeric_reviews_r2':'rear_early_edge_trial1_numeric_reviews_r1','front_box_trailing_trial2_physical_r2':'rear_early_edge_trial1_physical_r1','front_box_trailing_trial2':'rear_early_edge_trial1','front_box_trailing_physical_preparation_r2':'rear_early_edge_physical_preparation_r1','front_box_trailing_physical_r2':'rear_early_edge_physical_r1','front_box_trailing_admission_preparation_r2':'rear_early_edge_preparation_r1','staged_front_box_trailing_v2':'staged_rear_early_edge_v1','front_box_trailing_stage_source_binding_v2':'rear_early_edge_stage_source_binding_v1','front_box_trailing_r2_':'rear_early_edge_r1_','FRONT_BOX_TRAILING_R2_':'REAR_EARLY_EDGE_R1_'}
pat=re.compile('|'.join(map(re.escape,sorted(mapping,key=len,reverse=True))));inverse={v:k for k,v in mapping.items()};rev=re.compile('|'.join(map(re.escape,sorted(inverse,key=len,reverse=True))));remap=lambda t:pat.sub(lambda m:mapping[m.group()],t);invert=lambda t:rev.sub(lambda m:inverse[m.group()],t)
parent=W/'run_front_box_trailing_trial2_physical_r2.py';dest=W/'run_rear_early_edge_trial1_physical_r1.py';text=remap(parent.read_text());edits=[]
def edit(a,b):
 global text
 assert text.count(a)==1,(a[:120],text.count(a));text=text.replace(a,b);edits.append(dict(old=a,new=b))
edit(next(l for l in text.splitlines() if l.startswith('CHECKS=')),"CHECKS=['COLLECTOR_WIRING_CHECK.json','AUDIT_FAMILY_IMPORT_CHECK.json','NATIVE_WAIT_SOURCE_CHECK.json','NATIVE_UNCHANGED_PUSH_SOURCE_CHECK_V2.json','../rear_early_edge_candidate_v1/NATIVE_STAGE_CONTIGUOUS_REAR_AUDIT_V1.json','../rear_early_edge_candidate_v1/NATIVE_LOADED_BOUT_JOINT_REPLAY_V4.json','../rear_early_edge_physical_preparation_r1/REVIEW_ROUTE_AND_EXIT_COUNT_CHECK.json']")
edit('assert len(used)==98','assert len(used)==100')
edit("expected.append('--front-box-trailing-landing')","expected.append('--rear-early-edge')")
edit("prelaunch=dict(parsed);assert prelaunch.pop('front_box_trailing_landing') is True", "prelaunch=dict(parsed);assert prelaunch.pop('rear_early_edge') is True;assert prelaunch.pop('front_box_trailing_landing') is True")
edit(next(l for l in text.splitlines() if l.startswith(" aborted=W/'front_box_trailing_physical_r1'"))+'\n','')
edit("rear=W/'front_corridor_lateral_physical_r1'", "rear=W/'front_loaded_z_quarter_physical_r2'")
needle=" inventory=read(D/'AUDIT_FAMILY_IMPORT_CHECK.json')['inventory'];assert len(inventory)==10 and sum(x['count'] for x in inventory)==224"
edit(needle," joint=read(W/'rear_early_edge_candidate_v1/NATIVE_LOADED_BOUT_JOINT_REPLAY_V4.json');assert joint['joint_candidate_all_accepted'] is True and joint['native_action_updates']==962\n"+needle)
restored=text
for e in reversed(edits):
 if e['new']=='':
  # Removal is restored at its unchanged neighboring preflight statement.
  anchor=" plan,config=configuration();ready=parent_readiness();assert ready['ready'],ready\n";assert restored.count(anchor)==1;restored=restored.replace(anchor,anchor+e['old'])
 else:assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert invert(restored)==parent.read_text();ast.parse(text)
with dest.open('x') as f:f.write(text)
cp=W/'close_front_box_trailing_trial2_physical_v1.py';cd=W/'close_rear_early_edge_trial1_physical_v1.py';ct=remap(cp.read_text());assert invert(ct)==cp.read_text();ast.parse(ct)
with cd.open('x') as f:f.write(ct)
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,launcher_parent=str(parent),launcher_parent_sha256=sha(parent),launcher=str(dest),launcher_sha256=sha(dest),replacements=mapping,edits=edits,inverse_checked=True,closure_parent=str(cp),closure_parent_sha256=sha(cp),closure=str(cd),closure_sha256=sha(cd),source_sha256={str(p):sha(p) for p in [Path(__file__),P/'PLAN.json',P/'REVIEW_AND_WATCHER_PREPARATION.json']},configuration_checked=False,physical_started=False,training_ready=False)
with (P/'LAUNCHER_DERIVATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(prepared=True,conditions=10,audits=224,direct_parent='front_box_trailing_physical_r2',wait_for_quarter=True,physical_started=False)))
