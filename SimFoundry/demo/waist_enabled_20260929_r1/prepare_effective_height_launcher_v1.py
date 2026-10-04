"""Prepare complete matched launcher and closure, without starting physics."""
from pathlib import Path
import ast,re,json,hashlib,datetime
W=Path(__file__).resolve().parent;P=W/'front_effective_height_physical_preparation_r2';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
mapping=dict(read(P/'REVIEW_AND_WATCHER_PREPARATION.json')['replacements']);mapping.update(staged_front_loaded_z_quarter_v1='staged_front_effective_height_v1',front_loaded_z_quarter_preparation_r1='front_effective_height_preparation_r1');reverse={v:k for k,v in mapping.items()}
pat=re.compile('|'.join(map(re.escape,sorted(mapping,key=len,reverse=True))));rev=re.compile('|'.join(map(re.escape,sorted(reverse,key=len,reverse=True))))
def remap(t):return pat.sub(lambda m:mapping[m.group()],t)
old=W/'run_front_loaded_z_quarter_trial2_physical_r2.py';new=W/'run_front_effective_height_trial1_physical_r2.py';text=remap(old.read_text());edits=[]
def edit(a,b):
 global text
 assert text.count(a)==1,(a[:100],text.count(a));text=text.replace(a,b);edits.append(dict(old=a,new=b))
edit("PREVIOUS=W/'front_corridor_lateral_physical_r1'", "PREVIOUS=W/'front_loaded_z_quarter_physical_r2'")
edit(next(l for l in text.splitlines() if l.startswith('CHECKS=')),"CHECKS="+repr(['COLLECTOR_WIRING_CHECK.json','NATIVE_COMMAND_CHAIN_CHECK.json','INDEPENDENT_RECORD_CHECK_V1.json','AUDIT_FAMILY_IMPORT_CHECK.json','NATIVE_WAIT_ENABLED_CHECK_V2.json','NATIVE_WAIT_DISABLED_CHECK_V2.json','NATIVE_FRONT_DEFAULTOFF_CHECK.json']))
edit('assert len(used)==93','assert len(used)==97')
edit("expected.append('--front-loaded-z-quarter')", "expected.append('--joint-transport-effective-quarter-height')")
edit("prelaunch=dict(parsed);assert prelaunch.pop('front_loaded_z_quarter')", "prelaunch=dict(parsed);assert prelaunch.pop('joint_transport_effective_quarter_height') is True;assert prelaunch.pop('front_loaded_z_quarter')")
edit("str(W/'watch_front_corridor_lateral_trial1_physical_audits_r1.py')", "str(W/'watch_front_loaded_z_quarter_trial2_physical_audits_r2.py')")
# New closure is only permitted once original parent audits finish.
restored=text
for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert rev.sub(lambda m:reverse[m.group()],restored)==old.read_text();ast.parse(text)
with new.open('x') as f:f.write(text)
oldc=W/'close_front_loaded_z_quarter_trial2_physical_v1.py';newc=W/'close_front_effective_height_trial1_physical_v1.py';ct=remap(oldc.read_text());ce=[]
for a,b in [('front_corridor_lateral_physical_r1','front_loaded_z_quarter_physical_r2'),("comparison_role='quarter_z_against_lateral_parent'", "comparison_role='effective_height_against_quarter_parent'")]:
 assert a in ct;ct=ct.replace(a,b);ce.append(dict(old=a,new=b))
restored=ct
for e in reversed(ce):restored=restored.replace(e['new'],e['old'])
assert rev.sub(lambda m:reverse[m.group()],restored)==oldc.read_text();ast.parse(ct)
with newc.open('x') as f:f.write(ct)
with (P/'LAUNCHER_DERIVATION.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),launcher_parent=str(old),launcher_parent_sha256=sha(old),launcher=str(new),launcher_sha256=sha(new),closure_parent=str(oldc),closure_parent_sha256=sha(oldc),closure=str(newc),closure_sha256=sha(newc),replacements=mapping,launcher_edits=edits,closure_edits=ce,inverse_checked=True,source_sha256={str(p):sha(p) for p in [Path(__file__),P/'PLAN.json',P/'REVIEW_AND_WATCHER_PREPARATION.json']},physical_started=False,training_ready=False),f,indent=2)
print('PREPARED_NOT_STARTED')
