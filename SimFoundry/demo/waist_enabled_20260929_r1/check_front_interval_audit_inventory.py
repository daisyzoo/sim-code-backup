"""Validate distinct full audit inventory, reversible files and import graph.
No physical data or runtime success is claimed by source/inventory readiness.
"""
from pathlib import Path
import sys,json,hashlib,ast,datetime,importlib
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W.parents[1])]
import front_interval_stage_run_contract as new
import closed_peak_trial_run_contract as old
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=json.loads((W/'FRONT_INTERVAL_REMAINING_AUDITS_PREPARATION.json').read_text())
for item in prep['files']:
 src=W/item['parent'];dst=W/item['new'];assert sha(src)==item['parent_sha256'] and sha(dst)==item['new_sha256'];text=dst.read_text()
 for e in reversed(item['edits']):assert text.count(e['new'])==e['count'];text=text.replace(e['new'],e['old'])
 assert text==src.read_text()
def mapped(n):return n.replace('audit_closed_peak_trial_','audit_front_interval_stage_').replace('audit_front_diagonal_entry_live','audit_front_interval_diagonal_live')
assert set(new.REPORTS)=={mapped(n) for n in old.REPORTS};assert new.ADDITIONAL==[mapped(n) for n in old.ADDITIONAL]
for wait in [False,True]:assert new.primary(wait)==[mapped(n) for n in old.primary(wait)]
for config in [dict(),dict(initial_top_selected=True),dict(front_route_selected=True),dict(contact_center_calibration=dict(enabled=True))]:assert new.controls(config)==[mapped(n) for n in old.controls(config)]
modules={x[:-3] for x in new.REPORTS};results=[]
for n in sorted(modules):
 p=W/(n+'.py');assert p.exists();tree=ast.parse(p.read_text());constants={x.value for x in ast.walk(tree) if isinstance(x,ast.Constant) and isinstance(x.value,str)};report=new.REPORTS[n+'.py'][0];assert report in constants,(n,report)
 results.append(dict(auditor=n+'.py',sha256=sha(p),report=report))
 # Some preserved parent auditors intentionally execute their CLI at import.
 # Compile those, and import only adapters with no unguarded argv access.
 compile(tree,str(p),'exec')
 unguarded=[]
 for node in tree.body:
  if isinstance(node,(ast.FunctionDef,ast.ClassDef)):continue
  if isinstance(node,ast.If) and '__name__' in ast.unparse(node.test):continue
  unguarded.extend(x for x in ast.walk(node) if isinstance(x,ast.Attribute) and isinstance(x.value,ast.Name) and x.value.id=='sys' and x.attr=='argv')
 if n.startswith('audit_front_interval_') and not unguarded:importlib.import_module(n)
 results[-1]['import_checked']=bool(n.startswith('audit_front_interval_') and not unguarded)
# Source checks completed before this expected missing-flag rejection.
from front_interval_stage_source_binding import verify_trial_provenance
try:verify_trial_provenance(W/'joint_edge_intersection_physical_r1/case_840014')
except KeyError as e:assert e.args==('front_corridor_interval',)
else:raise AssertionError('wrong stage accepted')
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,distinct_audits=len(modules),files=results,wrong_stage_missing_flag_rejected=True,preparation_sha256=sha(W/'FRONT_INTERVAL_REMAINING_AUDITS_PREPARATION.json'),checker_sha256=sha(__file__),training_ready=False,physics_verified=False)
with (W/'FRONT_INTERVAL_AUDIT_INVENTORY_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print('PASS distinct audits',len(modules))
