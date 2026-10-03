"""Independent check of the actual changed proposal plus all observed fallback records."""
from pathlib import Path
import ast,copy,datetime,hashlib,json,sys
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W.parents[1])];D=W/'staged_front_corridor_midpoint'
from audit_front_corridor_midpoint_record import verify
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();d=json.loads((D/'DRAFT_CHECK.json').read_text())
for p,h in d['source_sha256'].items():assert sha(p)==h,p
# Run the bound real observation screen with the independent record verifier
# appended to each original helper call; never change the runtime helper.
p=W/'check_front_corridor_midpoint_draft.py';tree=ast.parse(p.read_text());cut=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='negatives' for t in n.targets));ns={'__file__':str(p),'__name__':'independent_midpoint_record_check'}
exec(compile(ast.Module(body=tree.body[:cut],type_ignores=[]),str(p),'exec'),ns)
original=ns['select'];results=[]
def checked(**args):
 value,r=original(**args);results.append(verify(record=r,**args));return value,r
# Reexecute only the real observation loops, preserving exact inputs/source.
loop=next(n for n in tree.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='run');ns['select']=checked;ns['counts']=[];exec(compile(ast.Module(body=[loop],type_ignores=[]),str(p),'exec'),ns)
args=ns['args'] # overwritten by final loop; use explicitly captured failing sample
sample=ns['sample'];args=sample[2];_,r=original(**args);assert r['changed'];assert verify(record=r,**args)['changed']
negatives=[]
for label,edit in [('goal',lambda x:x.__setitem__('goal_x',x['goal_x']+.001)),('margin',lambda x:x.__setitem__('original_table_margin_m',.004)),('segment_gap',lambda x:x['candidate_routes']['routes'][0]['segments'][0].__setitem__('minimum_axis_gap_m',.2)),('path_start',lambda x:x['candidate_routes']['routes'][0]['points'][0].__setitem__(0,0.0)),('eligibility',lambda x:x['candidate_routes']['routes'][0].__setitem__('eligible',False)),('changed',lambda x:x.__setitem__('changed',False))]:
 bad=copy.deepcopy(r);edit(bad)
 try:verify(record=bad,**args)
 except (AssertionError,ValueError):negatives.append(label)
 else:raise AssertionError('Accepted bad '+label)
for key,value in [('prior_stop_reason','already_stopped'),('hand_obstacle_gap_m',.004),('parent_guard_reason','non_target_motion_10mm')]:
 try:verify(record=r,**dict(args,**{key:value}))
 except (AssertionError,ValueError):negatives.append('context_'+key)
 else:raise AssertionError('Accepted changed context '+key)
assert len(results)==4796 and sum(x['changed'] for x in results)==1
sources=dict(d['source_sha256']);sources.update({str(p):sha(p) for p in [Path(__file__),W/'audit_front_corridor_midpoint_record.py',D/'DRAFT_CHECK.json']})
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,observed_records=len(results),changed_records=sum(r['changed'] for r in results),negative_cases_rejected=negatives,changed_proof=next(r for r in results if r['changed']),source_sha256=sources,episode_command_binding_complete=False,training_ready=False)
with (W/'staged_front_corridor_midpoint_integrated/INDEPENDENT_RECORD_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','scope']},indent=2))
