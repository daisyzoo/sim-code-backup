"""Prepare isolated front-interval source binding and full COP reconstruction.
Preserve existing auditor files and running experiment source freezes.
"""
from pathlib import Path
import json,hashlib,datetime,ast
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest=[]
def write(parent,dest,edits):
 src=(W/parent).read_text();text=src;records=[]
 for old,new in edits:
  assert old in text,(parent,old);count=text.count(old);text=text.replace(old,new);records.append(dict(old=old,new=new,count=count))
 restored=text
 for edit in reversed(records):assert restored.count(edit['new'])==edit['count'],(dest,edit['new'],restored.count(edit['new']),edit['count']);restored=restored.replace(edit['new'],edit['old'])
 assert restored==src;ast.parse(text)
 with (W/dest).open('x') as f:f.write(text)
 manifest.append(dict(parent=parent,parent_sha256=sha(W/parent),new=dest,new_sha256=sha(W/dest),edits=records,reverse_matches=True))
write('joint_edge_stage_source_binding.py','front_interval_stage_source_binding.py',[
 ('isolated edge/clearance diagnostic stage','isolated front corridor interval diagnostic stage'),
 ('edge_clearance_intersection','front_corridor_interval'),
 ('staged_joint_front_corridor_interval','staged_front_corridor_interval'),
 ("prep['reverse_reconstruction_matches']","prep['reverse_collector_matches']"),
 ("reversed(prep['edits'])","reversed(prep['collector_edits'])"),
 ("for name in ['joint_front_corridor_interval_candidate.py','joint_edge_clearance_adapter_candidate.py']", "for name in ['front_top_route_micro.py','front_cop_route_micro.py']"),
 (" assert recovered==(parent/'collect_paired_sorting.py').read_text()", """ assert recovered==(parent/'collect_paired_sorting.py').read_text()
 assert prep['joint_edge_repair_combined'] is False
 component_path=W/'FRONT_CORRIDOR_INTERVAL_CANDIDATE_PREPARATION.json';component=json.loads(component_path.read_text());assert sha(component_path)==prep['front_component_preparation_sha256'] and component['reverse_matches'] and component['default_off']
 assert sha(component['candidate'])==component['candidate_sha256']==sha(S/'front_top_route_micro.py')
 assert sha(component['parent'])==component['parent_sha256']==sha(parent/'front_top_route_micro.py')
 recovered_component=(S/'front_top_route_micro.py').read_text()
 for edit in reversed(component['edits']):assert recovered_component.count(edit['new'])==1;recovered_component=recovered_component.replace(edit['new'],edit['old'])
 assert recovered_component==(parent/'front_top_route_micro.py').read_text()"""),
])
write('audit_front_diagonal_entry_live.py','audit_front_interval_diagonal_live.py',[
 ('from scipy.optimize import linprog','from scipy.optimize import linprog\nfrom audit_front_interval_goal_records import verify_interval_rows'),
 ("def reconstruct(rows, plan, tr, ori, packets, key):\n", """def reconstruct(rows, plan, tr, ori, packets, key):
 interval_enabled=plan.get('front_corridor_interval',{}).get('enabled',False)
 interval=verify_interval_rows(rows,plan,tr,ori,key,enabled=interval_enabled)
"""),
 ("  if row['mode']!='front_guard_lift':", "  if interval_enabled:goal_x=interval['goals'][t]\n  if row['mode']!='front_guard_lift':"),
 (" p=Path(sys.argv[1]).resolve();log=", " from front_interval_stage_source_binding import verify_observation_binding\n p=Path(sys.argv[1]).resolve();binding=verify_observation_binding(p);log="),
 (" if enabled:\n  config=", " if enabled:\n  assert args['front_corridor_interval'] is True and log['plan']['front_corridor_interval']['enabled'] is True\n  config="),
 ("report=dict(passed=not errors,enabled=enabled", "report=dict(passed=not errors,source_binding=binding,interval_verifier_sha256=sha(Path(__file__).with_name('audit_front_interval_goal_records.py')),enabled=enabled"),
 ("FRONT_DIAGONAL_ENTRY_LIVE_AUDIT.json", "FRONT_INTERVAL_DIAGONAL_LIVE_AUDIT.json"),
])
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),audits=manifest,preparer_sha256=sha(__file__),scope=__doc__,all_applicable_audits_ready=False,simulation_started=False,training_ready=False)
with (W/'FRONT_INTERVAL_CORE_AUDIT_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print('prepared', [x['new'] for x in manifest])
