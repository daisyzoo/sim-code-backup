"""Verify new review routing and known stale-reason regressions on actual logs.
Runs the exact reviewer bout loop; original task quality computation untouched.
"""
from pathlib import Path
import ast,json,hashlib,datetime,sys,collections
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));P=W/'rear_early_edge_physical_preparation_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
from watch_rear_early_edge_trial1_numeric_reviews_r1 import check
routing=check();assert routing['passed']
reviewer=W/'review_rear_early_edge_trial1_v1_stage_episode.py';nodes=list(ast.walk(ast.parse(reviewer.read_text())));loop=next(n for n in nodes if isinstance(n,ast.For) and ast.unparse(n.target)=='row' and ast.unparse(n.iter)=='rows');last=next(n for n in nodes if isinstance(n,ast.If) and ast.unparse(n.test)=='current is not None' and 'episode_end' in ast.unparse(n));code=compile(ast.fix_missing_locations(ast.Module(body=[loop,last],type_ignores=[])),str(reviewer),'exec')
cases=[('front_box_trailing_physical_r1',840023,'push_box_to_bin',4,0,1),('front_box_trailing_physical_r2',840023,'push_box_to_bin',9,0,0),('front_box_trailing_physical_r2',840022,'push_box_to_bin',4,0,1),('front_box_trailing_physical_r2',840020,'nudge_mailer_to_bin',0,6,1),('front_box_trailing_physical_r2',840020,'push_box_to_bin',7,2,0),('front_loaded_z_quarter_physical_r2',840022,'push_box_to_bin',4,0,1),('front_loaded_z_quarter_physical_r2',840022,'nudge_mailer_to_bin',0,4,0)]
records=[];sources=dict(routing['source_sha256']);sources[str(reviewer)]=sha(reviewer)
for run,layout,task,tilt,lost,release in cases:
 p=W/run/f'case_{layout}'/f'layout_{layout}_{task}'/'frontal_bypass.json';data=json.loads(p.read_text());env=dict(rows=data['rows'],bouts=[],current=None);exec(code,env);counts=collections.Counter(x['exit_reason'] for x in env['bouts']);assert (counts['incipient_tilt_independent'],counts['lost_contact'],counts['normal_release'])==(tilt,lost,release),(str(p),dict(counts));sources[str(p)]=sha(p);records.append(dict(episode=str(p.parent),true_exit_counts=dict(counts),expected_known_regression_passed=True))
for p,h in sources.items():assert sha(p)==h
sources[str(Path(__file__))]=sha(__file__)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,routing=routing,actual_regression_cases=records,source_sha256=sources,quality_gates_changed=False,physical_review_executed=False,simulation_started=False,training_ready=False)
with (P/'REVIEW_ROUTE_AND_EXIT_COUNT_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,actual_exit_cases=len(records),routing_invalid_rejected=routing['invalid_marker_rejections'])))
