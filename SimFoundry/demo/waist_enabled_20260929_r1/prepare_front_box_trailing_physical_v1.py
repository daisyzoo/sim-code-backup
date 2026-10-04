"""Prepare matched front-box trailing recovery diagnostic, without launching.
Copy complete original two groups,8push2wait,1200/70frames and224audits.
Only the explicit front-box trailing flag differs from reserve parent.
"""
from pathlib import Path
import json,hashlib,datetime,ast,copy
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'front_box_trailing_physical_preparation_r1';D=W/'front_box_trailing_preparation_r1';S=W/'staged_front_box_trailing_v1';P.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
mapping={'front_corridor_lateral':'front_box_trailing','FRONT_CORRIDOR_LATERAL':'FRONT_BOX_TRAILING','front-corridor-lateral-replan':'front-box-trailing-landing','front_corridor_lateral_replan':'front_box_trailing_landing'}
# Longest substitution first prevents partial rewriting of the option name.
def remap(text):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):text=text.replace(a,b)
 return text
def invert(text):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[1])):text=text.replace(b,a)
 return text
files=[]
oldprep=read(W/'front_corridor_lateral_physical_preparation_r1/REVIEW_AND_WATCHER_PREPARATION.json')
for r in oldprep['files']:
 parent=Path(r['path']);assert sha(parent)==r['sha256'];dest=W/remap(parent.name);text=remap(parent.read_text());assert invert(text)==parent.read_text();ast.parse(text)
 with dest.open('x') as f:f.write(text)
 files.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest)))
(P/'REVIEW_AND_WATCHER_PREPARATION.json').write_text(json.dumps(dict(created_at_utc=now(),scope=__doc__,files=files,replacements=mapping,simulation_started=False,training_ready=False),indent=2))
parent=W/'joint_transport_reserve_physical_r1';proto=read(parent/'PROTOCOL.json');base=proto['plan'];plan=copy.deepcopy(read(W/'front_corridor_lateral_physical_preparation_r1/PLAN.json'))
plan.update(created_at_utc=now(),collector=str(S/'collect_paired_sorting.py'),collector_sha256=sha(S/'collect_paired_sorting.py'),parent_protocol=str(parent/'PROTOCOL.json'),parent_protocol_sha256=sha(parent/'PROTOCOL.json'),parent_run=str(parent),scope=__doc__,groups=copy.deepcopy(base['groups']),commands=copy.deepcopy(base['commands']),required_before_launch=['All front-box trailing preparation proofs pass and all source hashes bind.','Existing lateral full10 collection and10actual image reviews complete; its producer is terminal.','Reserve parent collection and actual10 reviews complete. Parent224 audits must close before final comparative result.','GPU free and original30GiB startup /25GiB reserve storage requirements pass.'],simulation_started=False,training_ready=False)
for item in plan['commands']:
 args=item['args'];args[args.index('--out-dir')+1]=str(W/'front_box_trailing_physical_r1'/f"case_{item['layout_id']}");args.append('--front-box-trailing-landing')
(P/'PLAN.json').write_text(json.dumps(plan,indent=2))
parent_runner=W/'run_front_corridor_lateral_trial1_physical_r1.py';dest=W/'run_front_box_trailing_trial1_physical_r1.py';text=remap(parent_runner.read_text());edits=[]
def edit(a,b):
 global text
 assert text.count(a)==1,(a[:100],text.count(a));text=text.replace(a,b);edits.append(dict(old=a,new=b))
a=next(line for line in text.splitlines() if line.startswith('CHECKS='))
edit(a,"CHECKS=['COLLECTOR_WIRING_CHECK.json','INDEPENDENT_EVENT_CHECK.json','SELECTION_AUDIT_CHECK.json','NATIVE_CAPTURE_CHECK.json','AUDIT_FAMILY_IMPORT_CHECK.json','FAMILY_NATIVE_WAIT_CHECK.json','RECOVERY_STREAM_CHECK.json','ARCHIVE_DISPATCH_CHECK.json','NATIVE_FRONT_DEFAULTOFF_CHECK.json']")
edit('assert len(used)==92','assert len(used)==98')
edit("rear=W/'rear_trailing_physical_r1'","rear=W/'front_corridor_lateral_physical_r1'")
# The unchanged variable name refers to sequencing, not the comparison parent.
# Include the three independent helpers and source binder in the frozen evidence.
a="  for row in r['adapters']+r.get('shared_unchanged_adapters',[]):"
edit(a,"  for row in r['adapters']+r.get('shared_unchanged_adapters',[])+r.get('helpers',[])+[r['source_binding']]:")
restored=text
for e in reversed(edits):restored=restored.replace(e['new'],e['old'])
assert invert(restored)==parent_runner.read_text();ast.parse(text)
with dest.open('x') as f:f.write(text)
closer_parent=W/'close_front_corridor_lateral_trial1_physical_v1.py';closer=W/'close_front_box_trailing_trial1_physical_v1.py';ct=remap(closer_parent.read_text());ct=ct.replace("comparison_role='lateral_corridor_against_reserve_parent'","comparison_role='front_box_trailing_against_reserve_parent'");assert invert(ct.replace("comparison_role='front_box_trailing_against_reserve_parent'","comparison_role='lateral_corridor_against_reserve_parent'"))==closer_parent.read_text();ast.parse(ct)
with closer.open('x') as f:f.write(ct)
report=dict(passed=True,created_at_utc=now(),launcher_parent=str(parent_runner),launcher_parent_sha256=sha(parent_runner),launcher=str(dest),launcher_sha256=sha(dest),replacements=mapping,edits=edits,inverse_checked=True,closure_parent=str(closer_parent),closure_parent_sha256=sha(closer_parent),closure=str(closer),closure_sha256=sha(closer),source_sha256={str(p):sha(p) for p in [Path(__file__),P/'PLAN.json',P/'REVIEW_AND_WATCHER_PREPARATION.json',parent/'PROTOCOL.json']},physical_started=False,training_ready=False)
(P/'LAUNCHER_DERIVATION.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(prepared=True,conditions=10,audits=224,physical_started=False,configuration_pending=True)))
