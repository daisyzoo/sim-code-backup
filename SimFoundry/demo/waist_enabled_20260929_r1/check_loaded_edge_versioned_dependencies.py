"""Explicit dependency renames preserve original region/reference/normal math.
AST equality after reversing declared symbols, names and report strings; not new
physical audit evidence. New pose source contract separately validated.
"""
from pathlib import Path
import ast,json,hashlib,datetime
w=Path(__file__).resolve().parent;version=w/'LOADED_EDGE_AUDIT_VERSION_MAP.json';v=json.loads(version.read_text());sources={str(version):hashlib.sha256(version.read_bytes()).hexdigest()};rows=[]
for old,new in v['modules'].items():
 if old=='audit_recontact_pose_live':continue
 original=w/(old+'.py');candidate=w/(new+'.py');text=candidate.read_text()
 for a,b in v['modules'].items():text=text.replace(b,a)
 for a,b in v['reports'].items():text=text.replace(b,a)
 assert ast.dump(ast.parse(original.read_text()),include_attributes=False)==ast.dump(ast.parse(text),include_attributes=False),new
 tree=ast.parse(candidate.read_text());imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
 for name in imports:
  assert name not in v['modules'],('unversioned dependency',new,name)
 for n in ast.walk(tree):
  if isinstance(n,ast.Constant) and isinstance(n.value,str):assert n.value not in {x+'.py' for x in v['modules']},('old subprocess',new,n.value)
 for p in [original,candidate]:sources[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 rows.append(dict(module=new,original_math_ast_exact=True))
sources[str(Path(__file__))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=rows,source_sha256=sources,physical_validation=False,training_ready=False)
(w/'staged_loaded_edge_coverage/DEPENDENCY_VERSION_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS explicit unchanged-math modules',len(rows))
