"""Preserve full original224-audit family with explicit trailing-box recovery.
Original task gates, full horizons, source binding, pressure, non-target and
final command checks remain. Creating adapters does not certify readiness.
"""
from pathlib import Path
import json,hashlib,datetime,ast,re
W=Path(__file__).resolve().parent;D=W/'front_box_trailing_preparation_r1';S=W/'staged_front_box_trailing_v1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for name in ['COLLECTOR_WIRING_CHECK.json','INDEPENDENT_EVENT_CHECK.json','SELECTION_AUDIT_CHECK.json','NATIVE_CAPTURE_CHECK.json']:
 proof=json.loads((D/name).read_text());assert proof['passed']
 for p,h in proof['source_sha256'].items():assert sha(p)==h,p
# Publish separately named auditor helpers; original checked helpers remain frozen.
helpers=[]
for old,new in [('audit_trailing_events','audit_front_box_trailing_events_v1'),('audit_trailing_preflight','audit_front_box_trailing_preflight_v1'),('audit_trailing_planning','audit_front_box_trailing_planning_v1')]:
 source=D/(old+'.py');dest=W/(new+'.py');text=source.read_text();edits=[]
 if old=='audit_trailing_planning':
  a='from audit_trailing_preflight import';b='from audit_front_box_trailing_preflight_v1 import';assert text.count(a)==1;text=text.replace(a,b);edits.append(dict(old=a,new=b))
 with dest.open('x') as f:f.write(text)
 helpers.append(dict(parent=str(source),parent_sha256=sha(source),path=str(dest),sha256=sha(dest),edits=edits))
oldfile=W/'joint_transport_reserve_preparation_r1/AUDIT_FAMILY_V2_PREPARATION.json';old=json.loads(oldfile.read_text());parents=old['adapters']+old['shared_unchanged_adapters'];mapping={Path(x['path']).stem:Path(x['path']).stem.replace('joint_transport_reserve_r2_','front_box_trailing_r1_').replace('joint_transport_reserve_','front_box_trailing_') for x in parents};mapping.update(joint_transport_reserve_stage_source_binding_v2='front_box_trailing_stage_source_binding_v1',staged_joint_transport_reserve_v1='staged_front_box_trailing_v1',JOINT_TRANSPORT_RESERVE_R2_='FRONT_BOX_TRAILING_R1_',JOINT_TRANSPORT_RESERVE_STREAM_V2_AUDIT='FRONT_BOX_TRAILING_STREAM_V2_AUDIT')
pat=re.compile('|'.join(map(re.escape,sorted(mapping,key=len,reverse=True))));inverse={v:k for k,v in mapping.items()};rev=re.compile('|'.join(map(re.escape,sorted(inverse,key=len,reverse=True))));entries=[]
for record in parents:
 parent=Path(record['path']);assert sha(parent)==record['sha256'];dest=W/(mapping[parent.stem]+'.py');text=pat.sub(lambda m:mapping[m.group()],parent.read_text());edits=[]
 def change(a,b):
  global text
  assert text.count(a)==1,(dest.name,a,text.count(a));text=text.replace(a,b);edits.append(dict(old=a,new=b))
 if parent.name=='audit_joint_transport_reserve_front_recovery_stream_v2.py':
  change('from audit_front_initial_center_planning_v2 import SelectionAudit','from audit_front_initial_center_planning_v2 import SelectionAudit\nfrom audit_front_box_trailing_planning_v1 import SelectionAudit as TrailingSelectionAudit\nfrom audit_front_box_trailing_events_v1 import RecoveryEventAudit as TrailingEventAudit')
  change('def __init__(self,repo,stage,side="left"):', 'def __init__(self,repo,stage,side="left",*,trailing_landing=False):')
  change('  assert side in ("left","right");self.side=side;self.inactive="right" if side=="left" else "left"','  assert type(trailing_landing) is bool\n  self.trailing_landing=trailing_landing\n  assert side in ("left","right");self.side=side;self.inactive="right" if side=="left" else "left"')
  change('self.selection=SelectionAudit(repo,stage);','self.selection=(TrailingSelectionAudit if trailing_landing and side=="right" else SelectionAudit)(repo,stage);')
  change("if self.side=='right':assert event.get('front_box_recenter_version')=='front_box_recenter_v1'", "if self.side=='right':assert event.get('front_box_recenter_version')==('front_box_trailing_20mm_reserve_05mm_v1' if self.trailing_landing else 'front_box_recenter_v1')")
  change('(BoxRecoveryEventAudit if self.side=="right" else RecoveryEventAudit)(self.repo,self.stage)','((TrailingEventAudit if self.trailing_landing else BoxRecoveryEventAudit) if self.side=="right" else RecoveryEventAudit)(self.repo,self.stage)')
  change("task=str(z['task_id'])","task=str(z['task_id']);meta=json.loads(str(z['collect_meta']))")
  change("checker=RecoveryStreamAudit(ROOT,S,side);filtered=0.","trailing=meta.get('front_box_trailing_landing',False);assert type(trailing) is bool\n checker=RecoveryStreamAudit(ROOT,S,side,trailing_landing=trailing);filtered=0.")
  a="W/'audit_front_initial_center_planning_v2.py',W/'audit_front_initial_center_preflight.py'"
  change(a,a+",W/'audit_front_box_trailing_events_v1.py',W/'audit_front_box_trailing_planning_v1.py',W/'audit_front_box_trailing_preflight_v1.py'")
 restored=text
 for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert rev.sub(lambda m:inverse[m.group()],restored)==parent.read_text();ast.parse(text)
 with dest.open('x') as f:f.write(text)
 entries.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest),edits=edits))
parent=W/'joint_transport_reserve_stage_source_binding_v2.py';dest=W/'front_box_trailing_stage_source_binding_v1.py';text=parent.read_text();changes=[]
def edit(a,b):
 global text
 assert text.count(a)==1,(a[:100],text.count(a));text=text.replace(a,b);changes.append(dict(old=a,new=b))
edit("S=W/'staged_joint_transport_reserve_v1'","S=W/'staged_front_box_trailing_v1'")
a=text.index('def verify_preparation():');b=text.index('\ndef verify_settings',a)
edit(text[a:b],'''TRAILING_HELPERS=['trailing_plan.py','trailing_static.py','trailing_selection.py','trailing_lifecycle.py','trailing_adapter.py','trailing_runtime.py']

def verify_preparation():
 from joint_transport_reserve_stage_source_binding_v2 import verify_preparation as verify_original
 parent_used,bound=verify_original()
 prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());parent=Path(prep['parent']);assert parent==W/'staged_joint_transport_reserve_v1'
 original=json.loads((parent/'COLLECTOR_PREPARATION.json').read_text())['stage_sha256']
 for name,h in original.items():assert sha(parent/name)==h,name
 for name,h in prep['stage_sha256'].items():assert sha(S/name)==h,name
 assert set(prep['changed_files'])=={'collect_paired_sorting.py'}
 for name,edits in prep['changed_files'].items():
  restored=(S/name).read_text()
  for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
  assert restored==(parent/name).read_text()
 for name,h in original.items():
  if name not in prep['changed_files']:assert sha(S/name)==h
 assert set(prep['stage_sha256'])==set(original)|set(TRAILING_HELPERS)
 for name,h in prep['added_runtime_files'].items():assert sha(S/name)==h==sha(Path(prep['runtime_source'])/name)
 used={name:sha(S/name) for name in [*parent_used,*TRAILING_HELPERS]};assert len(used)==98
 for name in ['COLLECTOR_WIRING_CHECK.json','INDEPENDENT_EVENT_CHECK.json','SELECTION_AUDIT_CHECK.json','NATIVE_CAPTURE_CHECK.json']:
  p=W/'front_box_trailing_preparation_r1'/name;proof=json.loads(p.read_text());assert proof['passed']
  for f,h in proof['source_sha256'].items():assert sha(f)==h,f
  bound[str(p)]=sha(p)
 for p in [S/'COLLECTOR_PREPARATION.json',Path(__file__),W/'audit_front_box_trailing_events_v1.py',W/'audit_front_box_trailing_planning_v1.py',W/'audit_front_box_trailing_preflight_v1.py']:bound[str(p)]=sha(p)
 return used,bound
''')
a=text.index('def verify_settings(args):');b=text.index('\ndef verify_trial_provenance',a)
edit(text[a:b],'''def verify_settings(args):
 from joint_transport_reserve_stage_source_binding_v2 import verify_settings as verify_parent
 args=dict(args);assert type(args['front_box_trailing_landing']) is bool
 args.pop('front_box_trailing_landing')
 return verify_parent(args)
''')
edit(' verify_settings(args)\n prefix='," verify_settings(args)\n if not args['front_box_trailing_landing']:expected={k:v for k,v in expected.items() if k not in TRAILING_HELPERS}\n prefix=")
a=" spec=json.loads((W/'staged_front_box_recenter_v3/COLLECTOR_PREPARATION.json').read_text())['box_recenter'];assert meta['front_box_recenter']==spec"
b=" spec=json.loads((W/'staged_front_box_recenter_v3/COLLECTOR_PREPARATION.json').read_text())['box_recenter']\n args=json.loads((ep.parent/'provenance.json').read_text())['args'];trailing=args['front_box_trailing_landing'];assert type(trailing) is bool\n if trailing:\n  assert meta['front_box_trailing_landing'] is True\n  spec.pop('center_xy_m');spec.update(version='front_box_trailing_20mm_reserve_05mm_v1',landing_world_offset_m=[0.,.020,0.],landing_xy_tolerance_m=.002,planning_xy_reserve_m=.0005,current_rotation_for_measured_landing=True)\n else:assert 'front_box_trailing_landing' not in meta\n assert meta['front_box_recenter']==spec"
edit(a,b)
edit("assert all(r.get('front_box_recenter_version')=='front_box_recenter_v1' for r in data['rows'])","assert all(r.get('front_box_recenter_version')==spec['version'] for r in data['rows'])")
restored=text
for e in reversed(changes):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==parent.read_text();ast.parse(text)
with dest.open('x') as f:f.write(text)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=entries,helpers=helpers,replacements=mapping,source_binding=dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest),edits=changes),expected_full_invocations=224,source_sha256={str(p):sha(p) for p in [Path(__file__),oldfile,D/'SELECTION_AUDITOR_PREPARATION.json',D/'EVENT_AUDITOR_PREPARATION.json']},native_checks_pending=True,physical_started=False,training_ready=False)
with (D/'AUDIT_FAMILY_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print('Created',len(entries),'family adapters,3 helper auditors,1source binding;224 original invocations retained')
