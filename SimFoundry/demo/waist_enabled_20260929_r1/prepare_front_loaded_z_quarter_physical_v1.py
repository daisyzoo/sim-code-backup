"""Prepare quarter-Z matched diagnostic against lateral parent: original8push2wait.
Keep complete layouts,1200/70frames,original224audits and actual image review.
New quarter flag is the sole semantic difference; no physical launch or admission.
"""
from pathlib import Path
import json,hashlib,datetime,ast,copy
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'front_loaded_z_quarter_physical_preparation_r1';D=W/'front_loaded_z_quarter_preparation_r1';S=W/'staged_front_loaded_z_quarter_v1';P.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
mapping={'front_corridor_lateral':'front_loaded_z_quarter','FRONT_CORRIDOR_LATERAL':'FRONT_LOADED_Z_QUARTER'}
def remap(t):
 for a,b in mapping.items():t=t.replace(a,b)
 return t
def invert(t):
 for a,b in mapping.items():t=t.replace(b,a)
 return t
files=[]
for r in read(W/'front_corridor_lateral_physical_preparation_r1/REVIEW_AND_WATCHER_PREPARATION.json')['files']:
 parent=Path(r['path']);assert sha(parent)==r['sha256'];dest=W/remap(parent.name);text=remap(parent.read_text());assert invert(text)==parent.read_text();ast.parse(text)
 with dest.open('x') as f:f.write(text)
 files.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest)))
(P/'REVIEW_AND_WATCHER_PREPARATION.json').write_text(json.dumps(dict(created_at_utc=now(),scope=__doc__,files=files,replacements=mapping,simulation_started=False,training_ready=False),indent=2))
parent=W/'front_corridor_lateral_physical_r1';proto=read(parent/'PROTOCOL.json');base=proto['plan'];plan=copy.deepcopy(read(W/'front_corridor_lateral_physical_preparation_r1/PLAN.json'))
plan.update(created_at_utc=now(),collector=str(S/'collect_paired_sorting.py'),collector_sha256=sha(S/'collect_paired_sorting.py'),parent_protocol=str(parent/'PROTOCOL.json'),parent_protocol_sha256=sha(parent/'PROTOCOL.json'),parent_run=str(parent),scope=__doc__,groups=copy.deepcopy(base['groups']),commands=copy.deepcopy(base['commands']),required_before_launch=['Quarter native command chain, full archived streams, independent records, enabled/disabled source fixtures and original audit family pass with bound sources.','Current front-box trial completes original10conditions and10actual reviews, with producer terminal.','Direct lateral parent completes collection and10actual reviews. Its original224audits must close before final comparison.','GPU free and original30GiB startup/25GiB reserve storage requirements pass.'],simulation_started=False,training_ready=False)
for item in plan['commands']:
 args=item['args'];args[args.index('--out-dir')+1]=str(W/'front_loaded_z_quarter_physical_r1'/f"case_{item['layout_id']}");assert '--front-corridor-lateral-replan' in args;args.append('--front-loaded-z-quarter')
(P/'PLAN.json').write_text(json.dumps(plan,indent=2))
parent_runner=W/'run_front_corridor_lateral_trial1_physical_r1.py';dest=W/'run_front_loaded_z_quarter_trial1_physical_r1.py';text=remap(parent_runner.read_text());edits=[]
def edit(a,b):
 global text
 assert text.count(a)==1,(a[:120],text.count(a));text=text.replace(a,b);edits.append(dict(old=a,new=b))
edit("PREVIOUS=W/'joint_transport_reserve_physical_r1'","PREVIOUS=W/'front_corridor_lateral_physical_r1'")
edit(next(l for l in text.splitlines() if l.startswith('CHECKS=')),"CHECKS=['COLLECTOR_WIRING_CHECK.json','NATIVE_COMMAND_CHAIN_CHECK.json','AUDIT_FAMILY_IMPORT_CHECK.json','FAMILY_NATIVE_WAIT_ENABLED_CHECK.json','FAMILY_NATIVE_WAIT_DISABLED_CHECK.json','NATIVE_FRONT_DEFAULTOFF_CHECK.json']")
edit('assert len(used)==92','assert len(used)==93')
edit("expected.append('--front-corridor-lateral-replan')","expected.append('--front-loaded-z-quarter')")
edit("prelaunch=dict(parsed);assert prelaunch.pop('front_loaded_z_quarter_replan') is True;","prelaunch=dict(parsed);assert prelaunch.pop('front_loaded_z_quarter') is True;assert prelaunch.pop('front_corridor_lateral_replan') is True;")
edit("str(W/'watch_joint_transport_reserve_trial1_physical_audits_r1.py')","str(W/'watch_front_corridor_lateral_trial1_physical_audits_r1.py')")
edit("rear=W/'rear_trailing_physical_r1'","rear=W/'front_box_trailing_physical_r1'")
edit("  for row in r['adapters']+r.get('shared_unchanged_adapters',[]):","  for row in r['adapters']+r.get('shared_unchanged_adapters',[])+[r['source_binding']]:")
restored=text
for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert invert(restored)==parent_runner.read_text();ast.parse(text)
with dest.open('x') as f:f.write(text)
closer_parent=W/'close_front_corridor_lateral_trial1_physical_v1.py';closer=W/'close_front_loaded_z_quarter_trial1_physical_v1.py';ct=remap(closer_parent.read_text());ct=ct.replace('joint_transport_reserve_physical_r1','front_corridor_lateral_physical_r1').replace("comparison_role='lateral_corridor_against_reserve_parent'","comparison_role='quarter_z_against_lateral_parent'")
restored_ct=ct.replace('front_corridor_lateral_physical_r1','joint_transport_reserve_physical_r1').replace("comparison_role='quarter_z_against_lateral_parent'","comparison_role='lateral_corridor_against_reserve_parent'");assert invert(restored_ct)==closer_parent.read_text();ast.parse(ct)
with closer.open('x') as f:f.write(ct)
report=dict(passed=True,created_at_utc=now(),launcher_parent=str(parent_runner),launcher_parent_sha256=sha(parent_runner),launcher=str(dest),launcher_sha256=sha(dest),replacements=mapping,edits=edits,inverse_checked=True,closure_parent=str(closer_parent),closure_parent_sha256=sha(closer_parent),closure=str(closer),closure_sha256=sha(closer),source_sha256={str(p):sha(p) for p in [Path(__file__),P/'PLAN.json',P/'REVIEW_AND_WATCHER_PREPARATION.json',parent/'PROTOCOL.json']},physical_started=False,training_ready=False)
(P/'LAUNCHER_DERIVATION.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(prepared=True,conditions=10,audits=224,direct_parent=str(parent),physical_started=False,configuration_pending=True)))
