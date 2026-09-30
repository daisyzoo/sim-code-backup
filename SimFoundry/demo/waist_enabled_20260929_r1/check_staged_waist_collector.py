"""Execute staged CLI + actual layout-selection AST with mocked physics validator."""
from pathlib import Path
import json,sys,types,io,contextlib,hashlib,tempfile,ast
from unittest.mock import patch
from build_fresh_waist_pilot_contract import prelaunch_snapshot
root=Path(__file__).resolve().parent;repo=root.parents[1];stage=root/'staged_waist_collector';sys.path.insert(0,str(repo))
source=(stage/'collect_paired_sorting.py').read_text();prefix=source.split('app = AppLauncher(args, enable_cameras=True).app')[0]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();manifest=json.loads((stage/'MANIFEST.json').read_text());assert sha(stage/'collect_paired_sorting.py')==manifest['candidate_collector_sha256']
protocol_path=Path(manifest.get('source_protocol_path',root/'contact_stability_groups_r1/PROTOCOL.json'))
assert not manifest.get('source_protocol_sha256') or sha(protocol_path)==manifest['source_protocol_sha256']
base=json.loads(protocol_path.read_text())['settings']+['--out-dir','/tmp/waist_candidate_no_output','--layout-start','81000','--wait-layout-start','82000','--wait-episodes','1']
rows=[]
with tempfile.TemporaryDirectory() as temp:
 contract_path=Path(temp)/'waist.json';contract=dict(pilot_collector_sha256=sha(stage/'collect_paired_sorting.py'),layouts=[dict(layout_id=81000,box_xyz=[.4,.1,.7725],planned_split='train')],wait_layouts=[dict(layout_id=82000,box_xyz=[.5,-.1,.7725],planned_split='train')]);contract['prelaunch_collector_settings']=prelaunch_snapshot(stage/'collect_paired_sorting.py',json.loads(protocol_path.read_text())['settings'],contract['layouts'],contract['wait_layouts'])[0];contract_path.write_text(json.dumps(contract));digest=sha(contract_path)
 pilot=list(base);pilot[pilot.index('--role')+1]='pilot';pilot+=['--waist-pilot-contract',str(contract_path)]
 def setarg(argv,key,value):
  a=list(argv);a[a.index(key)+1]=str(value);return a
 trials=[('diagnostic_default',base,True,None),('pilot_without_contract',pilot[:-2],False,None),('bound_pilot_fixture',pilot,True,None),('collector_changed',pilot,False,'source'),('unknown_schedule',setarg(pilot,'--layout-start',99999),False,None),('altered_physics',setarg(pilot,'--environment-seed',1),False,'physics'),('diagnostic_with_contract',base+['--waist-pilot-contract',str(contract_path)],False,None),('alternate_layout_source',pilot+['--diagnostic-layout-json','/tmp/unregistered'],False,None)]
 for label,argv,expected,failure in trials:
  def validate(path,*,settings=None):
   if failure=='physics':raise ValueError('Fixture physical settings differ')
   return (dict(contract,pilot_collector_sha256='0'*64) if failure=='source' else contract),digest
  sys.argv=['staged_collector',*argv];err=io.StringIO();accepted=True;scope={'__file__':str(stage/'collect_paired_sorting.py'),'__name__':'staged_cli'}
  # dataclass needs the module registered just as in normal Python imports.
  module=types.ModuleType('staged_cli');sys.modules['staged_cli']=module;module.__dict__.update(scope);scope=module.__dict__
  try:
   with patch('simfoundry.data.waist_pilot_protocol.validate_waist_contract',side_effect=validate) as mock,contextlib.redirect_stderr(err):exec(compile(prefix,'staged_collector_prefix','exec'),scope)
  except SystemExit as exc:assert exc.code==2;accepted=False
  assert accepted==expected,(label,err.getvalue());rows.append(dict(case=label,accepted=accepted))
  if label=='diagnostic_default':assert scope['waist_admission'] is None and scope['args'].role=='diagnostic'
  if label=='bound_pilot_fixture':
   assert scope['args'].role=='pilot';assert scope['waist_contract_hash']==digest
   tree=ast.parse(source);assignments=[n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='layout' for t in n.targets) and 'waist_admission.layout' in ast.unparse(n.value)];assert len(assignments)==2
   for assignment in assignments:
    wait='wait=True' in ast.unparse(assignment.value);scope['i']=0 if wait else 81000
    value=eval(compile(ast.Expression(assignment.value),'actual_layout_selection','eval'),scope)
    assert value['layout_id']==(82000 if wait else 81000);value['box_xyz'][0]=999
   assert scope['waist_admission'].layout(81000)['box_xyz'][0]==.4
   copies=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='waist_admission is not None' and any(isinstance(v,ast.Name) and v.id=='contract_bytes' for v in ast.walk(n))]
   assert len(copies)==1;scope['root']=Path(temp)/'output';scope['root'].mkdir()
   copy_code=compile(ast.Module(body=copies,type_ignores=[]),'actual_contract_snapshot','exec');exec(copy_code,scope)
   assert (scope['root']/'waist_pilot_contract.json').read_bytes()==contract_path.read_bytes()
   saved=contract_path.read_bytes();contract_path.write_text('{}')
   try:exec(copy_code,scope)
   except ValueError as exc:assert 'changed before output snapshot' in str(exc)
   else:raise AssertionError('Changed snapshot accepted')
   contract_path.write_bytes(saved)
   bindings=[v for n in ast.walk(tree) if isinstance(n,ast.Dict) for k,v in zip(n.keys,n.values) if isinstance(k,ast.Constant) and k.value=='waist_pilot_contract_sha256']
   assert len(bindings)==1 and eval(compile(ast.Expression(bindings[0]),'actual_raw_meta_binding','eval'),scope)==digest
for p,h in manifest['live_source_sha256'].items():assert sha(p)==h,p
(stage/'CLI_AND_LAYOUT_TESTS.json').write_text(json.dumps(dict(cases=rows,actual_layout_ast_branches=2,actual_contract_snapshot_and_tamper_check=True,actual_raw_meta_hash_binding=True,candidate_collector_sha256=manifest['candidate_collector_sha256'],live_frozen_sources_unchanged=True,scope='Actual parser/validation/layout expressions, mocked full physical-evidence validator. Tests plumbing only. Full validator separately implemented/tested; no real approved contract, pilot data, dynamics or training admission.',training_ready=False),indent=2));print(json.dumps(rows,indent=2))
