"""Prepare full original224-audit inventory with declared fractional-Z record audits.
Do not relax original task/physics/control gates or launch collection. Full native
fixtures and source/fallback checks remain required before physical readiness.
"""
from pathlib import Path
import json,hashlib,datetime,ast,re
W=Path(__file__).resolve().parent;D=W/'front_loaded_z_quarter_preparation_r1';S=W/'staged_front_loaded_z_quarter_v1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
proofs=[D/'COLLECTOR_WIRING_CHECK.json',D/'NATIVE_COMMAND_CHAIN_CHECK.json',W/'front_loaded_z_fraction_stream_check_r2/RESULT.json',W/'front_loaded_z_fraction_record_check_r3/RESULT.json',W/'front_loaded_z_fraction_right_record_check_r1/RESULT.json']
for p in proofs:
 r=read(p);assert r['passed']
 for f,h in r['source_sha256'].items():assert sha(f)==h,f
oldfile=W/'front_corridor_lateral_preparation_r1/AUDIT_FAMILY_PREPARATION.json';parents=read(oldfile)['adapters'];assert len(parents)==42
mapping={Path(r['path']).stem:Path(r['path']).stem.replace('front_corridor_lateral_r1_','front_loaded_z_quarter_r1_').replace('front_corridor_lateral_','front_loaded_z_quarter_') for r in parents}
mapping.update(front_corridor_lateral_stage_source_binding_v1='front_loaded_z_quarter_stage_source_binding_v1',staged_front_corridor_lateral_v1='staged_front_loaded_z_quarter_v1',FRONT_CORRIDOR_LATERAL_R1_='FRONT_LOADED_Z_QUARTER_R1_',FRONT_CORRIDOR_LATERAL_STREAM_V2_AUDIT='FRONT_LOADED_Z_QUARTER_STREAM_V2_AUDIT')
pat=re.compile('|'.join(map(re.escape,sorted(mapping,key=len,reverse=True))));inverse={v:k for k,v in mapping.items()};rev=re.compile('|'.join(map(re.escape,sorted(inverse,key=len,reverse=True))));entries=[]
for record in parents:
 parent=Path(record['path']);assert sha(parent)==record['sha256'];dest=W/(mapping[parent.stem]+'.py');text=pat.sub(lambda m:mapping[m.group()],parent.read_text());edits=[]
 def change(a,b):
  global text
  assert text.count(a)==1,(dest.name,a,text.count(a));text=text.replace(a,b);edits.append(dict(old=a,new=b))
 if parent.name.endswith(('_v1_z_execution.py','_v2_z_execution.py')):
  change('from audit_front_loaded_z_priority_record import verify_record','from audit_front_loaded_z_fraction_record_v1 import verify_record')
  change('verify_record(**e.arguments(t,m))',"verify_record(**e.arguments(t,m),expected_fraction=.25 if e.meta.get('front_loaded_z_quarter') else 1.)")
  change("'audit_front_loaded_z_priority_record.py','audit_front_loaded_z_priority_applied_row.py'","'audit_front_loaded_z_fraction_record_v1.py','audit_front_loaded_z_fraction_applied_v1.py','audit_front_loaded_z_fraction_task_v1.py'")
 restored=text
 for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert rev.sub(lambda m:inverse[m.group()],restored)==parent.read_text();ast.parse(text)
 with dest.open('x') as f:f.write(text)
 entries.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest),edits=edits))
parent=W/'front_corridor_lateral_stage_source_binding_v1.py';dest=W/'front_loaded_z_quarter_stage_source_binding_v1.py';text=parent.read_text();edits=[]
def edit(a,b):
 global text
 assert text.count(a)==1,(a[:90],text.count(a));text=text.replace(a,b);edits.append(dict(old=a,new=b))
edit("S=W/'staged_front_corridor_lateral_v1'","S=W/'staged_front_loaded_z_quarter_v1'")
a=text.index('def verify_preparation():');b=text.index('\ndef verify_settings',a)
edit(text[a:b],'''QUARTER_HELPER='front_loaded_z_fraction.py'
QUARTER_META=dict(version='front_loaded_z_quarter_v1',fraction=.25,z_target='parent_linear_achieved_to_original_requested',original_task_retained=True,training_ready=False)

def verify_preparation():
 from front_corridor_lateral_stage_source_binding_v1 import verify_preparation as verify_parent
 parent_used,bound=verify_parent();D=W/'front_loaded_z_quarter_preparation_r1'
 prep=json.loads((D/'STAGE_PREPARATION.json').read_text());parent=Path(prep['parent']);assert parent==W/'staged_front_corridor_lateral_v1'
 for p,h in prep['source_sha256'].items():assert sha(p)==h,p
 for p,h in prep['candidate_sha256'].items():assert sha(p)==h,p
 restored=(S/'collect_paired_sorting.py').read_text()
 for e in reversed(prep['collector_edits']):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert restored==(parent/'collect_paired_sorting.py').read_text()
 for name in parent_used:
  if name!='collect_paired_sorting.py':assert sha(S/name)==sha(parent/name)
 assert sha(S/QUARTER_HELPER)==sha(W/'front_loaded_z_fraction_candidate_v1'/QUARTER_HELPER)
 used={name:sha(S/name) for name in [*parent_used,QUARTER_HELPER]};assert len(used)==93
 checks=[D/'COLLECTOR_WIRING_CHECK.json',D/'NATIVE_COMMAND_CHAIN_CHECK.json',W/'front_loaded_z_fraction_stream_check_r2/RESULT.json',W/'front_loaded_z_fraction_record_check_r3/RESULT.json',W/'front_loaded_z_fraction_right_record_check_r1/RESULT.json']
 for p in checks:
  r=json.loads(p.read_text());assert r['passed']
  for f,h in r['source_sha256'].items():assert sha(f)==h,f
  bound[str(p)]=sha(p)
 for p in [D/'STAGE_PREPARATION.json',Path(__file__),W/'audit_front_loaded_z_fraction_record_v1.py',W/'audit_front_loaded_z_fraction_applied_v1.py',W/'audit_front_loaded_z_fraction_task_v1.py']:bound[str(p)]=sha(p)
 return used,bound
''')
a=text.index('def verify_settings(args):');b=text.index('\ndef verify_trial_provenance',a)
edit(text[a:b],'''def verify_settings(args):
 from front_corridor_lateral_stage_source_binding_v1 import verify_settings as verify_parent
 args=dict(args);quarter=args.pop('front_loaded_z_quarter');assert type(quarter) is bool
 if quarter:assert args['front_loaded_z_priority'] and args['joint_transport_clearance'] and args['role']=='diagnostic' and not any(args.get(k) for k in ['policy_port','idle','waist_probe','waist_pilot_contract'])
 return verify_parent(args)
''')
edit(' verify_settings(args)\n prefix='," verify_settings(args)\n if not args['front_loaded_z_quarter']:expected={k:v for k,v in expected.items() if k!=QUARTER_HELPER}\n prefix=")
anchor=" assert meta['front_loaded_z_priority_applied_frames']==sum(r['applied'] for r in log['rows'])"
edit(anchor,anchor+"\n quarter=json.loads((ep.parent/'provenance.json').read_text())['args']['front_loaded_z_quarter'];assert type(quarter) is bool\n if quarter:assert meta['front_loaded_z_quarter']==QUARTER_META\n else:assert 'front_loaded_z_quarter' not in meta and all('reduced_z_task' not in r for r in log['rows'])\n for r in log['rows']:\n  if 'reduced_z_task' in r:assert quarter and r['reduced_z_task']['fraction']==.25")
restored=text
for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==parent.read_text();ast.parse(text)
with dest.open('x') as f:f.write(text)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=entries,replacements=mapping,source_binding=dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest),edits=edits),expected_full_invocations=224,source_sha256={str(p):sha(p) for p in [Path(__file__),oldfile,*proofs]},native_checks_pending=True,physics_started=False,training_ready=False)
with (D/'AUDIT_FAMILY_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(adapters=len(entries),source_binding=str(dest),expected_full_invocations=224,physics_started=False)))
