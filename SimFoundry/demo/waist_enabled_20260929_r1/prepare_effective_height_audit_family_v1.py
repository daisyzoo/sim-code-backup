"""Derive all42 parent adapters and97-source binding; preserve original224 audits."""
from pathlib import Path
import ast,json,hashlib,datetime,re
W=Path(__file__).resolve().parent;D=W/'front_effective_height_preparation_r1';S=W/'staged_front_effective_height_v1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
proofs=[D/n for n in ['COLLECTOR_WIRING_CHECK.json','NATIVE_COMMAND_CHAIN_CHECK.json','INDEPENDENT_RECORD_CHECK_V1.json']]
for p in proofs:
 v=read(p);assert v['passed']
 for f,h in v['source_sha256'].items():assert sha(f)==h,f
old=W/'front_loaded_z_quarter_preparation_r1/AUDIT_FAMILY_PREPARATION.json';parents=read(old)['adapters'];assert len(parents)==42
mapping={Path(r['path']).stem:Path(r['path']).stem.replace('front_loaded_z_quarter_','front_effective_height_') for r in parents}
mapping.update(front_loaded_z_quarter_stage_source_binding_v1='front_effective_height_stage_source_binding_v1',staged_front_loaded_z_quarter_v1='staged_front_effective_height_v1',FRONT_LOADED_Z_QUARTER_R1_='FRONT_EFFECTIVE_HEIGHT_R1_',FRONT_LOADED_Z_QUARTER_STREAM_V2_AUDIT='FRONT_EFFECTIVE_HEIGHT_STREAM_V2_AUDIT',audit_joint_transport_reserve_records_v2='audit_effective_height_transport_records_v1')
pat=re.compile('|'.join(map(re.escape,sorted(mapping,key=len,reverse=True))));inverse={v:k for k,v in mapping.items()};rev=re.compile('|'.join(map(re.escape,sorted(inverse,key=len,reverse=True))));entries=[]
for r in parents:
 parent=Path(r['path']);assert sha(parent)==r['sha256'];dest=W/(mapping[parent.stem]+'.py');text=pat.sub(lambda m:mapping[m.group()],parent.read_text());edits=[]
 if parent.name=='audit_front_loaded_z_quarter_stream_v2.py':
  a='JointStreamAudit(JointRecordAudit(ROOT,S,guard))';b="JointStreamAudit(JointRecordAudit(ROOT,S,guard,effective_quarter_height=meta.get('joint_transport_effective_quarter_height',False)))";assert text.count(a)==1;text=text.replace(a,b);edits.append(dict(old=a,new=b))
  a="W/'audit_effective_height_transport_records_v1.py'";assert text.count(a)==1;b=a+",W/'audit_effective_height_contact_v1.py'";text=text.replace(a,b);edits.append(dict(old=a,new=b))
 restored=text
 for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert rev.sub(lambda m:inverse[m.group()],restored)==parent.read_text();ast.parse(text)
 with dest.open('x') as f:f.write(text)
 entries.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest),edits=edits))
parent=W/'front_loaded_z_quarter_stage_source_binding_v1.py';dest=W/'front_effective_height_stage_source_binding_v1.py';text=parent.read_text();edits=[]
def edit(a,b):
 global text
 assert text.count(a)==1,(a[:100],text.count(a));text=text.replace(a,b);edits.append(dict(old=a,new=b))
edit("S=W/'staged_front_loaded_z_quarter_v1'","S=W/'staged_front_effective_height_v1'")
a=text.index('def verify_preparation():');b=text.index('\ndef verify_settings',a)
edit(text[a:b],'''EFFECTIVE_HELPERS=['effective_loaded_contact_task_v1.py','joint_transport_effective_height_solver_v1.py','joint_transport_effective_height_certificate_v1.py','joint_transport_effective_height_runtime_v1.py']

def verify_preparation():
 from front_loaded_z_quarter_stage_source_binding_v1 import verify_preparation as verify_parent
 parent_used,bound=verify_parent();D=W/'front_effective_height_preparation_r1';prep=json.loads((D/'STAGE_PREPARATION.json').read_text());parent=Path(prep['parent']);assert parent==W/'staged_front_loaded_z_quarter_v1'
 for p,h in prep['source_sha256'].items():assert sha(p)==h,p
 for p,h in prep['candidate_sha256'].items():assert sha(p)==h,p
 restored=(S/'collect_paired_sorting.py').read_text()
 for e in reversed(prep['collector_edits']):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert restored==(parent/'collect_paired_sorting.py').read_text()
 for n in parent_used:
  if n!='collect_paired_sorting.py':assert sha(S/n)==sha(parent/n)
 for n in EFFECTIVE_HELPERS:assert sha(S/n)==sha(W/n)
 used={n:sha(S/n) for n in [*parent_used,*EFFECTIVE_HELPERS]};assert len(used)==97
 for p in [D/'COLLECTOR_WIRING_CHECK.json',D/'NATIVE_COMMAND_CHAIN_CHECK.json',D/'INDEPENDENT_RECORD_CHECK_V1.json']:
  r=json.loads(p.read_text());assert r['passed']
  for f,h in r['source_sha256'].items():assert sha(f)==h,f
  bound[str(p)]=sha(p)
 for p in [D/'STAGE_PREPARATION.json',D/'RECORD_AUDITOR_PREPARATION.json',Path(__file__),W/'audit_effective_height_transport_records_v1.py',W/'audit_effective_height_contact_v1.py']:bound[str(p)]=sha(p)
 return used,bound
''')
a=text.index('def verify_settings(args):');b=text.index('\ndef verify_trial_provenance',a)
edit(text[a:b],'''def verify_settings(args):
 from front_loaded_z_quarter_stage_source_binding_v1 import verify_settings as verify_parent
 args=dict(args);enabled=args.pop('joint_transport_effective_quarter_height');assert type(enabled) is bool
 if enabled:assert args['front_loaded_z_quarter'] and args['front_loaded_z_priority'] and args['joint_transport_clearance'] and args['role']=='diagnostic' and not any(args.get(k) for k in ['policy_port','idle','waist_probe','waist_pilot_contract'])
 return verify_parent(args)
''')
a=" if not args['front_loaded_z_quarter']:expected={k:v for k,v in expected.items() if k!=QUARTER_HELPER}"
edit(a,a+"\n if not args['joint_transport_effective_quarter_height']:expected={k:v for k,v in expected.items() if k not in EFFECTIVE_HELPERS}")
a=" assert meta['joint_transport_clearance']==data['spec']==spec and data['training_ready'] is False"
edit(a," enabled=json.loads((ep.parent/'provenance.json').read_text())['args']['joint_transport_effective_quarter_height'];assert type(enabled) is bool\n if enabled:\n  spec=dict(spec,version='joint_transport_clearance_effective_quarter_v1',effective_quarter_height=True,contact_height_target='verified_effective_quarter_task',original_full_task_objective=True,original_height_tolerance_m=2e-7)\n  assert meta['joint_transport_effective_quarter_height'] is True\n else:assert 'joint_transport_effective_quarter_height' not in meta\n"+a)
a=" assert meta['joint_transport_applied_frames']==sum(r['applied'] for r in rows)"
edit(a,a+"\n if enabled:assert all(r['effective_quarter_height'] is True for r in rows)\n else:assert all('effective_quarter_height' not in r for r in rows)")
restored=text
for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==parent.read_text();ast.parse(text)
with dest.open('x') as f:f.write(text)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=entries,replacements=mapping,source_binding=dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest),edits=edits),expected_full_invocations=224,source_sha256={str(p):sha(p) for p in [Path(__file__),old,*proofs]},native_checks_pending=True,physics_started=False,training_ready=False)
with (D/'AUDIT_FAMILY_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(adapters=len(entries),active_sources_enabled=97,expected_full_invocations=224,physics_started=False)))
