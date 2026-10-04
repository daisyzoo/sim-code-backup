"""Prepare a fresh full8push2wait trial after the r1 admission integration failure.
Compare against the same reserve parent. Never resume/overwrite aborted r1 or
omit its failed/unexecuted conditions. Original controls224 and quality gates.
"""
from pathlib import Path
import ast,json,hashlib,re,copy,datetime
W=Path(__file__).resolve().parent;P=W/'front_box_trailing_physical_preparation_r2';D=W/'front_box_trailing_admission_preparation_r2';S=W/'staged_front_box_trailing_v2';P.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
mapping={'front_box_trailing_trial1_physical_r1':'front_box_trailing_trial2_physical_r2','front_box_trailing_trial1_numeric_reviews_r1':'front_box_trailing_trial2_numeric_reviews_r2','front_box_trailing_trial1':'front_box_trailing_trial2','front_box_trailing_physical_preparation_r1':'front_box_trailing_physical_preparation_r2','front_box_trailing_physical_r1':'front_box_trailing_physical_r2','front_box_trailing_preparation_r1':'front_box_trailing_admission_preparation_r2','staged_front_box_trailing_v1':'staged_front_box_trailing_v2','front_box_trailing_stage_source_binding_v1':'front_box_trailing_stage_source_binding_v2','front_box_trailing_r1_':'front_box_trailing_r2_','FRONT_BOX_TRAILING_R1_':'FRONT_BOX_TRAILING_R2_'}
pat=re.compile('|'.join(map(re.escape,sorted(mapping,key=len,reverse=True))));inverse={v:k for k,v in mapping.items()};rev=re.compile('|'.join(map(re.escape,sorted(inverse,key=len,reverse=True))));remap=lambda t:pat.sub(lambda m:mapping[m.group()],t);invert=lambda t:rev.sub(lambda m:inverse[m.group()],t)
files=[]
for r in read(W/'front_box_trailing_physical_preparation_r1/REVIEW_AND_WATCHER_PREPARATION.json')['files']:
 parent=Path(r['path']);assert sha(parent)==r['sha256'];dest=W/remap(parent.name);text=remap(parent.read_text());assert invert(text)==parent.read_text();ast.parse(text)
 with dest.open('x') as f:f.write(text)
 files.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest)))
(P/'REVIEW_AND_WATCHER_PREPARATION.json').write_text(json.dumps(dict(created_at_utc=now(),scope=__doc__,files=files,replacements=mapping,simulation_started=False,training_ready=False),indent=2))
oldplan=W/'front_box_trailing_physical_preparation_r1/PLAN.json';plan=copy.deepcopy(read(oldplan));plan.update(created_at_utc=now(),collector=str(S/'collect_paired_sorting.py'),collector_sha256=sha(S/'collect_paired_sorting.py'),scope=__doc__,required_before_launch=['Native generated recovery events reach repaired admission and original final guard; full source/audit family fixtures and complete configuration pass.','Aborted front-box r1 producer terminal and failure diagnosis preserves all10planned conditions; no retry of frozen r1.','Same reserve direct parent and lateral prior full10collection/10actual reviews complete; full parent224 closure required for final comparison.','GPU free and original30GiB startup/25GiB reserve storage gates.'],simulation_started=False,training_ready=False)
for c in plan['commands']:
 args=c['args'];args[args.index('--out-dir')+1]=str(W/'front_box_trailing_physical_r2'/f"case_{c['layout_id']}")
(P/'PLAN.json').write_text(json.dumps(plan,indent=2))
parent=W/'run_front_box_trailing_trial1_physical_r1.py';dest=W/'run_front_box_trailing_trial2_physical_r2.py';text=remap(parent.read_text());edits=[]
def edit(a,b):
 global text
 assert text.count(a)==1,(a[:120],text.count(a));text=text.replace(a,b);edits.append(dict(old=a,new=b))
edit(next(l for l in text.splitlines() if l.startswith('CHECKS=')),"CHECKS=['COLLECTOR_BINDING_CHECK.json','AUDIT_FAMILY_IMPORT_CHECK.json','FAMILY_NATIVE_WAIT_CHECK.json','NATIVE_CAPTURE_ADMISSION_CHECK.json']")
anchor=" plan,config=configuration();ready=parent_readiness();assert ready['ready'],ready"
edit(anchor,anchor+"\n aborted=W/'front_box_trailing_physical_r1';aborted_protocol=read(aborted/'PROTOCOL.json');aborted_state=read(aborted/'STATUS.json');failure=read(aborted/'RUNTIME_ABORT_DIAGNOSIS_V1.json');assert aborted_state['status']=='runtime_or_audit_failed' and failure['planned_conditions']==10 and failure['completed_conditions']==5 and failure['runtime_aborted_conditions']==1 and failure['unexecuted_conditions']==4;bound(failure['source_sha256']);proc=identity(aborted_protocol['producer_pid']);assert proc is None or proc['state']=='Z'")
restored=text
for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert invert(restored)==parent.read_text();ast.parse(text)
with dest.open('x') as f:f.write(text)
cp=W/'close_front_box_trailing_trial1_physical_v1.py';cd=W/'close_front_box_trailing_trial2_physical_v1.py';ct=remap(cp.read_text());assert invert(ct)==cp.read_text();ast.parse(ct)
with cd.open('x') as f:f.write(ct)
report=dict(passed=True,created_at_utc=now(),launcher_parent=str(parent),launcher_parent_sha256=sha(parent),launcher=str(dest),launcher_sha256=sha(dest),replacements=mapping,edits=edits,inverse_checked=True,closure_parent=str(cp),closure_parent_sha256=sha(cp),closure=str(cd),closure_sha256=sha(cd),source_sha256={str(p):sha(p) for p in [Path(__file__),oldplan,P/'PLAN.json',P/'REVIEW_AND_WATCHER_PREPARATION.json',W/'front_box_trailing_physical_r1/RUNTIME_ABORT_DIAGNOSIS_V1.json']},physical_started=False,training_ready=False)
(P/'LAUNCHER_DERIVATION.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(prepared=True,conditions=10,audits=224,aborted_r1_retained=True,physical_started=False)))
