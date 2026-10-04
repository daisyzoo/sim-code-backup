"""Execute native parser, source list, lifecycle construction and metadata; no simulator."""
from pathlib import Path
import sys,json,hashlib,datetime,ast,types,contextlib,io
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_rear_trailing_contact_v1';B=W/'staged_joint_transport_bounded_v1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());sources={str(S/'COLLECTOR_PREPARATION.json'):sha(S/'COLLECTOR_PREPARATION.json')}
for p,h in prep['source_sha256'].items():assert sha(p)==h,p;sources[p]=h
for n,h in prep['stage_sha256'].items():assert sha(S/n)==h,n;sources[str(S/n)]=h
p=W/'joint_transport_physical_r1/PROTOCOL.json';protocol=json.loads(p.read_text());sources[str(p)]=sha(p)
source=(S/'collect_paired_sorting.py').read_text();tree=ast.parse(source);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');collect=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='collect')
start=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='paths');end=next(i for i,n in enumerate(main.body) if isinstance(n,ast.For) and ast.unparse(n.target)=='path' and ast.unparse(n.iter)=='paths')
archive=compile(ast.Module(body=main.body[start:end],type_ignores=[]),str(S/'collect_paired_sorting.py'),'exec')
init=next(n for n in collect.body if isinstance(n,ast.If) and ast.unparse(n.test)=='args.unloaded_recontact_pose')
metadata=next(n for n in collect.body if isinstance(n,ast.If) and ast.unparse(n.test)=='args.rear_box_trailing_preference')
def execute(node,ns):exec(compile(ast.Module(body=[node],type_ignores=[]),str(S/'collect_paired_sorting.py'),'exec'),ns);return ns
rows=[];negative=[];enabled_args=None
unused={'inactive_transport_clearance.py','transport_constraint_certificate.py','transport_path_certificate.py','inactive_transport_runtime.py'}
expected=set(prep['stage_sha256'])-unused
for command in protocol['plan']['commands']:
 cli=command['args'];before,_=parser_namespace(B/'collect_paired_sorting.py',cli,full=True);off,_=parser_namespace(S/'collect_paired_sorting.py',cli,full=True);on,_=parser_namespace(S/'collect_paired_sorting.py',cli+['--rear-box-trailing-preference'],full=True)
 assert off['rear_box_trailing_preference'] is False and on['rear_box_trailing_preference'] is True
 assert {k:v for k,v in off.items() if k!='rear_box_trailing_preference'}==before=={k:v for k,v in on.items() if k!='rear_box_trailing_preference'}
 enabled_args=on
 for flag,a in [(False,off),(True,on)]:
  ns=dict(args=types.SimpleNamespace(**a),ROOT=ROOT,STAGE=S,Path=Path,__file__=str(S/'collect_paired_sorting.py'),waist_admission=None,json=json);exec(archive,ns);paths=set(ns['paths']);stage_paths={p.name for p in paths if p.parent==S};assert stage_paths==expected-(set(prep['added_files']) if not flag else set())
  for p in paths:assert p.is_file(),p;sources[str(p)]=sha(p)
  ep=types.SimpleNamespace(collect_meta={});execute(metadata,dict(args=ns['args'],episode=ep))
  assert ('rear_box_trailing_preference' in ep.collect_meta)==flag
  for side in ['left','right']:
   runtime=execute(init,dict(args=ns['args'],side=side))['recontact_lifecycle']
   if side=='right':assert runtime.original.box_center_preference and runtime.entry_lift;assert getattr(runtime.original,'box_trailing_preference',False)==flag
   else:assert runtime.box_center_preference is False and not hasattr(runtime,'box_trailing_preference')
 rows.append(dict(layout_id=command['layout_id'],original_arguments_exact=True,off_active_sources=len(expected)-5,on_active_sources=len(expected),bilateral_constructor_checked=True,metadata_checked=True))
base=protocol['plan']['commands'][0]['args']+['--rear-box-trailing-preference']
variants=[(label,[x for x in base if x!=flag]) for label,flag in [('no_entry_lift','--rear-box-entry-lift'),('no_center','--rear-box-center-preference'),('no_minimum_motion','--minimum-motion-recontact'),('no_interior','--recontact-interior-preference'),('no_unloaded','--unloaded-recontact-pose')]]
for label,change in [('pilot',['--role','pilot']),('policy',['--policy-port','8000']),('idle',['--idle']),('probe',['--waist-probe'])]:variants.append((label,base+change))
for label,cli in variants:
 with contextlib.redirect_stderr(io.StringIO()):
  try:parser_namespace(S/'collect_paired_sorting.py',cli,full=True)
  except (SystemExit,ValueError) as e:
   if isinstance(e,SystemExit):assert e.code!=0
   negative.append(dict(case=label,rejected=True))
  else:raise AssertionError('Invalid config accepted '+label)
# Roll back only the five recorded insertions: entire original collector must match.
reverse=source
for e in reversed(prep['collector_edits']):assert reverse.count(e['new'])==1;reverse=reverse.replace(e['new'],e['old'])
assert reverse==(B/'collect_paired_sorting.py').read_text()
for p in [Path(__file__),W/'prepare_closed_peak_trial.py',B/'collect_paired_sorting.py']:sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,commands=rows,negative=negative,active_stage_sources=len(expected),reversible_edits=5,source_sha256=sources,physical_launch_ready=False,training_ready=False)
with (D/'PARSER_SOURCE_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,commands=len(rows),negative=len(negative),active_stage_sources=len(expected))))
