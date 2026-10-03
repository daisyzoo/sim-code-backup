"""Check independent arithmetic auditor against known boundaries and tampering.
Logged stop inputs are arithmetic fixtures, not newly executed robot commands.
No old physics after a changed command is treated as a counterfactual rollout.
"""
from pathlib import Path
import ast,copy,datetime,hashlib,json,sys
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from front_loaded_projection_independent_math import verify
from front_loaded_material_projection import cap_loaded_reference
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();out=W/'FRONT_LOADED_PROJECTION_AUDIT_CHECK.json';assert not out.exists()
sources={};rows=[];negative=[]
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
prep=read(W/'FRONT_LOADED_PROJECTION_AUDIT_PREPARATION.json')
for p,h in prep['source_sha256'].items():assert sha(p)==h;sources[p]=h
for p in [Path(__file__),W/'front_loaded_material_projection.py',W/'FRONT_LOADED_PROJECTION_STAGE_CHECK.json']:sources[str(p)]=sha(p)
assert read(W/'FRONT_LOADED_PROJECTION_STAGE_CHECK.json')['passed']
# Keep runtime-controller imports out of the checker, including dynamic imports.
for name in ['front_loaded_projection_independent_math.py','audit_front_loaded_material_projection.py']:
 tree=ast.parse((W/name).read_text())
 for n in ast.walk(tree):
  if isinstance(n,ast.Import):assert all('front_loaded_material_projection' not in a.name and 'front_loaded_reference_adapter' not in a.name for a in n.names)
  if isinstance(n,ast.ImportFrom):assert n.module not in ['front_loaded_material_projection','front_loaded_reference_adapter','front_initial_loaded_reference_cap']
  if isinstance(n,ast.Call):assert not (isinstance(n.func,ast.Name) and n.func.id in ['eval','exec','__import__'])
for layout,task in [(840023,'nudge_mailer_to_bin'),(840020,'push_box_to_bin')]:
 ep=W/'front_loaded_physical_r1'/f'case_{layout}'/f'layout_{layout}_{task}'
 r=read(ep/'self_clearance.json')['failure']['record'];diag=read(ep/'LOADED_CAP_EMPTY_INTERSECTION_V2_DIAGNOSTIC.json')
 kw=dict(parent=r['parent_xy'],previous=r['previous_command_xy'],reference=r['reference_xy'],material=r['material_surface_xy'],normal=r['normal_load_n'])
 def production(k):return cap_loaded_reference(enabled=True,capture_complete=True,mode='top_push',parent_xy=k['parent'],previous_xy=k['previous'],reference_xy=k['reference'],surface_xy=k['material'],normal_load_n=k['normal'])
 a=production(kw);result=verify(a,**kw);assert result['feasible'] and result['boundary_following_repair'] and result['command_xy']==diag['unissued_geometric_alternative_xy'];rows.append(dict(episode=ep.name,case='real_logged_stop_arithmetic',passed=True))
 mutations={
 'wrong_strategy':lambda x:x.update(projection_strategy='old_segment'),
 'wrong_cap':lambda x:x.update(cap_xy_m=.02),
 'false_old_feasibility':lambda x:x.update(previous_added_segment_was_feasible=True),
 'hidden_boundary_repair':lambda x:x.update(boundary_following_repair=False),
 'unprojected_parent':lambda x:x.update(command_xy=list(kw['parent'])),
 'wrong_history':lambda x:x.update(previous_command_xy=[v+.001 for v in kw['previous']]),
 'wrong_bounds':lambda x:x.update(lower=[v-.001 for v in x['lower']]),
 'wrong_delta':lambda x:x.update(command_delta_xy=[0.,0.]),
 'wrong_changed':lambda x:x.update(changed=False),
 'false_stop':lambda x:x.update(requires_recontact=True),
 }
 for label,mutate in mutations.items():
  bad=copy.deepcopy(a);mutate(bad);rejected=False
  try:verify(bad,**kw)
  except (AssertionError,ValueError,KeyError):rejected=True
  assert rejected,(ep.name,label);negative.append(dict(episode=ep.name,case=label,rejected=True))
 empty=copy.deepcopy(kw);empty['material'][0]+=1.;ea=production(empty);assert not verify(ea,**empty)['feasible'];rows.append(dict(episode=ep.name,case='synthetic_genuine_empty',passed=True))
 # A feasible identity and capped case whose old segment also remains feasible.
 for label,k in [('identity',dict(parent=[.001,.002],previous=[0.,0.],reference=[0.,0.],material=[0.,0.],normal=1.)),('old_segment_feasible_cap',dict(parent=[.003,0.],previous=[0.,0.],reference=[0.,0.],material=[-.009,0.],normal=1.))]:
  ca=production(k);v=verify(ca,**k);assert v['feasible'] and not v['boundary_following_repair'];rows.append(dict(episode=ep.name,case=label,passed=True))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,rows=rows,negative=negative,source_sha256=sources,production_controller_imported_by_independent_auditor=False,physical_audit_executed=False,integrated_into_run_contract=False,training_ready=False)
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,positive=len(rows),tampering_rejected=len(negative),physical_audit_executed=False)))
