"""Version original full audit graph for the isolated material projection.
No gate/formula changes except explicitly reviewed nearest-parent cap arithmetic
and stronger source/metadata binding. No physical readiness or data admission.
"""
from pathlib import Path
import ast,datetime,hashlib,json
W=Path(__file__).resolve().parent;S=W/'staged_front_loaded_projection';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();records=[]
replacements=[('audit_front_loaded_initial_live','audit_front_projection_initial_live'),('front_loaded_stage','front_projection_stage'),('FRONT_LOADED_STAGE','FRONT_PROJECTION_STAGE'),('staged_front_loaded_reference','staged_front_loaded_projection')]
def rename(s):
 for a,b in replacements:s=s.replace(a,b)
 return s
def write(parent,name,s,edits=None):
 dest=W/name;assert not dest.exists();ast.parse(s);dest.write_text(s);records.append(dict(parent=str(parent),parent_sha256=sha(parent),path=str(dest),sha256=sha(dest),global_replacements=replacements,edits=edits or []))
for p in sorted(W.glob('audit_front_loaded_stage_*.py')):
 s=rename(p.read_text());edits=[]
 if p.name=='audit_front_loaded_stage_cop.py':
  a='audit_front_loaded_material_cap';b='audit_front_loaded_material_projection';assert s.count(a)==2;s=s.replace(a,b);edits.append(dict(old=a,new=b,count=2))
  a="'front_initial_center_reference_ledger.py'";b="'front_loaded_projection_independent_math.py',"+a;assert s.count(a)==1;s=s.replace(a,b);edits.append(dict(old=a,new=b,count=1))
 write(p,rename(p.name),s,edits)
for name in ['front_loaded_stage_audit_context.py','audit_front_loaded_initial_live.py','front_loaded_stage_run_contract.py']:
 p=W/name;write(p,rename(name),rename(p.read_text()))
p=W/'front_loaded_stage_source_binding.py';s=rename(p.read_text());edits=[]
def edit(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b);edits.append(dict(old=a,new=b,count=1))
start=s.index(' recovered=');end=s.index('\n prov=',start);old=s[start:end]
new=''' for name,h in prep['parent_stage_sha256'].items():
  assert sha(parent/name)==h
  recovered=(S/name).read_text()
  for edit in reversed(prep['edits']):
   if edit['file']==name:
    assert recovered.count(edit['new'])==1
    recovered=recovered.replace(edit['new'],edit['old'])
  assert recovered==(parent/name).read_text()
 assert json.loads((parent/'CHECK.json').read_text())['stage_sha256']==parent_prep['stage_sha256']
 for original,h in prep['new_helper_source_sha256'].items():
  assert sha(original)==h and sha(S/Path(original).name)==h
 for check_name in ['FRONT_LOADED_PROJECTION_STAGE_CHECK.json','FRONT_LOADED_PROJECTION_AUDIT_CHECK.json']:
  checked=json.loads((W/check_name).read_text());assert checked['passed'] is True
  for original,h in checked['source_sha256'].items():assert sha(original)==h
 helpers={Path(name).name for name in parent_prep['helper_source_sha256']}|{'front_loaded_material_projection.py'}
''';edit(old,new)
a="assert args['front_loaded_reference_cap'] is True;settings=semantic_settings(args);"
b="assert args['front_loaded_material_projection'] is True;assert args['front_loaded_reference_cap'] is True;settings=semantic_settings(args);assert settings.pop('front_loaded_material_projection') is True;";edit(a,b)
a=" inherited_helpers={Path(name).name for name in parent_prep['helper_source_sha256']}"
b=" grandparent_prep=json.loads((Path(parent_prep['parent_stage'])/'PREPARATION.json').read_text())\n inherited_helpers={Path(name).name for name in grandparent_prep['helper_source_sha256']}";edit(a,b)
a=" assert meta['front_loaded_reference_cap'] is True";edit(a," assert meta['front_loaded_material_projection'] is True and meta['front_loaded_projection_strategy']=='nearest_parent_in_slew_hand_material_intersection'\n"+a)
a="  assert plan['front_loaded_reference_cap']==meta['frontal_bypass_plan']['front_loaded_reference_cap']==cap_expected";edit(a,"  cap_expected.update(projection_strategy='nearest_parent_in_slew_hand_material_intersection',stop_observation_archive=True)\n"+a)
write(p,'front_projection_stage_source_binding.py',s,edits)
# CHECK is an interface/mathematical manifest; it does not claim full native or physical execution.
prep=json.loads((S/'PREPARATION.json').read_text());checks=['FRONT_LOADED_MATERIAL_PROJECTION_CHECK.json','FRONT_LOADED_PROJECTION_STAGE_CHECK.json','FRONT_LOADED_PROJECTION_AUDIT_CHECK.json']
for name in checks:
 check=json.loads((W/name).read_text());assert check['passed']
 for path,h in check['source_sha256'].items():assert sha(path)==h
with (S/'CHECK.json').open('x') as f:json.dump(dict(passed=True,scope='Only named completed mathematical/interface checks; no native-source fixture or physical success claim.',stage_sha256=prep['stage_sha256'],source_sha256={str(W/n):sha(W/n) for n in checks},simulation_started=False,training_ready=False),f,indent=2)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=records,generator_sha256=sha(__file__),syntax_passed=True,native_source_fixture_tested=False,transitive_dependencies_tested=False,simulation_started=False,training_ready=False)
with (W/'FRONT_PROJECTION_STAGE_AUDITS_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print('Prepared',len(records),'audit/contract modules; no simulation launch')
