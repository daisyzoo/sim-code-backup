"""Execute actual new geometry/legacy-audit command-chain AST on native fixtures.
This checks order and rejection semantics only; full original math equivalence
and independent new final command math have separate reports. No new physics.
"""
from pathlib import Path
import sys,ast,json,hashlib,datetime,copy
import numpy as np
w=Path(__file__).resolve().parent;sys.path.insert(0,str(w))
from audit_loaded_edge_self_clearance import near
stage=w/'staged_loaded_edge_coverage';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();fixture=stage/'NATIVE_FILES_CHECK.json';d=json.loads(fixture.read_text());assert d['passed']
for p,h in d['source_sha256'].items():assert sha(p)==h
geo=w/'audit_loaded_edge_self_clearance.py';legacy=w/'audit_loaded_edge_loaded_execution.py'
a=ast.parse(geo.read_text());b=ast.parse(legacy.read_text())
geoloop=next(n for n in ast.walk(a) if isinstance(n,ast.For) and ast.unparse(n.target)=='c' and ast.unparse(n.iter)=='coordinates')
ix=next(i for i,n in enumerate(geoloop.body) if isinstance(n,ast.If) and ast.unparse(n.test)=="'loaded_edge_coverage' in c")
gcode=compile(ast.fix_missing_locations(ast.Module(body=geoloop.body[ix:ix+3],type_ignores=[])),'<actual final chain>','exec')
lloop=next(n for n in ast.walk(b) if isinstance(n,ast.For) and ast.unparse(n.target)=='f' and ast.unparse(n.iter)=="fr['rows']")
ix=next(i for i,n in enumerate(lloop.body) if isinstance(n,ast.Assign) and ast.unparse(n)=='legacy_actual = u[t]')
lcode=compile(ast.fix_missing_locations(ast.Module(body=lloop.body[ix:ix+3],type_ignores=[])),'<actual legacy binding>','exec')
counts=dict(frames=0,overrides=0);negative=[];sources=dict(d['source_sha256'])
for item in d['records']:
 if item['decisions']==0:continue
 ep=Path(item['fixture']);coords=json.loads((ep/'coordination.json').read_text());edges={r['step']:r for r in json.loads((ep/'loaded_edge_coverage.json').read_text())['rows']}
 with np.load(ep/'raw.npz') as z:u=z['action'][:,12:23].copy()
 for c in coords:
  t=c['step'];tr=c['loaded_edge_coverage'];old=c['joint_edge_refinement'];target=np.array(old['final_upper_command'],dtype=np.float32)
  ns=dict(np=np,near=near,c=c,t=t,u=u,target=target.copy(),verified_edges=edges,controller_frames=0);exec(gcode,ns);assert ns['controller_frames']==1 and np.array_equal(ns['target'],u[t])
  ns=dict(np=np,near=near,c=c,t=t,u=u,trace=old,verified_edges=edges,selected=True,eligible=old['input_selected']);exec(lcode,ns);assert np.array_equal(ns['legacy_actual'],target)
  counts['frames']+=1;counts['overrides']+=int(tr['override'])
  if tr['override'] and not negative:
   cases=[]
   for label,mutate in [('missing_verified',lambda ns:ns.__setitem__('verified_edges',{})),('false_acceptance',lambda ns:ns['c']['loaded_edge_coverage'].__setitem__('accepted',False)),('wrong_final',lambda ns:ns['c']['loaded_edge_coverage']['final_upper_command'].__setitem__(0,.2)),('wrong_parent',lambda ns:ns['c']['loaded_edge_coverage']['parent_upper_command'].__setitem__(0,.2))]:
    for kind,code in [('geometry',gcode),('legacy',lcode)]:
     ns=dict(np=np,near=near,c=copy.deepcopy(c),t=t,u=u.copy(),target=target.copy(),trace=copy.deepcopy(old),verified_edges=copy.deepcopy(edges),controller_frames=0,selected=True,eligible=old['input_selected']);mutate(ns)
     # Match independent evidence too: chain must still bind parent/final raw action.
     if label in ['wrong_final','wrong_parent','false_acceptance']:ns['verified_edges'][t]=copy.deepcopy(ns['c']['loaded_edge_coverage'])
     try:exec(code,ns)
     except AssertionError:negative.append(kind+':'+label)
     else:raise AssertionError('accepted '+kind+':'+label)
 for name in ['raw.npz','coordination.json','loaded_edge_coverage.json']:sources[str(ep/name)]=sha(ep/name)
assert counts==dict(frames=2398,overrides=58) and len(negative)==8
for p in [Path(__file__),geo,legacy,fixture]:sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,counts=counts,negative_checks=negative,source_sha256=sources,physical_validation=False,training_ready=False)
(stage/'COMMAND_CHAIN_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',counts,negative,flush=True)
