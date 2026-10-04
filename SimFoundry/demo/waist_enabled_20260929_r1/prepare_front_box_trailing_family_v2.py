"""Original224-audit family with exact declared-version admission repair.
No load, geometry, phase, normal/reference math or original task gate changes.
All old failed stage and audit sources remain immutable.
"""
from pathlib import Path
import ast,json,hashlib,re,datetime
W=Path(__file__).resolve().parent;D=W/'front_box_trailing_admission_preparation_r2';C=W/'front_box_trailing_admission_fix_candidate_v1';S=W/'staged_front_box_trailing_v2';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
stage=read(D/'STAGE_PREPARATION.json');assert stage['passed'];proof=read(C/'NATIVE_ADMISSION_CHECK.json');assert proof['passed']
for p,h in proof['source_sha256'].items():assert sha(p)==h,p
oldfile=W/'front_box_trailing_preparation_r1/AUDIT_FAMILY_PREPARATION.json';old=read(oldfile);parents=old['adapters'];assert len(parents)==42
mapping={Path(r['path']).stem:Path(r['path']).stem.replace('front_box_trailing_r1_','front_box_trailing_r2_') if 'front_box_trailing_r1_' in Path(r['path']).stem else Path(r['path']).stem.replace('front_box_trailing_','front_box_trailing_r2_') for r in parents}
mapping.update(front_box_trailing_stage_source_binding_v1='front_box_trailing_stage_source_binding_v2',staged_front_box_trailing_v1='staged_front_box_trailing_v2',FRONT_BOX_TRAILING_R1_='FRONT_BOX_TRAILING_R2_',FRONT_BOX_TRAILING_STREAM_V2_AUDIT='FRONT_BOX_TRAILING_R2_STREAM_V2_AUDIT')
pat=re.compile('|'.join(map(re.escape,sorted(mapping,key=len,reverse=True))));inverse={v:k for k,v in mapping.items()};rev=re.compile('|'.join(map(re.escape,sorted(inverse,key=len,reverse=True))));entries=[];changed={Path(r['parent']).name:r for r in stage['audit_consumer_candidates']}
for record in parents:
 parent=Path(record['path']);assert sha(parent)==record['sha256'];dest=W/(mapping[parent.stem]+'.py');text=pat.sub(lambda m:mapping[m.group()],parent.read_text());edits=[]
 if parent.name in changed:
  c=changed[parent.name];assert sha(c['candidate'])==c['candidate_sha256'];e=c['edit'];assert text.count(e['old'])==1;text=text.replace(e['old'],e['new']);edits.append(e)
 restored=text
 for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert rev.sub(lambda m:inverse[m.group()],restored)==parent.read_text();ast.parse(text)
 with dest.open('x') as f:f.write(text)
 entries.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest),edits=edits))
parent=W/'front_box_trailing_stage_source_binding_v1.py';dest=W/'front_box_trailing_stage_source_binding_v2.py';text=parent.read_text();edits=[]
def edit(a,b):
 global text
 assert text.count(a)==1,(a[:100],text.count(a));text=text.replace(a,b);edits.append(dict(old=a,new=b))
edit("S=W/'staged_front_box_trailing_v1'","S=W/'staged_front_box_trailing_v2'")
a=text.index('def verify_preparation():');b=text.index('\ndef verify_settings',a)
edit(text[a:b],'''def verify_preparation():
 from front_box_trailing_stage_source_binding_v1 import verify_preparation as verify_parent
 parent_used,bound=verify_parent();D=W/'front_box_trailing_admission_preparation_r2';C=W/'front_box_trailing_admission_fix_candidate_v1'
 prep=json.loads((D/'STAGE_PREPARATION.json').read_text());parent=Path(prep['parent']);assert parent==W/'staged_front_box_trailing_v1' and Path(prep['stage'])==S
 assert prep['passed'] and set(prep['changed_files'])=={'waist_coordination_clearance.py'}
 for n,h in prep['parent_files'].items():assert sha(parent/n)==h,n
 for n,h in prep['stage_sha256'].items():assert sha(S/n)==h,n
 for name,e in prep['changed_files'].items():
  text=(S/name).read_text();assert text.count(e['new'])==1 and text.replace(e['new'],e['old'])==(parent/name).read_text()
 for name,h in prep['parent_files'].items():
  if name not in prep['changed_files']:assert sha(S/name)==h,name
 assert sha(S/'waist_coordination_clearance.py')==sha(C/'waist_coordination_clearance.py')
 for row in prep['audit_consumer_candidates']:
  assert sha(row['parent'])==row['parent_sha256'] and sha(row['candidate'])==row['candidate_sha256']
  bound[row['parent']]=row['parent_sha256'];bound[row['candidate']]=row['candidate_sha256']
 proof=json.loads((C/'NATIVE_ADMISSION_CHECK.json').read_text());assert proof['passed'] and proof['native_saved_events']==392 and len(proof['negative_rejections'])==14
 for p,h in {**prep['source_sha256'],**proof['source_sha256']}.items():assert sha(p)==h,p;bound[p]=h
 used={n:sha(S/n) for n in parent_used};assert len(used)==98
 for p in [D/'STAGE_PREPARATION.json',C/'NATIVE_ADMISSION_CHECK.json',Path(__file__)]:bound[str(p)]=sha(p)
 return used,bound
''')
restored=text
for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==parent.read_text();ast.parse(text)
with dest.open('x') as f:f.write(text)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=entries,helpers=old['helpers'],replacements=mapping,source_binding=dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest),edits=edits),expected_full_invocations=224,source_sha256={str(p):sha(p) for p in [Path(__file__),oldfile,D/'STAGE_PREPARATION.json',C/'NATIVE_ADMISSION_CHECK.json']},native_integration_checks_pending=True,physical_started=False,training_ready=False)
with (D/'AUDIT_FAMILY_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(adapters=len(entries),changed_consumers=len(changed),source_binding=str(dest),expected_full_invocations=224,physical_started=False)))
