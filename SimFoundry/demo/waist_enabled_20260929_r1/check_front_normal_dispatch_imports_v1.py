from pathlib import Path
import ast,datetime,hashlib,json,subprocess,sys,os
w=Path('/home/user/Documents/zoo/sim/SimFoundry/demo/waist_enabled_20260929_r1');d=w/'front_normal_dispatch_imports_r1';d.mkdir(exist_ok=False)
r=json.loads((w/'front_normal_audit_dispatch_r1/RESULT.json').read_text()); paths=[Path(x['destination']) for x in r['created']]+[w/'run_front_normal_trial1_physical_v1.py',w/'watch_front_normal_trial1_numeric_reviews_v1.py',w/'review_front_normal_trial1_episode_v1.py',w/'review_front_normal_trial1_incomplete_episode_v1.py']
rows=[]
for p in paths:
 tree=ast.parse(p.read_text());compile(tree,str(p),'exec')
 top=ast.Module(body=[n for n in tree.body if not isinstance(n,(ast.FunctionDef,ast.ClassDef)) and not (isinstance(n,ast.If) and '__name__' in ast.unparse(n.test))],type_ignores=[])
 if any(isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id=='sys' and n.attr=='argv' for n in ast.walk(top)):
  rows.append(dict(path=str(p),compiled=True,import_skipped='CLI executes at import; no dataset supplied'));continue
 print('IMPORT',p.name,flush=True)
 c=subprocess.run([sys.executable,'-c','import sys,importlib;sys.path.insert(0,sys.argv[1]);importlib.import_module(sys.argv[2])',str(w),p.stem],capture_output=True,text=True,timeout=60)
 (d/(p.stem+'.log')).write_text(c.stdout+'\n'+c.stderr);rows.append(dict(path=str(p),compiled=True,import_returncode=c.returncode))
 if c.returncode:print('FAIL',p.name,c.stderr[-1500:],flush=True)
passed=all(x.get('import_returncode',0)==0 for x in rows)
out=dict(passed=passed,scope='Compile all newly dispatched modules and import guarded modules without simulation or fabricated physics. CLI-only modules require actual physical episode audit.',rows=rows,physical_launch_ready=False,training_ready=False,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
(d/'RESULT.json').write_text(json.dumps(out,indent=2));print('PASSED',passed,flush=True)
