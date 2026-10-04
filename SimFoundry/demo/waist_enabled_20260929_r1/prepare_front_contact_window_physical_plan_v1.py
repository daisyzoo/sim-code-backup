"""Prepare the complete matched 8push+2wait window comparison; do not launch.
Retain all224 parent audit invocations plus one window audit per condition.
"""
from pathlib import Path
import json,hashlib,copy,datetime,ast
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'front_contact_window_preparation_r2';S=W/'staged_front_contact_window_v2';P=W/'front_contact_window_physical_preparation_r1';P.mkdir(exist_ok=False);R=W/'front_contact_window_physical_r1';parent=W/'front_loaded_z_quarter_physical_r2';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
original=read(parent/'PROTOCOL.json')['plan'];summary=read(parent/'NUMERIC_VISUAL_SUMMARY.json');assert summary['actual_reviews']==10 and summary['push_passed']==6 and summary['wait_passed']==2
plan=copy.deepcopy(original);plan.update(created_at_utc=now(),status='prepared_not_launched',collector=str(S/'collect_paired_sorting.py'),collector_sha256=sha(S/'collect_paired_sorting.py'),parent_run=str(parent),parent_protocol=str(parent/'PROTOCOL.json'),parent_protocol_sha256=sha(parent/'PROTOCOL.json'),scope=__doc__,simulation_started=False,training_ready=False,expected_conditions=10,expected_original_audits=224,expected_additional_window_audits=10,expected_audits=234,original_gates_unchanged=True,candidate_only_new_flag='--front-contact-window',direct_parent_numeric_visual_sha256=sha(parent/'NUMERIC_VISUAL_SUMMARY.json'),required_before_launch=['Enabled1200-frame front source-contract integration and existing off/wait/source/native/independent-observation checks pass; fixtures are not physical proof.','All234 scheduled audits, source hashes, original control mathematics, numeric reviewers and exact producer identities validated in launcher configuration.','Current early-edge run finishes10conditions and10actual image reviews; its producer terminal.','GPU empty; original30GiB startup and25GiB remaining-case reserve unchanged.','Direct quarter parent full224 audit closure required for final comparison.','No selective retry/admission. Full original paired groups,zero start,11D,no assist and h10 requirements retained.'],benefit_assessment='Require actual improvement in difficult front-bag completion and no loss of existing conditions. Front-box may not benefit because prior full recorded loss stream has no added evidence. Candidate success cannot be inferred from static replay or front-box compatibility fixture. Multiple seeds and untouched broad layouts remain later goal requirements.')
for c,old in zip(plan['commands'],original['commands']):
 args=list(old['args']);args[args.index('--out-dir')+1]=str(R/f"case_{c['layout_id']}");assert '--front-contact-window' not in args;args.append('--front-contact-window');c['args']=args
 assert {k:v for k,v in c.items() if k!='args'}=={k:v for k,v in old.items() if k!='args'}
assert len(plan['commands'])==6 and sum(len(c['tasks']) for c in plan['commands'])==10 and sum(c['wait'] for c in plan['commands'])==2
with (P/'PLAN.json').open('x') as f:json.dump(plan,f,indent=2,ensure_ascii=False)
# Reuse original numeric/visual protocols. Longest specific path substitutions
# precede generic audit module names, preserving comparison mathematical code.
replacements=[('front_loaded_z_quarter_stage_source_binding_v1','front_contact_window_stage_source_binding_v2'),('front_loaded_z_quarter_physical_preparation_r2','front_contact_window_physical_preparation_r1'),('front_loaded_z_quarter_physical_r2','front_contact_window_physical_r1'),('front_loaded_z_quarter_trial2','front_contact_window_trial1'),('front_loaded_z_quarter','front_window'),('FRONT_LOADED_Z_QUARTER_R2','FRONT_CONTACT_WINDOW_R1')]
def remap(text):
 for a,b in replacements:text=text.replace(a,b)
 return text
files=[]
for row in read(W/'front_loaded_z_quarter_physical_preparation_r2/REVIEW_AND_WATCHER_PREPARATION.json')['files']:
 old=Path(row['path']);assert sha(old)==row['sha256'];new=W/remap(old.name);text=remap(old.read_text());edits=[]
 if old.name.startswith('watch_') and 'physical_audits' in old.name:
  a='assert len(all_rows)==224';b='assert len(all_rows)==234';assert text.count(a)==1;text=text.replace(a,b);edits.append([a,b])
 restored=text
 for a,b in reversed(edits):assert restored.count(b)==1;restored=restored.replace(b,a)
 for a,b in reversed(replacements):restored=restored.replace(b,a)
 assert restored==old.read_text(),old.name
 ast.parse(text)
 with new.open('x') as f:f.write(text)
 files.append(dict(parent=str(old),parent_sha256=sha(old),path=str(new),sha256=sha(new),edits=edits))
with (P/'REVIEW_AND_WATCHER_PREPARATION.json').open('x') as f:json.dump(dict(created_at_utc=now(),scope=__doc__,files=files,replacements=replacements,inverse_checked=True,original_math_unchanged=True,simulation_started=False,training_ready=False),f,indent=2)
with (P/'PLAN_DERIVATION.json').open('x') as f:json.dump(dict(created_at_utc=now(),source_sha256={str(p):sha(p) for p in [Path(__file__),P/'PLAN.json',P/'REVIEW_AND_WATCHER_PREPARATION.json',parent/'PROTOCOL.json',parent/'NUMERIC_VISUAL_SUMMARY.json',D/'AUDIT_FAMILY_PREPARATION.json',D/'AUDIT_FAMILY_IMPORT_INVENTORY_CHECK_V2.json']},only_command_changes=['output directory','append --front-contact-window'],same_original_groups_tasks_seeds_horizons=True,launcher_prepared=False,queued=False,simulation_started=False,training_ready=False),f,indent=2)
print(json.dumps(dict(conditions=10,audits=234,direct_parent=str(parent),reviewer_files=len(files),queued=False,simulation_started=False)))
