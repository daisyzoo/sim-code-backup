"""Inject isolated sources into this CPU-only test process, never running files."""
from pathlib import Path
import sys,types,json,hashlib,unittest
root=Path(__file__).resolve().parent;repo=root.parents[1];stage=root/'staged_initial_top_release'
sys.path[:0]=[str(root),str(repo/'tests'),str(repo)]
manifest=json.loads((stage/'MANIFEST.json').read_text())
for p,h in manifest['source_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
for name in ('confirmed_position_release','top_contact_bypass','initial_top_route_candidate','initial_top_route'):
 path=stage/(name+'.py');module_name='simfoundry.data.'+name
 module=types.ModuleType(module_name);module.__file__=str(repo/'simfoundry/data'/path.name)
 sys.modules[module_name]=module
 exec(compile(path.read_text(),str(path),'exec'),module.__dict__)
modules=json.loads((root/'FRONT_CLEARANCE_HYSTERESIS_TESTS.json').read_text())['modules']+['test_staged_position_release','test_initial_top_route_candidate','test_staged_initial_top']
suite=unittest.defaultTestLoader.loadTestsFromNames(modules);result=unittest.TextTestRunner(verbosity=1).run(suite)
for p,h in manifest['source_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
(stage/'TESTS.json').write_text(json.dumps(dict(tests_run=result.testsRun,passed=result.wasSuccessful(),modules=modules,production_frozen_sources_unchanged=True,candidate_sha256=manifest['candidate_sha256'],scope='Isolated module substitution for unit/regression checks only. No core integration, simulator dynamics, data approval or trained model.',training_ready=False),indent=2))
raise SystemExit(0 if result.wasSuccessful() else 1)
