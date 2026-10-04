"""Version full original224-audit family for lateral midpoint declaration.
Only source namespace/binding and explicit phase argument change; old math and
non-push lift/reference checks remain. No physical launch or training admission.
"""
from pathlib import Path
import json,hashlib,datetime,ast,re
W=Path(__file__).resolve().parent;D=W/'front_corridor_lateral_preparation_r1';S=W/'staged_front_corridor_lateral_v1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
oldfile=W/'joint_transport_reserve_preparation_r1/AUDIT_FAMILY_V2_PREPARATION.json';old=json.loads(oldfile.read_text());parents=old['adapters']+old['shared_unchanged_adapters']
mapping={Path(x['path']).stem:Path(x['path']).stem.replace('joint_transport_reserve_r2_','front_corridor_lateral_r1_').replace('joint_transport_reserve_','front_corridor_lateral_') for x in parents}
mapping.update(joint_transport_reserve_stage_source_binding_v2='front_corridor_lateral_stage_source_binding_v1',staged_joint_transport_reserve_v1='staged_front_corridor_lateral_v1',audit_front_corridor_midpoint_cop='audit_front_corridor_lateral_cop_v1',audit_front_corridor_midpoint_observations='audit_front_corridor_lateral_observations_v1',audit_front_corridor_midpoint_record='audit_front_corridor_lateral_record_v1',JOINT_TRANSPORT_RESERVE_R2_='FRONT_CORRIDOR_LATERAL_R1_',JOINT_TRANSPORT_RESERVE_STREAM_V2_AUDIT='FRONT_CORRIDOR_LATERAL_STREAM_V2_AUDIT')
pat=re.compile('|'.join(map(re.escape,sorted(mapping,key=len,reverse=True))));inverse={v:k for k,v in mapping.items()};rev=re.compile('|'.join(map(re.escape,sorted(inverse,key=len,reverse=True))));entries=[]
for record in parents:
 parent=Path(record['path']);assert sha(parent)==record['sha256'];dest=W/(mapping[parent.stem]+'.py');assert not dest.exists();s=pat.sub(lambda m:mapping[m.group()],parent.read_text());edits=[]
 def change(a,b):
  global s
  assert s.count(a)==1,(dest.name,a,s.count(a));s=s.replace(a,b);edits.append(dict(old=a,new=b))
 if parent.name in ['audit_joint_transport_reserve_r2_v1_execution.py','audit_joint_transport_reserve_r2_v2_execution.py']:
  change('midpoint_enabled=True,expected_steps=range(1,n))',"midpoint_enabled=True,expected_steps=range(1,n),lateral_y_enabled=meta.get('front_corridor_lateral_replan',False))")
 if parent.name=='audit_joint_transport_reserve_r2_v1_diagonal_live.py':
  change("midpoint_enabled=True,expected_steps=range(1,len(tr['box'])))","midpoint_enabled=True,expected_steps=range(1,len(tr['box'])),lateral_y_enabled=args['front_corridor_lateral_replan'])")
 restored=s
 for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert rev.sub(lambda m:inverse[m.group()],restored)==parent.read_text();ast.parse(s)
 with dest.open('x') as f:f.write(s)
 entries.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest),edits=edits))
# Source binding keeps every original observation check, replacing only preparation
# and settings delegation, plus binding the explicit new metadata to arguments.
parent=W/'joint_transport_reserve_stage_source_binding_v2.py';dest=W/'front_corridor_lateral_stage_source_binding_v1.py';s=parent.read_text();changes=[]
def edit(a,b):
 global s
 assert s.count(a)==1,(a[:80],s.count(a));s=s.replace(a,b);changes.append(dict(old=a,new=b))
edit("S=W/'staged_joint_transport_reserve_v1'","S=W/'staged_front_corridor_lateral_v1'")
a=s.index('def verify_preparation():');b=s.index('\ndef verify_settings',a)
edit(s[a:b],'''def verify_preparation():
 from joint_transport_reserve_stage_source_binding_v2 import verify_preparation as verify_original
 parent_used,bound=verify_original()
 prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());parent=Path(prep['parent']);assert parent==W/'staged_joint_transport_reserve_v1'
 for name,h in prep['parent_files'].items():assert sha(parent/name)==h,name
 for name,h in prep['stage_sha256'].items():assert sha(S/name)==h,name
 assert set(prep['changed_files'])=={'front_corridor_midpoint_runtime.py','front_initial_center_route.py','collect_paired_sorting.py'}
 for name,edits in prep['changed_files'].items():
  restored=(S/name).read_text()
  for e in reversed(edits):
   assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
  assert restored==(parent/name).read_text()
 for name,h in prep['parent_files'].items():
  if name not in prep['changed_files']:assert sha(S/name)==h
 assert sha(S/'SUPPORT_ERROR_BOUND.md')==sha(parent/'SUPPORT_ERROR_BOUND.md')
 used={name:sha(S/name) for name in parent_used};assert len(used)==92
 for name in ['COLLECTOR_WIRING_CHECK.json','INTEGRATED_NATIVE_BOUNDARY_CHECK.json','INDEPENDENT_AUDITOR_CHECK.json','ARCHIVE_COMPLETENESS_CHECK.json','SINGLE_UNISSUED_JOINT_PROPOSAL.json']:
  p=W/'front_corridor_lateral_preparation_r1'/name;proof=json.loads(p.read_text());assert proof.get('passed',proof.get('diagnostic_dependencies_complete')) is True
  for f,h in proof['source_sha256'].items():assert sha(f)==h,f
  bound[str(p)]=sha(p)
 bound[str(S/'COLLECTOR_PREPARATION.json')]=sha(S/'COLLECTOR_PREPARATION.json')
 bound[str(Path(__file__))]=sha(Path(__file__))
 return used,bound
''')
a=s.index('def verify_settings(args):');b=s.index('\ndef verify_trial_provenance',a)
edit(s[a:b],'''def verify_settings(args):
 from joint_transport_reserve_stage_source_binding_v2 import verify_settings as verify_parent
 args=dict(args);assert type(args['front_corridor_lateral_replan']) is bool
 args.pop('front_corridor_lateral_replan')
 return verify_parent(args)
''')
anchor=" assert meta['front_corridor_midpoint_replan'] is True"
edit(anchor,anchor+"\n args=json.loads((ep.parent/'provenance.json').read_text())['args'];lateral=args['front_corridor_lateral_replan'];assert type(lateral) is bool\n if lateral:\n  assert meta['front_corridor_lateral_replan'] is True\n  assert type(meta['front_corridor_lateral_replanned_frames']) is int\n else:assert 'front_corridor_lateral_replan' not in meta and 'front_corridor_lateral_replanned_frames' not in meta")
edit("  assert meta['front_corridor_midpoint_replanned_frames']==0","  assert meta['front_corridor_midpoint_replanned_frames']==0\n  if lateral:assert meta['front_corridor_lateral_replanned_frames']==0")
edit("   assert plan['front_corridor_midpoint']['enabled'] is True","   assert plan['front_corridor_midpoint']['enabled'] is True\n   assert plan['front_corridor_midpoint']['phase']==('front_x_and_lateral_y' if lateral else 'front_x_only')")
anchor="  assert meta['front_corridor_midpoint_replanned_frames']==sum(r.get('front_corridor_midpoint',{}).get('changed',False) for r in rows)"
edit(anchor,anchor+"\n  if lateral:assert meta['front_corridor_lateral_replanned_frames']==sum(bool(r.get('front_corridor_midpoint',{}).get('changed')) and r['front_corridor_midpoint']['route_stage']=='lateral_y' for r in rows)")
restored=s
for e in reversed(changes):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==parent.read_text();ast.parse(s)
with dest.open('x') as f:f.write(s)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=entries,replacements=mapping,source_binding=dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest),edits=changes),expected_full_invocations=224,source_sha256={str(p):sha(p) for p in [Path(__file__),oldfile,D/'AUDITOR_PREPARATION.json',D/'PREPARATION_PROGRESS.json']},native_checks_pending=True,physical_started=False,training_ready=False)
with (D/'AUDIT_FAMILY_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print('Created',len(entries),'family adapters and one source binding; expected224 invocations unchanged')
