"""Prepare matched effective-height experiment; original8push2wait/224audits, no launch."""
from pathlib import Path
import re,ast,copy,datetime,hashlib,json
W=Path(__file__).resolve().parent;D=W/'front_effective_height_preparation_r1';S=W/'staged_front_effective_height_v1';P=W/'front_effective_height_physical_preparation_r2';R=W/'front_effective_height_physical_r1';parent=W/'front_loaded_z_quarter_physical_r2'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
original=read(parent/'PROTOCOL.json')['plan'];summary=read(parent/'NUMERIC_VISUAL_SUMMARY.json');assert summary['actual_reviews']==10 and summary['push_passed']==6 and summary['wait_passed']==2
plan=copy.deepcopy(original);plan.update(created_at_utc=now(),status='prepared_not_launched',collector=str(S/'collect_paired_sorting.py'),collector_sha256=sha(S/'collect_paired_sorting.py'),parent_run=str(parent),parent_protocol=str(parent/'PROTOCOL.json'),parent_protocol_sha256=sha(parent/'PROTOCOL.json'),scope=__doc__,simulation_started=False,training_ready=False,expected_conditions=10,expected_audits=224,original_gates_unchanged=True,candidate_only_new_flag='--joint-transport-effective-quarter-height',direct_parent_numeric_visual_sha256=sha(parent/'NUMERIC_VISUAL_SUMMARY.json'),required_before_launch=['Native wait enabled/disabled and full1200 defaultoff stream integration pass; recorded-state tests are not physical proof.','Original224 audit inventory and numeric/actual image review retained.','Parent collection and10actual reviews complete; parent224 audits must close before final comparison.','No active GPU collector; original >30GiB startup and25GiB remainder reserve.','No selective retries/admission; original complete paired groups, zero start11D, no assist, non-target15mm and h10 retained.'],benefit_assessment='Measure difficult front-bag and front-box outcomes and every original condition. Correct target binding does not by itself prove solver convergence, physical stability, complete paired groups, or model generalization.')
for c,old in zip(plan['commands'],original['commands']):
 args=list(old['args']);args[args.index('--out-dir')+1]=str(R/f"case_{c['layout_id']}");assert '--joint-transport-effective-quarter-height' not in args;args.append('--joint-transport-effective-quarter-height');c['args']=args
 assert {k:v for k,v in c.items() if k!='args'}=={k:v for k,v in old.items() if k!='args'}
assert len(plan['commands'])==6 and sum(len(c['tasks']) for c in plan['commands'])==10
P.mkdir(exist_ok=False)
with (P/'PLAN.json').open('x') as f:json.dump(plan,f,indent=2)
replacements=[('front_loaded_z_quarter_physical_preparation_r2','front_effective_height_physical_preparation_r2'),('front_loaded_z_quarter_physical_r2','front_effective_height_physical_r1'),('front_loaded_z_quarter_trial2','front_effective_height_trial1'),('front_loaded_z_quarter','front_effective_height'),('FRONT_LOADED_Z_QUARTER_R2','FRONT_EFFECTIVE_HEIGHT_R1')]
mapping=dict(replacements);inverse={v:k for k,v in replacements}
pattern=re.compile('|'.join(map(re.escape,sorted(mapping,key=len,reverse=True))))
reverse=re.compile('|'.join(map(re.escape,sorted(inverse,key=len,reverse=True))))
def remap(t):return pattern.sub(lambda m:mapping[m.group()],t)
files=[]
for row in read(W/'front_loaded_z_quarter_physical_preparation_r2/REVIEW_AND_WATCHER_PREPARATION.json')['files']:
 old=Path(row['path']);assert sha(old)==row['sha256'];new=W/remap(old.name);text=remap(old.read_text());restored=text
 restored=reverse.sub(lambda m:inverse[m.group()],restored)
 assert restored==old.read_text();ast.parse(text)
 if new.exists():assert new.read_text()==text
 else:
  with new.open('x') as f:f.write(text)
 files.append(dict(parent=str(old),parent_sha256=sha(old),path=str(new),sha256=sha(new),edits=[]))
with (P/'REVIEW_AND_WATCHER_PREPARATION.json').open('x') as f:json.dump(dict(created_at_utc=now(),files=files,replacements=replacements,inverse_checked=True,original_math_unchanged=True,simulation_started=False,training_ready=False),f,indent=2)
with (P/'PLAN_DERIVATION.json').open('x') as f:json.dump(dict(created_at_utc=now(),source_sha256={str(p):sha(p) for p in [Path(__file__),P/'PLAN.json',P/'REVIEW_AND_WATCHER_PREPARATION.json',parent/'PROTOCOL.json',parent/'NUMERIC_VISUAL_SUMMARY.json',D/'AUDIT_FAMILY_PREPARATION.json',D/'AUDIT_FAMILY_IMPORT_CHECK.json']},only_command_changes=['output directory','append --joint-transport-effective-quarter-height'],same_original_groups_tasks_seeds_horizons=True,launcher_prepared=False,simulation_started=False,training_ready=False),f,indent=2)
print(json.dumps(dict(conditions=10,audits=224,reviewer_files=len(files),simulation_started=False)))
